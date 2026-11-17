import { computed, inject, provide, type ComputedRef, type InjectionKey, type Ref } from 'vue'
import type { Study, User } from '@/api/types'

// A study can be viewed by anyone it is visible to, but only members of the
// laboratory that owns it may change it or its data. Superusers are no
// exception (the backend enforces the same rule).
export function canEditStudy(
  study: Pick<Study, 'laboratory_id'> | null | undefined,
  user: User | null | undefined,
): boolean {
  return !!study && !!user?.laboratory_id && study.laboratory_id === user.laboratory_id
}

const studyReadOnlyKey: InjectionKey<Ref<boolean> | ComputedRef<boolean>> = Symbol('studyReadOnly')

// Called by the study page so the planning and data-entry components below
// it can hide their add/edit/delete controls.
export function provideStudyReadOnly(readOnly: Ref<boolean> | ComputedRef<boolean>) {
  provide(studyReadOnlyKey, readOnly)
}

// `true` when the surrounding study belongs to another laboratory. Outside
// a study page nothing is provided and components stay editable.
export function useStudyReadOnly(): ComputedRef<boolean> {
  const readOnly = inject(studyReadOnlyKey, null)
  return computed(() => !!readOnly?.value)
}
