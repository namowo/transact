<script setup lang="ts">
import { computed, ref } from 'vue'
import { useToast } from '@nuxt/ui/composables'
import { useAuthStore } from '@/stores/auth'
import { downloadTextFile, parseCsv, toCsv, type DecimalSeparator } from './csv'

// Download a table as CSV, edit it in a spreadsheet, upload it again. Shared
// by the tabs that support this round trip; the tab supplies the rows to
// export and applies the uploaded rows.

type Cell = string | number | null | undefined

interface ImportOutcome {
  ok: boolean
  title: string
  description?: string
}

const props = defineProps<{
  disabled?: boolean
  // Base name of the downloaded file, e.g. "my-study_results".
  filename: string
  // Remembers "don't show again" for this tab's explanation.
  hintKey: string
  // Rows to export, header row first.
  buildRows: () => Cell[][]
  // Columns the user may edit / columns that are information only, for the explanation.
  editableColumns: string[]
  infoColumns: string[]
  idColumn: string
  // Extra paragraphs for the explanation pop-up.
  notes?: string[]
  // Applies the uploaded table (header row first); the decimal separator is the user's choice.
  applyImport: (table: string[][], decimal: DecimalSeparator) => Promise<ImportOutcome>
}>()

const toast = useToast()
const auth = useAuthStore()

const hintStorageKey = computed(() => `transact.${props.hintKey}.csvHintDismissed`)
const hintVisible = ref(false)
const hintDontShowAgain = ref(false)

function hintDismissed(): boolean {
  try {
    return localStorage.getItem(hintStorageKey.value) === '1'
  } catch {
    return false
  }
}

function onDownloadClick() {
  if (hintDismissed()) {
    download()
    return
  }
  hintDontShowAgain.value = false
  hintVisible.value = true
}

function confirmDownload() {
  if (hintDontShowAgain.value) {
    try {
      localStorage.setItem(hintStorageKey.value, '1')
    } catch {
      // Storage unavailable: the hint simply shows again next time.
    }
  }
  hintVisible.value = false
  download()
}

function download() {
  const date = new Date().toISOString().slice(0, 10)
  // CSV files always use a point as decimal separator, whatever the profile's number format.
  downloadTextFile(`${props.filename}_${date}.csv`, toCsv(props.buildRows()))
  // The next step of the round trip: edit the file, then upload it here.
  openImportDialog()
}

const importVisible = ref(false)
const importing = ref(false)
const pendingFile = ref<File | null>(null)
const decimalSeparator = ref<DecimalSeparator>(auth.decimalSeparator)

const decimalOptions = [
  { value: '.', label: 'Point', description: 'Example: 1.5' },
  { value: ',', label: 'Comma', description: 'Example: 1,5' },
]
function openImportDialog() {
  pendingFile.value = null
  decimalSeparator.value = auth.decimalSeparator
  importVisible.value = true
}

async function runImport() {
  const file = pendingFile.value
  if (!file) return
  const decimal = decimalSeparator.value
  importVisible.value = false
  importing.value = true
  try {
    const outcome = await props.applyImport(parseCsv(await file.text()), decimal)
    toast.add({
      color: outcome.ok ? 'success' : 'error',
      title: outcome.title,
      description: outcome.description,
      duration: outcome.ok ? undefined : 10000,
    })
  } catch {
    toast.add({
      color: 'error',
      title: 'Import failed',
      description: 'Could not read or save this file. Please try again.',
    })
  } finally {
    importing.value = false
  }
}
</script>

<template>
  <div class="flex items-center gap-2 border border-default rounded-md px-2 py-1">
    <span class="text-xs font-medium text-muted">CSV</span>
    <UButton
      type="button"
      label="Download"
      icon="i-lucide-download"
      variant="outline"
      size="sm"
      :disabled="disabled"
      @click="onDownloadClick"
    />
    <UButton
      type="button"
      label="Upload"
      icon="i-lucide-upload"
      variant="outline"
      size="sm"
      :loading="importing"
      :disabled="disabled"
      @click="openImportDialog"
    />

    <UModal
      v-model:open="importVisible"
      title="Upload CSV"
      :ui="{ content: 'max-w-md', footer: 'justify-end' }"
    >
      <template #body>
        <div class="flex flex-col gap-4">
          <p class="text-sm text-surface-500 dark:text-surface-400">
            Upload a file downloaded from this table. The columns {{ editableColumns.join(', ') }} will replace the
            current values. The {{ idColumn }} and info_* columns are not changed.
          </p>
          <UFileUpload
            v-model="pendingFile"
            accept=".csv,text/csv"
            label="Drop your CSV file here"
            description="or click to choose a file"
            icon="i-lucide-file-spreadsheet"
            class="w-full min-h-32"
          />
          <URadioGroup
            v-model="decimalSeparator"
            legend="Decimal separator used in the file"
            :items="decimalOptions"
          />
        </div>
      </template>
      <template #footer>
        <UButton label="Cancel" icon="i-lucide-x" variant="ghost" @click="importVisible = false" />
        <UButton label="Import" icon="i-lucide-upload" :disabled="!pendingFile" @click="runImport" />
      </template>
    </UModal>

    <UModal
      v-model:open="hintVisible"
      title="Editing the CSV file"
      :ui="{ content: 'max-w-lg', footer: 'justify-end' }"
    >
      <template #body>
        <div class="flex flex-col gap-4 text-sm">
          <p>
            Edit the file in a spreadsheet and upload it again with <strong>Upload</strong> to update the
            values.
          </p>
          <ul class="flex flex-col gap-2 list-disc pl-5">
            <li>
              <strong>You may edit:</strong>
              <template v-for="(column, index) in editableColumns" :key="column">
                <code>{{ column }}</code>{{ index < editableColumns.length - 1 ? ', ' : '.' }}
              </template>
            </li>
            <li>
              <strong>Do not edit:</strong> <code>{{ idColumn }}</code>. It tells the upload which row a line
              belongs to, so don't change, delete or duplicate it, and don't add rows.
            </li>
            <li>
              <strong>Information only:</strong>
              <template v-for="(column, index) in infoColumns" :key="column">
                <code>{{ column }}</code>{{ index < infoColumns.length - 1 ? ', ' : '.' }}
              </template>
              Changes to these columns are ignored.
            </li>
          </ul>
          <p v-for="note in notes ?? []" :key="note">{{ note }}</p>
          <p>Downloaded files always use a point as decimal separator (for example 1.5). When uploading you choose the decimal separator your file uses (point or comma); it defaults to your profile's number format.</p>
          <UCheckbox v-model="hintDontShowAgain" label="Don't show this again" />
        </div>
      </template>
      <template #footer>
        <UButton label="Cancel" icon="i-lucide-x" variant="ghost" @click="hintVisible = false" />
        <UButton label="Download CSV" icon="i-lucide-download" @click="confirmDownload" />
      </template>
    </UModal>
  </div>
</template>
