<script setup lang="ts">
// A card whose body folds away under its header; the chevron button on the
// right toggles it.
const collapsed = defineModel<boolean>('collapsed', { default: false })
</script>

<template>
  <UCard :ui="{ header: 'py-3 sm:py-3', body: collapsed ? 'p-0 sm:p-0' : undefined }">
    <template #header>
      <div class="flex items-center justify-between gap-2">
        <div class="flex min-w-0 flex-wrap items-center gap-2">
          <slot name="header" />
        </div>
        <UButton
          icon="i-lucide-chevron-down"
          color="neutral"
          variant="ghost"
          size="sm"
          square
          :aria-label="collapsed ? 'Expand' : 'Collapse'"
          :aria-expanded="!collapsed"
          :ui="{ leadingIcon: ['transition-transform', collapsed ? '-rotate-90' : ''] }"
          @click="collapsed = !collapsed"
        />
      </div>
    </template>

    <UCollapsible :open="!collapsed" :unmount-on-hide="false">
      <template #content>
        <slot />
      </template>
    </UCollapsible>
  </UCard>
</template>
