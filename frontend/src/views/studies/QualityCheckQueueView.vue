<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import DataTable from 'openvue/datatable'
import Column from 'openvue/column'
import { listStudies, passQualityCheck } from '@/api/studies'
import type { Study } from '@/api/types'

const studies = ref<Study[]>([])
const loading = ref(false)
const loadError = ref('')
const actionError = ref('')
const actingOnId = ref<string | null>(null)

const pendingStudies = computed(() => studies.value.filter((s) => !s.quality_check_passed))

async function load() {
  loading.value = true
  loadError.value = ''
  try {
    studies.value = await listStudies()
  } catch {
    loadError.value = 'Could not load studies.'
  } finally {
    loading.value = false
  }
}

onMounted(load)

async function approve(study: Study) {
  if (
    !window.confirm(
      'Pass the quality check for this study? This will also publish it immediately.',
    )
  ) {
    return
  }
  actionError.value = ''
  actingOnId.value = study.id
  try {
    const updated = await passQualityCheck(study.id)
    studies.value = studies.value.map((s) => (s.id === updated.id ? updated : s))
  } catch {
    actionError.value = 'Could not pass the quality check for this study. Please try again.'
  } finally {
    actingOnId.value = null
  }
}
</script>

<template>
  <div class="flex flex-col gap-6">
    <h1 class="text-2xl font-bold text-surface-900 dark:text-surface-0">Quality Check</h1>

    <UAlert v-if="loadError" color="error" variant="outline" :description="loadError" />
    <UAlert v-if="actionError" color="error" variant="outline" :description="actionError" />

    <div class="overflow-x-auto">
      <DataTable :value="pendingStudies" :loading="loading" data-key="id">
        <Column field="title" header="Title" />
        <Column header="Laboratory">
          <template #body="{ data }">{{ data.laboratory?.laboratory_name ?? '—' }}</template>
        </Column>
        <Column field="year" header="Year" />
        <Column header="" style="width: 12rem">
          <template #body="{ data }">
            <UButton
              label="Pass quality check"
              size="sm"
              :loading="actingOnId === data.id"
              @click="approve(data)"
            />
          </template>
        </Column>
      </DataTable>
    </div>
  </div>
</template>
