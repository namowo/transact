<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Button from 'primevue/button'
import Dialog from 'primevue/dialog'
import InputText from 'primevue/inputtext'
import InputNumber from 'primevue/inputnumber'
import Textarea from 'primevue/textarea'
import ToggleSwitch from 'primevue/toggleswitch'
import Message from 'primevue/message'
import LaboratorySelect from '@/components/auth/LaboratorySelect.vue'
import CategorySelect from '@/components/scenarios/CategorySelect.vue'
import { getLabMethodConfig, type MethodFieldConfig } from '@/data/labMethods'

const props = defineProps<{ methodKey: string }>()

const config = computed(() => getLabMethodConfig(props.methodKey))

const items = ref<any[]>([])
const loading = ref(false)
const loadError = ref('')

async function load() {
  if (!config.value) return
  loading.value = true
  loadError.value = ''
  try {
    items.value = await config.value.api.list()
  } catch {
    loadError.value = 'Could not load this list. Please try again.'
  } finally {
    loading.value = false
  }
}

onMounted(load)
watch(() => props.methodKey, load)

function emptyForm(fields: MethodFieldConfig[]): Record<string, any> {
  const form: Record<string, any> = {}
  for (const field of fields) {
    form[field.key] = field.type === 'boolean' ? false : null
  }
  return form
}

const dialogVisible = ref(false)
const editingId = ref<number | null>(null)
const form = ref<Record<string, any>>({})
const submitting = ref(false)
const submitError = ref('')

function openCreateDialog() {
  if (!config.value) return
  editingId.value = null
  form.value = emptyForm(config.value.fields)
  submitError.value = ''
  dialogVisible.value = true
}

function openEditDialog(row: Record<string, any>) {
  if (!config.value) return
  editingId.value = row.id
  const next = emptyForm(config.value.fields)
  for (const field of config.value.fields) {
    next[field.key] = row[field.key] ?? (field.type === 'boolean' ? false : null)
  }
  form.value = next
  submitError.value = ''
  dialogVisible.value = true
}

async function submitForm() {
  if (!config.value) return
  submitting.value = true
  submitError.value = ''
  try {
    if (editingId.value === null) {
      const created = await config.value.api.create(form.value)
      items.value = [...items.value, created]
    } else {
      const updated = await config.value.api.update(editingId.value, form.value)
      items.value = items.value.map((item) => (item.id === updated.id ? updated : item))
    }
    dialogVisible.value = false
  } catch {
    submitError.value = 'Could not save this entry. Please try again.'
  } finally {
    submitting.value = false
  }
}

async function deleteRow(row: Record<string, any>) {
  if (!config.value) return
  if (!window.confirm('Delete this entry? This cannot be undone.')) return
  try {
    await config.value.api.delete(row.id)
    items.value = items.value.filter((item) => item.id !== row.id)
  } catch {
    loadError.value = 'Could not delete this entry. Please try again.'
  }
}

function columnValue(row: Record<string, any>, key: string) {
  const value = row[key]
  if (typeof value === 'boolean') return value ? 'Yes' : 'No'
  return value ?? '—'
}
</script>

<template>
  <div v-if="config" class="flex flex-col gap-6">
    <div class="flex items-center justify-between">
      <h1 class="text-2xl font-bold text-surface-900 dark:text-surface-0">
        {{ config.label }} methods
      </h1>
      <Button label="Add entry" icon="pi pi-plus" @click="openCreateDialog" />
    </div>

    <Message v-if="loadError" severity="error" size="small">{{ loadError }}</Message>

    <div class="overflow-x-auto">
      <DataTable :value="items" :loading="loading" data-key="id">
        <Column
          v-for="colKey in config.listColumns"
          :key="colKey"
          :field="colKey"
          :header="config.fields.find((f) => f.key === colKey)?.label ?? colKey"
        >
          <template #body="{ data }">{{ columnValue(data, colKey) }}</template>
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
      :header="editingId === null ? `Add ${config.label.toLowerCase()} entry` : `Edit entry`"
      modal
      :style="{ width: '32rem' }"
    >
      <div class="flex flex-col gap-4">
        <div v-for="field in config.fields" :key="field.key" class="flex flex-col gap-2">
          <label class="font-medium text-sm">{{ field.label }}</label>

          <LaboratorySelect v-if="field.type === 'laboratory'" v-model="form[field.key]" />

          <CategorySelect
            v-else-if="field.type === 'category'"
            v-model="form[field.key]"
            :label="field.label"
            :api="field.categoryApi!"
          />

          <InputNumber v-else-if="field.type === 'number'" v-model="form[field.key]" fluid />

          <div v-else-if="field.type === 'boolean'" class="flex items-center gap-2">
            <ToggleSwitch v-model="form[field.key]" :input-id="field.key" />
          </div>

          <Textarea v-else-if="field.type === 'textarea'" v-model="form[field.key]" rows="2" fluid />

          <InputText v-else v-model="form[field.key]" fluid />
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
