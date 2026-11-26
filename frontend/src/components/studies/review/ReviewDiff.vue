<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { getReviewDiff } from '@/api/studyReview'
import { getErrorMessage } from '@/api/errors'
import type { ReviewDiffRow, ReviewRound, StudyReviewDiff } from '@/api/types'
import { formatDateTime, formatValue } from './reviewLabels'

// What changed in the study between two review rounds, or since a round
// (compared with the current data). Quality checkers can pin a comment to a
// changed record or field straight from here.

const props = defineProps<{ studyId: string; rounds: ReviewRound[]; canComment: boolean }>()
const emit = defineEmits<{
  comment: [target: { section: string; target_id: string; target_label: string; field_label: string | null }]
}>()

const CURRENT = 0

const fromRound = ref<number>(1)
const toRound = ref<number>(CURRENT)

function resetRange() {
  const last = props.rounds.at(-1)?.number ?? 0
  if (last >= 2) {
    fromRound.value = last - 1
    toRound.value = last
  } else {
    fromRound.value = 1
    toRound.value = CURRENT
  }
}

watch(() => props.rounds.length, resetRange, { immediate: true })

const roundLabel = (r: ReviewRound) => `Round ${r.number} · ${formatDateTime(r.submitted_at)}`
const fromItems = computed(() => props.rounds.map((r) => ({ label: roundLabel(r), value: r.number })))
const toItems = computed(() => [
  ...props.rounds.filter((r) => r.number > fromRound.value).map((r) => ({ label: roundLabel(r), value: r.number })),
  { label: 'Current data', value: CURRENT },
])

watch(fromRound, (from) => {
  if (toRound.value !== CURRENT && toRound.value <= from) toRound.value = CURRENT
})

const diff = ref<StudyReviewDiff | null>(null)
const loading = ref(false)
const error = ref('')

async function load() {
  if (!props.rounds.length) return
  loading.value = true
  error.value = ''
  try {
    diff.value = await getReviewDiff(props.studyId, fromRound.value, toRound.value || null)
  } catch (err) {
    error.value = getErrorMessage(err, 'Could not compare the rounds.')
  } finally {
    loading.value = false
  }
}

watch([fromRound, toRound, () => props.rounds.length], load, { immediate: true })

const changedSections = computed(() => diff.value?.sections.filter((s) => s.rows.length) ?? [])

const changeStyle: Record<ReviewDiffRow['change'], { label: string; color: 'success' | 'error' | 'warning' }> = {
  added: { label: 'Added', color: 'success' },
  removed: { label: 'Removed', color: 'error' },
  changed: { label: 'Changed', color: 'warning' },
}

const expanded = ref<Set<string>>(new Set())
function toggle(key: string) {
  const next = new Set(expanded.value)
  if (next.has(key)) next.delete(key)
  else next.add(key)
  expanded.value = next
}
</script>

<template>
  <div class="flex flex-col gap-4">
    <UAlert
      v-if="!rounds.length"
      color="neutral"
      variant="subtle"
      icon="i-lucide-git-compare"
      description="Changes can be compared once the study was submitted for quality check."
    />

    <template v-else>
      <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
        <UFormField label="Compare">
          <USelect v-model="fromRound" :items="fromItems" class="w-full" />
        </UFormField>
        <UFormField label="With">
          <USelect v-model="toRound" :items="toItems" class="w-full" />
        </UFormField>
      </div>

      <UAlert v-if="error" color="error" variant="outline" :description="error" />

      <div v-if="loading" class="flex flex-col gap-2" aria-busy="true">
        <USkeleton v-for="n in 4" :key="n" class="h-10 w-full" />
      </div>

      <UAlert
        v-else-if="diff && !changedSections.length"
        color="neutral"
        variant="subtle"
        icon="i-lucide-equal"
        title="No changes"
        description="The study's data is the same in both versions."
      />

      <section v-for="section in changedSections" v-else :key="section.key" class="flex flex-col gap-2">
        <div class="flex flex-wrap items-center gap-2">
          <h3 class="font-semibold text-sm">{{ section.label }}</h3>
          <UBadge v-if="section.added" :label="`+${section.added}`" color="success" variant="subtle" size="sm" />
          <UBadge v-if="section.changed" :label="`~${section.changed}`" color="warning" variant="subtle" size="sm" />
          <UBadge v-if="section.removed" :label="`−${section.removed}`" color="error" variant="subtle" size="sm" />
        </div>

        <div class="rounded-lg border border-default divide-y divide-default">
          <div v-for="row in section.rows" :key="row.id" class="p-2 flex flex-col gap-2">
            <div class="flex items-center gap-2" :class="{ 'pl-7': row.change === 'changed' }">
              <UButton
                v-if="row.change !== 'changed'"
                :icon="expanded.has(section.key + row.id) ? 'i-lucide-chevron-down' : 'i-lucide-chevron-right'"
                color="neutral"
                variant="ghost"
                size="xs"
                :aria-label="expanded.has(section.key + row.id) ? 'Hide fields' : 'Show fields'"
                @click="toggle(section.key + row.id)"
              />
              <UBadge :label="changeStyle[row.change].label" :color="changeStyle[row.change].color" variant="soft" size="sm" />
              <span class="text-sm font-medium truncate">{{ row.label }}</span>
              <span v-if="row.change === 'changed'" class="text-xs text-muted shrink-0">
                {{ row.fields.length }} field{{ row.fields.length === 1 ? '' : 's' }}
              </span>
              <UButton
                v-if="canComment"
                icon="i-lucide-message-square-plus"
                color="neutral"
                variant="ghost"
                size="xs"
                class="ml-auto"
                aria-label="Comment on this record"
                @click="emit('comment', { section: section.key, target_id: row.id, target_label: row.label, field_label: null })"
              />
            </div>

            <div v-if="expanded.has(section.key + row.id) || row.change === 'changed'" class="overflow-x-auto">
              <table class="w-full text-sm">
                <tbody>
                  <tr v-for="field in row.fields" :key="field.key" class="group align-top">
                    <td class="py-1 pr-3 text-muted whitespace-nowrap">{{ field.label }}</td>
                    <td v-if="row.change !== 'added'" class="py-1 pr-3">
                      <span :class="row.change === 'changed' ? 'line-through text-error' : ''">{{ formatValue(field.old) }}</span>
                    </td>
                    <td v-if="row.change !== 'removed'" class="py-1 pr-3">
                      <span :class="row.change === 'changed' ? 'text-success' : ''">{{ formatValue(field.new) }}</span>
                    </td>
                    <td class="py-1 w-6">
                      <UButton
                        v-if="canComment"
                        icon="i-lucide-message-square-plus"
                        color="neutral"
                        variant="link"
                        size="xs"
                        class="opacity-0 group-hover:opacity-100 focus:opacity-100"
                        :aria-label="`Comment on ${field.label}`"
                        @click="emit('comment', { section: section.key, target_id: row.id, target_label: row.label, field_label: field.label })"
                      />
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </section>
    </template>
  </div>
</template>
