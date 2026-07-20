<script setup lang="ts">
import { onMounted, ref } from 'vue'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Button from 'primevue/button'
import Dialog from 'primevue/dialog'
import Select from 'primevue/select'
import Message from 'primevue/message'
import LaboratorySelect from '@/components/auth/LaboratorySelect.vue'
import {
  cuttingMethodApi,
  pickingMethodApi,
  samplingMethodApi,
  scrapingMethodApi,
  swabMethodApi,
  tapeMethodApi,
  vacuumMethodApi,
} from '@/api/methods'
import type {
  CuttingMethod,
  PickingMethod,
  SamplingMethod,
  ScrapingMethod,
  SwabMethod,
  TapeMethod,
  VacuumMethod,
} from '@/api/types'

const items = ref<SamplingMethod[]>([])
const loading = ref(false)
const loadError = ref('')

const swabMethods = ref<SwabMethod[]>([])
const tapeMethods = ref<TapeMethod[]>([])
const vacuumMethods = ref<VacuumMethod[]>([])
const cuttingMethods = ref<CuttingMethod[]>([])
const scrapingMethods = ref<ScrapingMethod[]>([])
const pickingMethods = ref<PickingMethod[]>([])

function describeSubMethod(m: { id: number; description?: string | null }) {
  return m.description?.trim() || `#${m.id}`
}

async function load() {
  loading.value = true
  loadError.value = ''
  try {
    const [sampling, swab, tape, vacuum, cutting, scraping, picking] = await Promise.all([
      samplingMethodApi.list(),
      swabMethodApi.list(),
      tapeMethodApi.list(),
      vacuumMethodApi.list(),
      cuttingMethodApi.list(),
      scrapingMethodApi.list(),
      pickingMethodApi.list(),
    ])
    items.value = sampling
    swabMethods.value = swab
    tapeMethods.value = tape
    vacuumMethods.value = vacuum
    cuttingMethods.value = cutting
    scrapingMethods.value = scraping
    pickingMethods.value = picking
  } catch {
    loadError.value = 'Could not load sampling methods. Please try again.'
  } finally {
    loading.value = false
  }
}

onMounted(load)

interface SamplingForm {
  laboratory_id: number | null
  swab_method_id: number | null
  tape_method_id: number | null
  vacuum_method_id: number | null
  cutting_method_id: number | null
  scraping_method_id: number | null
  picking_method_id: number | null
}

function emptyForm(): SamplingForm {
  return {
    laboratory_id: null,
    swab_method_id: null,
    tape_method_id: null,
    vacuum_method_id: null,
    cutting_method_id: null,
    scraping_method_id: null,
    picking_method_id: null,
  }
}

const dialogVisible = ref(false)
const editingId = ref<number | null>(null)
const form = ref<SamplingForm>(emptyForm())
const submitting = ref(false)
const submitError = ref('')

function openCreateDialog() {
  editingId.value = null
  form.value = emptyForm()
  submitError.value = ''
  dialogVisible.value = true
}

function openEditDialog(row: SamplingMethod) {
  editingId.value = row.id
  form.value = {
    laboratory_id: row.laboratory_id ?? null,
    swab_method_id: row.swab_method_id ?? null,
    tape_method_id: row.tape_method_id ?? null,
    vacuum_method_id: row.vacuum_method_id ?? null,
    cutting_method_id: row.cutting_method_id ?? null,
    scraping_method_id: row.scraping_method_id ?? null,
    picking_method_id: row.picking_method_id ?? null,
  }
  submitError.value = ''
  dialogVisible.value = true
}

async function submitForm() {
  submitting.value = true
  submitError.value = ''
  try {
    if (editingId.value === null) {
      const created = await samplingMethodApi.create(form.value)
      items.value = [...items.value, created]
    } else {
      const updated = await samplingMethodApi.update(editingId.value, form.value)
      items.value = items.value.map((item) => (item.id === updated.id ? updated : item))
    }
    dialogVisible.value = false
  } catch {
    submitError.value = 'Could not save this entry. Please try again.'
  } finally {
    submitting.value = false
  }
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
      <Button label="Add entry" icon="pi pi-plus" @click="openCreateDialog" />
    </div>

    <Message v-if="loadError" severity="error" size="small">{{ loadError }}</Message>

    <div class="overflow-x-auto">
      <DataTable :value="items" :loading="loading" data-key="id">
        <Column header="Laboratory">
          <template #body="{ data }">{{ data.laboratory?.laboratory_name ?? '—' }}</template>
        </Column>
        <Column header="Swab">
          <template #body="{ data }">{{ data.swab_method ? describeSubMethod(data.swab_method) : '—' }}</template>
        </Column>
        <Column header="Tape">
          <template #body="{ data }">{{ data.tape_method ? describeSubMethod(data.tape_method) : '—' }}</template>
        </Column>
        <Column header="Vacuum">
          <template #body="{ data }">{{ data.vacuum_method ? describeSubMethod(data.vacuum_method) : '—' }}</template>
        </Column>
        <Column header="" style="width: 6rem">
          <template #body="{ data }">
            <div class="flex gap-1 justify-end">
              <Button icon="pi pi-pencil" text rounded aria-label="Edit" @click="openEditDialog(data)" />
              <Button
                icon="pi pi-trash"
                text
                rounded
                severity="danger"
                aria-label="Delete"
                @click="deleteRow(data)"
              />
            </div>
          </template>
        </Column>
      </DataTable>
    </div>

    <Dialog
      v-model:visible="dialogVisible"
      :header="editingId === null ? 'Add sampling method entry' : 'Edit entry'"
      modal
      :style="{ width: '32rem' }"
    >
      <div class="flex flex-col gap-4">
        <div class="flex flex-col gap-2">
          <label class="font-medium text-sm">Laboratory</label>
          <LaboratorySelect v-model="form.laboratory_id" />
        </div>
        <div class="flex flex-col gap-2">
          <label class="font-medium text-sm">Swab method</label>
          <Select
            v-model="form.swab_method_id"
            :options="swabMethods"
            :option-label="(o: SwabMethod) => describeSubMethod(o)"
            option-value="id"
            show-clear
            filter
            fluid
            placeholder="Select a swab method"
          />
        </div>
        <div class="flex flex-col gap-2">
          <label class="font-medium text-sm">Tape method</label>
          <Select
            v-model="form.tape_method_id"
            :options="tapeMethods"
            :option-label="(o: TapeMethod) => describeSubMethod(o)"
            option-value="id"
            show-clear
            filter
            fluid
            placeholder="Select a tape method"
          />
        </div>
        <div class="flex flex-col gap-2">
          <label class="font-medium text-sm">Vacuum method</label>
          <Select
            v-model="form.vacuum_method_id"
            :options="vacuumMethods"
            :option-label="(o: VacuumMethod) => describeSubMethod(o)"
            option-value="id"
            show-clear
            filter
            fluid
            placeholder="Select a vacuum method"
          />
        </div>
        <div class="flex flex-col gap-2">
          <label class="font-medium text-sm">Cutting method</label>
          <Select
            v-model="form.cutting_method_id"
            :options="cuttingMethods"
            :option-label="(o: CuttingMethod) => describeSubMethod(o)"
            option-value="id"
            show-clear
            filter
            fluid
            placeholder="Select a cutting method"
          />
        </div>
        <div class="flex flex-col gap-2">
          <label class="font-medium text-sm">Scraping method</label>
          <Select
            v-model="form.scraping_method_id"
            :options="scrapingMethods"
            :option-label="(o: ScrapingMethod) => describeSubMethod(o)"
            option-value="id"
            show-clear
            filter
            fluid
            placeholder="Select a scraping method"
          />
        </div>
        <div class="flex flex-col gap-2">
          <label class="font-medium text-sm">Picking method</label>
          <Select
            v-model="form.picking_method_id"
            :options="pickingMethods"
            :option-label="(o: PickingMethod) => describeSubMethod(o)"
            option-value="id"
            show-clear
            filter
            fluid
            placeholder="Select a picking method"
          />
        </div>

        <Message v-if="submitError" severity="error" size="small">{{ submitError }}</Message>
      </div>
      <template #footer>
        <Button label="Cancel" text @click="dialogVisible = false" />
        <Button label="Save" :loading="submitting" @click="submitForm" />
      </template>
    </Dialog>
  </div>
</template>
