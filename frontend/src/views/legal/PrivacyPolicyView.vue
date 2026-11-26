<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { RouterLink, useRoute } from 'vue-router'
import PrivacyPolicyContent from '@/components/legal/PrivacyPolicyContent.vue'
import { privacyPolicyApi } from '@/api/privacyPolicy'
import { usePrivacyPolicyStore } from '@/stores/privacyPolicy'
import type { PrivacyPolicy } from '@/api/types'

// The active policy, or an earlier version with ?version=<id>.
const route = useRoute()
const store = usePrivacyPolicyStore()

const requestedId = computed(() => {
  const id = Number(route.query.version)
  return Number.isInteger(id) && id > 0 ? id : null
})

const earlier = ref<PrivacyPolicy | null>(null)
const loading = ref(true)
const notFound = ref(false)

const policy = computed(() => (requestedId.value ? earlier.value : store.active))
const isOutdated = computed(
  () => !!policy.value && !!store.active && policy.value.id !== store.active.id,
)

watch(
  requestedId,
  async (id) => {
    loading.value = true
    notFound.value = false
    earlier.value = null
    try {
      await store.load()
      if (id) {
        earlier.value = await privacyPolicyApi.get(id)
      } else if (store.active?.mode === 'url' && store.active.url) {
        window.location.href = store.active.url
      }
    } catch {
      notFound.value = true
    } finally {
      loading.value = false
    }
  },
  { immediate: true },
)

function formatDate(value: string | null) {
  return value ? new Date(value).toLocaleDateString() : ''
}
</script>

<template>
  <div class="flex flex-col gap-4">
    <div class="flex flex-col gap-1">
      <h1 class="text-2xl font-bold text-surface-900 dark:text-surface-0">Privacy Policy</h1>
      <p v-if="policy?.version" class="text-sm text-muted">
        Version {{ policy.version }} · in force since {{ formatDate(policy.published_at) }}
      </p>
    </div>

    <div v-if="loading" class="flex flex-col gap-3" aria-busy="true">
      <USkeleton class="h-4 w-full" />
      <USkeleton class="h-4 w-11/12" />
      <USkeleton class="h-4 w-4/5" />
      <USkeleton class="h-4 w-2/3" />
    </div>

    <p v-else-if="notFound" class="text-sm text-muted">
      This version of the privacy policy doesn't exist.
    </p>

    <template v-else-if="policy">
      <UAlert
        v-if="isOutdated"
        color="warning"
        variant="subtle"
        icon="i-lucide-history"
        title="This is an earlier version of the privacy policy."
      >
        <template #description>
          <RouterLink :to="{ name: 'privacy-policy' }" class="text-primary hover:underline">
            Read the current version
          </RouterLink>
        </template>
      </UAlert>
      <PrivacyPolicyContent :policy="policy" />
    </template>

    <p v-else class="text-sm text-muted">No privacy policy has been set up yet.</p>
  </div>
</template>
