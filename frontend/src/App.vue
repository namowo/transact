<script setup lang="ts">
import { computed, watch } from 'vue'
import { RouterView } from 'vue-router'
import { en } from '@nuxt/ui/locale'
import { usePrimeVue } from 'openvue/config'
import { useAuthStore } from '@/stores/auth'

// Keeps the interface texts in English but follows the user's locale for
// number input (decimal separator) and date formats - in Nuxt UI via the
// UApp locale, in OpenVue via the day/month names and first day of the week.
const auth = useAuthStore()
const appLocale = computed(() => ({ ...en, code: auth.locale }))

const primevue = usePrimeVue()
watch(
  () => auth.locale,
  (code) => {
    const names = (options: Intl.DateTimeFormatOptions, count: number, start: (i: number) => Date) =>
      Array.from({ length: count }, (_, i) => new Intl.DateTimeFormat(code, options).format(start(i)))
    // 2023-01-01 was a Sunday, matching OpenVue's Sunday-first name lists.
    const day = (i: number) => new Date(2023, 0, 1 + i)
    const month = (i: number) => new Date(2023, i, 1)
    const locale = primevue.config.locale
    if (!locale) return
    locale.dayNames = names({ weekday: 'long' }, 7, day)
    locale.dayNamesShort = names({ weekday: 'short' }, 7, day)
    locale.dayNamesMin = names({ weekday: 'narrow' }, 7, day)
    locale.monthNames = names({ month: 'long' }, 12, month)
    locale.monthNamesShort = names({ month: 'short' }, 12, month)
    const weekInfo = (new Intl.Locale(code) as unknown as { weekInfo?: { firstDay: number } }).weekInfo
    locale.firstDayOfWeek = (weekInfo?.firstDay ?? 7) % 7
  },
  { immediate: true },
)
</script>

<template>
  <UApp :locale="appLocale">
    <RouterView />
  </UApp>
</template>
