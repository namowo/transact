import { beforeEach, describe, expect, it, vi } from 'vitest'
import type { CatalogDataset, DataModelDefinition } from '@/api/types'
import { decodeSharedModel, encodeSharedModel } from '../shareLink'
import {
  addJoin,
  inferJoins,
  isFilterComplete,
  joinedFields,
  removeJoin,
  requestDefinition,
  switchDataset,
  withJoins,
} from '../definition'

const definition: DataModelDefinition = {
  dataset: 'results',
  joins: ['contact', 'scenario'],
  columns: ['study.title', 'result.dna_concentration'],
  filters: [{ field: 'scenario.category', op: 'in', value: ['Handling', 'Wearing'] }],
  study_ids: null,
  sort: [],
}

describe('share links', () => {
  it('round-trips a model, including non-ASCII text', () => {
    const encoded = encodeSharedModel({
      name: 'Übertragung µl – °C',
      description: 'Handschuhe',
      definition,
    })
    expect(encoded).toMatch(/^[A-Za-z0-9_-]+$/)
    expect(decodeSharedModel(encoded)).toEqual({
      name: 'Übertragung µl – °C',
      description: 'Handschuhe',
      definition,
    })
  })

  it('rejects links that are cut off or tampered with', () => {
    const encoded = encodeSharedModel({ name: 'x', definition })
    expect(decodeSharedModel(encoded.slice(0, 10))).toBeNull()
    expect(decodeSharedModel('not base64 at all!')).toBeNull()
    const bogus = btoa(JSON.stringify({ n: 'x', m: { dataset: 1, columns: 'a' } }))
    expect(decodeSharedModel(bogus)).toBeNull()
  })

  it('fills in missing optional parts', () => {
    const minimal = btoa(JSON.stringify({ m: { dataset: 'studies', columns: ['study.title'] } }))
    expect(decodeSharedModel(minimal)).toEqual({
      name: 'Shared data model',
      description: null,
      definition: {
        dataset: 'studies',
        joins: null,
        columns: ['study.title'],
        filters: [],
        study_ids: null,
        sort: [],
      },
    })
  })
})

describe('definition helpers', () => {
  it('detects incomplete filters', () => {
    expect(isFilterComplete({ field: 'a', op: 'in', value: [] })).toBe(false)
    expect(isFilterComplete({ field: 'a', op: 'in', value: ['x'] })).toBe(true)
    expect(isFilterComplete({ field: 'a', op: 'gt', value: null })).toBe(false)
    expect(isFilterComplete({ field: 'a', op: 'gt', value: 0 })).toBe(true)
    expect(isFilterComplete({ field: 'a', op: 'between', value: [null, null] })).toBe(false)
    expect(isFilterComplete({ field: 'a', op: 'between', value: [1, null] })).toBe(true)
    expect(isFilterComplete({ field: 'a', op: 'is_null' })).toBe(true)
    expect(isFilterComplete({ field: 'a', op: 'contains', value: '' })).toBe(false)
  })

  it('leaves incomplete filters and empty study scopes out of requests', () => {
    const request = requestDefinition({
      ...definition,
      filters: [
        ...definition.filters,
        { field: 'result.dna_concentration', op: 'gt', value: null },
      ],
      study_ids: [],
    })
    expect(request.filters).toEqual(definition.filters)
    expect(request.study_ids).toBeNull()
  })

  it('keeps shared joins, columns and filters when switching datasets', () => {
    const switched = switchDataset(definition, contacts)
    expect(switched.dataset).toBe('contacts')
    expect(switched.joins).toEqual(['scenario'])
    expect(switched.columns).toEqual(['study.title'])
    expect(switched.filters).toEqual(definition.filters)
  })
})

const field = (key: string, table: string) => ({
  key,
  label: key,
  group: table,
  table,
  type: 'category' as const,
})

const results: CatalogDataset = {
  key: 'results',
  label: 'Results',
  description: '',
  default_sort: [],
  tables: [
    { key: 'result', label: 'Result', description: '', requires: [], required: true },
    { key: 'study', label: 'Study', description: '', requires: [], required: true },
    { key: 'contact', label: 'Contact', description: '', requires: [], required: false },
    { key: 'scenario', label: 'Scenario', description: '', requires: ['contact'], required: false },
    {
      key: 'donor_surface',
      label: 'Donor surface',
      description: '',
      requires: ['contact'],
      required: false,
    },
    { key: 'laboratory', label: 'Laboratory', description: '', requires: [], required: false },
  ],
  fields: [
    field('study.title', 'study'),
    field('result.dna_concentration', 'result'),
    field('contact.duration', 'contact'),
    field('scenario.category', 'scenario'),
    field('donor_surface.label', 'donor_surface'),
    field('laboratory.name', 'laboratory'),
  ],
}

const contacts: CatalogDataset = {
  key: 'contacts',
  label: 'Contacts',
  description: '',
  default_sort: [],
  tables: [
    { key: 'contact', label: 'Contact', description: '', requires: [], required: true },
    { key: 'study', label: 'Study', description: '', requires: [], required: true },
    { key: 'scenario', label: 'Scenario', description: '', requires: [], required: false },
  ],
  fields: [field('study.title', 'study'), field('scenario.category', 'scenario')],
}

describe('joins', () => {
  const base: DataModelDefinition = {
    dataset: 'results',
    joins: [],
    columns: ['study.title'],
    filters: [],
    study_ids: null,
    sort: [],
  }

  it('joins the tables a table requires', () => {
    expect(addJoin(base, results, 'donor_surface').joins).toEqual(['contact', 'donor_surface'])
  })

  it('offers only fields of required and joined tables', () => {
    const keys = (joins: string[]) => joinedFields(results, joins).map((f) => f.key)
    expect(keys([])).toEqual(['study.title', 'result.dna_concentration'])
    expect(keys(['scenario'])).toEqual([
      'study.title',
      'result.dna_concentration',
      'contact.duration',
      'scenario.category',
    ])
  })

  it('removing a table removes its dependents and their columns and filters', () => {
    const joined: DataModelDefinition = {
      ...base,
      joins: ['contact', 'scenario', 'donor_surface', 'laboratory'],
      columns: ['study.title', 'contact.duration', 'donor_surface.label', 'laboratory.name'],
      filters: [{ field: 'scenario.category', op: 'in', value: ['Handling'] }],
    }
    const result = removeJoin(joined, results, 'contact')
    expect(result.definition.joins).toEqual(['laboratory'])
    expect(result.definition.columns).toEqual(['study.title', 'laboratory.name'])
    expect(result.definition.filters).toEqual([])
    expect(result.removedColumns).toBe(2)
    expect(result.removedFilters).toBe(1)
  })

  it('infers joins for models saved without them', () => {
    const old: DataModelDefinition = {
      ...base,
      joins: null,
      columns: ['study.title', 'donor_surface.label'],
      filters: [{ field: 'laboratory.name', op: 'eq', value: 'x' }],
    }
    expect(inferJoins(old, results)).toEqual(['contact', 'donor_surface', 'laboratory'])
    expect(withJoins(old, results).joins).toEqual(['contact', 'donor_surface', 'laboratory'])
    expect(withJoins(base, results)).toBe(base)
  })
})

describe('browser-saved data models', () => {
  beforeEach(() => {
    localStorage.clear()
    vi.resetModules()
  })

  it('creates, updates and removes models in localStorage', async () => {
    const { useLocalDataModels, isLocalId, LOCAL_DATA_MODELS_KEY } =
      await import('@/composables/useLocalDataModels')
    const local = useLocalDataModels()

    const created = local.create({ name: 'Mine', definition })
    expect(isLocalId(created.id)).toBe(true)
    expect(created.source).toBe('local')
    expect(JSON.parse(localStorage.getItem(LOCAL_DATA_MODELS_KEY)!)).toHaveLength(1)

    local.update(created.id, { name: 'Renamed', is_public: true })
    expect(local.get(created.id)?.name).toBe('Renamed')
    // Browser-saved models can't be public.
    expect(local.get(created.id)?.is_public).toBe(false)

    local.remove(created.id)
    expect(local.models.value).toEqual([])
    expect(JSON.parse(localStorage.getItem(LOCAL_DATA_MODELS_KEY)!)).toEqual([])
  })

  it('survives corrupt storage', async () => {
    localStorage.setItem('transact-data-models', '{not json')
    const { useLocalDataModels } = await import('@/composables/useLocalDataModels')
    expect(useLocalDataModels().models.value).toEqual([])
  })
})
