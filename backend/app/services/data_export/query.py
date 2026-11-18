"""Turns a data model definition into SQL.

Everything a definition names is resolved through the dataset catalog in
`fields.py`; anything unknown is rejected with a `DefinitionError` before a
query is built. Every query is restricted to the studies the viewer may
download (see `visible_study_ids`).
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Any, Optional

from sqlalchemy import Select, and_, distinct, func, or_, select
from sqlalchemy.orm import aliased
from sqlalchemy.sql.elements import ColumnElement

from app.models.study import Study
from app.models.user import User
from app.schemas.data_model import DataModelDefinition, DataModelFilter, FilterOp
from app.services.data_export.fields import Dataset, Field, Table, get_dataset

OPERATORS: dict[str, list[FilterOp]] = {
    "string": ["contains", "eq", "neq", "in", "not_in", "is_null", "not_null"],
    "category": ["in", "not_in", "eq", "neq", "contains", "is_null", "not_null"],
    "number": ["eq", "neq", "gt", "gte", "lt", "lte", "between", "is_null", "not_null"],
    "boolean": ["eq", "is_null", "not_null"],
    "date": ["gt", "gte", "lt", "lte", "between", "is_null", "not_null"],
}

MAX_IN_VALUES = 1000


class DefinitionError(ValueError):
    """The definition references something the catalog doesn't offer, or a
    filter value doesn't fit its field."""


def visible_study_ids(user: Optional[User]) -> Select:
    """Studies whose data `user` may download: published studies that passed
    quality check, plus - for signed-in users - every study of their own
    laboratory. Superusers get nothing extra; their powers cover the
    platform, not other laboratories' research data."""
    study = aliased(Study)
    public = and_(study.published.is_(True), study.quality_check_passed.is_(True))
    condition = public
    if user is not None and user.laboratory_id is not None:
        condition = or_(public, study.laboratory_id == user.laboratory_id)
    return select(study.id).where(condition)


def resolve_dataset(definition: DataModelDefinition) -> Dataset:
    dataset = get_dataset(definition.dataset)
    if dataset is None:
        raise DefinitionError(f"Unknown dataset '{definition.dataset}'.")
    return dataset


def _field(dataset: Dataset, key: str) -> Field:
    found = dataset.get(key)
    if found is None:
        raise DefinitionError(f"Unknown field '{key}' for dataset '{dataset.key}'.")
    return found


def resolve_columns(dataset: Dataset, definition: DataModelDefinition) -> list[Field]:
    if len(set(definition.columns)) != len(definition.columns):
        raise DefinitionError("Each column may be selected only once.")
    return [_field(dataset, key) for key in definition.columns]


def _coerce(field: Field, value: Any) -> Any:
    if value is None:
        raise DefinitionError(f"Filter on '{field.key}' needs a value.")
    try:
        if field.type == "number":
            if isinstance(value, bool):
                raise ValueError
            return float(value)
        if field.type == "boolean":
            if isinstance(value, bool):
                return value
            if str(value).lower() in ("true", "1", "yes"):
                return True
            if str(value).lower() in ("false", "0", "no"):
                return False
            raise ValueError
        if field.type == "date":
            if isinstance(value, (date, datetime)):
                return value
            return datetime.fromisoformat(str(value))
        if isinstance(value, (dict, list)):
            raise ValueError
        return str(value)
    except (TypeError, ValueError):
        raise DefinitionError(
            f"Invalid value {value!r} for filter on '{field.key}' ({field.type})."
        ) from None


def _as_list(field: Field, value: Any) -> list[Any]:
    if not isinstance(value, list) or not value:
        raise DefinitionError(f"Filter on '{field.key}' needs a non-empty list of values.")
    if len(value) > MAX_IN_VALUES:
        raise DefinitionError(f"Filter on '{field.key}' has too many values.")
    return [_coerce(field, item) for item in value]


def compile_filter(dataset: Dataset, flt: DataModelFilter) -> ColumnElement:
    field = _field(dataset, flt.field)
    if flt.op not in OPERATORS[field.type]:
        raise DefinitionError(
            f"Operator '{flt.op}' is not available for '{field.key}' ({field.type})."
        )
    expr = field.expr
    op = flt.op
    if op == "is_null":
        return expr.is_(None)
    if op == "not_null":
        return expr.is_not(None)
    if op == "in":
        return expr.in_(_as_list(field, flt.value))
    if op == "not_in":
        # NULLs are "not in" any list, which SQL's NOT IN would drop.
        return or_(expr.is_(None), expr.not_in(_as_list(field, flt.value)))
    if op == "between":
        bounds = flt.value
        if not isinstance(bounds, list) or len(bounds) != 2:
            raise DefinitionError(f"Filter on '{field.key}' needs [from, to].")
        low, high = (_coerce(field, b) if b is not None else None for b in bounds)
        if low is None and high is None:
            raise DefinitionError(f"Filter on '{field.key}' needs at least one bound.")
        parts = []
        if low is not None:
            parts.append(expr >= low)
        if high is not None:
            parts.append(expr <= high)
        return and_(*parts)
    if op == "contains":
        text = _coerce(field, flt.value)
        escaped = text.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        return expr.ilike(f"%{escaped}%", escape="\\")
    value = _coerce(field, flt.value)
    if op == "eq":
        return expr == value
    if op == "neq":
        return or_(expr.is_(None), expr != value)
    return {
        "gt": expr > value,
        "gte": expr >= value,
        "lt": expr < value,
        "lte": expr <= value,
    }[op]


def _used_fields(dataset: Dataset, definition: DataModelDefinition) -> list[Field]:
    keys = [*definition.columns, *(f.field for f in definition.filters), *(s.field for s in definition.sort)]
    return [_field(dataset, key) for key in keys]


def resolve_tables(dataset: Dataset, definition: DataModelDefinition) -> list[Table]:
    """The tables to join: the definition's joins (or, for definitions
    without any, the tables its fields come from), everything those
    require, and the required tables. Every field used must come from one
    of them."""
    used = _used_fields(dataset, definition)
    if definition.joins is None:
        requested = [f.table for f in used]
    else:
        unknown = [key for key in definition.joins if dataset.get_table(key) is None]
        if unknown:
            raise DefinitionError(f"Unknown table '{unknown[0]}' for dataset '{dataset.key}'.")
        requested = definition.joins
    tables = dataset.resolve_tables(requested)
    joined = {t.key for t in tables}
    for field in used:
        if field.table not in joined:
            raise DefinitionError(
                f"'{field.label}' comes from the table '{field.group}', which isn't joined."
            )
    return tables


def normalize_definition(definition: DataModelDefinition) -> DataModelDefinition:
    """The definition with its joins spelled out: the optional tables it
    uses, including ones only required by others. Older definitions without
    joins get them inferred."""
    dataset = get_dataset(definition.dataset)
    if dataset is None:
        return definition
    try:
        tables = resolve_tables(dataset, definition)
    except (DefinitionError, KeyError):
        return definition
    return definition.model_copy(
        update={"joins": [t.key for t in tables if not t.required]}
    )


def _where(dataset: Dataset, definition: DataModelDefinition, user: Optional[User]):
    conditions = [dataset.study_id.in_(visible_study_ids(user))]
    if definition.study_ids is not None:
        conditions.append(dataset.study_id.in_(definition.study_ids))
    conditions.extend(compile_filter(dataset, flt) for flt in definition.filters)
    return conditions


def _from(dataset: Dataset, definition: DataModelDefinition):
    return dataset.from_clause(resolve_tables(dataset, definition))


def validate_definition(definition: DataModelDefinition) -> None:
    """Raise `DefinitionError` if the definition can't be run. Used when
    saving, so broken models are never stored."""
    dataset = resolve_dataset(definition)
    resolve_columns(dataset, definition)
    for flt in definition.filters:
        compile_filter(dataset, flt)
    resolve_tables(dataset, definition)


def build_select(
    definition: DataModelDefinition,
    user: Optional[User],
    *,
    limit: Optional[int] = None,
) -> tuple[Select, list[Field]]:
    """The query returning the definition's rows, and the fields of its
    columns in order."""
    dataset = resolve_dataset(definition)
    columns = resolve_columns(dataset, definition)
    stmt = (
        select(*(f.expr.label(f"c{i}") for i, f in enumerate(columns)))
        .select_from(_from(dataset, definition))
        .where(*_where(dataset, definition, user))
    )
    # Default sorts only apply when their fields' tables are joined.
    joined = {t.key for t in resolve_tables(dataset, definition)}
    sorts = [(s.field, s.dir) for s in definition.sort] or [
        (key, "asc")
        for key in dataset.default_sort
        if dataset.get(key) is not None and dataset.get(key).table in joined
    ]
    order = []
    for key, direction in sorts:
        expr = _field(dataset, key).expr
        order.append(expr.desc().nulls_last() if direction == "desc" else expr.asc().nulls_last())
    # A unique tie-breaker keeps the row order stable between downloads.
    order.append(dataset.row_id)
    stmt = stmt.order_by(*order)
    if limit is not None:
        stmt = stmt.limit(limit)
    return stmt, columns


def build_counts(definition: DataModelDefinition, user: Optional[User]) -> Select:
    """Number of rows and of distinct studies the definition returns."""
    dataset = resolve_dataset(definition)
    return (
        select(func.count(), func.count(distinct(dataset.study_id)))
        .select_from(_from(dataset, definition))
        .where(*_where(dataset, definition, user))
    )


def build_study_ids(definition: DataModelDefinition, user: Optional[User]) -> Select:
    """The ids of the studies the definition's rows come from."""
    dataset = resolve_dataset(definition)
    return (
        select(dataset.study_id)
        .select_from(_from(dataset, definition))
        .where(*_where(dataset, definition, user))
        .distinct()
    )


def build_values(
    dataset: Dataset, field: Field, user: Optional[User], *, limit: int = 500
) -> Select:
    """Distinct values of a field across the viewer's visible studies, for
    filter pickers."""
    value = field.expr.label("value")
    return (
        select(value)
        .select_from(dataset.from_clause(dataset.resolve_tables([field.table])))
        .where(dataset.study_id.in_(visible_study_ids(user)), field.expr.is_not(None))
        .group_by(value)
        .order_by(value)
        .limit(limit)
    )


__all__ = [
    "OPERATORS",
    "DefinitionError",
    "build_counts",
    "build_select",
    "build_study_ids",
    "build_values",
    "compile_filter",
    "normalize_definition",
    "resolve_tables",
    "validate_definition",
    "visible_study_ids",
]
