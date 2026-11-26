<script setup lang="ts">
import { computed, ref } from 'vue'
import { surfaceLabel, sampleSetLabel, extractionMethodLabel } from '@/components/data/sampleLabel'
import type { Sample } from '@/api/types'
import type { TableColumn, TableRow } from '@nuxt/ui'
import { manualSorting, useTableView } from '@/composables/useTableView'
import { sortHeader } from '@/composables/tableColumns'
import TablePagination from '@/components/ui/TablePagination.vue'

// Picking a sample by a bare id is meaningless once a study has more than
// a handful, so this mirrors ItemSelect's filterable-table picker: a button
// showing the current pick opens a modal table with enough columns (surface,
// sample set, methods, elution volume, area) to tell rows apart at a
// glance, instead of a flat dropdown of ids.
const props = defineProps<{ samples: Sample[]; error?: string }>()

const sampleId = defineModel<string | null>({ default: null })

const selectedSample = computed(() => props.samples.find((r) => r.id === sampleId.value) ?? null)

function sampleButtonLabel(sample: Sample | null): string {
  if (!sample) return 'Select a sample'
  return surfaceLabel(sample.surface)
}

const pickerVisible = ref(false)

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

const view = useTableView(rows, {
  searchFields: ['surfaceLabel', 'sampleSetLabel', 'extractionMethodLabel'],
})

const columns: TableColumn<SampleRow>[] = [
  { id: 'surfaceLabel', accessorKey: 'surfaceLabel', header: sortHeader('Surface') },
  { id: 'sampleSetLabel', accessorKey: 'sampleSetLabel', header: sortHeader('Sample set') },
  {
    id: 'extractionMethodLabel',
    accessorKey: 'extractionMethodLabel',
    header: sortHeader('Extraction method'),
  },
  { id: 'elution_volume', accessorKey: 'elution_volume', header: 'Elution volume' },
  { id: 'area', accessorKey: 'area', header: 'Area' },
]

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
        <UInput
          v-model="view.search"
          icon="i-lucide-search"
          placeholder="Keyword Search"
          class="w-full"
        />

        <UTable
          v-model:sorting="view.sorting"
          :sorting-options="manualSorting"
          :data="view.rows"
          :columns="columns"
          :get-row-id="(row: SampleRow) => row.sample.id"
          empty="No samples found."
          sticky
          class="max-h-96"
          :ui="{ tr: 'cursor-pointer' }"
          :on-select="(_e: Event, row: TableRow<SampleRow>) => selectSample(row.original.sample)"
        >
          <template #elution_volume-cell="{ row }">
            {{
              row.original.sample.elution_volume != null
                ? `${row.original.sample.elution_volume} µL`
                : '—'
            }}
          </template>
          <template #area-cell="{ row }">
            {{ row.original.sample.area != null ? `${row.original.sample.area} cm²` : '—' }}
          </template>
        </UTable>
        <TablePagination
          v-model:page="view.page"
          v-model:page-size="view.pageSize"
          :total="view.total"
        />
      </div>
    </template>
    <template #footer>
      <UButton label="Close" icon="i-lucide-x" variant="ghost" @click="pickerVisible = false" />
    </template>
  </UModal>
</template>
