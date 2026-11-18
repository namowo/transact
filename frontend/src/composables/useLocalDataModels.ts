import { ref } from 'vue'
import type { DataModel, DataModelSave } from '@/api/types'

// Guests have no account to save data models to, so theirs are kept in
// this browser's localStorage.
export const LOCAL_DATA_MODELS_KEY = 'transact-data-models'
export const LOCAL_ID_PREFIX = 'local-'

function read(): DataModel[] {
  try {
    const parsed = JSON.parse(localStorage.getItem(LOCAL_DATA_MODELS_KEY) ?? '[]')
    return Array.isArray(parsed)
      ? parsed.filter((m) => typeof m?.id === 'string' && m?.definition)
      : []
  } catch {
    return []
  }
}

// Shared across components so every view sees the same list.
const models = ref<DataModel[]>(read())

function persist() {
  try {
    localStorage.setItem(LOCAL_DATA_MODELS_KEY, JSON.stringify(models.value))
  } catch {
    // Storage full or disabled: the models stay usable for this session.
  }
}

function newId() {
  const random =
    typeof crypto !== 'undefined' && 'randomUUID' in crypto
      ? crypto.randomUUID()
      : Math.random().toString(36).slice(2)
  return `${LOCAL_ID_PREFIX}${random}`
}

export function isLocalId(id: string | undefined | null): boolean {
  return !!id?.startsWith(LOCAL_ID_PREFIX)
}

export function useLocalDataModels() {
  function get(id: string) {
    return models.value.find((m) => m.id === id) ?? null
  }

  function create(payload: DataModelSave): DataModel {
    const now = new Date().toISOString()
    const model: DataModel = {
      id: newId(),
      name: payload.name,
      description: payload.description ?? null,
      definition: payload.definition,
      is_public: false,
      source: 'local',
      created_at: now,
      updated_at: now,
    }
    models.value = [...models.value, model]
    persist()
    return model
  }

  function update(id: string, payload: Partial<DataModelSave>): DataModel | null {
    const existing = get(id)
    if (!existing) return null
    const updated: DataModel = {
      ...existing,
      ...payload,
      is_public: false,
      source: 'local',
      updated_at: new Date().toISOString(),
    }
    models.value = models.value.map((m) => (m.id === id ? updated : m))
    persist()
    return updated
  }

  function remove(id: string) {
    models.value = models.value.filter((m) => m.id !== id)
    persist()
  }

  /** Re-read storage, e.g. after another tab changed it. */
  function reload() {
    models.value = read()
  }

  return { models, get, create, update, remove, reload }
}
