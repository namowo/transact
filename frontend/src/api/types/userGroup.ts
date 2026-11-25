// Keys of the permissions a group can grant (backend: app/core/permission_catalog.py).
export type Permission =
  | 'users.manage'
  | 'groups.manage'
  | 'laboratories.manage'
  | 'laboratories.edit_all_data'
  | 'studies.view_all'
  | 'studies.quality_check'
  | 'catalog.edit'
  | 'catalog.delete'
  | 'methods.manage'
  | 'site_settings.manage'
  | 'data.enter'
  | 'lab.manage_members'
  | 'lab.manage_groups'
  | 'lab.manage_settings'

// "global" permissions act on the whole platform, "laboratory" ones on the
// holder's own laboratory. Laboratory groups may only hold the latter.
export type PermissionScope = 'global' | 'laboratory'

export interface PermissionInfo {
  key: Permission
  label: string
  description: string
  scope: PermissionScope
}

// Built-in groups; they can't be deleted or renamed.
export type SystemGroupKey = 'administrator' | 'lab_administrator' | 'quality_checker'

export interface UserGroupBrief {
  id: string
  name: string
  system_key: SystemGroupKey | null
  // Set for groups belonging to a laboratory; null for platform-wide groups.
  laboratory_id: string | null
}

export interface UserGroup extends UserGroupBrief {
  description: string | null
  permissions: Permission[]
  member_count: number
}

export interface UserGroupPayload {
  name: string
  description?: string | null
  permissions: Permission[]
  laboratory_id?: string | null
}
