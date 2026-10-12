<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import * as webauthnApi from '@/api/webauthn'
import { listStudies } from '@/api/studies'
import type { Study } from '@/api/types'

const auth = useAuthStore()
const router = useRouter()

const showPasskeyBanner = ref(false)
const studies = ref<Study[]>([])
const statsLoading = ref(false)

onMounted(async () => {
  if (auth.user && !auth.user.passkey_prompt_dismissed) {
    const credentials = await webauthnApi.listCredentials().catch(() => [])
    showPasskeyBanner.value = credentials.length === 0
  }

  statsLoading.value = true
  studies.value = await listStudies().catch(() => [])
  statsLoading.value = false
})

function onSetUpPasskey() {
  showPasskeyBanner.value = false
  auth.dismissPasskeyPromptBanner()
  router.push({ name: 'profile' })
}

function onDismissPasskeyBanner() {
  showPasskeyBanner.value = false
  auth.dismissPasskeyPromptBanner()
}

const publishedCount = computed(() => studies.value.filter((s) => s.published).length)
const labCount = computed(
  () => new Set(studies.value.map((s) => s.laboratory_id).filter(Boolean)).size,
)

const stats = computed(() => [
  { label: 'Studies in the repository', value: studies.value.length, icon: 'i-lucide-book-open' },
  { label: 'Contributing laboratories', value: labCount.value, icon: 'i-lucide-building-2' },
  { label: 'Published datasets', value: publishedCount.value, icon: 'i-lucide-globe' },
])
</script>

<template>
  <div class="flex flex-col gap-10">
    <UAlert
      v-if="showPasskeyBanner"
      color="info"
      variant="outline"
      description="Sign in faster next time — set up a passkey for your account."
      orientation="horizontal"
      close
      @update:open="onDismissPasskeyBanner"
    >
      <template #actions>
        <UButton label="Set up a passkey" size="sm" @click="onSetUpPasskey" />
      </template>
    </UAlert>

    <!-- Hero -->
    <div
      class="relative overflow-hidden rounded-2xl border border-default bg-linear-to-br from-primary-50 to-elevated/40 dark:from-primary-950/40 dark:to-elevated/40 px-6 py-10 sm:px-10 sm:py-14"
    >
      <div class="relative flex flex-col items-center text-center gap-5 max-w-2xl mx-auto">
        <div class="flex items-center gap-3">
          <img src="/transact_logo_dark.png" alt="TransAct" class="size-10 dark:hidden" />
          <img
            src="/transact_logo_light.png"
            alt="TransAct"
            class="size-10 hidden dark:block"
          />
          <span class="text-lg font-bold tracking-tight text-surface-900 dark:text-surface-0"
            >TransAct</span
          >
        </div>

        <h1 class="text-3xl sm:text-4xl font-extrabold tracking-tight text-surface-900 dark:text-surface-0">
          Welcome back, {{ auth.user?.first_name }}
        </h1>

        <p class="text-surface-600 dark:text-surface-300 text-base sm:text-lg">
          TransAct helps forensic molecular biology laboratories record, standardize, and share
          raw DNA/RNA transfer data — building the evidence base for activity-level crime scene
          reconstruction.
        </p>

        <div class="flex flex-wrap items-center justify-center gap-3 mt-1">
          <UButton label="Browse studies" icon="i-lucide-book-open" size="lg" :to="{ name: 'studies-all' }" />
          <UButton
            label="Your laboratory"
            icon="i-lucide-building-2"
            size="lg"
            color="neutral"
            variant="outline"
            :to="{ name: 'studies-laboratory' }"
          />
          <UButton
            label="Documentation"
            icon="i-lucide-file-text"
            size="lg"
            color="neutral"
            variant="ghost"
            :to="{ name: 'docs' }"
          />
        </div>
      </div>
    </div>

    <!-- Live stats -->
    <div class="grid grid-cols-1 sm:grid-cols-3 gap-4">
      <UCard v-for="stat in stats" :key="stat.label">
        <div class="flex items-center gap-4">
          <div
            class="flex items-center justify-center size-11 rounded-lg bg-primary/10 text-primary shrink-0"
          >
            <UIcon :name="stat.icon" class="size-6" />
          </div>
          <div class="min-w-0">
            <p class="text-2xl font-bold text-surface-900 dark:text-surface-0">
              {{ statsLoading ? '–' : stat.value }}
            </p>
            <p class="text-sm text-surface-500 truncate">{{ stat.label }}</p>
          </div>
        </div>
      </UCard>
    </div>
  </div>
</template>
