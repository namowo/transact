from typing import Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, field_validator, model_validator


class ChecklistItem(BaseModel):
    # Stable id, so a study's ticks and notes survive renaming or moving the
    # item. New items may omit it; the server assigns one.
    id: Optional[str] = Field(default=None, max_length=64)
    text: str = Field(max_length=500)


class ChecklistSection(BaseModel):
    title: str = Field(max_length=200)
    items: list[ChecklistItem] = Field(default_factory=list, max_length=100)

    @field_validator("title")
    @classmethod
    def _title(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Every section needs a title.")
        return value

    @field_validator("items")
    @classmethod
    def _items(cls, items: list[ChecklistItem]) -> list[ChecklistItem]:
        # Empty items are dropped rather than rejected - they're usually a
        # row the editor added but didn't fill in.
        return [
            ChecklistItem(id=item.id, text=item.text.strip()) for item in items if item.text.strip()
        ]


class PlanningChecklistUpdate(BaseModel):
    sections: list[ChecklistSection] = Field(max_length=50)

    @model_validator(mode="after")
    def _ids(self) -> "PlanningChecklistUpdate":
        seen: set[str] = set()
        for section in self.sections:
            for item in section.items:
                if not item.id or item.id in seen:
                    item.id = uuid4().hex
                seen.add(item.id)
        return self


class PlanningChecklistProgress(BaseModel):
    """What a study has ticked off, and its notes per item."""

    checked: list[str] = Field(default_factory=list, max_length=5000)
    notes: dict[str, str] = Field(default_factory=dict)

    @field_validator("notes")
    @classmethod
    def _notes(cls, notes: dict[str, str]) -> dict[str, str]:
        cleaned = {key: value.strip() for key, value in notes.items() if value and value.strip()}
        if any(len(value) > 2000 for value in cleaned.values()):
            raise ValueError("Notes can be at most 2000 characters long.")
        return cleaned


class PlanningChecklistRead(PlanningChecklistProgress):
    laboratory_id: Optional[UUID] = None
    sections: list[ChecklistSection]
    # True while the laboratory hasn't saved its own checklist.
    is_default: bool
    # Whether the current user may edit this laboratory's checklist.
    can_edit: bool = False
    # Whether the current user may tick items off for this study.
    can_check: bool = False
