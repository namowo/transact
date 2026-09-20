<script setup lang="ts">
defineProps<{
  title?: string
  message: string
  confirmLabel?: string
  cancelLabel?: string
  confirmColor?: 'primary' | 'secondary' | 'success' | 'info' | 'warning' | 'error' | 'neutral'
}>()

const emit = defineEmits<{
  close: [confirmed: boolean]
}>()
</script>

<template>
  <UModal :title="title ?? 'Confirm'" @update:open="(open: boolean) => !open && emit('close', false)">
    <template #body>
      <p class="text-sm">{{ message }}</p>
    </template>

    <template #footer>
      <UButton
        :label="cancelLabel ?? 'Cancel'"
        variant="ghost"
        color="neutral"
        @click="emit('close', false)"
      />
      <UButton
        :label="confirmLabel ?? 'Confirm'"
        :color="confirmColor ?? 'primary'"
        @click="emit('close', true)"
      />
    </template>
  </UModal>
</template>
