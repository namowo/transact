import type { DataModelDefinition } from '@/api/types'

export interface SharedDataModel {
  name: string
  description?: string | null
  definition: DataModelDefinition
}

function toBase64Url(bytes: Uint8Array): string {
  let binary = ''
  for (const byte of bytes) binary += String.fromCharCode(byte)
  return btoa(binary).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '')
}

function fromBase64Url(text: string): Uint8Array {
  const base64 = text.replace(/-/g, '+').replace(/_/g, '/')
  const padded = base64 + '='.repeat((4 - (base64.length % 4)) % 4)
  const binary = atob(padded)
  return Uint8Array.from(binary, (char) => char.charCodeAt(0))
}

/** Encodes a model into a URL-safe string, so it can be shared as a link
 * without saving it anywhere. */
export function encodeSharedModel(model: SharedDataModel): string {
  const payload = { n: model.name, d: model.description ?? undefined, m: model.definition }
  return toBase64Url(new TextEncoder().encode(JSON.stringify(payload)))
}

/** The model a share link carries, or null if it can't be read. */
export function decodeSharedModel(text: string): SharedDataModel | null {
  try {
    const payload = JSON.parse(new TextDecoder().decode(fromBase64Url(text)))
    const definition = payload?.m
    if (
      typeof definition?.dataset !== 'string' ||
      !Array.isArray(definition.columns) ||
      !definition.columns.every((c: unknown) => typeof c === 'string')
    ) {
      return null
    }
    return {
      name: typeof payload.n === 'string' ? payload.n : 'Shared data model',
      description: typeof payload.d === 'string' ? payload.d : null,
      definition: {
        dataset: definition.dataset,
        joins: Array.isArray(definition.joins) ? definition.joins : null,
        columns: definition.columns,
        filters: Array.isArray(definition.filters) ? definition.filters : [],
        study_ids: Array.isArray(definition.study_ids) ? definition.study_ids : null,
        sort: Array.isArray(definition.sort) ? definition.sort : [],
      },
    }
  } catch {
    return null
  }
}
