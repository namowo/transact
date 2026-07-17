<script setup lang="ts">
import { ref } from 'vue'
import IconField from 'primevue/iconfield'
import InputIcon from 'primevue/inputicon'
import InputPassword from 'primevue/inputpassword'
import Chip from 'primevue/chip'
import Check from '@primeicons/vue/check'
import Eye from '@primeicons/vue/eye'
import EyeSlash from '@primeicons/vue/eye-slash'
import Lock from '@primeicons/vue/lock'
import Times from '@primeicons/vue/times'

const value = defineModel<string>({ default: '' })
const mask = ref(true)

const rules = [
  { label: '8+ characters', test: (v: string) => v.length >= 8 },
  { label: 'Number', test: (v: string) => /\d/.test(v) },
  { label: 'Uppercase letter', test: (v: string) => /[A-Z]/.test(v) },
  { label: 'Special character', test: (v: string) => /[^a-zA-Z0-9]/.test(v) },
]
</script>

<template>
  <div>
    <IconField>
      <InputIcon>
        <Lock />
      </InputIcon>
      <InputPassword v-model="value" :mask="mask" fluid />
      <InputIcon class="cursor-pointer" @click="mask = !mask">
        <Eye v-if="mask" :size="16" />
        <EyeSlash v-else :size="16" />
      </InputIcon>
    </IconField>
    <div class="mt-3 flex items-center flex-wrap gap-1.5">
      <Chip
        v-for="rule in rules"
        :key="rule.label"
        :class="
          'py-1! px-2! text-xs! gap-1.5! bg-transparent! border border-surface-200 dark:border-surface-700 ' +
          (rule.test(value)
            ? 'text-green-600! dark:text-green-400!'
            : 'text-surface-500! dark:text-surface-400!')
        "
      >
        <span
          :class="
            'size-4 inline-flex items-center justify-center rounded-full ' +
            (rule.test(value)
              ? 'bg-green-600 text-surface-0 dark:bg-green-400 dark:text-surface-900'
              : 'bg-surface-200 dark:bg-surface-700 text-surface-500 dark:text-surface-400')
          "
        >
          <Check v-if="rule.test(value)" :size="12" />
          <Times v-else :size="12" />
        </span>
        {{ rule.label }}
      </Chip>
    </div>
  </div>
</template>
