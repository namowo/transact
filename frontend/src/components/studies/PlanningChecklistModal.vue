<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useDebounceFn } from '@vueuse/core'
import { useToast } from '@nuxt/ui/composables'
import {
  downloadPlanningSheet,
  getPlanningChecklist,
  resetPlanningChecklist,
  savePlanningChecklist,
  savePlanningChecklistProgress,
  type ChecklistSection,
  type PlanningChecklist,
} from '@/api/studies'
import { getErrorMessage } from '@/api/errors'
import { useConfirm } from '@/composables/useConfirm'

// The planning checklist, opened from the study's planning step. It shows the
// checklist of the study's laboratory. Members of the laboratory tick items
// off and add notes per study (saved as they go). The checklist itself is that - the default one until a lab admin
// saves their own, which they can do right here. It can be printed, or
// downloaded as Excel to also plan the individuals and items, which are then
// uploaded again in the data entry step.

const props = defineProps<{ studyId: string; studyTitle?: string | null }>()

const open = defineModel<boolean>('open', { default: false })

const toast = useToast()
const confirm = useConfirm()

const checklist = ref<PlanningChecklist | null>(null)
const loading = ref(false)
const loadError = ref('')

async function load() {
  loading.value = true
  loadError.value = ''
  try {
    checklist.value = await getPlanningChecklist(props.studyId)
    checked.value = new Set(checklist.value.checked)
    notes.value = { ...checklist.value.notes }
    openNotes.value = new Set(Object.keys(notes.value))
  } catch (err) {
    loadError.value = getErrorMessage(err, 'Could not load the checklist. Please try again.')
  } finally {
    loading.value = false
  }
}

watch(open, (isOpen) => {
  if (!isOpen) return
  editing.value = false
  load()
})

const sections = computed(() => checklist.value?.sections ?? [])

// -- Ticking items off (members of the study's laboratory) --

const checked = ref(new Set<string>())
const notes = ref<Record<string, string>>({})
// Items whose note field is shown.
const openNotes = ref(new Set<string>())
const progressState = ref<'idle' | 'saving' | 'saved' | 'error'>('idle')

const allItemIds = computed(() =>
  sections.value.flatMap((section) => section.items.map((item) => item.id).filter((id): id is string => !!id)),
)
const doneCount = computed(() => allItemIds.value.filter((id) => checked.value.has(id)).length)

async function saveProgress() {
  progressState.value = 'saving'
  try {
    await savePlanningChecklistProgress(props.studyId, {
      checked: [...checked.value],
      notes: notes.value,
    })
    progressState.value = 'saved'
  } catch {
    progressState.value = 'error'
  }
}

// Notes save once typing pauses; ticks save right away.
const saveProgressSoon = useDebounceFn(saveProgress, 600)

function setChecked(id: string | undefined, value: boolean | 'indeterminate') {
  if (!id) return
  const next = new Set(checked.value)
  if (value === true) next.add(id)
  else next.delete(id)
  checked.value = next
  saveProgress()
}

function setNote(id: string | undefined, value: string) {
  if (!id) return
  notes.value = { ...notes.value, [id]: value }
  saveProgressSoon()
}

function showNote(id: string | undefined) {
  if (!id) return
  openNotes.value = new Set(openNotes.value).add(id)
}

// -- Editing (lab admins) --

const editing = ref(false)
const draft = ref<ChecklistSection[]>([])
const saving = ref(false)
const saveError = ref('')
const showTitleErrors = ref(false)

function startEditing() {
  draft.value = sections.value.map((section) => ({
    title: section.title,
    items: section.items.map((item) => ({ ...item })),
  }))
  if (!draft.value.length) addSection()
  saveError.value = ''
  showTitleErrors.value = false
  editing.value = true
}

function cancelEditing() {
  editing.value = false
}

function move<T>(list: T[], index: number, offset: number) {
  const target = index + offset
  if (target < 0 || target >= list.length) return
  const [entry] = list.splice(index, 1)
  list.splice(target, 0, entry as T)
}

function addSection() {
  draft.value.push({ title: '', items: [{ text: '' }] })
}

function removeSection(index: number) {
  draft.value.splice(index, 1)
}

function addItem(section: ChecklistSection) {
  section.items.push({ text: '' })
}

function removeItem(section: ChecklistSection, index: number) {
  section.items.splice(index, 1)
}

const missingTitle = computed(() => draft.value.some((section) => !section.title.trim()))

async function save() {
  const laboratoryId = checklist.value?.laboratory_id
  if (!laboratoryId) return
  if (missingTitle.value) {
    showTitleErrors.value = true
    return
  }
  saving.value = true
  saveError.value = ''
  try {
    const saved = await savePlanningChecklist(laboratoryId, draft.value)
    checklist.value = { ...saved, checked: [...checked.value], notes: notes.value, can_check: checklist.value!.can_check }
    editing.value = false
    toast.add({ color: 'success', title: 'Checklist saved', description: "All of your laboratory's studies use it now." })
  } catch (err) {
    saveError.value = getErrorMessage(err, 'Could not save the checklist. Please try again.')
  } finally {
    saving.value = false
  }
}

function confirmReset() {
  const laboratoryId = checklist.value?.laboratory_id
  if (!laboratoryId) return
  confirm.require({
    header: 'Reset to default checklist',
    message: "Replace your laboratory's checklist with the default one? Your own sections and items are lost.",
    rejectLabel: 'Cancel',
    acceptLabel: 'Reset',
    acceptColor: 'error',
    accept: async () => {
      try {
        const reset = await resetPlanningChecklist(laboratoryId)
        checklist.value = { ...reset, checked: [...checked.value], notes: notes.value, can_check: checklist.value!.can_check }
        editing.value = false
        toast.add({ color: 'success', title: 'Default checklist restored' })
      } catch (err) {
        saveError.value = getErrorMessage(err, 'Could not reset the checklist. Please try again.')
      }
    },
  })
}

// -- Download / print --

const downloading = ref(false)

async function onDownloadExcel() {
  downloading.value = true
  try {
    await downloadPlanningSheet(props.studyId, props.studyTitle)
  } catch (err) {
    toast.add({
      color: 'error',
      title: 'Download failed',
      description: getErrorMessage(err, 'Could not create the Excel file. Please try again.'),
    })
  } finally {
    downloading.value = false
  }
}

function onPrint() {
  window.print()
}
</script>

<template>
  <UModal
    v-model:open="open"
    :title="editing ? 'Edit planning checklist' : 'Planning checklist'"
    :description="editing ? 'Changes apply to all studies of your laboratory.' : props.studyTitle || undefined"
    :dismissible="!editing"
    :ui="{ content: 'max-w-3xl', footer: 'justify-between' }"
  >
    <template #body>
      <div v-if="loading" class="flex justify-center py-8">
        <UProgress class="w-12" />
      </div>

      <UAlert v-else-if="loadError" color="error" variant="subtle" :description="loadError" />

      <!-- Editing -->
      <div v-else-if="editing" class="flex flex-col gap-4">
        <div
          v-for="(section, sectionIndex) in draft"
          :key="sectionIndex"
          class="flex flex-col gap-3 rounded-lg border border-default p-3"
        >
          <div class="flex items-start gap-2">
            <UFormField
              class="flex-1"
              :error="showTitleErrors && !section.title.trim() ? 'Please give this section a title.' : undefined"
            >
              <UInput
                v-model="section.title"
                placeholder="Section title, e.g. Ethics"
                class="w-full"
                :ui="{ base: 'font-semibold' }"
              />
            </UFormField>
            <UFieldGroup>
              <UButton
                icon="i-lucide-arrow-up"
                color="neutral"
                variant="outline"
                aria-label="Move section up"
                :disabled="sectionIndex === 0"
                @click="move(draft, sectionIndex, -1)"
              />
              <UButton
                icon="i-lucide-arrow-down"
                color="neutral"
                variant="outline"
                aria-label="Move section down"
                :disabled="sectionIndex === draft.length - 1"
                @click="move(draft, sectionIndex, 1)"
              />
              <UButton
                icon="i-lucide-trash-2"
                color="error"
                variant="outline"
                aria-label="Remove section"
                @click="removeSection(sectionIndex)"
              />
            </UFieldGroup>
          </div>

          <ul class="flex flex-col gap-2 pl-4">
            <li v-for="(_, itemIndex) in section.items" :key="itemIndex" class="flex items-center gap-2">
              <span class="size-4 shrink-0 rounded-sm border-2 border-accented" />
              <UInput
                v-model="section.items[itemIndex]!.text"
                placeholder="Checklist item"
                size="sm"
                class="flex-1"
                @keydown.enter.prevent="addItem(section)"
              />
              <UFieldGroup size="sm">
                <UButton
                  icon="i-lucide-arrow-up"
                  color="neutral"
                  variant="ghost"
                  aria-label="Move item up"
                  :disabled="itemIndex === 0"
                  @click="move(section.items, itemIndex, -1)"
                />
                <UButton
                  icon="i-lucide-arrow-down"
                  color="neutral"
                  variant="ghost"
                  aria-label="Move item down"
                  :disabled="itemIndex === section.items.length - 1"
                  @click="move(section.items, itemIndex, 1)"
                />
                <UButton
                  icon="i-lucide-x"
                  color="neutral"
                  variant="ghost"
                  aria-label="Remove item"
                  @click="removeItem(section, itemIndex)"
                />
              </UFieldGroup>
            </li>
          </ul>
          <UButton
            label="Add item"
            icon="i-lucide-plus"
            size="sm"
            color="neutral"
            variant="ghost"
            class="self-start ml-4"
            @click="addItem(section)"
          />
        </div>

        <UButton
          label="Add section"
          icon="i-lucide-plus"
          color="neutral"
          variant="outline"
          class="self-start"
          @click="addSection"
        />
        <UAlert v-if="saveError" color="error" variant="subtle" :description="saveError" />
      </div>

      <!-- Viewing -->
      <div v-else class="flex flex-col gap-6">
        <UAlert
          color="info"
          variant="subtle"
          icon="i-lucide-file-spreadsheet"
          title="Plan individuals and items in Excel"
          description="The Excel version also has sheets for the individuals (age, sex, etc.) and items you plan to use. When you add data to the repository, upload the filled-in file under Data entry, so nothing has to be typed in twice."
        />
        <div v-if="allItemIds.length" class="flex flex-col gap-1.5">
          <div class="flex items-center justify-between text-sm">
            <span class="font-medium">{{ doneCount }} of {{ allItemIds.length }} done</span>
            <span v-if="progressState === 'saving'" class="text-muted">Saving…</span>
            <span v-else-if="progressState === 'saved'" class="text-muted">Saved</span>
            <span v-else-if="progressState === 'error'" class="text-error">Could not save. Please try again.</span>
          </div>
          <UProgress :model-value="doneCount" :max="allItemIds.length" size="sm" />
        </div>
        <UAlert v-if="saveError" color="error" variant="subtle" :description="saveError" />
        <p v-if="!sections.length" class="text-sm text-muted">This checklist is empty.</p>
        <div v-for="section in sections" :key="section.title" class="flex flex-col gap-2">
          <h3 class="font-semibold text-highlighted">{{ section.title }}</h3>
          <ul class="flex flex-col gap-2">
            <li v-for="(item, itemIndex) in section.items" :key="item.id ?? itemIndex" class="flex flex-col gap-1">
              <div class="flex items-start gap-2">
                <UCheckbox
                  :model-value="!!item.id && checked.has(item.id)"
                  :label="item.text"
                  :disabled="!checklist?.can_check"
                  class="flex-1"
                  :ui="{
                    label: !!item.id && checked.has(item.id) ? 'line-through text-muted font-normal' : 'text-toned font-normal',
                  }"
                  @update:model-value="setChecked(item.id, $event)"
                />
                <UButton
                  v-if="checklist?.can_check && item.id && !openNotes.has(item.id)"
                  icon="i-lucide-message-square-plus"
                  size="xs"
                  color="neutral"
                  variant="ghost"
                  aria-label="Add a note"
                  @click="showNote(item.id)"
                />
              </div>
              <UTextarea
                v-if="checklist?.can_check && item.id && openNotes.has(item.id)"
                :model-value="notes[item.id] ?? ''"
                placeholder="Note, e.g. who, when, reference number"
                :rows="1"
                autoresize
                size="sm"
                class="ml-6"
                @update:model-value="setNote(item.id, String($event))"
              />
              <p v-else-if="item.id && notes[item.id]" class="ml-6 text-sm text-muted whitespace-pre-line">
                {{ notes[item.id] }}
              </p>
            </li>
          </ul>
        </div>
      </div>
    </template>

    <template #footer>
      <template v-if="editing">
        <UButton
          v-if="!checklist?.is_default"
          label="Reset to default"
          icon="i-lucide-rotate-ccw"
          color="error"
          variant="ghost"
          :disabled="saving"
          @click="confirmReset"
        />
        <span v-else />
        <div class="flex gap-2">
          <UButton label="Cancel" color="neutral" variant="ghost" :disabled="saving" @click="cancelEditing" />
          <UButton label="Save checklist" icon="i-lucide-save" :loading="saving" @click="save" />
        </div>
      </template>
      <template v-else>
        <div class="flex items-center gap-2">
          <UButton
            v-if="checklist?.can_edit"
            label="Edit checklist"
            icon="i-lucide-pencil"
            color="neutral"
            variant="ghost"
            :disabled="loading || !!loadError"
            @click="startEditing"
          />
          <UBadge
            v-if="checklist"
            :label="checklist.is_default ? 'Default checklist' : 'Laboratory checklist'"
            color="neutral"
            variant="subtle"
          />
        </div>
        <div class="flex gap-2">
          <UButton
            label="Download as Excel"
            icon="i-lucide-file-spreadsheet"
            color="neutral"
            variant="outline"
            :loading="downloading"
            @click="onDownloadExcel"
          />
          <UButton label="Print" icon="i-lucide-printer" :disabled="!sections.length" @click="onPrint" />
        </div>
      </template>
    </template>
  </UModal>

  <!-- What gets printed: a full-page copy outside the dialog, so the dialog's
       scrolling and size limits don't cut it off. #print-area hides the rest
       of the page while printing (see assets/main.css). -->
  <Teleport v-if="open && !editing" to="body">
    <!-- The wrapper keeps #print-area from being hidden by the print rule
         that hides every body child not containing it. -->
    <div class="hidden print:block">
    <div id="print-area" class="flex flex-col gap-6 text-black print:static!">
      <div class="flex flex-col gap-1">
        <h1 class="text-2xl font-bold">Planning checklist</h1>
        <p v-if="props.studyTitle">{{ props.studyTitle }}</p>
      </div>
      <div v-for="section in sections" :key="section.title" class="flex flex-col gap-2">
        <h2 class="text-lg font-semibold">{{ section.title }}</h2>
        <ul class="flex flex-col gap-3">
          <li v-for="(item, itemIndex) in section.items" :key="item.id ?? itemIndex" class="flex items-start gap-3 text-sm">
            <span
              class="mt-0.5 size-4 shrink-0 rounded-sm border-2 border-black flex items-center justify-center text-xs leading-none"
            >{{ item.id && checked.has(item.id) ? '✓' : '' }}</span>
            <span class="flex-1">
              {{ item.text }}
              <span v-if="item.id && notes[item.id]" class="block mt-1 italic whitespace-pre-line">{{ notes[item.id] }}</span>
              <span v-else class="block mt-1 border-b border-dashed border-black w-full h-5" />
            </span>
          </li>
        </ul>
      </div>
      <div class="flex flex-col gap-2">
        <h2 class="text-lg font-semibold">Notes</h2>
        <div v-for="n in 4" :key="n" class="border-b border-dashed border-black h-7" />
      </div>
    </div>
    </div>
  </Teleport>
</template>
