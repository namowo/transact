<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import type { TableColumn } from '@nuxt/ui'
import LegalPageEditor from '@/components/settings/LegalPageEditor.vue'
import { privacyPolicyApi } from '@/api/privacyPolicy'
import { getErrorMessage } from '@/api/errors'
import { useConfirm } from '@/composables/useConfirm'
import { usePrivacyPolicyStore } from '@/stores/privacyPolicy'
import type { LegalPageMode, PrivacyPolicyAdmin } from '@/api/types'
import { usePagination } from '@/composables/useTableView'
import TablePagination from '@/components/ui/TablePagination.vue'

// Published versions are frozen: changing the policy means writing a new
// version as a draft and publishing it, which asks every user to agree
// again. All versions are kept.
const store = usePrivacyPolicyStore()
const confirm = useConfirm()

const versions = ref<PrivacyPolicyAdmin[]>([])
const loading = ref(false)
const busy = ref<'' | 'create' | 'save' | 'discard' | 'publish'>('')
const error = ref('')
const success = ref('')

// Edited copy of the draft.
const form = reactive<{ mode: LegalPageMode; text: string; url: string }>({
  mode: 'text',
  text: '',
  url: '',
})

const draft = computed(() => versions.value.find((v) => v.status === 'draft') ?? null)
const active = computed(() => versions.value.find((v) => v.status === 'active') ?? null)
const published = computed(() => versions.value.filter((v) => v.status !== 'draft'))
const publishedPages = usePagination(published)
const nextVersion = computed(() => (active.value?.version ?? 0) + 1)

const isDirty = computed(
  () =>
    !!draft.value &&
    (form.mode !== draft.value.mode ||
      form.text !== (draft.value.text ?? '') ||
      form.url !== (draft.value.url ?? '')),
)

const publishOpen = ref(false)
const notifyUsers = ref(true)

const columns: TableColumn<PrivacyPolicyAdmin>[] = [
  { id: 'version', header: 'Version' },
  { id: 'status', header: 'Status' },
  { id: 'published', header: 'Published' },
  { id: 'consents', header: 'Agreed by' },
  { id: 'actions', header: '' },
]

function resetForm() {
  form.mode = draft.value?.mode ?? 'text'
  form.text = draft.value?.text ?? ''
  form.url = draft.value?.url ?? ''
}

async function load() {
  loading.value = true
  try {
    versions.value = await privacyPolicyApi.list()
    resetForm()
  } catch (err) {
    error.value = getErrorMessage(err, 'Could not load the privacy policy.')
  } finally {
    loading.value = false
  }
}

onMounted(load)

async function run(action: typeof busy.value, fn: () => Promise<unknown>, done = '') {
  busy.value = action
  error.value = ''
  success.value = ''
  try {
    await fn()
    await load()
    success.value = done
  } catch (err) {
    error.value = getErrorMessage(err, 'Something went wrong. Please try again.')
  } finally {
    busy.value = ''
  }
}

function saveDraftChanges() {
  if (!draft.value || !isDirty.value) return Promise.resolve()
  return privacyPolicyApi.updateDraft(draft.value.id, {
    mode: form.mode,
    text: form.text,
    url: form.url,
  })
}

function createDraft() {
  run('create', () => privacyPolicyApi.createDraft())
}

function saveDraft() {
  run('save', saveDraftChanges, 'Draft saved. Users don’t see it until you publish it.')
}

function discardDraft() {
  if (!draft.value) return
  const id = draft.value.id
  confirm.require({
    header: 'Discard draft?',
    message: 'The draft and its changes are deleted. The published policy stays as it is.',
    acceptLabel: 'Discard',
    acceptColor: 'error',
    accept: () => run('discard', () => privacyPolicyApi.discardDraft(id), 'Draft discarded.'),
  })
}

function openPublish() {
  notifyUsers.value = true
  publishOpen.value = true
}

function publish() {
  if (!draft.value) return
  const id = draft.value.id
  const notify = notifyUsers.value
  publishOpen.value = false
  run(
    'publish',
    async () => {
      await saveDraftChanges()
      await privacyPolicyApi.publish(id, notify)
      // Admins have to agree to the new version too.
      await store.load(true)
    },
    `Version ${nextVersion.value} is published.` +
      (notify ? ' All users are being emailed about it.' : ''),
  )
}

function formatDate(value: string | null) {
  return value ? new Date(value).toLocaleString() : '—'
}

function personName(person: PrivacyPolicyAdmin['published_by']) {
  return person ? `${person.first_name} ${person.last_name}` : null
}
</script>

<template>
  <div class="flex flex-col gap-4">
    <div class="flex flex-col gap-1">
      <h2 class="text-lg font-semibold text-surface-900 dark:text-surface-0">Privacy Policy</h2>
      <p class="text-sm text-muted">
        Published versions can't be changed. To change the policy, create a new version and
        publish it once it's ready: every user then has to agree to the new version before they
        can continue. All earlier versions are kept below.
      </p>
    </div>

    <div v-if="loading && !versions.length" class="flex flex-col gap-3" aria-busy="true">
      <USkeleton class="h-16 w-full" />
      <USkeleton v-for="n in 3" :key="n" class="h-10 w-full" />
    </div>

    <template v-else>
      <UAlert
        v-if="active"
        color="neutral"
        variant="subtle"
        icon="i-lucide-shield-check"
        :title="`Version ${active.version} is in force`"
        :description="`Published ${formatDate(active.published_at)}${
          personName(active.published_by) ? ` by ${personName(active.published_by)}` : ''
        }. Agreed by ${active.consent_count} ${active.consent_count === 1 ? 'user' : 'users'}.`"
        :actions="[
          {
            label: 'View',
            icon: 'i-lucide-external-link',
            color: 'neutral',
            variant: 'outline',
            to: { name: 'privacy-policy', query: { version: active.id } },
            target: '_blank',
          },
        ]"
      />
      <UAlert
        v-else
        color="warning"
        variant="subtle"
        icon="i-lucide-shield-alert"
        title="No privacy policy is published yet"
        description="New users can sign up without agreeing to one."
      />

      <div v-if="draft" class="flex flex-col gap-3 rounded-md border border-default p-4">
        <div class="flex flex-wrap items-center gap-2">
          <UBadge label="Draft" color="warning" variant="subtle" />
          <span class="text-sm text-muted">
            Will become version {{ nextVersion }}. Only visible to admins until it's published.
          </span>
        </div>
        <LegalPageEditor
          v-model:mode="form.mode"
          v-model:text="form.text"
          v-model:url="form.url"
          save-label="Save draft"
          :saving="busy === 'save'"
          @save="saveDraft"
        >
          <template #actions>
            <UButton
              label="Discard draft"
              icon="i-lucide-trash-2"
              color="error"
              variant="ghost"
              :loading="busy === 'discard'"
              @click="discardDraft"
            />
            <UButton
              label="Publish…"
              icon="i-lucide-send"
              color="neutral"
              variant="outline"
              :loading="busy === 'publish'"
              @click="openPublish"
            />
          </template>
        </LegalPageEditor>
      </div>

      <div v-else>
        <UButton
          :label="active ? 'Create new version' : 'Write privacy policy'"
          icon="i-lucide-file-plus"
          :loading="busy === 'create'"
          @click="createDraft"
        />
        <p v-if="active" class="mt-2 text-xs text-muted">
          The new version starts as a copy of version {{ active.version }}.
        </p>
      </div>

      <UAlert v-if="error" color="error" variant="outline" :description="error" />
      <UAlert v-if="success" color="success" variant="outline" :description="success" />

      <div v-if="published.length" class="flex flex-col gap-2">
        <h3 class="text-sm font-semibold text-surface-900 dark:text-surface-0">Version history</h3>
        <UTable
          :data="publishedPages.rows"
          :columns="columns"
          :get-row-id="(row: PrivacyPolicyAdmin) => String(row.id)"
          class="rounded-md border border-default"
          :ui="{ td: 'py-2 text-sm' }"
        >
          <template #version-cell="{ row }">
            <span class="font-medium text-highlighted">Version {{ row.original.version }}</span>
          </template>
          <template #status-cell="{ row }">
            <UBadge
              :label="row.original.status === 'active' ? 'In force' : 'Superseded'"
              :color="row.original.status === 'active' ? 'success' : 'neutral'"
              variant="subtle"
              size="sm"
            />
          </template>
          <template #published-cell="{ row }">
            <div class="flex flex-col">
              <span>{{ formatDate(row.original.published_at) }}</span>
              <span v-if="personName(row.original.published_by)" class="text-xs text-muted">
                by {{ personName(row.original.published_by) }}
              </span>
            </div>
          </template>
          <template #consents-cell="{ row }">
            {{ row.original.consent_count }}
            {{ row.original.consent_count === 1 ? 'user' : 'users' }}
          </template>
          <template #actions-cell="{ row }">
            <div class="flex justify-end">
              <UButton
                label="View"
                icon="i-lucide-external-link"
                size="sm"
                color="neutral"
                variant="ghost"
                :to="{ name: 'privacy-policy', query: { version: row.original.id } }"
                target="_blank"
              />
            </div>
          </template>
        </UTable>
        <TablePagination v-model:page="publishedPages.page" v-model:page-size="publishedPages.pageSize" :total="publishedPages.total" />
      </div>
    </template>

    <UModal
      v-model:open="publishOpen"
      :title="`Publish version ${nextVersion}?`"
      :ui="{ footer: 'justify-end' }"
    >
      <template #body>
        <div class="flex flex-col gap-4 text-sm">
          <p>
            Version {{ nextVersion }} becomes the privacy policy in force right away.
            <strong>It can't be changed afterwards</strong> – further changes need another new
            version.
          </p>
          <p>
            Every user, you included, has to agree to it the next time they use TransAct before
            they can continue.
          </p>
          <UCheckbox
            v-model="notifyUsers"
            label="Email all users about the new privacy policy"
            description="Recommended. Sent to every active, confirmed account."
          />
        </div>
      </template>
      <template #footer>
        <UButton
          label="Cancel"
          icon="i-lucide-x"
          variant="ghost"
          color="neutral"
          @click="publishOpen = false"
        />
        <UButton :label="`Publish version ${nextVersion}`" icon="i-lucide-send" @click="publish" />
      </template>
    </UModal>
  </div>
</template>
