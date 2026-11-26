"""Snapshots of a study's data, and the differences between two of them.

A snapshot is plain JSON, taken when a study is submitted for quality
review (see `app.models.study_review`), so quality checkers can see what
changed from one review round to the next:

    {"version": 1, "sections": {
        "<section>": {
            "fields": {"<field key>": "<field label>", ...},
            "rows": {"<record id>": {"label": "...", "values": {"<field key>": value}}},
        }, ...}}

Field labels are stored with the snapshot, so old snapshots still read
correctly after the download catalog changes.

The data-entry sections reuse the download catalog
(`app.services.data_export.fields`), but only with the fields of each
section's own tables: a result row there also carries its sample, contact
and scenario, and a changed contact would otherwise show up as a change of
every result.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Any, Callable, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.study import Study
from app.services.data_export.fields import get_dataset

SNAPSHOT_VERSION = 1


@dataclass(frozen=True)
class Section:
    key: str
    label: str


# In the order the study page shows them. "general" is for comments on the
# study as a whole and has no data of its own.
GENERAL = Section("general", "General")
SECTIONS: tuple[Section, ...] = (
    Section("details", "Study details"),
    Section("scenarios", "Scenarios"),
    Section("individuals", "Individuals"),
    Section("items", "Items"),
    Section("contacts", "Contacts"),
    Section("results", "Samples & results"),
    Section("pcr", "PCR profiles"),
    Section("contributors", "Mixture contributors"),
)
COMMENT_SECTIONS: tuple[Section, ...] = (GENERAL, *SECTIONS)
SECTION_KEYS = {s.key for s in COMMENT_SECTIONS}
SECTION_LABELS = {s.key: s.label for s in COMMENT_SECTIONS}


@dataclass(frozen=True)
class _DatasetSection:
    key: str
    dataset: str
    # Table labels (Field.group) whose fields belong to the section.
    groups: tuple[str, ...]
    # Fields joined into a row's label.
    label_fields: tuple[str, ...]
    label_suffix: str = ""
    # Builds the label from the label fields' values instead of joining them.
    label_format: Optional[Callable[..., str]] = None


def _individual_label(name, sex, age) -> str:
    details = ", ".join(str(p) for p in (sex, f"{age}y" if age is not None else None) if p)
    return f"{name or 'Individual'}{f' ({details})' if details else ''}"


_DATASET_SECTIONS: tuple[_DatasetSection, ...] = (
    _DatasetSection(
        "individuals",
        "individuals",
        ("Individual",),
        ("individual.name", "individual.sex", "individual.age"),
        label_format=_individual_label,
    ),
    _DatasetSection(
        "contacts",
        "contacts",
        ("Contact", "Conditions during contact", "Donor surface", "Recipient surface"),
        ("contact.name",),
    ),
    _DatasetSection(
        "results",
        "results",
        ("Sample", "Sampling method", "Extraction method", "Sampled surface", "Result", "Quantification method"),
        ("sample.name",),
    ),
    _DatasetSection(
        "pcr",
        "pcr_profiles",
        ("PCR", "PCR method", "CE method", "EPG analysis", "EPG interpretation"),
        ("sample.name",),
        " (PCR)",
    ),
    _DatasetSection("contributors", "pcr_contributors", ("Contributor",), ("sample.name", "contributor.label")),
)


def _json_value(value: Any) -> Any:
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, timedelta):
        return value.total_seconds()
    if isinstance(value, float) and value.is_integer():
        return int(value)
    return value


def _join_label(*parts: Any) -> str:
    texts = dict.fromkeys(str(p) for p in parts if p not in (None, ""))
    return " · ".join(texts) or "(unnamed)"


async def _dataset_section(db: AsyncSession, study_id: UUID, spec: _DatasetSection) -> dict:
    dataset = get_dataset(spec.dataset)
    assert dataset is not None, spec.dataset
    fields = [
        f for f in dataset.fields if f.group in spec.groups and not f.key.endswith(".id")
    ]
    label_fields = [dataset.get(key) for key in spec.label_fields]
    used = {f.table for f in (*fields, *label_fields)}
    stmt = (
        select(
            dataset.row_id.label("row_id"),
            *(f.expr.label(f"l{i}") for i, f in enumerate(label_fields)),
            *(f.expr.label(f"c{i}") for i, f in enumerate(fields)),
        )
        .select_from(dataset.from_clause(dataset.resolve_tables(used)))
        .where(dataset.study_id == study_id)
    )
    rows: dict[str, dict] = {}
    for row in (await db.execute(stmt)).mappings():
        label_values = [row[f"l{i}"] for i in range(len(label_fields))]
        label = (spec.label_format or _join_label)(*label_values)
        rows[str(row["row_id"])] = {
            "label": label + spec.label_suffix,
            "values": {f.key: _json_value(row[f"c{i}"]) for i, f in enumerate(fields)},
        }
    return {"fields": {f.key: f.label for f in fields}, "rows": rows}


def _section(fields: dict[str, str], rows: dict[str, dict]) -> dict:
    return {"fields": fields, "rows": rows}


def _details_section(study: Study) -> dict:
    fields = {
        "title": "Title",
        "description": "Description",
        "authors": "Authors",
        "year": "Year",
        "journal": "Journal",
        "doi": "DOI",
        "abstract": "Abstract",
        "corresponding_author_name": "Corresponding author",
        "corresponding_author_email": "Corresponding author email",
        "corresponding_author_phone": "Corresponding author phone",
        "purpose": "Purpose",
        "laboratory": "Laboratory",
    }
    authors = ", ".join(
        " ".join(p for p in (a.title, a.first_name, a.last_name) if p) for a in study.authors
    )
    purpose = (
        "Plan a transfer experiment"
        if study.plan_a_transfer_experiment
        else "Add data to repository"
        if study.add_data_to_repository
        else None
    )
    values = {
        "title": study.title,
        "description": study.description,
        "authors": authors or None,
        "year": study.year,
        "journal": study.journal,
        "doi": study.doi,
        "abstract": study.abstract,
        "corresponding_author_name": study.corresponding_author_name,
        "corresponding_author_email": study.corresponding_author_email,
        "corresponding_author_phone": study.corresponding_author_phone,
        "purpose": purpose,
        "laboratory": study.laboratory.laboratory_name if study.laboratory else None,
    }
    return _section(fields, {str(study.id): {"label": "Study", "values": values}})


def _names(objects) -> Optional[str]:
    names = sorted(o.name for o in objects if o.name)
    return "; ".join(names) or None


def _scenarios_section(study: Study) -> dict:
    fields = {
        "name": "Name",
        "category": "Category",
        "realistic": "Realistic",
        "contact_templates": "Planned contacts",
        "persistencies": "Persistence",
    }
    rows = {
        str(sc.id): {
            "label": _join_label(sc.name),
            "values": {
                "name": sc.name,
                "category": sc.scenario_category.name if sc.scenario_category else None,
                "realistic": sc.realistic,
                "contact_templates": _names(sc.contact_templates),
                "persistencies": _names(sc.persistencies),
            },
        }
        for sc in study.scenarios
    }
    return _section(fields, rows)


def _items_section(study: Study) -> dict:
    fields = {
        "category": "Category",
        "subcategory": "Subcategory",
        "description": "Description",
        "scenarios": "Scenarios",
    }
    rows = {}
    for item in study.items:
        category = item.item_category.name if item.item_category else None
        subcategory = item.item_subcategory.name if item.item_subcategory else None
        rows[str(item.id)] = {
            "label": _join_label(subcategory or category, item.description),
            "values": {
                "category": category,
                "subcategory": subcategory,
                "description": item.description,
                "scenarios": _names(item.scenarios),
            },
        }
    return _section(fields, rows)


async def take_snapshot(db: AsyncSession, study_id: UUID) -> dict:
    """The study's current data, as stored with a review round."""
    study = (
        await db.execute(
            select(Study).where(Study.id == study_id).execution_options(populate_existing=True)
        )
    ).scalar_one()
    sections = {
        "details": _details_section(study),
        "scenarios": _scenarios_section(study),
        "items": _items_section(study),
    }
    for spec in _DATASET_SECTIONS:
        sections[spec.key] = await _dataset_section(db, study_id, spec)
    return {"version": SNAPSHOT_VERSION, "sections": sections}


def _field_changes(fields: dict[str, str], old: dict, new: dict) -> list[dict]:
    changes = []
    for key in dict.fromkeys([*fields, *old, *new]):
        before, after = old.get(key), new.get(key)
        if before != after:
            changes.append({"key": key, "label": fields.get(key, key), "old": before, "new": after})
    return changes


def diff_snapshots(old: dict, new: dict) -> list[dict]:
    """Per section, the records added, removed or changed from `old` to
    `new`, with old and new value of each changed field."""
    old_sections = old.get("sections", {})
    new_sections = new.get("sections", {})
    result = []
    for section in SECTIONS:
        before = old_sections.get(section.key, {})
        after = new_sections.get(section.key, {})
        fields = {**before.get("fields", {}), **after.get("fields", {})}
        old_rows, new_rows = before.get("rows", {}), after.get("rows", {})
        rows = []
        for row_id in dict.fromkeys([*old_rows, *new_rows]):
            was, now = old_rows.get(row_id), new_rows.get(row_id)
            if was is None:
                change = "added"
            elif now is None:
                change = "removed"
            else:
                change = "changed"
            changes = _field_changes(
                fields, (was or {}).get("values", {}), (now or {}).get("values", {})
            )
            if change == "changed" and not changes:
                continue
            rows.append(
                {
                    "id": row_id,
                    "label": (now or was)["label"],
                    "change": change,
                    "fields": changes,
                }
            )
        rows.sort(key=lambda r: (r["label"].lower(), r["id"]))
        result.append(
            {
                "key": section.key,
                "label": section.label,
                "added": sum(r["change"] == "added" for r in rows),
                "removed": sum(r["change"] == "removed" for r in rows),
                "changed": sum(r["change"] == "changed" for r in rows),
                "rows": rows,
            }
        )
    return result


def snapshot_records(snapshot: dict) -> dict[str, list[dict]]:
    """Per section, the records a comment can be pinned to: id and label."""
    return {
        key: sorted(
            ({"id": row_id, "label": row["label"]} for row_id, row in section.get("rows", {}).items()),
            key=lambda r: r["label"].lower(),
        )
        for key, section in snapshot.get("sections", {}).items()
    }
