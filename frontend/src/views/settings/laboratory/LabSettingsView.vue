<script setup lang="ts">
import { computed, ref } from 'vue'
import { setAdminDataEntry } from '@/api/laboratories'
import { getErrorMessage } from '@/api/errors'
import { useConfirm } from '@/composables/useConfirm'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
const confirm = useConfirm()
const laboratory = computed(() => auth.user?.laboratory ?? null)
const saving = ref(false)
const error = ref('')

async function apply(allow: boolean) {
  if (!laboratory.value) return
  saving.value = true
  error.value = ''
  try {
    await setAdminDataEntry(laboratory.value.id, allow)
    // The laboratory is part of the current user; reload it.
    await auth.fetchCurrentUser()
  } catch (err) {
    error.value = getErrorMessage(err, 'Could not save the setting. Please try again.')
  } finally {
    saving.value = false
  }
}

function toggleAdminDataEntry(allow: boolean) {
  if (allow) {
    apply(true)
    return
  }
  confirm.require({
    header: 'Stop admin data entry',
    message:
      'Platform admins will no longer be able to create or edit studies and data of your laboratory. You can switch this back on at any time.',
    rejectLabel: 'Cancel',
    acceptLabel: 'Switch off',
    acceptColor: 'warning',
    accept: () => apply(false),
  })
}
</script>

<template>
  <div class="flex flex-col gap-6 max-w-2xl">
    <h1 class="text-2xl font-bold text-surface-900 dark:text-surface-0">Laboratory Settings</h1>

    <UAlert v-if="error" color="error" variant="outline" :description="error" />

    <UCard v-if="laboratory">
      <div class="flex items-start justify-between gap-4">
        <div class="flex flex-col gap-1">
          <p class="font-medium text-highlighted">Allow platform admins to edit our data</p>
          <p class="text-sm text-muted">
            Platform admins can prepare studies and enter data on behalf of
            {{ laboratory.laboratory_name }}, for example before your team takes over. Switch this
            off once you manage your data yourselves. Published studies stay visible to everyone
            either way.
          </p>
        </div>
        <USwitch
          :model-value="laboratory.allow_admin_data_entry"
          :loading="saving"
          :disabled="saving"
          aria-label="Allow platform admins to edit our data"
          @update:model-value="toggleAdminDataEntry"
        />
      </div>
    </UCard>
  </div>
</template>
