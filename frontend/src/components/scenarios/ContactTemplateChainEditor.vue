<script setup lang="ts">
import { computed, ref } from 'vue'
import type { ChainSlot, ContactTemplateDraft } from './contactTemplateDraft'

const props = defineProps<{ drafts: ContactTemplateDraft[] }>()
const emit = defineEmits<{ move: [payload: { uid: string; slot: ChainSlot }] }>()

interface Item {
  uid: string
  label: string
}

const items = computed<Item[]>(() =>
  props.drafts.map((d, i) => ({ uid: d.uid, label: d.name || `Contact template #${i + 1}` })),
)
const byUid = computed(() => new Map(items.value.map((i) => [i.uid, i])))

const chains = computed<Item[][]>(() => {
  const successor = new Map(props.drafts.filter((d) => d.followsUid).map((d) => [d.followsUid!, d.uid]))
  const heads = props.drafts.filter((d) => !d.followsUid && successor.has(d.uid))
  return heads.map((head) => {
    const chain: Item[] = []
    for (let uid: string | undefined = head.uid; uid && !chain.some((c) => c.uid === uid); uid = successor.get(uid)) {
      chain.push(byUid.value.get(uid)!)
    }
    return chain
  })
})

const loose = computed(() => {
  const inChain = new Set(chains.value.flat().map((i) => i.uid))
  return items.value.filter((i) => !inChain.has(i.uid))
})

const dragging = ref<string | null>(null)
const hover = ref<string | null>(null)

function onDragStart(event: DragEvent, uid: string) {
  dragging.value = uid
  event.dataTransfer?.setData('text/plain', uid)
  if (event.dataTransfer) event.dataTransfer.effectAllowed = 'move'
}

function onDragEnd() {
  dragging.value = null
  hover.value = null
}

function onDrop(slot: ChainSlot) {
  if (dragging.value) emit('move', { uid: dragging.value, slot })
  onDragEnd()
}
</script>

<template>
  <div class="flex flex-col gap-3 rounded-md border border-default p-4">
    <div>
      <h4 class="font-medium text-sm">Contact chain</h4>
      <p class="text-xs text-muted">
        Drag a contact template into a gap to place it in a chain. Drag it back to "Not chained" to remove it.
      </p>
    </div>

    <div
      v-for="chain in chains"
      :key="chain[0]!.uid"
      class="flex flex-wrap items-center gap-1"
    >
      <div
        :class="[
          'h-8 rounded-md border-2 border-dashed transition-all',
          hover === `start:${chain[0]!.uid}` ? 'w-10 border-primary' : dragging ? 'w-6 border-default' : 'w-1 border-transparent',
        ]"
        @dragover.prevent="hover = `start:${chain[0]!.uid}`"
        @dragleave="hover = null"
        @drop.prevent="onDrop({ kind: 'start', uid: chain[0]!.uid })"
      />
      <template v-for="(item, index) in chain" :key="item.uid">
        <UBadge
          :label="item.label"
          color="primary"
          variant="subtle"
          size="lg"
          draggable="true"
          class="cursor-grab select-none"
          :class="dragging === item.uid ? 'opacity-40' : ''"
          icon="i-lucide-grip-vertical"
          @dragstart="onDragStart($event, item.uid)"
          @dragend="onDragEnd"
        />
        <div
          :class="[
            'h-8 flex items-center justify-center rounded-md border-2 border-dashed transition-all',
            hover === `after:${item.uid}` ? 'w-10 border-primary' : dragging ? 'w-8 border-default' : 'w-6 border-transparent',
          ]"
          @dragover.prevent="hover = `after:${item.uid}`"
          @dragleave="hover = null"
          @drop.prevent="onDrop({ kind: 'after', uid: item.uid })"
        >
          <UIcon v-if="!dragging && index < chain.length - 1" name="i-lucide-arrow-right" class="text-dimmed" />
        </div>
      </template>
    </div>

    <div
      :class="[
        'flex flex-wrap items-center gap-2 rounded-md border-2 border-dashed p-3 min-h-14 transition-colors',
        hover === 'detach' ? 'border-primary bg-elevated' : 'border-default',
      ]"
      @dragover.prevent="hover = 'detach'"
      @dragleave="hover = null"
      @drop.prevent="onDrop({ kind: 'detach' })"
    >
      <span class="text-xs text-muted">Not chained</span>
      <template v-for="item in loose" :key="item.uid">
        <!-- A loose template can start a chain by being dropped after it. -->
        <div class="flex items-center gap-1">
          <UBadge
            :label="item.label"
            color="neutral"
            variant="outline"
            size="lg"
            draggable="true"
            class="cursor-grab select-none"
            :class="dragging === item.uid ? 'opacity-40' : ''"
            icon="i-lucide-grip-vertical"
            @dragstart="onDragStart($event, item.uid)"
            @dragend="onDragEnd"
          />
          <div
            v-if="dragging && dragging !== item.uid"
            :class="[
              'h-8 w-8 rounded-md border-2 border-dashed flex items-center justify-center',
              hover === `after:${item.uid}` ? 'border-primary' : 'border-default',
            ]"
            @dragover.prevent.stop="hover = `after:${item.uid}`"
            @dragleave="hover = null"
            @drop.prevent.stop="onDrop({ kind: 'after', uid: item.uid })"
          >
            <UIcon name="i-lucide-arrow-right" class="text-dimmed" />
          </div>
        </div>
      </template>
    </div>
  </div>
</template>
