"""User groups and who may change them.

Rules, enforced here so every endpoint applies them the same way:

- Global groups (no laboratory) are created and edited by users with
  `groups.manage`. They may hold any permission.
- Laboratory groups are created and edited by the laboratory's admins
  (`lab.manage_groups` in that laboratory) or by `groups.manage` holders.
  They may only hold laboratory-scoped permissions.
- Nobody can hand out a permission they don't hold themselves: a group can
  only be given permissions - and only be assigned to someone - by a user
  who holds all of its permissions. `users.manage` holders are exempt from
  the latter so admins can always fix memberships.
- The administrator group can't be deleted, always keeps the permissions to
  manage users and groups, and always keeps at least one active member.
"""

from typing import Iterable, Optional
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import delete, func, insert, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.permission_catalog import (
    LABORATORY_PERMISSIONS,
    LOCKED_ADMINISTRATOR_PERMISSIONS,
    SYSTEM_GROUPS,
    Permission,
    SystemGroup,
)
from app.crud.exceptions import NotFoundError
from app.models.user import User
from app.models.user_group import UserGroup, user_group_member


def _forbidden(detail: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=detail)


def _bad_request(detail: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)


# --- Built-in groups ---------------------------------------------------------


async def get_system_group(db: AsyncSession, key: SystemGroup) -> UserGroup:
    """The built-in group `key`, created with its default permissions if it
    doesn't exist yet (fresh databases, tests)."""
    result = await db.execute(select(UserGroup).where(UserGroup.system_key == key.value))
    group = result.scalars().first()
    if group is None:
        info = SYSTEM_GROUPS[key]
        group = UserGroup(
            name=info.name,
            description=info.description,
            system_key=key.value,
            permissions=sorted(p.value for p in info.permissions),
        )
        db.add(group)
        await db.flush()
    return group


async def ensure_system_groups(db: AsyncSession) -> None:
    for key in SystemGroup:
        await get_system_group(db, key)
    await db.commit()


async def add_to_system_group(db: AsyncSession, user: User, key: SystemGroup) -> None:
    """Add `user` to a built-in group (no permission checks; for setup and
    approval flows). Doesn't commit."""
    group = await get_system_group(db, key)
    if all(g.id != group.id for g in user.groups):
        user.groups.append(group)


async def list_members_with(db: AsyncSession, permission: Permission) -> list[User]:
    """Active users whose groups grant `permission`."""
    result = await db.execute(
        select(User)
        .join(user_group_member, user_group_member.c.user_id == User.id)
        .join(UserGroup, UserGroup.id == user_group_member.c.group_id)
        .where(User.is_active.is_(True))
        .where(UserGroup.permissions.contains([permission.value]))
        .distinct()
    )
    return list(result.scalars().all())


async def anyone_has(db: AsyncSession, permission: Permission) -> bool:
    result = await db.execute(
        select(user_group_member.c.user_id)
        .join(UserGroup, UserGroup.id == user_group_member.c.group_id)
        .where(UserGroup.permissions.contains([permission.value]))
        .limit(1)
    )
    return result.first() is not None


# --- Reading -----------------------------------------------------------------


async def get(db: AsyncSession, group_id: UUID) -> UserGroup:
    group = await db.get(UserGroup, group_id)
    if group is None:
        raise NotFoundError(status_code=status.HTTP_404_NOT_FOUND, message="Group not found.")
    return group


async def member_counts(db: AsyncSession, group_ids: Iterable[UUID]) -> dict[UUID, int]:
    ids = list(group_ids)
    if not ids:
        return {}
    result = await db.execute(
        select(user_group_member.c.group_id, func.count())
        .where(user_group_member.c.group_id.in_(ids))
        .group_by(user_group_member.c.group_id)
    )
    return dict(result.all())


def can_see_group(actor: User, group: UserGroup) -> bool:
    if group.laboratory_id is None:
        return True
    return actor.can(Permission.MANAGE_GROUPS) or actor.can(Permission.MANAGE_USERS) or (
        group.laboratory_id == actor.laboratory_id
    )


async def list_visible(
    db: AsyncSession, actor: User, laboratory_id: Optional[UUID] = None
) -> list[UserGroup]:
    """Global groups plus the laboratory groups `actor` may see. With
    `laboratory_id`, only global groups and that laboratory's groups."""
    statement = select(UserGroup).order_by(UserGroup.laboratory_id.nulls_first(), UserGroup.name)
    if laboratory_id is not None:
        statement = statement.where(
            (UserGroup.laboratory_id.is_(None)) | (UserGroup.laboratory_id == laboratory_id)
        )
    result = await db.execute(statement)
    return [group for group in result.scalars().all() if can_see_group(actor, group)]


# --- Defining groups ---------------------------------------------------------


def _assert_may_define(actor: User, laboratory_id: Optional[UUID]) -> None:
    if actor.can(Permission.MANAGE_GROUPS):
        return
    if laboratory_id is not None and actor.can_in_laboratory(
        Permission.MANAGE_LAB_GROUPS, laboratory_id
    ):
        return
    if laboratory_id is None:
        raise _forbidden("Only admins can manage platform-wide groups.")
    raise _forbidden("You can only manage the groups of your own laboratory.")


def _validate_permissions(
    actor: User,
    laboratory_id: Optional[UUID],
    requested: set[str],
    current: set[str],
) -> None:
    if laboratory_id is not None:
        outside = requested - {p.value for p in LABORATORY_PERMISSIONS}
        if outside:
            raise _bad_request(
                "Laboratory groups can only hold laboratory permissions: "
                + ", ".join(sorted(outside))
            )
    # Only what changes needs to be held: an admin who lost a permission can
    # still rename a group that grants it, and remove it from the group.
    added = requested - current
    missing = added - actor.permissions
    if missing:
        raise _forbidden(
            "You can't grant permissions you don't have yourself: "
            + ", ".join(sorted(missing))
        )


async def _assert_unique_name(
    db: AsyncSession, name: str, laboratory_id: Optional[UUID], exclude: Optional[UUID] = None
) -> None:
    statement = select(UserGroup.id).where(func.lower(UserGroup.name) == name.strip().lower())
    statement = statement.where(
        UserGroup.laboratory_id.is_(None)
        if laboratory_id is None
        else UserGroup.laboratory_id == laboratory_id
    )
    if exclude is not None:
        statement = statement.where(UserGroup.id != exclude)
    if (await db.execute(statement)).first() is not None:
        raise _bad_request("A group with this name already exists.")


async def create(
    db: AsyncSession,
    actor: User,
    *,
    name: str,
    description: Optional[str],
    permissions: list[Permission],
    laboratory_id: Optional[UUID],
) -> UserGroup:
    _assert_may_define(actor, laboratory_id)
    requested = {p.value for p in permissions}
    _validate_permissions(actor, laboratory_id, requested, set())
    await _assert_unique_name(db, name, laboratory_id)
    group = UserGroup(
        name=name.strip(),
        description=description,
        laboratory_id=laboratory_id,
        permissions=sorted(requested),
    )
    db.add(group)
    await db.commit()
    await db.refresh(group)
    return group


async def update(
    db: AsyncSession,
    actor: User,
    group: UserGroup,
    *,
    name: Optional[str],
    description: Optional[str],
    permissions: Optional[list[Permission]],
    fields_set: set[str],
) -> UserGroup:
    _assert_may_define(actor, group.laboratory_id)
    if group.system_key is not None and "name" in fields_set and name != group.name:
        raise _bad_request("Built-in groups can't be renamed.")
    if "name" in fields_set and name is not None:
        await _assert_unique_name(db, name, group.laboratory_id, exclude=group.id)
        group.name = name.strip()
    if "description" in fields_set:
        group.description = description
    if permissions is not None:
        requested = {p.value for p in permissions}
        current = set(group.permissions)
        _validate_permissions(actor, group.laboratory_id, requested, current)
        removed = current - requested
        if removed - actor.permissions:
            raise _forbidden("You can't revoke permissions you don't have yourself.")
        if group.system_key == SystemGroup.ADMINISTRATOR.value:
            locked = {p.value for p in LOCKED_ADMINISTRATOR_PERMISSIONS} & removed
            if locked:
                raise _bad_request(
                    "The Administrator group always keeps the permissions to manage "
                    "users and groups."
                )
        group.permissions = sorted(requested)
    await db.commit()
    await db.refresh(group)
    return group


async def delete_group(db: AsyncSession, actor: User, group: UserGroup) -> None:
    _assert_may_define(actor, group.laboratory_id)
    if group.system_key is not None:
        raise _bad_request("Built-in groups can't be deleted.")
    missing = set(group.permissions) - actor.permissions
    if missing:
        raise _forbidden("You can't delete a group granting permissions you don't have.")
    await db.delete(group)
    await db.commit()


# --- Assigning groups --------------------------------------------------------


def may_assign(actor: User, target: User, group: UserGroup) -> bool:
    """Whether `actor` may add `target` to `group` or remove them from it."""
    if group.laboratory_id is not None and group.laboratory_id != target.laboratory_id:
        return False
    if actor.can(Permission.MANAGE_USERS):
        return True
    if not actor.can_in_laboratory(Permission.MANAGE_LAB_MEMBERS, target.laboratory_id):
        return False
    return set(group.permissions) <= actor.permissions


async def _active_administrators(db: AsyncSession) -> set[UUID]:
    admin_group = await get_system_group(db, SystemGroup.ADMINISTRATOR)
    result = await db.execute(
        select(User.id)
        .join(user_group_member, user_group_member.c.user_id == User.id)
        .where(user_group_member.c.group_id == admin_group.id)
        .where(User.is_active.is_(True))
    )
    return set(result.scalars())


async def assert_keeps_an_administrator(db: AsyncSession, leaving: UUID) -> None:
    """Raise if `leaving` is the last active administrator."""
    administrators = await _active_administrators(db)
    if leaving in administrators and not administrators - {leaving}:
        raise _bad_request("At least one active user must stay in the Administrator group.")


async def set_user_groups(
    db: AsyncSession, actor: User, target: User, group_ids: Iterable[UUID]
) -> User:
    requested = set(group_ids)
    current = {group.id for group in target.groups}
    changed = requested ^ current
    groups = {group.id: group for group in target.groups}
    for group_id in changed - current:
        groups[group_id] = await get(db, group_id)
    for group_id in changed:
        group = groups[group_id]
        if not may_assign(actor, target, group):
            raise _forbidden(f'You can\'t change membership of the group "{group.name}".')

    admin_group = await get_system_group(db, SystemGroup.ADMINISTRATOR)
    if admin_group.id in current - requested:
        await assert_keeps_an_administrator(db, target.id)

    removed = current - requested
    added = requested - current
    if removed:
        await db.execute(
            delete(user_group_member).where(
                user_group_member.c.user_id == target.id,
                user_group_member.c.group_id.in_(removed),
            )
        )
    if added:
        await db.execute(
            insert(user_group_member),
            [{"user_id": target.id, "group_id": group_id} for group_id in added],
        )
    await db.commit()
    await db.refresh(target, attribute_names=["groups"])
    return target


async def leave_laboratory_groups(db: AsyncSession, user: User) -> None:
    """Drop `user` from every laboratory group and from the lab admin group -
    called when they leave their laboratory. Doesn't commit."""
    lab_admin_group = await get_system_group(db, SystemGroup.LAB_ADMINISTRATOR)
    user.groups = [
        group
        for group in user.groups
        if group.laboratory_id is None and group.id != lab_admin_group.id
    ]
