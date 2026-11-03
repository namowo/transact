<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import DataView from 'openvue/dataview'
import { useAuthStore } from '@/stores/auth'
import { samplingMethodApi } from '@/api/methods'
import { getLabMethodConfig, type MethodFieldConfig } from '@/data/labMethods'
import type { SamplingMethod } from '@/api/types'
import SamplingMethodFormModal from './SamplingMethodFormModal.vue'

const auth = useAuthStore()
const laboratoryId = computed(() => auth.user?.laboratory_id ?? null)

const items = ref<SamplingMethod[]>([])
const loading = ref(false)
const loadError = ref('')

const subMethodBadges: Array<{
  key: keyof SamplingMethod
  configKey: string
  label: string
  color: 'primary' | 'secondary' | 'success' | 'warning' | 'error' | 'info' | 'neutral'
}> = [
  { key: 'swab_method', configKey: 'swab', label: 'Swab', color: 'primary' },
  { key: 'tape_method', configKey: 'tape', label: 'Tape', color: 'secondary' },
  { key: 'vacuum_method', configKey: 'vacuum', label: 'Vacuum', color: 'success' },
  { key: 'cutting_method', configKey: 'cutting', label: 'Cutting', color: 'warning' },
  { key: 'scraping_method', configKey: 'scraping', label: 'Scraping', color: 'info' },
  { key: 'picking_method', configKey: 'picking', label: 'Picking', color: 'error' },
]

type SamplingMethodEntry = {
  label: string
  color: (typeof subMethodBadges)[number]['color']
  details: Array<{ label: string; value: string }>
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any -- sub-method record shape is dynamic per method
function formatFieldValue(field: MethodFieldConfig, record: Record<string, any>): string | null {
  if (field.type === 'category') {
    const relationKey = field.key.replace(/_id$/, '')
    const value = record[relationKey]?.name
    return value ? String(value) : null
  }
  if (field.type === 'boolean') {
    return record[field.key] ? 'Yes' : null
  }
  const value = record[field.key]
  if (value === null || value === undefined || value === '') return null
  if (field.type === 'number') {
    return field.unit ? `${value} ${field.unit}` : String(value)
  }
  if (field.type === 'select') {
    return field.options?.find((o) => o.value === value)?.label ?? String(value)
  }
  return String(value)
}

const rows = computed(() =>
  items.value.map((item) => ({
    item,
    entries: subMethodBadges
      // eslint-disable-next-line @typescript-eslint/no-explicit-any -- sub-method field is dynamic per key
      .filter((badge) => (item as any)[badge.key])
      .map((badge): SamplingMethodEntry => {
        // eslint-disable-next-line @typescript-eslint/no-explicit-any -- sub-method field is dynamic per key
        const record = (item as any)[badge.key] as Record<string, unknown>
        const config = getLabMethodConfig(badge.configKey)
        const details = (config?.fields ?? [])
          .map((field) => {
            const value = formatFieldValue(field, record)
            return value ? { label: field.label, value } : null
          })
          .filter((d): d is { label: string; value: string } => !!d)
        return { label: badge.label, color: badge.color, details }
      }),
  })),
)

const searchTerm = ref('')

const filteredRows = computed(() => {
  const term = searchTerm.value.trim().toLowerCase()
  if (!term) return rows.value
  return rows.value.filter(
    (row) =>
      row.entries.some((entry) => entry.label.toLowerCase().includes(term)) ||
      row.entries.some((entry) =>
        entry.details.some(
          (d) => d.label.toLowerCase().includes(term) || d.value.toLowerCase().includes(term),
        ),
      ),
  )
})

async function load() {
  loading.value = true
  loadError.value = ''
  try {
    const all = await samplingMethodApi.list()
    items.value = all.filter((item) => item.laboratory_id === laboratoryId.value)
  } catch {
    loadError.value = 'Could not load sampling methods. Please try again.'
  } finally {
    loading.value = false
  }
}

onMounted(load)

const modalVisible = ref(false)
const editingRow = ref<SamplingMethod | null>(null)
const duplicateFrom = ref<SamplingMethod | null>(null)

function openCreate() {
  editingRow.value = null
  duplicateFrom.value = null
  modalVisible.value = true
}

function openEdit(row: SamplingMethod) {
  editingRow.value = row
  duplicateFrom.value = null
  modalVisible.value = true
}

function openDuplicate(row: SamplingMethod) {
  editingRow.value = null
  duplicateFrom.value = row
  modalVisible.value = true
}

async function deleteRow(row: SamplingMethod) {
  if (!window.confirm('Delete this entry? This cannot be undone.')) return
  try {
    await samplingMethodApi.delete(row.id)
    items.value = items.value.filter((item) => item.id !== row.id)
  } catch {
    loadError.value = 'Could not delete this entry. Please try again.'
  }
}
</script>

<template>
  <div class="flex flex-col gap-6">
    <div class="flex items-center justify-between">
      <h1 class="text-2xl font-bold text-surface-900 dark:text-surface-0">Sampling methods</h1>
      <UButton label="Add sampling method" icon="i-lucide-plus" @click="openCreate" />
    </div>

    <UAlert v-if="loadError" color="error" variant="outline" :description="loadError" />

    <div class="flex items-center justify-end">
      <UInput
        v-model="searchTerm"
        type="text"
        icon="i-lucide-search"
        placeholder="Keyword Search"
      />
    </div>

    <DataView :value="filteredRows" data-key="item.id" paginator :rows="10">
      <template #empty>No entries found.</template>

      <template #list="{ items: listItems }">
        <div class="flex flex-col gap-3">
          <UCard v-for="row in listItems" :key="row.item.id">
            <div class="flex items-start justify-between gap-4">
              <div class="flex flex-col gap-3 min-w-0">
                <span v-if="!row.entries.length" class="text-sm text-surface-500 dark:text-surface-400">
                  No sub-methods set
                </span>

                <div v-for="entry in row.entries" :key="entry.label" class="flex flex-col gap-1">
                  <UBadge :label="entry.label" :color="entry.color" variant="subtle" class="self-start" />
                  <dl v-if="entry.details.length" class="grid grid-cols-[auto_1fr] gap-x-3 gap-y-0.5 pl-1">
                    <template v-for="detail in entry.details" :key="detail.label">
                      <dt class="text-sm text-surface-500 dark:text-surface-400">{{ detail.label }}</dt>
                      <dd class="text-sm text-surface-700 dark:text-surface-300">{{ detail.value }}</dd>
                    </template>
                  </dl>
                </div>
              </div>

              <div class="flex gap-1 shrink-0">
                <UButton
                  icon="i-lucide-pencil"
                  variant="ghost"
                  square
                  aria-label="Edit"
                  @click="openEdit(row.item)"
                />
                <UButton
                  icon="i-lucide-copy"
                  variant="ghost"
                  square
                  aria-label="Duplicate"
                  @click="openDuplicate(row.item)"
                />
                <UButton
                  icon="i-lucide-trash-2"
                  variant="ghost"
                  square
                  color="error"
                  aria-label="Delete"
                  @click="deleteRow(row.item)"
                />
              </div>
            </div>
          </UCard>
        </div>
      </template>
    </DataView>

    <SamplingMethodFormModal
      v-model:visible="modalVisible"
      :editing-row="editingRow"
      :duplicate-from="duplicateFrom"
      @saved="load"
    />
  </div>
</template>
