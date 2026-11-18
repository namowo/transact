from datetime import datetime
from typing import Any, Literal, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

FilterOp = Literal[
    "eq",
    "neq",
    "in",
    "not_in",
    "contains",
    "gt",
    "gte",
    "lt",
    "lte",
    "between",
    "is_null",
    "not_null",
]

MAX_COLUMNS = 200
MAX_FILTERS = 50


class DataModelFilter(BaseModel):
    field: str
    op: FilterOp
    value: Any = None


class DataModelSort(BaseModel):
    field: str
    dir: Literal["asc", "desc"] = "asc"


class DataModelDefinition(BaseModel):
    """What a data model downloads. Field keys are validated against the
    dataset's catalog when the model is run or saved."""

    dataset: str
    # Optional tables to join onto the rows, by key. Required tables are
    # always joined, and a table's own requirements are joined with it.
    # None (older models and share links): inferred from the fields used.
    joins: Optional[list[str]] = Field(default=None, max_length=50)
    columns: list[str] = Field(min_length=1, max_length=MAX_COLUMNS)
    filters: list[DataModelFilter] = Field(default_factory=list, max_length=MAX_FILTERS)
    # None: all studies available to the viewer.
    study_ids: Optional[list[UUID]] = None
    sort: list[DataModelSort] = Field(default_factory=list, max_length=10)


class DataModelBase(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    description: Optional[str] = Field(default=None, max_length=5000)
    definition: DataModelDefinition
    is_public: bool = False


class DataModelCreate(DataModelBase):
    pass


class DataModelUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=200)
    description: Optional[str] = Field(default=None, max_length=5000)
    definition: Optional[DataModelDefinition] = None
    is_public: Optional[bool] = None


DataModelSource = Literal["preset", "public", "mine"]


class DataModelRead(DataModelBase):
    model_config = ConfigDict(from_attributes=True)

    # A UUID for saved models, "preset-..." for predefined ones.
    id: str
    source: DataModelSource
    owner_name: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


# --- Catalog -----------------------------------------------------------------


class CatalogTable(BaseModel):
    key: str
    label: str
    description: str
    requires: list[str]
    required: bool


class CatalogField(BaseModel):
    key: str
    label: str
    group: str
    table: str
    type: str
    description: Optional[str] = None
    unit: Optional[str] = None


class CatalogDataset(BaseModel):
    key: str
    label: str
    description: str
    default_sort: list[str]
    tables: list[CatalogTable]
    fields: list[CatalogField]


class Catalog(BaseModel):
    datasets: list[CatalogDataset]
    operators: dict[str, list[FilterOp]]


class DownloadableStudy(BaseModel):
    id: UUID
    title: str
    year: Optional[str] = None
    laboratory_name: Optional[str] = None
    # False for the viewer's own laboratory's unpublished or unchecked
    # studies, which only they can download.
    published: bool


# --- Preview -----------------------------------------------------------------


class PreviewColumn(BaseModel):
    key: str
    label: str
    type: str
    unit: Optional[str] = None


class DataModelPreview(BaseModel):
    columns: list[PreviewColumn]
    rows: list[list[Any]]
    total_rows: int
    study_count: int
