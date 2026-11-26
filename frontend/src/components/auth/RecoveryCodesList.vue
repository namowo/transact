<script setup lang="ts">
import { ref } from 'vue'

const props = defineProps<{ codes: string[] }>()

const copied = ref(false)

async function copy() {
  try {
    await navigator.clipboard.writeText(props.codes.join('\n'))
    copied.value = true
    setTimeout(() => (copied.value = false), 2000)
  } catch {
    copied.value = false
  }
}

function download() {
  const blob = new Blob([`TransAct recovery codes\n\n${props.codes.join('\n')}\n`], {
    type: 'text/plain',
  })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = 'transact-recovery-codes.txt'
  link.click()
  URL.revokeObjectURL(url)
}
</script>

<template>
  <div class="flex flex-col gap-3">
    <UAlert
      color="warning"
      variant="subtle"
      icon="i-lucide-triangle-alert"
      title="Save your recovery codes"
      description="Each code signs you in once if you lose your authenticator app. They're shown only now - keep them somewhere safe."
    />
    <ul
      class="grid grid-cols-2 gap-x-6 gap-y-1 list-none m-0 p-4 rounded-md bg-elevated font-mono text-sm"
    >
      <li v-for="code in props.codes" :key="code">{{ code }}</li>
    </ul>
    <div class="flex flex-wrap gap-2">
      <UButton
        :label="copied ? 'Copied' : 'Copy'"
        :icon="copied ? 'i-lucide-check' : 'i-lucide-copy'"
        color="neutral"
        variant="outline"
        size="sm"
        @click="copy"
      />
      <UButton
        label="Download"
        icon="i-lucide-download"
        color="neutral"
        variant="outline"
        size="sm"
        @click="download"
      />
    </div>
  </div>
</template>
