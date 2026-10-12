<script setup lang="ts">
import { computed } from 'vue'
import type { LegalPageMode } from '@/api/types'

const props = defineProps<{
  title: string
  mode: LegalPageMode
  text: string | null | undefined
  url: string | null | undefined
  saving?: boolean
}>()

const emit = defineEmits<{
  'update:mode': [LegalPageMode]
  'update:text': [string]
  'update:url': [string]
  save: []
}>()

const modeOptions = [
  { label: 'Custom text', value: 'text', icon: 'i-lucide-file-text' },
  { label: 'External link', value: 'url', icon: 'i-lucide-link' },
]

const text = computed({
  get: () => props.text ?? '',
  set: (value: string) => emit('update:text', value),
})

const url = computed({
  get: () => props.url ?? '',
  set: (value: string) => emit('update:url', value),
})
</script>

<template>
  <div class="flex flex-col gap-4">
    <h2 class="text-lg font-semibold text-surface-900 dark:text-surface-0">{{ title }}</h2>

    <URadioGroup
      :model-value="mode"
      :items="modeOptions"
      orientation="horizontal"
      variant="card"
      indicator="hidden"
      class="w-full [&>div]:flex-1"
      @update:model-value="(value: unknown) => emit('update:mode', value as LegalPageMode)"
    />

    <UInput
      v-if="mode === 'url'"
      v-model="url"
      type="url"
      placeholder="https://..."
      class="w-full"
    />

    <UEditor
      v-else
      v-model="text"
      content-type="html"
      class="rounded-md border border-default min-h-48"
    >
      <template #default="{ editor }">
        <UEditorToolbar
          :editor="editor"
          class="border-b border-default"
          :items="[
            { kind: 'heading', level: 1, icon: 'i-lucide-heading-1' },
            { kind: 'heading', level: 2, icon: 'i-lucide-heading-2' },
            { kind: 'heading', level: 3, icon: 'i-lucide-heading-3' },
            { type: 'separator' },
            { kind: 'mark', mark: 'bold', icon: 'i-lucide-bold' },
            { kind: 'mark', mark: 'italic', icon: 'i-lucide-italic' },
            { kind: 'mark', mark: 'underline', icon: 'i-lucide-underline' },
            { type: 'separator' },
            { kind: 'bulletList', icon: 'i-lucide-list' },
            { kind: 'orderedList', icon: 'i-lucide-list-ordered' },
            { kind: 'blockquote', icon: 'i-lucide-quote' },
            { type: 'separator' },
            { kind: 'link', icon: 'i-lucide-link' },
            { type: 'separator' },
            { kind: 'undo', icon: 'i-lucide-undo' },
            { kind: 'redo', icon: 'i-lucide-redo' },
          ]"
        />
      </template>
    </UEditor>

    <div class="flex justify-end">
      <UButton
        label="Save"
        icon="i-lucide-save"
        :loading="saving"
        @click="emit('save')"
      />
    </div>
  </div>
</template>
