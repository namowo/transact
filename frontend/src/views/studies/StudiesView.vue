<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import DataView from 'primevue/dataview'
import SelectButton from 'primevue/selectbutton'
import { useToast } from '@nuxt/ui/composables'
import { listStudies } from '@/api/studies'
import { useAuthStore } from '@/stores/auth'
import type { Study } from '@/api/types'

const props = defineProps<{ scope: 'laboratory' | 'all' }>()

const router = useRouter()
const auth = useAuthStore()
const toast = useToast()

const studies = ref<Study[]>([])
const loading = ref(false)

const searchQuery = ref('')
const sortKey = ref('year_desc')
const sortOptions = [
  { label: 'Newest first', value: 'year_desc' },
  { label: 'Oldest first', value: 'year_asc' },
  { label: 'Title A-Z', value: 'title_asc' },
  { label: 'Title Z-A', value: 'title_desc' },
]

function formatAuthors(authors: Study['authors']): string {
  return authors
    .map((author) => [author.title, author.first_name, author.last_name].filter(Boolean).join(' '))
    .join(', ')
}

async function load() {
  loading.value = true
  try {
    studies.value = await listStudies()
  } finally {
    loading.value = false
  }
}

onMounted(load)

const scopedStudies = computed(() =>
  props.scope === 'laboratory'
    ? studies.value.filter((study) => study.laboratory_id === auth.user?.laboratory_id)
    : studies.value,
)

const filteredStudies = computed(() => {
  const query = searchQuery.value.trim().toLowerCase()
  let items = scopedStudies.value

  if (query) {
    items = items.filter((study) =>
      [study.title, formatAuthors(study.authors), study.journal, study.doi]
        .filter((field): field is string => !!field)
        .some((field) => field.toLowerCase().includes(query)),
    )
  }

  const sorted = [...items]
  switch (sortKey.value) {
    case 'year_asc':
      sorted.sort((a, b) => (a.year ?? '').localeCompare(b.year ?? ''))
      break
    case 'year_desc':
      sorted.sort((a, b) => (b.year ?? '').localeCompare(a.year ?? ''))
      break
    case 'title_asc':
      sorted.sort((a, b) => (a.title ?? '').localeCompare(b.title ?? ''))
      break
    case 'title_desc':
      sorted.sort((a, b) => (b.title ?? '').localeCompare(a.title ?? ''))
      break
  }
  return sorted
})

function isOwnLab(study: Study) {
  return study.laboratory_id === auth.user?.laboratory_id
}

function canEdit(study: Study) {
  return !!auth.user && (auth.user.is_superuser || isOwnLab(study))
}

function downloadStudy(study: Study) {
  toast.add({
    color: 'info',
    title: 'Coming soon',
    description: `Downloading data for "${study.title}" will be available in a future update.`,
    duration: 4000,
  })
}

const showPurposeDialog = ref(false)

function choosePurpose(purpose: 'transfer' | 'repository') {
  showPurposeDialog.value = false
  router.push({ name: 'studies-new', query: { purpose } })
}
</script>

<template>
  <div class="flex flex-col gap-6">
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-2xl font-bold text-surface-900 dark:text-surface-0">
          {{ props.scope === 'laboratory' ? 'Studies by Laboratory' : 'All Studies' }}
        </h1>
        <p class="text-surface-500 dark:text-surface-400 text-sm mt-1">
          {{
            props.scope === 'laboratory'
              ? 'Studies belonging to your laboratory.'
              : auth.isAuthenticated
                ? 'Studies from all laboratories. You can only edit studies from your own laboratory.'
                : 'Published studies from all laboratories.'
          }}
        </p>
      </div>
      <UButton
        v-if="auth.isAuthenticated"
        label="Add study"
        icon="i-lucide-plus"
        @click="showPurposeDialog = true"
      />
    </div>

    <DataView :value="filteredStudies" :loading="loading" data-key="id" paginator :rows="10">
      <template #header>
        <div class="flex flex-col sm:flex-row gap-4 sm:items-center sm:justify-between">
          <UInput
            v-model="searchQuery"
            icon="i-lucide-search"
            placeholder="Search title, author, journal, DOI…"
            class="sm:max-w-sm w-full"
          />
          <SelectButton
            v-model="sortKey"
            :options="sortOptions"
            optionLabel="label"
            optionValue="value"
            :allowEmpty="false"
          />
        </div>
      </template>

      <template #empty>
        <div class="text-center text-surface-500 dark:text-surface-400 py-8">
          No studies found.
        </div>
      </template>

      <template #list="slotProps">
        <div class="flex flex-col">
          <div
            v-for="(item, index) in slotProps.items as Study[]"
            :key="item.id"
            class="flex flex-col sm:flex-row sm:items-start p-6 gap-4"
            :class="{ 'border-t border-surface-200 dark:border-surface-700': index !== 0 }"
          >
            <div class="flex-1 flex flex-col gap-2">
              <div class="flex flex-wrap items-center gap-2">
                <UBadge
                  :label="item.laboratory?.laboratory_name ?? 'Unknown laboratory'"
                  :color="isOwnLab(item) ? 'success' : 'neutral'"
                />
                <UBadge v-if="item.quality_check_passed" label="QC passed" color="info" />
                <span v-if="item.year" class="text-surface-500 dark:text-surface-400 text-sm">{{
                  item.year
                }}</span>
              </div>
              <div class="text-lg font-medium">{{ item.title }}</div>
              <div v-if="item.authors.length" class="text-sm text-surface-500 dark:text-surface-400">
                {{ formatAuthors(item.authors) }}
              </div>
              <div v-if="item.journal" class="text-sm text-surface-500 dark:text-surface-400">
                {{ item.journal }}
              </div>
              <p v-if="item.abstract" class="text-sm mt-1 line-clamp-3">{{ item.abstract }}</p>
              <a
                v-if="item.doi"
                :href="`https://doi.org/${item.doi}`"
                target="_blank"
                rel="noopener"
                class="text-sm text-primary w-fit"
                >DOI: {{ item.doi }}</a
              >
            </div>
            <div v-if="auth.isAuthenticated" class="flex flex-row items-start gap-4 shrink-0">
              <div class="flex flex-col gap-2">
                <span
                  class="text-xs font-semibold uppercase tracking-wide text-surface-500 dark:text-surface-400"
                >
                  Edit
                </span>
                <div class="flex flex-row sm:flex-col gap-2">
                  <UButton
                    label="Details"
                    icon="i-lucide-pencil"
                    color="neutral"
                    size="sm"
                    variant="outline"
                    :disabled="!canEdit(item)"
                    @click="
                      router.push({
                        name: 'studies-edit',
                        params: { id: item.id },
                        query: { step: 'details' },
                      })
                    "
                  />
                  <UButton
                    label="Planning"
                    icon="i-lucide-network"
                    color="neutral"
                    size="sm"
                    variant="outline"
                    :disabled="!canEdit(item)"
                    @click="
                      router.push({
                        name: 'studies-edit',
                        params: { id: item.id },
                        query: { step: 'planning' },
                      })
                    "
                  />
                  <UButton
                    v-if="item.add_data_to_repository"
                    label="Add data"
                    icon="i-lucide-database"
                    color="neutral"
                    size="sm"
                    variant="outline"
                    :disabled="!canEdit(item)"
                    @click="
                      router.push({
                        name: 'studies-edit',
                        params: { id: item.id },
                        query: { step: 'data-entry' },
                      })
                    "
                  />
                </div>
              </div>
              <UButton
                label="Download"
                icon="i-lucide-download"
                size="sm"
                variant="outline"
                @click="downloadStudy(item)"
              />
            </div>
          </div>
        </div>
      </template>
    </DataView>

    <UModal
      v-model:open="showPurposeDialog"
      title="What would you like to do?"
      :ui="{ content: 'max-w-lg' }"
    >
      <template #body>
      <div class="flex flex-col sm:flex-row gap-3">
        <UButton
          label="Plan a transfer experiment"
          class="flex-1"
          variant="outline"
          @click="choosePurpose('transfer')"
        />
        <UButton
          label="Add data to repository"
          class="flex-1"
          variant="outline"
          @click="choosePurpose('repository')"
        />
      </div>
      </template>
      <template #footer>
        <UButton label="Cancel" variant="ghost" @click="showPurposeDialog = false" />
      </template>
    </UModal>
  </div>
</template>
