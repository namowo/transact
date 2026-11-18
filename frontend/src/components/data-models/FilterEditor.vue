<script setup lang="ts">
import { computed, reactive, watch } from 'vue'
import { getFieldValues } from '@/api/dataModels'
import type {
  Catalog,
  CatalogDataset,
  CatalogField,
  DataModelFilter,
  FilterOp,
  FilterValue,
} from '@/api/types'
import { fieldLabel, isListOperator, operatorLabels, operatorNeedsValue } from './fieldLabel'

const props = defineProps<{
  dataset: CatalogDataset
  // The fields of the joined tables.
  fields: CatalogField[]
  operators: Catalog['operators']
}>()
const filters = defineModel<DataModelFilter[]>({ required: true })

const fieldsByKey = computed(() => new Map(props.fields.map((f) => [f.key, f])))

const fieldItems = computed(() => {
  const groups = new Map<string, { label: string; value: string }[]>()
  for (const field of props.fields) {
    const list = groups.get(field.group) ?? []
    list.push({ label: fieldLabel(field), value: field.key })
    groups.set(field.group, list)
  }
  return [...groups.entries()].map(([group, items]) => [
    { type: 'label' as const, label: group },
    ...items,
  ])
})

// Distinct values per field, loaded when a filter needs a picker.
const values = reactive<Record<string, { loading: boolean; items: string[] }>>({})

async function loadValues(field: CatalogField) {
  const cacheKey = `${props.dataset.key}:${field.key}`
  if (values[cacheKey]) return
  values[cacheKey] = { loading: true, items: [] }
  try {
    const result = await getFieldValues(props.dataset.key, field.key)
    values[cacheKey] = { loading: false, items: result.map(String) }
  } catch {
    values[cacheKey] = { loading: false, items: [] }
  }
}

function valuesFor(field: CatalogField) {
  return values[`${props.dataset.key}:${field.key}`] ?? { loading: false, items: [] }
}

function usesPicker(field: CatalogField | undefined, op: FilterOp) {
  if (!field) return false
  return (
    (field.type === 'category' && (isListOperator(op) || op === 'eq' || op === 'neq')) ||
    (field.type === 'string' && isListOperator(op))
  )
}

watch(
  () => filters.value.map((f) => [f.field, f.op]),
  () => {
    for (const flt of filters.value) {
      const field = fieldsByKey.value.get(flt.field)
      if (field && usesPicker(field, flt.op)) loadValues(field)
    }
  },
  { immediate: true },
)

function defaultValue(field: CatalogField, op: FilterOp): FilterValue {
  if (isListOperator(op)) return []
  if (op === 'between') return [null, null]
  if (field.type === 'boolean') return true
  return null
}

function update(index: number, patch: Partial<DataModelFilter>) {
  filters.value = filters.value.map((f, i) => (i === index ? { ...f, ...patch } : f))
}

function setField(index: number, key: string) {
  const field = fieldsByKey.value.get(key)
  if (!field) return
  const op = props.operators[field.type][0]!
  update(index, { field: key, op, value: defaultValue(field, op) })
}

function setOp(index: number, op: FilterOp) {
  const current = filters.value[index]!
  const field = fieldsByKey.value.get(current.field)
  if (!field) return
  // Keep a compatible value when switching between similar operators.
  const keep =
    (isListOperator(op) && isListOperator(current.op)) ||
    (!isListOperator(op) &&
      !isListOperator(current.op) &&
      op !== 'between' &&
      current.op !== 'between')
  update(index, { op, value: keep ? current.value : defaultValue(field, op) })
}

function setBound(index: number, bound: 0 | 1, value: string | number | null) {
  const current = filters.value[index]!
  const bounds = Array.isArray(current.value) ? [...current.value] : [null, null]
  bounds[bound] = value === '' ? null : value
  update(index, { value: bounds as FilterValue })
}

function add() {
  const field = props.fields.find((f) => f.key === 'study.year') ?? props.fields[0]!
  const op = props.operators[field.type][0]!
  filters.value = [...filters.value, { field: field.key, op, value: defaultValue(field, op) }]
}

function remove(index: number) {
  filters.value = filters.value.filter((_, i) => i !== index)
}

function operatorItems(field: CatalogField | undefined) {
  if (!field) return []
  return props.operators[field.type].map((op) => ({ label: operatorLabels[op], value: op }))
}

const booleanItems = [
  { label: 'yes', value: true },
  { label: 'no', value: false },
]

function asArray(value: FilterValue | undefined): (string | number | null)[] {
  return Array.isArray(value) ? value : []
}

function asScalar(value: FilterValue | undefined) {
  return Array.isArray(value) ? null : (value ?? null)
}
</script>

<template>
  <div class="flex flex-col gap-3">
    <p v-if="!filters.length" class="text-sm text-muted">
      No filters: every row from the selected studies is included.
    </p>

    <div
      v-for="(flt, index) in filters"
      :key="index"
      class="flex items-start gap-2 rounded-md border border-default p-2"
    >
      <div class="flex min-w-0 flex-1 flex-col gap-2 lg:flex-row lg:items-start">
        <USelectMenu
          :model-value="flt.field"
          :items="fieldItems"
          value-key="value"
          class="w-full lg:w-80 lg:shrink-0"
          :search-input="{ placeholder: 'Search fields…' }"
          @update:model-value="(key: string) => setField(index, key)"
        />

        <template v-for="field in [fieldsByKey.get(flt.field)]" :key="field?.key ?? flt.field">
          <UAlert
            v-if="!field"
            color="warning"
            variant="subtle"
            :description="`“${flt.field}” isn't available in this dataset. Remove the filter or pick another field.`"
          />
          <div v-else class="flex min-w-0 flex-1 flex-wrap items-center gap-2">
            <USelect
              :model-value="flt.op"
              :items="operatorItems(field)"
              class="w-40"
              @update:model-value="(op: unknown) => setOp(index, op as FilterOp)"
            />

            <template v-if="operatorNeedsValue(flt.op)">
              <!-- Pick from the values present in the data. -->
              <USelectMenu
                v-if="usesPicker(field, flt.op)"
                :model-value="
                  (isListOperator(flt.op) ? asArray(flt.value) : asScalar(flt.value)) as any
                "
                :items="valuesFor(field).items"
                :loading="valuesFor(field).loading"
                :multiple="isListOperator(flt.op)"
                create-item
                placeholder="Choose values"
                class="min-w-48 flex-1"
                @update:model-value="(v: any) => update(index, { value: v })"
                @create="
                  (item: string) =>
                    update(index, {
                      value: isListOperator(flt.op) ? [...asArray(flt.value), item] : item,
                    })
                "
              />

              <USelect
                v-else-if="field.type === 'boolean'"
                :model-value="asScalar(flt.value) as boolean"
                :items="booleanItems"
                class="w-28"
                @update:model-value="(v: unknown) => update(index, { value: v as boolean })"
              />

              <template v-else-if="flt.op === 'between'">
                <template v-if="field.type === 'number'">
                  <UInputNumber
                    :model-value="(asArray(flt.value)[0] as number | null) ?? undefined"
                    placeholder="from"
                    class="w-32"
                    :format-options="{ maximumFractionDigits: 6 }"
                    @update:model-value="
                      (v: number | null | undefined) => setBound(index, 0, v ?? null)
                    "
                  />
                  <span class="text-sm text-muted">and</span>
                  <UInputNumber
                    :model-value="(asArray(flt.value)[1] as number | null) ?? undefined"
                    placeholder="to"
                    class="w-32"
                    :format-options="{ maximumFractionDigits: 6 }"
                    @update:model-value="
                      (v: number | null | undefined) => setBound(index, 1, v ?? null)
                    "
                  />
                </template>
                <template v-else>
                  <UInput
                    type="date"
                    :model-value="(asArray(flt.value)[0] as string | null) ?? ''"
                    @update:model-value="(v: string | number) => setBound(index, 0, String(v))"
                  />
                  <span class="text-sm text-muted">and</span>
                  <UInput
                    type="date"
                    :model-value="(asArray(flt.value)[1] as string | null) ?? ''"
                    @update:model-value="(v: string | number) => setBound(index, 1, String(v))"
                  />
                </template>
              </template>

              <UInputNumber
                v-else-if="field.type === 'number'"
                :model-value="(asScalar(flt.value) as number | null) ?? undefined"
                class="w-36"
                :format-options="{ maximumFractionDigits: 6 }"
                @update:model-value="
                  (v: number | null | undefined) => update(index, { value: v ?? null })
                "
              />

              <UInput
                v-else-if="field.type === 'date'"
                type="date"
                :model-value="(asScalar(flt.value) as string | null) ?? ''"
                @update:model-value="
                  (v: string | number) => update(index, { value: String(v) || null })
                "
              />

              <UInput
                v-else
                :model-value="(asScalar(flt.value) as string | null) ?? ''"
                placeholder="Text"
                class="min-w-48 flex-1"
                @update:model-value="(v: string | number) => update(index, { value: String(v) })"
              />
            </template>
          </div>
        </template>
      </div>
      <UButton
        variant="ghost"
        color="neutral"
        icon="i-lucide-trash-2"
        aria-label="Remove filter"
        @click="remove(index)"
      />
    </div>

    <UButton
      icon="i-lucide-plus"
      variant="soft"
      color="neutral"
      label="Add filter"
      class="self-start"
      @click="add"
    />
  </div>
</template>
