import { computed, inject, provide, type ComputedRef, type InjectionKey, type Ref } from 'vue'
import type { Study, User } from '@/api/types'

type StudyOwner = Pick<Study, 'laboratory_id' | 'laboratory'>

function isMember(study: StudyOwner, user: User) {
  return !!user.laboratory_id && study.laboratory_id === user.laboratory_id
}

// Admins with "Edit data of all laboratories" may work on a laboratory's
// studies unless the laboratory has switched that off.
function actsForLaboratory(study: StudyOwner, user: User) {
  return (
    !!user.permissions?.includes('laboratories.edit_all_data') &&
    study.laboratory?.allow_admin_data_entry !== false
  )
}

// A study can be viewed by anyone it is visible to, but only members of the
// laboratory that owns it - or admins acting for it - may change it. Mirrors
// backend app/core/permissions.py.
export function canEditStudy(
  study: StudyOwner | null | undefined,
  user: User | null | undefined,
): boolean {
  if (!study || !user) return false
  return isMember(study, user) || actsForLaboratory(study, user)
}

// Adding and changing a study's data (scenarios, samples, results, ...)
// additionally needs the "Enter study data" permission for members.
export function canEnterStudyData(
  study: StudyOwner | null | undefined,
  user: User | null | undefined,
): boolean {
  if (!study || !user) return false
  if (isMember(study, user) && !!user.permissions?.includes('data.enter')) return true
  return actsForLaboratory(study, user)
}

const studyReadOnlyKey: InjectionKey<Ref<boolean> | ComputedRef<boolean>> = Symbol('studyReadOnly')

// Called by the study page so the planning and data-entry components below
// it can hide their add/edit/delete controls.
export function provideStudyReadOnly(readOnly: Ref<boolean> | ComputedRef<boolean>) {
  provide(studyReadOnlyKey, readOnly)
}

// `true` when the user may not change the surrounding study's data. Outside
// a study page nothing is provided and components stay editable.
export function useStudyReadOnly(): ComputedRef<boolean> {
  const readOnly = inject(studyReadOnlyKey, null)
  return computed(() => !!readOnly?.value)
}
