import { createPersistence, updatePersistence } from '@/api/persistences'
import type { Persistence } from '@/api/types'

export interface PersistenceDraft {
  id: number | null
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

function isBlankDraft(draft: PersistenceDraft): boolean {
  return (
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

export async function savePersistenceDraft(draft: PersistenceDraft): Promise<number | null> {
  if (isBlankDraft(draft)) return draft.id

  const payload = {
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
    : await createPersistence(payload)
  return persistence.id
}
