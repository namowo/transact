"""Write a data model's rows as CSV or Excel."""

from __future__ import annotations

import csv
import io
import re
from datetime import date, datetime, timezone
from decimal import Decimal
from tempfile import SpooledTemporaryFile
from typing import Any, AsyncIterator, Iterable, Literal, Optional
from uuid import UUID

from openpyxl import Workbook
from openpyxl.cell import WriteOnlyCell
from openpyxl.styles import Font
from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.study import Study
from app.schemas.data_model import DataModelDefinition
from app.services.data_export.fields import Field, get_dataset

HeaderStyle = Literal["label", "key"]

# Excel's sheet limit is 1,048,576 rows, one of which is the header.
XLSX_MAX_ROWS = 1_048_575
_FLUSH_EVERY = 500
_STREAM_PARTITION = 1000

OP_LABELS = {
    "eq": "is",
    "neq": "is not",
    "in": "is one of",
    "not_in": "is none of",
    "contains": "contains",
    "gt": ">",
    "gte": "≥",
    "lt": "<",
    "lte": "≤",
    "between": "between",
    "is_null": "is empty",
    "not_null": "is not empty",
}


def header(field: Field, style: HeaderStyle) -> str:
    if style == "key":
        return field.key
    return f"{field.label} ({field.unit})" if field.unit else field.label


def export_filename(name: str, extension: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")[:60] or "data"
    return f"transact-{slug}-{date.today().isoformat()}.{extension}"


def _csv_value(value: Any) -> Any:
    if value is None:
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return value


def _xlsx_value(value: Any) -> Any:
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, datetime) and value.tzinfo is not None:
        # Excel has no time zones; export as UTC.
        return value.astimezone(timezone.utc).replace(tzinfo=None)
    return value


async def stream_csv(
    db: AsyncSession, stmt: Select, columns: list[Field], style: HeaderStyle = "label"
) -> AsyncIterator[bytes]:
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    # A BOM makes Excel read the file as UTF-8 (µ, °, umlauts).
    buffer.write("\ufeff")
    writer.writerow(header(f, style) for f in columns)

    result = await db.stream(stmt.execution_options(yield_per=_STREAM_PARTITION))
    count = 0
    async for row in result:
        writer.writerow(_csv_value(v) for v in row)
        count += 1
        if count % _FLUSH_EVERY == 0:
            yield buffer.getvalue().encode("utf-8")
            buffer.seek(0)
            buffer.truncate()
    yield buffer.getvalue().encode("utf-8")


def describe_filters(definition: DataModelDefinition) -> list[str]:
    dataset = get_dataset(definition.dataset)
    lines = []
    for flt in definition.filters:
        field = dataset.get(flt.field) if dataset else None
        label = field.label if field else flt.field
        op = OP_LABELS.get(flt.op, flt.op)
        if flt.op in ("is_null", "not_null"):
            lines.append(f"{label} {op}")
        elif isinstance(flt.value, list):
            joiner = " and " if flt.op == "between" else ", "
            lines.append(f"{label} {op} {joiner.join('…' if v is None else str(v) for v in flt.value)}")
        else:
            lines.append(f"{label} {op} {flt.value}")
    return lines


async def _studies(db: AsyncSession, study_ids: Iterable[UUID]) -> list[Study]:
    ids = list(study_ids)
    if not ids:
        return []
    result = await db.execute(
        select(Study).where(Study.id.in_(ids)).order_by(Study.year, Study.title)
    )
    return list(result.scalars())


def _bold(ws, value: Any) -> WriteOnlyCell:
    cell = WriteOnlyCell(ws, value=value)
    cell.font = Font(bold=True)
    return cell


async def build_xlsx(
    db: AsyncSession,
    stmt: Select,
    columns: list[Field],
    *,
    name: str,
    definition: DataModelDefinition,
    study_ids: Iterable[UUID],
    source_url: Optional[str] = None,
    style: HeaderStyle = "label",
) -> SpooledTemporaryFile:
    """An .xlsx with a data sheet and an "About" sheet describing the model
    and listing the studies the rows come from, for citation."""
    workbook = Workbook(write_only=True)
    data = workbook.create_sheet("Data")
    data.append([_bold(data, header(f, style)) for f in columns])

    truncated = False
    count = 0
    result = await db.stream(stmt.execution_options(yield_per=_STREAM_PARTITION))
    async for row in result:
        if count >= XLSX_MAX_ROWS:
            truncated = True
            break
        data.append([_xlsx_value(v) for v in row])
        count += 1

    about = workbook.create_sheet("About")
    dataset = get_dataset(definition.dataset)
    about.append([_bold(about, "TransAct data export")])
    about.append(["Data model", name])
    about.append(["Dataset", dataset.label if dataset else definition.dataset])
    about.append(["Generated", datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")])
    about.append(["Rows", count])
    if source_url:
        about.append(["Source", source_url])
    if truncated:
        about.append(
            ["Note", f"Truncated to Excel's limit of {XLSX_MAX_ROWS:,} rows. Download as CSV for all rows."]
        )
    filters = describe_filters(definition)
    about.append([])
    about.append([_bold(about, "Filters")])
    for line in filters or ["None"]:
        about.append([line])

    about.append([])
    about.append([_bold(about, "Please cite the studies this data comes from")])
    about.append([_bold(about, h) for h in ("Title", "Authors", "Year", "Journal", "DOI", "Laboratory")])
    for study in await _studies(db, study_ids):
        authors = ", ".join(
            " ".join(p for p in (a.first_name, a.last_name) if p) for a in study.authors
        )
        about.append(
            [
                study.title,
                authors,
                study.year,
                study.journal,
                study.doi,
                study.laboratory.laboratory_name if study.laboratory else None,
            ]
        )

    out = SpooledTemporaryFile(max_size=16 * 1024 * 1024)
    workbook.save(out)
    out.seek(0)
    return out


def iter_file(file, chunk_size: int = 64 * 1024):
    try:
        while chunk := file.read(chunk_size):
            yield chunk
    finally:
        file.close()
