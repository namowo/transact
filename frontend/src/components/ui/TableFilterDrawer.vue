<script setup lang="ts">
// A "Filters" button that opens the table's filters in a drawer from the
// right. The badge counts the filters in use.
const props = withDefaults(
  defineProps<{
    activeCount?: number
    title?: string
    description?: string
  }>(),
  { activeCount: 0, title: 'Filters', description: 'Only rows matching every filter are shown.' },
)
const emit = defineEmits<{ reset: [] }>()

const open = defineModel<boolean>('open', { default: false })
</script>

<template>
  <UDrawer
    v-model:open="open"
    direction="right"
    :title="props.title"
    :description="props.description"
    :handle="false"
    :ui="{ content: 'w-full max-w-sm', body: 'flex flex-col gap-4' }"
  >
    <UButton
      icon="i-lucide-list-filter"
      label="Filters"
      color="neutral"
      :variant="activeCount ? 'soft' : 'outline'"
    >
      <template v-if="activeCount" #trailing>
        <UBadge
          :label="String(activeCount)"
          size="sm"
          color="primary"
          variant="solid"
          class="rounded-full"
        />
      </template>
    </UButton>

    <template #body>
      <slot />
    </template>

    <template #footer>
      <div class="flex justify-between gap-2">
        <UButton
          label="Clear filters"
          color="neutral"
          variant="ghost"
          icon="i-lucide-filter-x"
          :disabled="!activeCount"
          @click="emit('reset')"
        />
        <UButton label="Done" @click="open = false" />
      </div>
    </template>
  </UDrawer>
</template>
