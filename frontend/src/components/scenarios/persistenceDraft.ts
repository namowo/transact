import { createPersistence, updatePersistence } from '@/api/persistences'
import type { Persistence } from '@/api/types'

export interface PersistenceDraft {
  id: number | null
  // The study this persistence was created for. Only that study may edit
  // it - it's a shared m:n record other studies can link via a scenario,
  // but editing it there would silently change it everywhere it's used.
  // Null for a not-yet-saved draft, which is always editable.
  owningStudyId: number | null
  // Optional label to tell apart multiple persistencies on a scenario.
  name: string | null
  intervalOfPersistence: number | null
  temperature: number | null
  humidity: number | null
  uvIrradiation: number | null
  indoors: boolean
  changeOverTime: boolean
  durationOfDisturbance: number | null
  descriptionOfDisturbance: string | null
  disturbanceCategoryId: number | null
  geographicLocationCategoryId: number | null
}

export function emptyPersistenceDraft(): PersistenceDraft {
  return {
    id: null,
    owningStudyId: null,
    name: null,
    intervalOfPersistence: null,
    temperature: null,
    humidity: null,
    uvIrradiation: null,
    indoors: false,
    changeOverTime: false,
    durationOfDisturbance: null,
    descriptionOfDisturbance: null,
    disturbanceCategoryId: null,
    geographicLocationCategoryId: null,
  }
}

export function persistenceDraftFromPersistence(
  persistence: Persistence | null | undefined,
): PersistenceDraft {
  if (!persistence) return emptyPersistenceDraft()
  return {
    id: persistence.id,
    owningStudyId: persistence.owning_study_id ?? null,
    name: persistence.name ?? null,
    intervalOfPersistence: persistence.interval_of_persistence ?? null,
    temperature: persistence.temperature ?? null,
    humidity: persistence.humidity ?? null,
    uvIrradiation: persistence.uv_irradiation ?? null,
    indoors: !!persistence.indoors,
    changeOverTime: !!persistence.change_over_time,
    durationOfDisturbance: persistence.duration_of_disturbance ?? null,
    descriptionOfDisturbance: persistence.description_of_disturbance ?? null,
    disturbanceCategoryId: persistence.disturbance_category_id ?? null,
    geographicLocationCategoryId: persistence.geographic_location_category_id ?? null,
  }
}

export function isPersistenceEditable(draft: PersistenceDraft, currentStudyId: number): boolean {
  return draft.owningStudyId === null || draft.owningStudyId === currentStudyId
}

function authorCitation(authors: { last_name: string }[]): string | null {
  if (authors.length === 0) return null
  if (authors.length === 1) return authors[0].last_name
  if (authors.length === 2) return `${authors[0].last_name} & ${authors[1].last_name}`
  return `${authors[0].last_name} et al.`
}

function persistenceSubtitle(persistence: Persistence): string | null {
  const study = persistence.owning_study
  const citation = study ? authorCitation(study.authors) : null
  const title = study?.title

  const studyLabel = [citation, title].filter((part): part is string => !!part).join(' — ')
  if (studyLabel) return studyLabel

  const categoryParts = [
    persistence.disturbance_category?.name,
    persistence.geographic_location_category?.name,
  ].filter((part): part is string => !!part)
  return categoryParts.length ? categoryParts.join(' – ') : null
}

export function persistenceLabel(persistence: Persistence): string {
  const subtitle = persistenceSubtitle(persistence)
  if (persistence.name) return subtitle ? `${persistence.name} (${subtitle})` : persistence.name
  return subtitle ?? `Persistence #${persistence.id}`
}

export function isBlankPersistenceDraft(draft: PersistenceDraft): boolean {
  if (draft.id !== null) return false
  return (
    !draft.name &&
    draft.intervalOfPersistence == null &&
    draft.temperature == null &&
    draft.humidity == null &&
    draft.uvIrradiation == null &&
    !draft.indoors &&
    !draft.changeOverTime &&
    draft.durationOfDisturbance == null &&
    !draft.descriptionOfDisturbance &&
    !draft.disturbanceCategoryId &&
    !draft.geographicLocationCategoryId
  )
}

export async function savePersistenceDraft(
  draft: PersistenceDraft,
  currentStudyId: number,
): Promise<number | null> {
  // A persistence owned by another study is linked read-only - never
  // rewritten here, since it's a shared record that study still owns.
  if (!isPersistenceEditable(draft, currentStudyId)) return draft.id
  if (isBlankPersistenceDraft(draft)) return draft.id

  const payload = {
    name: draft.name || null,
    interval_of_persistence: draft.intervalOfPersistence,
    temperature: draft.temperature,
    humidity: draft.humidity,
    uv_irradiation: draft.uvIrradiation,
    indoors: draft.indoors,
    change_over_time: draft.changeOverTime,
    duration_of_disturbance: draft.durationOfDisturbance,
    description_of_disturbance: draft.descriptionOfDisturbance || null,
    disturbance_category_id: draft.disturbanceCategoryId,
    geographic_location_category_id: draft.geographicLocationCategoryId,
  }

  const persistence = draft.id
    ? await updatePersistence(draft.id, payload)
    : await createPersistence({ ...payload, owning_study_id: currentStudyId })
  return persistence.id
}
