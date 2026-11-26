from datetime import datetime
from typing import Any, Dict, List, Literal, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

ReviewStatusValue = Literal["draft", "in_review", "changes_requested", "passed"]
CommentStatusValue = Literal["open", "addressed", "resolved"]


class ReviewUser(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    first_name: str
    last_name: str


class ReviewSection(BaseModel):
    key: str
    label: str


class ReviewRecord(BaseModel):
    id: str
    label: str


class ReviewRoundRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    number: int
    submitted_at: datetime
    submitted_by: Optional[ReviewUser] = None
    decision: Optional[Literal["changes_requested", "passed"]] = None
    decided_at: Optional[datetime] = None
    decided_by: Optional[ReviewUser] = None


class ReviewReplyRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    body: str
    author: Optional[ReviewUser] = None
    created_at: datetime
    edited_at: Optional[datetime] = None


class ReviewCommentRead(ReviewReplyRead):
    round_number: Optional[int] = None
    section: str
    target_id: Optional[str] = None
    target_label: Optional[str] = None
    field_label: Optional[str] = None
    status: CommentStatusValue
    status_changed_at: Optional[datetime] = None
    status_changed_by: Optional[ReviewUser] = None
    replies: List[ReviewReplyRead] = []


class ReviewProgress(BaseModel):
    total: int = 0
    open: int = 0
    addressed: int = 0
    resolved: int = 0


class StudyReviewRead(BaseModel):
    study_id: UUID
    status: ReviewStatusValue
    rounds: List[ReviewRoundRead]
    comments: List[ReviewCommentRead]
    progress: ReviewProgress
    sections: List[ReviewSection]
    # Whether the current user may comment/decide as a quality checker, and
    # whether they may work on the study (reply, mark addressed, submit).
    can_review: bool
    can_respond: bool


class ReviewQueueEntry(BaseModel):
    study_id: UUID
    title: Optional[str] = None
    laboratory_name: Optional[str] = None
    year: Optional[str] = None
    status: ReviewStatusValue
    round_number: int
    submitted_at: Optional[datetime] = None
    progress: ReviewProgress


class CommentCreate(BaseModel):
    body: str = Field(min_length=1, max_length=10_000)
    section: str = "general"
    target_id: Optional[str] = Field(default=None, max_length=200)
    target_label: Optional[str] = Field(default=None, max_length=500)
    field_label: Optional[str] = Field(default=None, max_length=500)


class ReplyCreate(BaseModel):
    body: str = Field(min_length=1, max_length=10_000)


class CommentUpdate(BaseModel):
    body: Optional[str] = Field(default=None, min_length=1, max_length=10_000)
    status: Optional[CommentStatusValue] = None


class DiffFieldChange(BaseModel):
    key: str
    label: str
    old: Any = None
    new: Any = None


class DiffRow(BaseModel):
    id: str
    label: str
    change: Literal["added", "removed", "changed"]
    fields: List[DiffFieldChange]


class DiffSection(BaseModel):
    key: str
    label: str
    added: int
    removed: int
    changed: int
    rows: List[DiffRow]


class StudyReviewDiff(BaseModel):
    # Round numbers; `to_round` None means the study's current data.
    from_round: int
    to_round: Optional[int] = None
    sections: List[DiffSection]


class StudyReviewRecords(BaseModel):
    """Per section, the records a comment can be pinned to."""

    records: Dict[str, List[ReviewRecord]]
