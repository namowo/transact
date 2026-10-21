<script setup lang="ts">
import { computed, ref } from 'vue'
import DataTable from 'openvue/datatable'
import Column from 'openvue/column'
import { FilterMatchMode } from '@openvue/core/api'
import { surfaceLabel, recoverySetLabel, extractionMethodLabel } from '@/components/data/recoveryLabel'
import type { Recovery } from '@/api/types'

// Picking a recovery by a bare id is meaningless once a study has more than
// a handful, so this mirrors ItemSelect's filterable-table picker: a button
// showing the current pick opens a modal table with enough columns (surface,
// recovery set, methods, elution volume, area) to tell rows apart at a
// glance, instead of a flat dropdown of ids.
const props = defineProps<{ recoveries: Recovery[]; error?: string }>()

const recoveryId = defineModel<string | null>({ default: null })

const selectedRecovery = computed(
  () => props.recoveries.find((r) => r.id === recoveryId.value) ?? null,
)

function recoveryButtonLabel(recovery: Recovery | null): string {
  if (!recovery) return 'Select a recovery'
  return surfaceLabel(recovery.surface)
}

const pickerVisible = ref(false)

function initFilters() {
  return {
    global: { value: null, matchMode: FilterMatchMode.CONTAINS },
  }
}

const filters = ref(initFilters())

function clearFilters() {
  filters.value = initFilters()
}

interface RecoveryRow {
  recovery: Recovery
  surfaceLabel: string
  recoverySetLabel: string
  extractionMethodLabel: string
}

const rows = computed<RecoveryRow[]>(() =>
  props.recoveries.map((recovery) => ({
    recovery,
    surfaceLabel: surfaceLabel(recovery.surface),
    recoverySetLabel: recoverySetLabel(recovery.recovery_set),
    extractionMethodLabel: extractionMethodLabel(recovery.extraction_method),
  })),
)

function selectRecovery(recovery: Recovery) {
  recoveryId.value = recovery.id
  pickerVisible.value = false
}
</script>

<template>
  <UFormField label="Recovery" :error="error">
    <div class="flex gap-2">
      <UButton
        :label="recoveryButtonLabel(selectedRecovery)"
        icon="i-lucide-search"
        color="neutral"
        variant="outline"
        class="w-full justify-start"
        :ui="{ base: 'truncate' }"
        @click="pickerVisible = true"
      />
      <UButton
        v-if="recoveryId"
        icon="i-lucide-x"
        variant="ghost"
        aria-label="Clear recovery"
        @click="recoveryId = null"
      />
    </div>
  </UFormField>

  <UModal
    v-model:open="pickerVisible"
    title="Select a recovery"
    :ui="{ content: 'max-w-3xl', footer: 'justify-end' }"
  >
    <template #body>
      <div class="flex flex-col gap-3">
        <div class="flex items-center justify-between gap-3">
          <UButton type="button" icon="i-lucide-filter-x" variant="outline" size="sm" @click="clearFilters()">
            Clear Filters
          </UButton>
          <UInput
            v-model="(filters['global'] as { value: string | null }).value"
            type="text"
            icon="i-lucide-search"
            placeholder="Keyword Search"
            class="w-full"
          />
        </div>

        <DataTable
          v-model:filters="filters"
          :value="rows"
          data-key="recovery.id"
          :global-filter-fields="['surfaceLabel', 'recoverySetLabel', 'extractionMethodLabel']"
          filter-display="menu"
          scrollable
          scroll-height="24rem"
          selection-mode="single"
          :meta-key-selection="false"
          :row-class="() => 'cursor-pointer hover:bg-elevated'"
          @row-click="({ data }: { data: RecoveryRow }) => selectRecovery(data.recovery)"
        >
          <template #empty>No recoveries found.</template>
          <Column field="surfaceLabel" header="Surface" sortable>
            <template #body="{ data }">{{ data.surfaceLabel }}</template>
          </Column>
          <Column field="recoverySetLabel" header="Recovery set" sortable>
            <template #body="{ data }">{{ data.recoverySetLabel }}</template>
          </Column>
          <Column field="extractionMethodLabel" header="Extraction method" sortable>
            <template #body="{ data }">{{ data.extractionMethodLabel }}</template>
          </Column>
          <Column header="Elution volume">
            <template #body="{ data }">
              {{ data.recovery.elution_volume != null ? `${data.recovery.elution_volume} µL` : '—' }}
            </template>
          </Column>
          <Column header="Area">
            <template #body="{ data }">
              {{ data.recovery.area != null ? `${data.recovery.area} cm²` : '—' }}
            </template>
          </Column>
        </DataTable>
      </div>
    </template>
    <template #footer>
      <UButton label="Close" icon="i-lucide-x" variant="ghost" @click="pickerVisible = false" />
    </template>
  </UModal>
</template>
