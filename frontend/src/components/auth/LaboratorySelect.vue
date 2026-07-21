<script setup lang="ts">
import { onMounted, ref } from 'vue'
import Select from 'primevue/select'
import Message from 'primevue/message'
import { listLaboratories } from '@/api/laboratories'
import type { Laboratory } from '@/api/types'

const modelValue = defineModel<number | null>({ default: null })

const laboratories = ref<Laboratory[]>([])
const loading = ref(false)
const loadError = ref('')

async function loadLaboratories() {
  loading.value = true
  loadError.value = ''
  try {
    laboratories.value = await listLaboratories()
  } catch {
    loadError.value = 'Could not load laboratories.'
  } finally {
    loading.value = false
  }
}

onMounted(loadLaboratories)
</script>

<template>
  <div>
    <Select
      v-model="modelValue"
      :options="laboratories"
      option-label="laboratory_name"
      option-value="id"
      filter
      show-clear
      :loading="loading"
      placeholder="Select your laboratory"
      class="w-full"
      fluid
    />
    <Message v-if="loadError" severity="error" size="small" variant="simple" class="mt-1">
      {{ loadError }}
    </Message>
  </div>
</template>
