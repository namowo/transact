<script setup lang="ts">
import { ref, computed } from 'vue'

const value = defineModel<string>({ default: '' })

defineProps<{ id?: string; invalid?: boolean; disabled?: boolean }>()

const show = ref(false)

const rules = [
  { regex: /.{8,}/, text: '8+ characters' },
  { regex: /\d/, text: 'Number' },
  { regex: /[A-Z]/, text: 'Uppercase letter' },
  { regex: /[^a-zA-Z0-9]/, text: 'Special character' },
]

const strength = computed(() => rules.map((rule) => ({ met: rule.regex.test(value.value), text: rule.text })))
const score = computed(() => strength.value.filter((rule) => rule.met).length)

const color = computed(() => {
  if (score.value === 0) return 'neutral'
  if (score.value <= 1) return 'error'
  if (score.value <= 3) return 'warning'
  return 'success'
})
</script>

<template>
  <div class="flex flex-col gap-2">
    <UInput
      :id="id"
      v-model="value"
      :type="show ? 'text' : 'password'"
      :color="invalid ? 'error' : color"
      :disabled="disabled"
      class="w-full"
      :ui="{ trailing: 'pe-1' }"
    >
      <template #trailing>
        <UButton
          color="neutral"
          variant="link"
          size="sm"
          :icon="show ? 'i-lucide-eye-off' : 'i-lucide-eye'"
          :aria-label="show ? 'Hide password' : 'Show password'"
          :aria-pressed="show"
          @click="show = !show"
        />
      </template>
    </UInput>

    <div class="flex items-center flex-wrap gap-1.5">
      <UBadge
        v-for="rule in strength"
        :key="rule.text"
        :color="rule.met ? 'success' : 'neutral'"
        variant="subtle"
        size="sm"
      >
        <UIcon :name="rule.met ? 'i-lucide-check' : 'i-lucide-x'" class="size-3" />
        {{ rule.text }}
      </UBadge>
    </div>
  </div>
</template>
