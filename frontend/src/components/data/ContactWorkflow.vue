<script setup lang="ts">
import { computed, ref } from 'vue'
import type { StepperItem } from '@nuxt/ui'
import ContactBuilder from './ContactBuilder.vue'
import ContactChains from './ContactChains.vue'
import type { LinkOp } from './ContactChains.vue'
import type { ContactChainInfo } from './ContactChainNode.vue'
import type { Contact, ContactTemplate, Scenario } from '@/api/types'

// Two steps for entering contacts: 1. create them, 2. chain them. Each step
// can be used on its own (click it in the stepper), or as a guided workflow
// where saving in step 1 continues straight to step 2 with the new contacts
// highlighted and ready to be linked.
const props = defineProps<{
  studyId: string
  scenarios: Scenario[]
  scenarioId: string | null
  contactTemplates: ContactTemplate[]
  contacts: Contact[]
  info: (contact: Contact) => ContactChainInfo
  canUndo: boolean
  active: boolean
}>()

const step = defineModel<'create' | 'chains'>('step', { required: true })

const emit = defineEmits<{ saved: [contacts: Contact[]]; change: [ops: LinkOp[]]; undo: [] }>()

const guided = ref(true)
const recentIds = ref<string[]>([])

// Highlights only make sense for contacts that still exist.
const highlightIds = computed(() => {
  const existing = new Set(props.contacts.map((c) => c.id))
  return recentIds.value.filter((id) => existing.has(id))
})

const stepItems: StepperItem[] = [
  {
    value: 'create',
    title: 'Create contacts',
    description: 'Drag individuals onto contact steps',
    icon: 'i-lucide-user-plus',
  },
  {
    value: 'chains',
    title: 'Chain contacts',
    description: 'Link contacts in their planned order',
    icon: 'i-lucide-link',
  },
]

function onSaved(contacts: Contact[]) {
  emit('saved', contacts)
  recentIds.value = guided.value ? contacts.map((c) => c.id) : [...recentIds.value, ...contacts.map((c) => c.id)]
  if (guided.value) step.value = 'chains'
}
</script>

<template>
  <div class="flex flex-col gap-4">
    <div class="flex flex-wrap items-center justify-between gap-4">
      <UStepper
        v-model="step"
        :items="stepItems"
        :linear="false"
        size="sm"
        class="flex-1 min-w-72 max-w-xl"
      />
      <USwitch
        v-model="guided"
        label="Guided workflow"
        description="Continue to chaining after saving"
        size="sm"
      />
    </div>

    <ContactBuilder
      v-show="step === 'create'"
      :study-id="studyId"
      :scenarios="scenarios"
      :scenario-id="scenarioId"
      :contact-templates="contactTemplates"
      :contacts="contacts"
      :info="info"
      :active="active && step === 'create'"
      :can-undo="canUndo"
      @saved="onSaved"
      @change="emit('change', $event)"
      @undo="emit('undo')"
    />

    <template v-if="step === 'chains'">
      <UAlert
        v-if="highlightIds.length"
        color="primary"
        variant="subtle"
        icon="i-lucide-sparkles"
        :description="`${highlightIds.length} new contact${highlightIds.length === 1 ? '' : 's'} highlighted. Link them by dragging, or use “Link by shared individual”.`"
        :actions="[
          { label: 'Create more', icon: 'i-lucide-arrow-left', color: 'neutral', variant: 'outline', size: 'xs', onClick: () => { step = 'create' } },
          { label: 'Clear highlight', color: 'neutral', variant: 'ghost', size: 'xs', onClick: () => { recentIds = [] } },
        ]"
        orientation="horizontal"
      />
      <ContactChains
        :contacts="contacts"
        :contact-templates="contactTemplates"
        :info="info"
        :can-undo="canUndo"
        :highlight-ids="highlightIds"
        @change="emit('change', $event)"
        @undo="emit('undo')"
      />
    </template>
  </div>
</template>
