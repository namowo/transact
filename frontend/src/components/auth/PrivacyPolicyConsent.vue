<script setup lang="ts">
import { RouterLink } from 'vue-router'

defineProps<{
  errorMessage?: string
}>()

const checked = defineModel<boolean>({ default: false })
</script>

<template>
  <div class="flex flex-col gap-2">
    <div class="flex items-start gap-2">
      <UCheckbox id="privacy-policy-accepted" v-model="checked" :color="errorMessage ? 'error' : undefined" />
      <label for="privacy-policy-accepted" class="text-sm">
        I have read and agree to the
        <RouterLink :to="{ name: 'privacy-policy' }" target="_blank" class="text-primary hover:underline">
          Privacy Policy
        </RouterLink>
      </label>
    </div>
    <UAlert v-if="errorMessage" color="error" variant="subtle" :description="errorMessage" />
  </div>
</template>
