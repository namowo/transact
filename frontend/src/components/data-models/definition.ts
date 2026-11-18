import type {
  CatalogDataset,
  CatalogField,
  DataModelDefinition,
  DataModelFilter,
} from '@/api/types'
import { isListOperator, operatorNeedsValue } from './fieldLabel'

/** Whether a filter has everything it needs to be applied. Filters still
 * being edited (no value yet) are left out of previews and downloads. */
export function isFilterComplete(filter: DataModelFilter): boolean {
  if (!operatorNeedsValue(filter.op)) return true
  const value = filter.value
  if (isListOperator(filter.op)) return Array.isArray(value) && value.length > 0
  if (filter.op === 'between') {
    return Array.isArray(value) && value.some((v) => v !== null && v !== '' && v !== undefined)
  }
  return value !== null && value !== undefined && value !== ''
}

/** The definition as sent to the server: complete filters only. */
export function requestDefinition(definition: DataModelDefinition): DataModelDefinition {
  return {
    ...definition,
    filters: definition.filters.filter(isFilterComplete),
    study_ids: definition.study_ids?.length ? definition.study_ids : null,
  }
}

// --- Tables -------------------------------------------------------------------

/** The given tables plus everything they require, as optional table keys
 * in the dataset's order. */
export function withRequirements(dataset: CatalogDataset, keys: Iterable<string>): string[] {
  const byKey = new Map(dataset.tables.map((t) => [t.key, t]))
  const wanted = new Set<string>()
  const pending = [...keys]
  while (pending.length) {
    const key = pending.pop()!
    const table = byKey.get(key)
    if (!table || wanted.has(key)) continue
    wanted.add(key)
    pending.push(...table.requires)
  }
  return dataset.tables.filter((t) => !t.required && wanted.has(t.key)).map((t) => t.key)
}

/** Tables that require `key`, directly or through others. */
export function dependentsOf(dataset: CatalogDataset, key: string): string[] {
  const dependents = new Set<string>()
  let changed = true
  while (changed) {
    changed = false
    for (const table of dataset.tables) {
      if (dependents.has(table.key)) continue
      if (table.requires.some((r) => r === key || dependents.has(r))) {
        dependents.add(table.key)
        changed = true
      }
    }
  }
  return [...dependents]
}

function usedFieldKeys(definition: DataModelDefinition): string[] {
  return [
    ...definition.columns,
    ...definition.filters.map((f) => f.field),
    ...definition.sort.map((s) => s.field),
  ]
}

/** The joins a definition without explicit ones needs for its fields. */
export function inferJoins(definition: DataModelDefinition, dataset: CatalogDataset): string[] {
  const tableOf = new Map(dataset.fields.map((f) => [f.key, f.table]))
  const tables = usedFieldKeys(definition)
    .map((key) => tableOf.get(key))
    .filter((t): t is string => !!t)
  return withRequirements(dataset, tables)
}

/** Fields of the required tables and the joined ones. */
export function joinedFields(dataset: CatalogDataset, joins: string[] | null): CatalogField[] {
  const joined = new Set([
    ...dataset.tables.filter((t) => t.required).map((t) => t.key),
    ...withRequirements(dataset, joins ?? []),
  ])
  return dataset.fields.filter((f) => joined.has(f.table))
}

/** Keep only columns, filters and sorts whose tables are joined. */
function pruneToJoins(
  definition: DataModelDefinition,
  dataset: CatalogDataset,
): DataModelDefinition {
  const keys = new Set(joinedFields(dataset, definition.joins).map((f) => f.key))
  return {
    ...definition,
    columns: definition.columns.filter((key) => keys.has(key)),
    filters: definition.filters.filter((f) => keys.has(f.field)),
    sort: definition.sort.filter((s) => keys.has(s.field)),
  }
}

export function addJoin(
  definition: DataModelDefinition,
  dataset: CatalogDataset,
  key: string,
): DataModelDefinition {
  return { ...definition, joins: withRequirements(dataset, [...(definition.joins ?? []), key]) }
}

/** Remove a table, the tables that depend on it, and the columns and
 * filters that came from them. */
export function removeJoin(
  definition: DataModelDefinition,
  dataset: CatalogDataset,
  key: string,
): { definition: DataModelDefinition; removedColumns: number; removedFilters: number } {
  const dropped = new Set([key, ...dependentsOf(dataset, key)])
  const next = pruneToJoins(
    { ...definition, joins: (definition.joins ?? []).filter((k) => !dropped.has(k)) },
    dataset,
  )
  return {
    definition: next,
    removedColumns: definition.columns.length - next.columns.length,
    removedFilters: definition.filters.length - next.filters.length,
  }
}

/** Carry a definition over to another dataset, keeping the joins, columns
 * and filters the new dataset also offers. */
export function switchDataset(
  definition: DataModelDefinition,
  dataset: CatalogDataset,
): DataModelDefinition {
  const next = pruneToJoins(
    {
      ...definition,
      dataset: dataset.key,
      joins: withRequirements(dataset, definition.joins ?? []),
    },
    dataset,
  )
  return next.columns.length ? next : { ...next, columns: defaultColumns(dataset) }
}

export function defaultColumns(dataset: CatalogDataset): string[] {
  const preferred = ['study.title', 'study.year', 'study.doi']
  const available = new Set(joinedFields(dataset, []).map((f) => f.key))
  return preferred.filter((key) => available.has(key))
}

export function emptyDefinition(dataset: CatalogDataset): DataModelDefinition {
  return {
    dataset: dataset.key,
    joins: [],
    columns: defaultColumns(dataset),
    filters: [],
    study_ids: null,
    sort: [],
  }
}

/** Fill in joins for definitions that don't spell them out. */
export function withJoins(
  definition: DataModelDefinition,
  dataset: CatalogDataset,
): DataModelDefinition {
  return Array.isArray(definition.joins)
    ? definition
    : { ...definition, joins: inferJoins(definition, dataset) }
}
