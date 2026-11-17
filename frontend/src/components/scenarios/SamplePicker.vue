<script setup lang="ts">
import { computed, ref } from 'vue'
import DataTable from 'openvue/datatable'
import Column from 'openvue/column'
import { FilterMatchMode } from '@openvue/core/api'
import { surfaceLabel, sampleSetLabel, extractionMethodLabel } from '@/components/data/sampleLabel'
import type { Sample } from '@/api/types'

// Picking a sample by a bare id is meaningless once a study has more than
// a handful, so this mirrors ItemSelect's filterable-table picker: a button
// showing the current pick opens a modal table with enough columns (surface,
// sample set, methods, elution volume, area) to tell rows apart at a
// glance, instead of a flat dropdown of ids.
const props = defineProps<{ samples: Sample[]; error?: string }>()

const sampleId = defineModel<string | null>({ default: null })

const selectedSample = computed(
  () => props.samples.find((r) => r.id === sampleId.value) ?? null,
)

function sampleButtonLabel(sample: Sample | null): string {
  if (!sample) return 'Select a sample'
  return surfaceLabel(sample.surface)
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

interface SampleRow {
  sample: Sample
  surfaceLabel: string
  sampleSetLabel: string
  extractionMethodLabel: string
}

const rows = computed<SampleRow[]>(() =>
  props.samples.map((sample) => ({
    sample,
    surfaceLabel: surfaceLabel(sample.surface),
    sampleSetLabel: sampleSetLabel(sample.sample_set),
    extractionMethodLabel: extractionMethodLabel(sample.extraction_method),
  })),
)

function selectSample(sample: Sample) {
  sampleId.value = sample.id
  pickerVisible.value = false
}
</script>

<template>
  <UFormField label="Sample" :error="error">
    <div class="flex gap-2">
      <UButton
        :label="sampleButtonLabel(selectedSample)"
        icon="i-lucide-search"
        color="neutral"
        variant="outline"
        class="w-full justify-start"
        :ui="{ base: 'truncate' }"
        @click="pickerVisible = true"
      />
      <UButton
        v-if="sampleId"
        icon="i-lucide-x"
        variant="ghost"
        aria-label="Clear sample"
        @click="sampleId = null"
      />
    </div>
  </UFormField>

  <UModal
    v-model:open="pickerVisible"
    title="Select a sample"
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
          data-key="sample.id"
          :global-filter-fields="['surfaceLabel', 'sampleSetLabel', 'extractionMethodLabel']"
          filter-display="menu"
          scrollable
          scroll-height="24rem"
          selection-mode="single"
          :meta-key-selection="false"
          :row-class="() => 'cursor-pointer hover:bg-elevated'"
          @row-click="({ data }: { data: SampleRow }) => selectSample(data.sample)"
        >
          <template #empty>No samples found.</template>
          <Column field="surfaceLabel" header="Surface" sortable>
            <template #body="{ data }">{{ data.surfaceLabel }}</template>
          </Column>
          <Column field="sampleSetLabel" header="Sample set" sortable>
            <template #body="{ data }">{{ data.sampleSetLabel }}</template>
          </Column>
          <Column field="extractionMethodLabel" header="Extraction method" sortable>
            <template #body="{ data }">{{ data.extractionMethodLabel }}</template>
          </Column>
          <Column header="Elution volume">
            <template #body="{ data }">
              {{ data.sample.elution_volume != null ? `${data.sample.elution_volume} µL` : '—' }}
            </template>
          </Column>
          <Column header="Area">
            <template #body="{ data }">
              {{ data.sample.area != null ? `${data.sample.area} cm²` : '—' }}
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
