import { ref } from 'vue'
import { defineStore } from 'pinia'
import { privacyPolicyApi } from '@/api/privacyPolicy'
import type { PrivacyPolicy, User } from '@/api/types'

// The privacy policy in force. Users have to agree to it before they can
// use the app; a newly published version asks them again.
export const usePrivacyPolicyStore = defineStore('privacyPolicy', () => {
  const active = ref<PrivacyPolicy | null>(null)
  const loading = ref(false)
  let loadPromise: Promise<void> | null = null

  function load(force = false) {
    if (!loadPromise || force) {
      loading.value = true
      loadPromise = privacyPolicyApi
        .getActive()
        .then((policy) => {
          active.value = policy
        })
        .catch(() => {
          loadPromise = null
        })
        .finally(() => {
          loading.value = false
        })
    }
    return loadPromise
  }

  function needsConsent(user: User | null | undefined) {
    return !!user && !!active.value && !user.accepted_privacy_policy_ids?.includes(active.value.id)
  }

  return { active, loading, load, needsConsent }
})
