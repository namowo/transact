<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { RouterLink, useRoute, useRouter } from 'vue-router'
import PrivacyPolicyContent from '@/components/legal/PrivacyPolicyContent.vue'
import { privacyPolicyApi } from '@/api/privacyPolicy'
import { getErrorMessage } from '@/api/errors'
import { useAuthStore } from '@/stores/auth'
import { usePrivacyPolicyStore } from '@/stores/privacyPolicy'

// Shown after signing in while the user hasn't agreed to the privacy
// policy in force, e.g. because a new version was published.
const auth = useAuthStore()
const store = usePrivacyPolicyStore()
const router = useRouter()
const route = useRoute()

const agreed = ref(false)
const submitting = ref(false)
const error = ref('')

// Agreed to an earlier version, so this one is an update.
const isUpdate = computed(() => (auth.user?.accepted_privacy_policy_ids?.length ?? 0) > 0)

onMounted(() => store.load(true))

function continueToApp() {
  router.push((route.query.redirect as string) || { name: 'dashboard' })
}

async function onAccept() {
  if (!store.active) return
  error.value = ''
  submitting.value = true
  try {
    await privacyPolicyApi.accept(store.active.id)
    await auth.fetchCurrentUser()
    continueToApp()
  } catch (err) {
    // Most likely a newer version was published meanwhile: show that one.
    error.value = getErrorMessage(err, 'Could not save your consent. Please try again.')
    agreed.value = false
    await store.load(true)
  } finally {
    submitting.value = false
  }
}

async function onLogout() {
  await auth.logout()
  router.push({ name: 'login' })
}
</script>

<template>
  <div class="flex flex-col gap-6">
    <div class="flex flex-col gap-1">
      <h1 class="text-3xl font-medium text-surface-900 dark:text-surface-0">
        {{ isUpdate ? 'We updated our privacy policy' : 'Privacy policy' }}
      </h1>
      <p class="text-sm text-surface-500 dark:text-surface-400">
        <template v-if="isUpdate">
          Please read the new version and agree to it to continue using TransAct.
        </template>
        <template v-else>Please read our privacy policy and agree to it to continue.</template>
      </p>
    </div>

    <div v-if="store.loading && !store.active" class="flex flex-col gap-3" aria-busy="true">
      <USkeleton class="h-4 w-full" />
      <USkeleton class="h-4 w-11/12" />
      <USkeleton class="h-4 w-4/5" />
      <USkeleton class="h-4 w-2/3" />
    </div>

    <template v-else-if="store.active">
      <div class="max-h-96 overflow-y-auto rounded-md border border-default p-4">
        <PrivacyPolicyContent :policy="store.active" />
      </div>
      <p class="text-xs text-muted -mt-4">
        Version {{ store.active.version }} ·
        <RouterLink :to="{ name: 'privacy-policy' }" target="_blank" class="text-primary hover:underline">
          Open in a new tab
        </RouterLink>
      </p>

      <UCheckbox v-model="agreed" label="I have read and agree to the Privacy Policy" />

      <UAlert v-if="error" color="error" variant="outline" :description="error" />

      <UButton
        label="Agree and continue"
        icon="i-lucide-arrow-right"
        trailing
        block
        :disabled="!agreed"
        :loading="submitting"
        @click="onAccept"
      />
    </template>

    <template v-else>
      <p class="text-sm text-muted">There is no privacy policy to agree to.</p>
      <UButton label="Continue" icon="i-lucide-arrow-right" trailing block @click="continueToApp" />
    </template>

    <p class="text-center text-sm text-surface-600 dark:text-surface-300">
      Signed in as {{ auth.user?.email }}.
      <button
        type="button"
        class="text-primary bg-transparent border-0 cursor-pointer p-0 hover:underline"
        @click="onLogout"
      >
        Log out
      </button>
    </p>
  </div>
</template>
