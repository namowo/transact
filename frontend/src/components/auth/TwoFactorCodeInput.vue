<script setup lang="ts">
import { computed, ref, watch } from 'vue'

// A code from the authenticator app (six digits), or - with
// `allowRecoveryCode` - one of the user's recovery codes.
const props = withDefaults(
  defineProps<{ allowRecoveryCode?: boolean; autofocus?: boolean; disabled?: boolean }>(),
  { allowRecoveryCode: false, autofocus: true, disabled: false },
)
const emit = defineEmits<{ complete: [code: string] }>()
const code = defineModel<string>({ default: '' })

const useRecoveryCode = ref(false)
const digits = ref<string[]>([])
const recoveryCode = ref('')

watch(digits, (value) => {
  if (!useRecoveryCode.value) code.value = value.join('')
})
watch(recoveryCode, (value) => {
  if (useRecoveryCode.value) code.value = value.trim()
})
// Cleared from outside (e.g. after a wrong code): clear the fields too.
watch(code, (value) => {
  if (value === '') {
    digits.value = []
    recoveryCode.value = ''
  }
})

const label = computed(() =>
  useRecoveryCode.value ? 'Recovery code' : 'Code from your authenticator app',
)

function toggle() {
  useRecoveryCode.value = !useRecoveryCode.value
  code.value = ''
}
</script>

<template>
  <div class="flex flex-col gap-2">
    <span class="font-medium text-sm">{{ label }}</span>
    <UPinInput
      v-if="!useRecoveryCode"
      v-model="digits"
      :length="6"
      otp
      :autofocus="props.autofocus"
      :disabled="props.disabled"
      aria-label="Six-digit code"
      @complete="(value: string[]) => emit('complete', value.join(''))"
    />
    <UInput
      v-else
      v-model="recoveryCode"
      placeholder="xxxxx-xxxxx"
      autocomplete="off"
      autofocus
      :disabled="props.disabled"
      class="w-full"
      aria-label="Recovery code"
    />
    <button
      v-if="props.allowRecoveryCode"
      type="button"
      class="self-start flex items-center gap-1 text-sm text-primary bg-transparent border-0 cursor-pointer p-0"
      @click="toggle"
    >
      <UIcon
        :name="useRecoveryCode ? 'i-lucide-smartphone' : 'i-lucide-life-buoy'"
        class="size-3"
      />
      {{ useRecoveryCode ? 'Use the authenticator app' : 'Use a recovery code' }}
    </button>
  </div>
</template>
