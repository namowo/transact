"""The permissions a user group can grant.

Permissions are defined here, in code; groups (see `app.models.user_group`)
bundle them and users get the union of their groups' permissions.

Each permission has a scope:

- "global" permissions act on the whole platform (all users, all
  laboratories, the shared catalog). Only global groups - which only admins
  holding `groups.manage` define - may contain them.
- "laboratory" permissions act on the holder's own laboratory. Laboratory
  groups, which a laboratory's admins define for their own members, may
  only contain these.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Literal


class Permission(str, Enum):
    # --- Platform ---------------------------------------------------------
    MANAGE_USERS = "users.manage"
    MANAGE_GROUPS = "groups.manage"
    MANAGE_LABORATORIES = "laboratories.manage"
    EDIT_ALL_LABORATORY_DATA = "laboratories.edit_all_data"
    VIEW_ALL_STUDIES = "studies.view_all"
    QUALITY_CHECK = "studies.quality_check"
    EDIT_CATALOG = "catalog.edit"
    DELETE_CATALOG = "catalog.delete"
    MANAGE_METHODS = "methods.manage"
    MANAGE_SITE_SETTINGS = "site_settings.manage"

    # --- Own laboratory ---------------------------------------------------
    ENTER_DATA = "data.enter"
    MANAGE_LAB_MEMBERS = "lab.manage_members"
    MANAGE_LAB_GROUPS = "lab.manage_groups"
    MANAGE_LAB_SETTINGS = "lab.manage_settings"


Scope = Literal["global", "laboratory"]


@dataclass(frozen=True)
class PermissionInfo:
    key: Permission
    label: str
    description: str
    scope: Scope


PERMISSIONS: tuple[PermissionInfo, ...] = (
    PermissionInfo(
        Permission.MANAGE_USERS,
        "Manage all users",
        "See every account, move users between laboratories, delete accounts "
        "and assign any group.",
        "global",
    ),
    PermissionInfo(
        Permission.MANAGE_GROUPS,
        "Manage groups and permissions",
        "Create platform-wide groups and decide which permissions every group "
        "grants.",
        "global",
    ),
    PermissionInfo(
        Permission.MANAGE_LABORATORIES,
        "Manage laboratories",
        "Create, edit, approve and delete laboratories, and move studies "
        "between them.",
        "global",
    ),
    PermissionInfo(
        Permission.EDIT_ALL_LABORATORY_DATA,
        "Edit data of all laboratories",
        "Create and edit studies and their data on behalf of any laboratory, "
        "e.g. to prepare data before the laboratory takes over. A laboratory "
        "can switch this off for itself.",
        "global",
    ),
    PermissionInfo(
        Permission.VIEW_ALL_STUDIES,
        "View all studies",
        "See unpublished studies of every laboratory.",
        "global",
    ),
    PermissionInfo(
        Permission.QUALITY_CHECK,
        "Quality check studies",
        "Review studies and pass their quality check before publication.",
        "global",
    ),
    PermissionInfo(
        Permission.EDIT_CATALOG,
        "Edit shared catalog",
        "Rename and edit entries of the shared lists (categories, devices, "
        "kits, items, ...).",
        "global",
    ),
    PermissionInfo(
        Permission.DELETE_CATALOG,
        "Delete from shared catalog",
        "Delete entries from the shared lists.",
        "global",
    ),
    PermissionInfo(
        Permission.MANAGE_METHODS,
        "Manage methods",
        "Create, edit and delete laboratory methods (extraction, PCR, CE, "
        "sampling, ...).",
        "global",
    ),
    PermissionInfo(
        Permission.MANAGE_SITE_SETTINGS,
        "Manage site settings",
        "Edit the legal notice and other site-wide settings.",
        "global",
    ),
    PermissionInfo(
        Permission.ENTER_DATA,
        "Enter study data",
        "Add and edit scenarios, individuals, items, samples and results of "
        "the laboratory's studies.",
        "laboratory",
    ),
    PermissionInfo(
        Permission.MANAGE_LAB_MEMBERS,
        "Manage laboratory members",
        "Approve membership requests, remove members and assign groups to "
        "members of the laboratory.",
        "laboratory",
    ),
    PermissionInfo(
        Permission.MANAGE_LAB_GROUPS,
        "Manage laboratory groups",
        "Create and edit the laboratory's own groups.",
        "laboratory",
    ),
    PermissionInfo(
        Permission.MANAGE_LAB_SETTINGS,
        "Manage laboratory settings",
        "Edit the planning checklist and decide whether platform admins may "
        "edit the laboratory's data.",
        "laboratory",
    ),
)

PERMISSION_INFO: dict[Permission, PermissionInfo] = {p.key: p for p in PERMISSIONS}
ALL_PERMISSIONS: frozenset[Permission] = frozenset(PERMISSION_INFO)
LABORATORY_PERMISSIONS: frozenset[Permission] = frozenset(
    p.key for p in PERMISSIONS if p.scope == "laboratory"
)


# --- Built-in groups ---------------------------------------------------------
#
# Created on demand (see crud.user_group.get_system_group) and by the
# migration that introduced groups. Admins may change their permissions,
# except that the administrator group always keeps the permissions needed to
# manage users and groups - otherwise nobody could undo the change.


class SystemGroup(str, Enum):
    ADMINISTRATOR = "administrator"
    LAB_ADMINISTRATOR = "lab_administrator"
    QUALITY_CHECKER = "quality_checker"


@dataclass(frozen=True)
class SystemGroupInfo:
    key: SystemGroup
    name: str
    description: str
    permissions: frozenset[Permission]


SYSTEM_GROUPS: dict[SystemGroup, SystemGroupInfo] = {
    SystemGroup.ADMINISTRATOR: SystemGroupInfo(
        SystemGroup.ADMINISTRATOR,
        "Administrator",
        "Runs the platform.",
        ALL_PERMISSIONS,
    ),
    SystemGroup.LAB_ADMINISTRATOR: SystemGroupInfo(
        SystemGroup.LAB_ADMINISTRATOR,
        "Lab administrator",
        "Manages the members and settings of their own laboratory.",
        frozenset(
            {
                Permission.MANAGE_LAB_MEMBERS,
                Permission.MANAGE_LAB_GROUPS,
                Permission.MANAGE_LAB_SETTINGS,
                Permission.EDIT_CATALOG,
            }
        ),
    ),
    SystemGroup.QUALITY_CHECKER: SystemGroupInfo(
        SystemGroup.QUALITY_CHECKER,
        "Quality checker",
        "Reviews studies before publication.",
        frozenset({Permission.QUALITY_CHECK}),
    ),
}

# The administrator group can never lose these.
LOCKED_ADMINISTRATOR_PERMISSIONS: frozenset[Permission] = frozenset(
    {Permission.MANAGE_USERS, Permission.MANAGE_GROUPS}
)
