<script setup lang="ts">
import { inject } from 'vue'
import { contactChainDndKey } from './contactChain'
import type { ContactChainNode } from './contactChain'
import type { Contact } from '@/api/types'

export interface ContactChainInfo {
  title: string
  templateName: string
  donor: { icon: string | null; label: string }
  recipient: { icon: string | null; label: string }
}

defineOptions({ name: 'ContactChainNode' })

const dnd = inject(contactChainDndKey, null)

defineProps<{
  node: ContactChainNode
  info: (contact: Contact) => ContactChainInfo
  first?: boolean
}>()
</script>

<template>
  <div class="flex items-start gap-2">
    <UIcon v-if="!first" name="i-lucide-arrow-right" class="shrink-0 mt-5 text-dimmed" />
    <div
      :draggable="!!dnd"
      :class="[
        'w-56 shrink-0 rounded-md border p-3 flex flex-col gap-1 text-sm select-none transition-colors',
        dnd ? 'cursor-grab' : '',
        dnd?.hoverTarget.value === node.contact.id
          ? 'border-primary bg-primary/10'
          : dnd?.dragged.value && dnd.canDropOn(node.contact)
            ? 'border-primary border-dashed'
            : 'border-default',
        dnd?.dragged.value?.id === node.contact.id ? 'opacity-40' : '',
        dnd?.dragged.value && dnd.dragged.value.id !== node.contact.id && !dnd.canDropOn(node.contact) ? 'opacity-50' : '',
      ]"
      @dragstart="dnd?.onDragStart($event, node.contact)"
      @dragend="dnd?.onDragEnd()"
      @dragover="dnd?.onDragOver($event, node.contact)"
      @dragleave="dnd && (dnd.hoverTarget.value = null)"
      @drop.prevent="dnd?.onDrop(node.contact)"
    >
      <span class="flex items-center justify-between gap-1">
        <span class="text-xs text-muted truncate">{{ info(node.contact).templateName }}</span>
        <UButton
          v-if="dnd && node.contact.previous_contact_id"
          icon="i-lucide-x"
          color="neutral"
          variant="ghost"
          size="xs"
          square
          aria-label="Unlink from previous contact"
          @click.stop="dnd.unlink(node.contact)"
        />
      </span>
      <span class="font-medium truncate">{{ info(node.contact).title }}</span>
      <span class="flex items-center gap-1.5 truncate">
        <UIcon v-if="info(node.contact).donor.icon" :name="info(node.contact).donor.icon!" class="shrink-0" />
        {{ info(node.contact).donor.label }}
      </span>
      <UIcon name="i-lucide-arrow-down" class="text-dimmed" />
      <span class="flex items-center gap-1.5 truncate">
        <UIcon v-if="info(node.contact).recipient.icon" :name="info(node.contact).recipient.icon!" class="shrink-0" />
        {{ info(node.contact).recipient.label }}
      </span>
    </div>
    <div v-if="node.next.length" class="flex flex-col gap-2">
      <ContactChainNode v-for="child in node.next" :key="child.contact.id" :node="child" :info="info" />
    </div>
  </div>
</template>
