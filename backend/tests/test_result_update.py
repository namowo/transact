"""Updating a result can clear a value by sending null."""

import pytest

from app.crud.result import crud_result
from app.schemas.result import ResultCreate, ResultUpdate


@pytest.mark.asyncio
async def test_update_clears_value_sent_as_null(db_session):
    result = await crud_result.create(db_session, ResultCreate(dna_concentration=1.5))

    updated = await crud_result.update(
        db_session, result.id, ResultUpdate(dna_concentration=None)
    )
    assert updated.dna_concentration is None


@pytest.mark.asyncio
async def test_update_keeps_fields_left_out(db_session):
    result = await crud_result.create(db_session, ResultCreate(dna_concentration=1.5))

    updated = await crud_result.update(db_session, result.id, ResultUpdate(pcrs=[]))
    assert updated.dna_concentration == 1.5
