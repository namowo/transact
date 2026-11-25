"""Data models: saved queries for downloading repository data.

Everything here works without an account. Guests download from studies
that are published and passed quality check; signed-in users additionally
get their own laboratory's studies. Saving models requires an account.
"""

from typing import Any, List, Literal, Optional
from uuid import UUID

from fastapi import APIRouter, Body, Depends, HTTPException, Query, Request, status
from fastapi.responses import StreamingResponse
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import noload

from app.core.deps import current_active_user, current_optional_user, get_async_session
from app.crud.data_model import crud_data_model as crud
from app.models.data_model import DataModel
from app.models.sample import Sample
from app.models.scenario import study_scenario
from app.models.study import Study
from app.models.user import User
from app.schemas.data_model import (
    Catalog,
    CatalogDataset,
    CatalogField,
    CatalogTable,
    DataModelCreate,
    DataModelDefinition,
    DataModelPreview,
    DataModelRead,
    DataModelUpdate,
    DownloadableStudy,
    PreviewColumn,
)
from app.services.data_export.fields import DATASETS, get_dataset
from app.services.data_export.presets import PRESETS, PRESETS_BY_ID, Preset
from app.services.data_export.query import (
    OPERATORS,
    DefinitionError,
    build_counts,
    build_select,
    build_study_ids,
    build_values,
    normalize_definition,
    validate_definition,
    visible_study_ids,
)
from app.services.data_export.writers import (
    HeaderStyle,
    attachment_headers,
    build_xlsx,
    export_filename,
    iter_file,
    stream_csv,
)

router = APIRouter()

PREVIEW_ROWS = 50
ExportFormat = Literal["csv", "xlsx"]

XLSX_MEDIA_TYPE = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


def _not_found() -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Data model not found.")


def _invalid(error: DefinitionError) -> HTTPException:
    return HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(error))


def _owner_name(model: DataModel) -> Optional[str]:
    owner = model.owner
    if owner is None:
        return None
    return " ".join(p for p in (owner.first_name, owner.last_name) if p) or None


def _read(model: DataModel, user: Optional[User]) -> DataModelRead:
    mine = user is not None and model.owner_id == user.id
    return DataModelRead(
        id=str(model.id),
        name=model.name,
        description=model.description,
        definition=normalize_definition(DataModelDefinition.model_validate(model.definition)),
        is_public=model.is_public,
        source="mine" if mine else "public",
        owner_name=_owner_name(model),
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


def _preset_read(preset: Preset) -> DataModelRead:
    return DataModelRead(
        id=preset.id,
        name=preset.name,
        description=preset.description,
        definition=normalize_definition(preset.definition),
        is_public=True,
        source="preset",
    )


async def _resolve(db: AsyncSession, id: str, user: Optional[User]) -> DataModelRead:
    """A preset, a public model, or one of the user's own."""
    if id in PRESETS_BY_ID:
        return _preset_read(PRESETS_BY_ID[id])
    try:
        model_id = UUID(id)
    except ValueError:
        raise _not_found() from None
    model = await crud.get(db, model_id)
    if model is None:
        raise _not_found()
    if not model.is_public and (user is None or model.owner_id != user.id):
        raise _not_found()
    return _read(model, user)


async def _own_model(db: AsyncSession, id: UUID, user: User) -> DataModel:
    model = await crud.get(db, id)
    if model is None or (not model.is_public and model.owner_id != user.id):
        raise _not_found()
    if model.owner_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only change your own data models.",
        )
    return model


def _narrow(
    definition: DataModelDefinition, study_ids: Optional[list[UUID]]
) -> DataModelDefinition:
    """Restrict a model to `study_ids` for one download. Narrows only: a
    model already scoped to some studies keeps just the overlap."""
    if not study_ids:
        return definition
    wanted = list(dict.fromkeys(study_ids))
    if definition.study_ids is not None:
        scoped = set(definition.study_ids)
        wanted = [study_id for study_id in wanted if study_id in scoped]
    return definition.model_copy(update={"study_ids": wanted})


def _check(definition: DataModelDefinition) -> None:
    try:
        validate_definition(definition)
    except DefinitionError as error:
        raise _invalid(error) from None


async def _download(
    db: AsyncSession,
    user: Optional[User],
    definition: DataModelDefinition,
    *,
    name: str,
    format: ExportFormat,
    header: HeaderStyle,
    source_url: Optional[str] = None,
) -> StreamingResponse:
    try:
        stmt, columns = build_select(definition, user)
    except DefinitionError as error:
        raise _invalid(error) from None
    headers = attachment_headers(name, format)
    if format == "csv":
        return StreamingResponse(
            stream_csv(db, stmt, columns, header),
            media_type="text/csv; charset=utf-8",
            headers=headers,
        )
    study_ids = (await db.execute(build_study_ids(definition, user))).scalars().all()
    workbook = await build_xlsx(
        db,
        stmt,
        columns,
        name=name,
        definition=definition,
        study_ids=study_ids,
        source_url=source_url,
        style=header,
    )
    return StreamingResponse(iter_file(workbook), media_type=XLSX_MEDIA_TYPE, headers=headers)


# --- Catalog ------------------------------------------------------------------


@router.get("/catalog", response_model=Catalog)
async def get_catalog():
    return Catalog(
        datasets=[
            CatalogDataset(
                key=ds.key,
                label=ds.label,
                description=ds.description,
                default_sort=ds.default_sort,
                tables=[
                    CatalogTable(
                        key=t.key,
                        label=t.label,
                        description=t.description,
                        requires=list(t.requires),
                        required=t.required,
                    )
                    for t in ds.tables
                ],
                fields=[
                    CatalogField(
                        key=f.key,
                        label=f.label,
                        group=f.group,
                        table=f.table,
                        type=f.type,
                        description=f.description,
                        unit=f.unit,
                    )
                    for f in ds.fields
                ],
            )
            for ds in DATASETS.values()
        ],
        operators=OPERATORS,
    )


@router.get("/catalog/{dataset}/fields/{field}/values", response_model=List[Any])
async def get_field_values(
    dataset: str,
    field: str,
    db: AsyncSession = Depends(get_async_session),
    user: Optional[User] = Depends(current_optional_user),
):
    """Distinct values of a field in the studies available to the viewer,
    to offer as filter choices."""
    ds = get_dataset(dataset)
    found = ds.get(field) if ds else None
    if found is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Field not found.")
    result = await db.execute(build_values(ds, found, user))
    return list(result.scalars())


@router.get("/studies", response_model=List[DownloadableStudy])
async def get_downloadable_studies(
    db: AsyncSession = Depends(get_async_session),
    user: Optional[User] = Depends(current_optional_user),
):
    """The studies the viewer may download data from, with what's needed to
    pick them: citation details and how much data each holds."""
    scenario_count = (
        select(func.count())
        .select_from(study_scenario)
        .where(study_scenario.c.study_id == Study.id)
        .scalar_subquery()
    )
    sample_count = (
        select(func.count(Sample.id)).where(Sample.study_id == Study.id).scalar_subquery()
    )
    result = await db.execute(
        select(Study, scenario_count, sample_count)
        # Only counts are needed; skip loading every scenario, sample and item.
        .options(noload(Study.scenarios), noload(Study.samples), noload(Study.items))
        .where(Study.id.in_(visible_study_ids(user)))
        .order_by(Study.year.desc().nulls_last(), Study.title)
    )
    return [
        DownloadableStudy(
            id=study.id,
            title=study.title,
            year=study.year,
            laboratory_name=study.laboratory.laboratory_name if study.laboratory else None,
            authors=[
                " ".join(p for p in (a.first_name, a.last_name) if p) for a in study.authors
            ],
            journal=study.journal,
            doi=study.doi,
            scenario_count=scenarios or 0,
            sample_count=samples or 0,
            published=bool(study.published and study.quality_check_passed),
        )
        for study, scenarios, samples in result.all()
    ]


# --- Running definitions --------------------------------------------------------


@router.post("/preview", response_model=DataModelPreview)
async def preview(
    definition: DataModelDefinition,
    db: AsyncSession = Depends(get_async_session),
    user: Optional[User] = Depends(current_optional_user),
):
    try:
        stmt, columns = build_select(definition, user, limit=PREVIEW_ROWS)
        counts = build_counts(definition, user)
    except DefinitionError as error:
        raise _invalid(error) from None
    rows = (await db.execute(stmt)).all()
    total_rows, study_count = (await db.execute(counts)).one()
    return DataModelPreview(
        columns=[PreviewColumn(key=f.key, label=f.label, type=f.type, unit=f.unit) for f in columns],
        rows=[list(row) for row in rows],
        total_rows=total_rows,
        study_count=study_count,
    )


@router.post("/download")
async def download_definition(
    definition: DataModelDefinition = Body(...),
    format: ExportFormat = Query("csv"),
    header: HeaderStyle = Query("label"),
    name: str = Query("data", max_length=200),
    db: AsyncSession = Depends(get_async_session),
    user: Optional[User] = Depends(current_optional_user),
):
    """Download an unsaved definition - for guests and unsaved edits."""
    return await _download(db, user, definition, name=name, format=format, header=header)


# --- Saved models ----------------------------------------------------------------


@router.get("", response_model=List[DataModelRead])
async def list_models(
    db: AsyncSession = Depends(get_async_session),
    user: Optional[User] = Depends(current_optional_user),
):
    """Predefined models, public models, and the user's own."""
    saved = await crud.list_visible(db, user)
    return [*(_preset_read(p) for p in PRESETS), *(_read(m, user) for m in saved)]


@router.post("", response_model=DataModelRead, status_code=status.HTTP_201_CREATED)
async def create_model(
    obj_in: DataModelCreate,
    db: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_active_user),
):
    _check(obj_in.definition)
    return _read(await crud.create(db, obj_in, user), user)


@router.get("/{id}", response_model=DataModelRead)
async def get_model(
    id: str,
    db: AsyncSession = Depends(get_async_session),
    user: Optional[User] = Depends(current_optional_user),
):
    return await _resolve(db, id, user)


@router.patch("/{id}", response_model=DataModelRead)
async def update_model(
    id: UUID,
    obj_in: DataModelUpdate,
    db: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_active_user),
):
    model = await _own_model(db, id, user)
    if obj_in.definition is not None:
        _check(obj_in.definition)
    return _read(await crud.update(db, model, obj_in), user)


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_model(
    id: UUID,
    db: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_active_user),
):
    await crud.delete(db, await _own_model(db, id, user))


@router.get("/{id}/download")
async def download_model(
    id: str,
    request: Request,
    format: ExportFormat = Query("csv"),
    header: HeaderStyle = Query("label"),
    study_ids: Optional[List[UUID]] = Query(
        None,
        description="Only include these studies (repeat the parameter for several). "
        "Narrows the model's own study selection, never widens it.",
    ),
    db: AsyncSession = Depends(get_async_session),
    user: Optional[User] = Depends(current_optional_user),
):
    """Download a saved or predefined model with the latest data. Works
    with an API key, so scripts can fetch fresh data on every run."""
    model = await _resolve(db, id, user)
    return await _download(
        db,
        user,
        _narrow(model.definition, study_ids),
        name=model.name,
        format=format,
        header=header,
        source_url=str(request.url.remove_query_params(["format", "header"])),
    )
