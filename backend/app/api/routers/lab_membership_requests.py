from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import (
    assert_manages_laboratory,
    current_active_user,
    current_lab_admin,
    current_superuser,
    get_async_session,
)
from app.crud.exceptions import NotFoundError
from app.crud.lab_membership_request import crud_lab_membership_request as crud
from app.crud.laboratory import crud_laboratory
from app.crud.user import crud_user
from app.models.laboratory import LaboratoryApprovalStatus
from app.models.lab_membership_request import LabMembershipRequest
from app.models.user import User
from app.schemas.lab_membership_request import (
    LabMembershipRequestCreateExisting,
    LabMembershipRequestCreateNewLab,
    LabMembershipRequestRead as ReadSchema,
)
from app.services.mail.messages import (
    send_lab_approved_mail,
    send_lab_denied_mail,
    send_membership_approved_mail,
    send_membership_denied_mail,
    send_new_lab_requested_mail,
    send_new_membership_request_mail,
)

router = APIRouter()


def _assert_can_review(request: LabMembershipRequest, user: User) -> None:
    if request.laboratory.approval_status == LaboratoryApprovalStatus.pending:
        if not user.is_superuser:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only a superuser can approve a new laboratory request.",
            )
    else:
        assert_manages_laboratory(user, request.laboratory_id)


@router.post(
    "/join-existing", response_model=ReadSchema, status_code=status.HTTP_201_CREATED
)
async def join_existing(
    obj_in: LabMembershipRequestCreateExisting,
    db: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_active_user),
):
    laboratory = await crud_laboratory.get(db, obj_in.laboratory_id)
    if laboratory.approval_status != LaboratoryApprovalStatus.approved:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This laboratory is not yet approved.",
        )

    request = await crud.create_join_request(db, user, obj_in.laboratory_id)

    lab_admins = [
        u
        for u in await crud_user.list_by_laboratory(db, obj_in.laboratory_id)
        if u.can_manage_lab_users
    ]
    for lab_admin in lab_admins:
        await send_new_membership_request_mail(lab_admin, user, laboratory)

    return request


@router.post(
    "/new-laboratory", response_model=ReadSchema, status_code=status.HTTP_201_CREATED
)
async def new_laboratory(
    obj_in: LabMembershipRequestCreateNewLab,
    db: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_active_user),
):
    request = await crud.create_new_lab_request(db, user, obj_in)

    for superuser in await crud_user.list_superusers(db):
        await send_new_lab_requested_mail(superuser, request.laboratory, user)

    return request


@router.get("/me", response_model=Optional[ReadSchema])
async def get_my_request(
    db: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_active_user),
):
    return await crud.get_pending_for_user(db, user.id)


@router.get("/pending-for-my-lab", response_model=List[ReadSchema])
async def get_pending_for_my_lab(
    db: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_lab_admin),
):
    return await crud.list_pending_for_laboratory(db, user.laboratory_id)


@router.get(
    "/pending-new-labs",
    response_model=List[ReadSchema],
    dependencies=[Depends(current_superuser)],
)
async def get_pending_new_labs(db: AsyncSession = Depends(get_async_session)):
    return await crud.list_pending_new_labs(db)


@router.post("/{id}/approve", response_model=ReadSchema)
async def approve(
    id: int,
    db: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_active_user),
):
    request = await crud.get(db, id)
    if request is None:
        raise NotFoundError(status_code=status.HTTP_404_NOT_FOUND)
    _assert_can_review(request, user)

    was_new_lab = request.laboratory.approval_status == LaboratoryApprovalStatus.pending
    result = await crud.approve(db, request, reviewer=user)

    if was_new_lab:
        await send_lab_approved_mail(result.user, result.laboratory)
    else:
        await send_membership_approved_mail(result.user, result.laboratory)

    return result


@router.post("/{id}/deny", response_model=ReadSchema)
async def deny(
    id: int,
    db: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_active_user),
):
    request = await crud.get(db, id)
    if request is None:
        raise NotFoundError(status_code=status.HTTP_404_NOT_FOUND)
    _assert_can_review(request, user)

    was_new_lab = request.laboratory.approval_status == LaboratoryApprovalStatus.pending
    result = await crud.deny(db, request, reviewer=user)

    if was_new_lab:
        await send_lab_denied_mail(result.user, result.laboratory)
    else:
        await send_membership_denied_mail(result.user, result.laboratory)

    return result
