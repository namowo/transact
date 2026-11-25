"""Each laboratory's planning checklist, falling back to a default one.

Lab admins can replace the default with their own sections; the checklist
modal and the Excel planning sheet both show the study laboratory's
checklist.
"""

import hashlib
from typing import Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.permission_catalog import Permission
from app.models.planning_checklist import PlanningChecklist
from app.models.study_checklist_progress import StudyChecklistProgress
from app.models.user import User

def _section(title: str, items: list[tuple[str, str]]) -> dict:
    return {"title": title, "items": [{"id": id, "text": text} for id, text in items]}


# Item ids are fixed so studies keep their ticks if a laboratory later
# customises the checklist starting from these items.
DEFAULT_SECTIONS: list[dict] = [
    _section(
        "Ethics",
        [
            ("ethics-approval", "Ethics approval obtained / application submitted"),
            ("ethics-consent", "Informed consent form prepared"),
            ("ethics-privacy", "Data protection / privacy assessment completed"),
        ],
    ),
    _section(
        "Instructions for participants",
        [
            ("instructions-drafted", "Written instructions drafted"),
            ("instructions-reviewed", "Instructions reviewed by a second person"),
            ("instructions-translated", "Instructions translated, if needed"),
        ],
    ),
    _section(
        "Data to collect from individuals",
        [
            ("individuals-demographics", "Demographic information (age, sex, etc.)"),
            (
                "individuals-habits",
                "Relevant habits/behaviour (e.g. handwashing, activity before sampling)",
            ),
            ("individuals-consent", "Consent and withdrawal documentation"),
        ],
    ),
    _section(
        "Timeline",
        [
            ("timeline-recruitment", "Recruitment period"),
            ("timeline-sampling", "Sampling date(s)"),
            ("timeline-analysis", "Analysis/processing deadline"),
        ],
    ),
    _section(
        "Similar studies",
        [
            ("similar-literature", "Literature search for comparable scenarios completed"),
            ("similar-reviewed", "Relevant studies listed and reviewed"),
        ],
    ),
]


def _normalize(sections: list[dict]) -> list[dict]:
    """Checklists saved before items had ids stored plain strings."""
    normalized = []
    for section in sections:
        items = []
        for item in section.get("items", []):
            if isinstance(item, str):
                digest = hashlib.sha1(f"{section.get('title')}\n{item}".encode()).hexdigest()
                item = {"id": f"legacy-{digest[:12]}", "text": item}
            items.append(item)
        normalized.append({"title": section.get("title", ""), "items": items})
    return normalized


def item_ids(sections: list[dict]) -> set[str]:
    return {item["id"] for section in sections for item in section["items"]}


def can_edit_checklist(user: Optional[User], laboratory_id: Optional[UUID]) -> bool:
    if user is None or laboratory_id is None:
        return False
    return user.can_in_laboratory(Permission.MANAGE_LAB_SETTINGS, laboratory_id)


async def get_sections(
    db: AsyncSession, laboratory_id: Optional[UUID]
) -> tuple[list[dict], bool]:
    """The laboratory's checklist sections and whether they're the default."""
    if laboratory_id is not None:
        checklist = await db.get(PlanningChecklist, laboratory_id)
        if checklist is not None:
            return _normalize(checklist.sections), False
    return DEFAULT_SECTIONS, True


async def save_sections(db: AsyncSession, laboratory_id: UUID, sections: list[dict]) -> None:
    checklist = await db.get(PlanningChecklist, laboratory_id)
    if checklist is None:
        db.add(PlanningChecklist(laboratory_id=laboratory_id, sections=sections))
    else:
        checklist.sections = sections
    await db.commit()


async def reset_sections(db: AsyncSession, laboratory_id: UUID) -> None:
    checklist = await db.get(PlanningChecklist, laboratory_id)
    if checklist is not None:
        await db.delete(checklist)
        await db.commit()


async def get_progress(db: AsyncSession, study_id: UUID) -> tuple[list[str], dict[str, str]]:
    progress = await db.get(StudyChecklistProgress, study_id)
    if progress is None:
        return [], {}
    return list(progress.checked), dict(progress.notes)


async def save_progress(
    db: AsyncSession,
    study_id: UUID,
    laboratory_id: Optional[UUID],
    checked: list[str],
    notes: dict[str, str],
) -> tuple[list[str], dict[str, str]]:
    """Store a study's ticks and notes, keeping only items of its checklist."""
    sections, _ = await get_sections(db, laboratory_id)
    known = item_ids(sections)
    checked = [id for id in dict.fromkeys(checked) if id in known]
    notes = {id: note for id, note in notes.items() if id in known}
    progress = await db.get(StudyChecklistProgress, study_id)
    if progress is None:
        db.add(StudyChecklistProgress(study_id=study_id, checked=checked, notes=notes))
    else:
        progress.checked = checked
        progress.notes = notes
    await db.commit()
    return checked, notes
