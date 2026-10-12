<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import LegalPageEditor from '@/components/settings/LegalPageEditor.vue'
import { siteSettingsApi } from '@/api/siteSettings'
import type { LegalPageMode, SiteSettings } from '@/api/types'

const settings = ref<SiteSettings | null>(null)
const loading = ref(false)

const sitePrint = reactive({ saving: false, error: '', success: false })
const privacyPolicy = reactive({ saving: false, error: '', success: false })

async function load() {
  loading.value = true
  try {
    settings.value = await siteSettingsApi.get()
  } finally {
    loading.value = false
  }
}

onMounted(load)

function updateSitePrint(field: 'mode' | 'text' | 'url', value: string) {
  if (!settings.value) return
  if (field === 'mode') settings.value.site_print_mode = value as LegalPageMode
  if (field === 'text') settings.value.site_print_text = value
  if (field === 'url') settings.value.site_print_url = value
}

function updatePrivacyPolicy(field: 'mode' | 'text' | 'url', value: string) {
  if (!settings.value) return
  if (field === 'mode') settings.value.privacy_policy_mode = value as LegalPageMode
  if (field === 'text') settings.value.privacy_policy_text = value
  if (field === 'url') settings.value.privacy_policy_url = value
}

async function saveSitePrint() {
  if (!settings.value) return
  sitePrint.saving = true
  sitePrint.error = ''
  sitePrint.success = false
  try {
    settings.value = await siteSettingsApi.update({
      site_print_mode: settings.value.site_print_mode,
      site_print_text: settings.value.site_print_text,
      site_print_url: settings.value.site_print_url,
    })
    sitePrint.success = true
  } catch {
    sitePrint.error = 'Could not save the Site Print page. Please try again.'
  } finally {
    sitePrint.saving = false
  }
}

async function savePrivacyPolicy() {
  if (!settings.value) return
  privacyPolicy.saving = true
  privacyPolicy.error = ''
  privacyPolicy.success = false
  try {
    settings.value = await siteSettingsApi.update({
      privacy_policy_mode: settings.value.privacy_policy_mode,
      privacy_policy_text: settings.value.privacy_policy_text,
      privacy_policy_url: settings.value.privacy_policy_url,
    })
    privacyPolicy.success = true
  } catch {
    privacyPolicy.error = 'Could not save the Privacy Policy page. Please try again.'
  } finally {
    privacyPolicy.saving = false
  }
}
</script>

<template>
  <div class="flex flex-col gap-6">
    <h1 class="text-2xl font-bold text-surface-900 dark:text-surface-0">Legal Pages</h1>

    <p class="text-sm text-muted">
      Configure the Site Print and Privacy Policy pages shown in the footer. Each can either
      link to an external page, or show custom text managed here.
    </p>

    <template v-if="settings">
      <div class="flex flex-col gap-3">
        <LegalPageEditor
          title="Site Print"
          :mode="settings.site_print_mode"
          :text="settings.site_print_text"
          :url="settings.site_print_url"
          :saving="sitePrint.saving"
          @update:mode="(v) => updateSitePrint('mode', v)"
          @update:text="(v) => updateSitePrint('text', v)"
          @update:url="(v) => updateSitePrint('url', v)"
          @save="saveSitePrint"
        />
        <UAlert v-if="sitePrint.error" color="error" variant="outline" :description="sitePrint.error" />
        <UAlert
          v-if="sitePrint.success"
          color="success"
          variant="outline"
          description="Site Print saved."
        />
      </div>

      <USeparator />

      <div class="flex flex-col gap-3">
        <LegalPageEditor
          title="Privacy Policy"
          :mode="settings.privacy_policy_mode"
          :text="settings.privacy_policy_text"
          :url="settings.privacy_policy_url"
          :saving="privacyPolicy.saving"
          @update:mode="(v) => updatePrivacyPolicy('mode', v)"
          @update:text="(v) => updatePrivacyPolicy('text', v)"
          @update:url="(v) => updatePrivacyPolicy('url', v)"
          @save="savePrivacyPolicy"
        />
        <UAlert
          v-if="privacyPolicy.error"
          color="error"
          variant="outline"
          :description="privacyPolicy.error"
        />
        <UAlert
          v-if="privacyPolicy.success"
          color="success"
          variant="outline"
          description="Privacy Policy saved."
        />
      </div>
    </template>
  </div>
</template>
