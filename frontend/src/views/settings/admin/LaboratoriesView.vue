<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useForm } from 'vee-validate'
import * as yup from 'yup'
import { createLaboratory, listLaboratories, updateLaboratory } from '@/api/laboratories'
import {
  approveMembershipRequest,
  denyMembershipRequest,
  listPendingNewLabs,
} from '@/api/labMembershipRequests'
import type { Laboratory, LaboratoryApprovalStatus, LabMembershipRequest } from '@/api/types'
import { COUNTRIES } from '@/constants/countries'
import { useAuthStore } from '@/stores/auth'
import type { ContextMenuItem, TableColumn, TableRow } from '@nuxt/ui'
import { manualSorting, useTableView } from '@/composables/useTableView'
import { sortHeader } from '@/composables/tableColumns'
import TableFilterDrawer from '@/components/ui/TableFilterDrawer.vue'
import TablePagination from '@/components/ui/TablePagination.vue'

const auth = useAuthStore()
const laboratories = ref<Laboratory[]>([])
const loading = ref(false)

const approvalStatusOptions = [
  { label: 'Pending', value: 'pending' },
  { label: 'Approved', value: 'approved' },
  { label: 'Denied', value: 'denied' },
]

const approvalStatusLabels: Record<LaboratoryApprovalStatus, string> = {
  pending: 'Pending',
  approved: 'Approved',
  denied: 'Denied',
}

const approvalStatusColors: Record<LaboratoryApprovalStatus, 'warning' | 'success' | 'error'> = {
  pending: 'warning',
  approved: 'success',
  denied: 'error',
}

const view = useTableView(laboratories, {
  searchFields: ['laboratory_name', 'institutional_affiliation', 'city', 'country'],
  filters: {
    laboratory_name: { field: 'laboratory_name' },
    institutional_affiliation: { field: 'institutional_affiliation' },
    city: { field: 'city' },
    country: { field: 'country' },
    approval_status: { field: 'approval_status', mode: 'equals' },
  },
  pageSize: 10,
})

const columns = computed<TableColumn<Laboratory>[]>(() => [
  { id: 'laboratory_name', accessorKey: 'laboratory_name', header: sortHeader('Name') },
  {
    id: 'institutional_affiliation',
    accessorKey: 'institutional_affiliation',
    header: sortHeader('Affiliation'),
  },
  { id: 'city', accessorKey: 'city', header: sortHeader('City') },
  { id: 'country', accessorKey: 'country', header: sortHeader('Country') },
  ...(auth.can('laboratories.manage')
    ? [
        { id: 'approval_status', accessorKey: 'approval_status', header: sortHeader('Status') },
        { id: 'actions', header: '', meta: { class: { td: 'w-12' } } },
      ]
    : []),
])

const requestColumns: TableColumn<LabMembershipRequest>[] = [
  { id: 'laboratory', header: 'Laboratory' },
  { id: 'affiliation', header: 'Affiliation' },
  { id: 'city', accessorKey: 'city', header: 'City' },
  { id: 'country', accessorKey: 'country', header: 'Country' },
  { id: 'requester', header: 'Requester' },
  { id: 'created_at', accessorKey: 'created_at', header: 'Requested' },
  { id: 'actions', header: '', meta: { class: { td: 'w-56' } } },
]

const requests = ref<LabMembershipRequest[]>([])
const requestsLoading = ref(false)
const requestsLoadError = ref('')
const requestsActionError = ref('')
const actingOnId = ref<string | null>(null)

const dialogVisible = ref(false)
// The laboratory being edited; null while adding a new one.
const editingLaboratory = ref<Laboratory | null>(null)
const submitting = ref(false)
const submitError = ref('')

// Mirrors the schema in components/auth/LaboratorySelect.vue's inline
// add-laboratory dialog, so both entry points enforce the same rules.
const schema = yup.object({
  laboratory_name: yup.string().trim().required('Laboratory name is required.'),
  institutional_affiliation: yup.string().trim().required('Institutional affiliation is required.'),
  director_head_of_laboratory: yup.string().trim().defined(),
  street_address: yup.string().trim().defined(),
  city: yup.string().trim().required('City is required.'),
  state: yup.string().trim().defined(),
  postal_code: yup.string().trim().defined(),
  country: yup.string().trim().required('Country is required.'),
  email: yup.string().trim().email('Please enter a valid email address.').defined(),
})

const { defineField, errors, handleSubmit, resetForm } = useForm({
  validationSchema: schema,
  initialValues: {
    laboratory_name: '',
    institutional_affiliation: '',
    director_head_of_laboratory: '',
    street_address: '',
    city: '',
    state: '',
    postal_code: '',
    country: '',
    email: '',
  },
})

const [laboratoryName] = defineField('laboratory_name')
const [institutionalAffiliation] = defineField('institutional_affiliation')
const [directorHeadOfLaboratory] = defineField('director_head_of_laboratory')
const [streetAddress] = defineField('street_address')
const [city] = defineField('city')
const [state] = defineField('state')
const [postalCode] = defineField('postal_code')
const [country] = defineField('country')
const [email] = defineField('email')

async function load() {
  loading.value = true
  try {
    laboratories.value = await listLaboratories()
  } finally {
    loading.value = false
  }
}

async function loadRequests() {
  requestsLoading.value = true
  requestsLoadError.value = ''
  try {
    requests.value = await listPendingNewLabs()
  } catch {
    requestsLoadError.value = 'Could not load pending laboratory requests.'
  } finally {
    requestsLoading.value = false
  }
}

onMounted(() => {
  load()
  loadRequests()
})

async function approve(request: LabMembershipRequest) {
  requestsActionError.value = ''
  actingOnId.value = request.id
  try {
    await approveMembershipRequest(request.id)
    requests.value = requests.value.filter((r) => r.id !== request.id)
    await load()
  } catch {
    requestsActionError.value = 'Could not approve this request. Please try again.'
  } finally {
    actingOnId.value = null
  }
}

async function deny(request: LabMembershipRequest) {
  requestsActionError.value = ''
  actingOnId.value = request.id
  try {
    await denyMembershipRequest(request.id)
    requests.value = requests.value.filter((r) => r.id !== request.id)
  } catch {
    requestsActionError.value = 'Could not deny this request. Please try again.'
  } finally {
    actingOnId.value = null
  }
}

function openDialog() {
  editingLaboratory.value = null
  resetForm()
  submitError.value = ''
  dialogVisible.value = true
}

function openEditDialog(lab: Laboratory) {
  if (!auth.can('laboratories.manage')) return
  editingLaboratory.value = lab
  resetForm({
    values: {
      laboratory_name: lab.laboratory_name,
      institutional_affiliation: lab.institutional_affiliation ?? '',
      director_head_of_laboratory: lab.director_head_of_laboratory ?? '',
      street_address: lab.street_address ?? '',
      city: lab.city ?? '',
      state: lab.state ?? '',
      postal_code: lab.postal_code ?? '',
      country: lab.country ?? '',
      email: lab.email ?? '',
    },
  })
  submitError.value = ''
  dialogVisible.value = true
}

function menuItems(lab: Laboratory): ContextMenuItem[] {
  return [{ label: 'Edit', icon: 'i-lucide-pencil', onSelect: () => openEditDialog(lab) }]
}

// The right-clicked row's menu.
const contextMenuItems = ref<ContextMenuItem[]>([])

function onRowContextMenu(_event: Event, row: TableRow<Laboratory>) {
  contextMenuItems.value = auth.can('laboratories.manage') ? menuItems(row.original) : []
}

// Keeps a country stored before the country list existed selectable.
const countryItems = computed(() =>
  country.value && !COUNTRIES.includes(country.value) ? [country.value, ...COUNTRIES] : COUNTRIES,
)

const submitLaboratory = handleSubmit(async (values) => {
  submitting.value = true
  submitError.value = ''
  const payload = {
    laboratory_name: values.laboratory_name.trim(),
    institutional_affiliation: values.institutional_affiliation.trim(),
    director_head_of_laboratory: values.director_head_of_laboratory.trim() || null,
    street_address: values.street_address.trim() || null,
    city: values.city.trim(),
    state: values.state.trim() || null,
    postal_code: values.postal_code.trim() || null,
    country: values.country.trim(),
    email: values.email.trim() || null,
  }
  const editing = editingLaboratory.value
  try {
    if (editing) {
      const updated = await updateLaboratory(editing.id, payload)
      laboratories.value = laboratories.value.map((lab) => (lab.id === updated.id ? updated : lab))
    } else {
      laboratories.value.push(await createLaboratory(payload))
    }
    dialogVisible.value = false
  } catch {
    submitError.value = editing
      ? 'Could not save the laboratory. Please try again.'
      : 'Could not create the laboratory. Please try again.'
  } finally {
    submitting.value = false
  }
})
</script>

<template>
  <div class="flex flex-col gap-6">
    <div class="flex items-center justify-between">
      <h1 class="text-2xl font-bold text-surface-900 dark:text-surface-0">Laboratories</h1>
      <UButton
        v-if="auth.can('laboratories.manage')"
        label="Add laboratory"
        icon="i-lucide-plus"
        @click="openDialog"
      />
    </div>

    <div v-if="requests.length || requestsLoading" class="flex flex-col gap-3">
      <h2 class="text-lg font-semibold text-surface-900 dark:text-surface-0">Pending approvals</h2>

      <UAlert
        v-if="requestsLoadError"
        color="error"
        variant="outline"
        :description="requestsLoadError"
      />
      <UAlert
        v-if="requestsActionError"
        color="error"
        variant="outline"
        :description="requestsActionError"
      />

      <UTable
        :data="requests"
        :columns="requestColumns"
        :loading="requestsLoading"
        :get-row-id="(request: LabMembershipRequest) => request.id"
      >
        <template #laboratory-cell="{ row }">{{
          row.original.laboratory?.laboratory_name
        }}</template>
        <template #affiliation-cell="{ row }">{{
          row.original.laboratory?.institutional_affiliation
        }}</template>
        <template #city-cell="{ row }">{{ row.original.laboratory?.city }}</template>
        <template #country-cell="{ row }">{{ row.original.laboratory?.country }}</template>
        <template #requester-cell="{ row }">
          {{ row.original.user.first_name }} {{ row.original.user.last_name }} ({{
            row.original.user.email
          }})
        </template>
        <template #created_at-cell="{ row }">
          {{ new Date(row.original.created_at).toLocaleDateString() }}
        </template>
        <template #actions-cell="{ row }">
          <div class="flex gap-1 justify-end">
            <UButton
              label="Approve"
              icon="i-lucide-check"
              size="sm"
              :loading="actingOnId === row.original.id"
              @click="approve(row.original)"
            />
            <UButton
              label="Deny"
              icon="i-lucide-x"
              color="error"
              variant="ghost"
              size="sm"
              :loading="actingOnId === row.original.id"
              @click="deny(row.original)"
            />
          </div>
        </template>
      </UTable>
    </div>

    <div class="flex flex-col gap-3">
      <div class="flex flex-wrap items-center justify-between gap-3">
        <UInput
          v-model="view.search"
          icon="i-lucide-search"
          placeholder="Keyword Search"
          class="w-full max-w-sm"
        />
        <TableFilterDrawer :active-count="view.activeFilterCount" @reset="view.resetFilters()">
          <UFormField label="Name">
            <UInput
              v-model="view.filters.laboratory_name"
              placeholder="Search by name"
              class="w-full"
            />
          </UFormField>
          <UFormField label="Affiliation">
            <UInput
              v-model="view.filters.institutional_affiliation"
              placeholder="Search by affiliation"
              class="w-full"
            />
          </UFormField>
          <UFormField label="City">
            <UInput v-model="view.filters.city" placeholder="Search by city" class="w-full" />
          </UFormField>
          <UFormField label="Country">
            <UInput v-model="view.filters.country" placeholder="Search by country" class="w-full" />
          </UFormField>
          <UFormField v-if="auth.can('laboratories.manage')" label="Status">
            <USelectMenu
              v-model="view.filters.approval_status"
              :items="approvalStatusOptions"
              value-key="value"
              placeholder="Any status"
              clear
              class="w-full"
            />
          </UFormField>
        </TableFilterDrawer>
      </div>

      <UContextMenu :items="contextMenuItems" :disabled="!auth.can('laboratories.manage')">
        <UTable
          v-model:sorting="view.sorting"
          :sorting-options="manualSorting"
          :data="view.rows"
          :columns="columns"
          :loading="loading"
          :get-row-id="(lab: Laboratory) => lab.id"
          empty="No laboratories found."
          :on-select="
            auth.can('laboratories.manage')
              ? (_e: Event, row: TableRow<Laboratory>) => openEditDialog(row.original)
              : undefined
          "
          :on-contextmenu="onRowContextMenu"
          :ui="{ tr: auth.can('laboratories.manage') ? 'cursor-pointer' : '' }"
        >
          <template #approval_status-cell="{ row }: { row: TableRow<Laboratory> }">
            <UBadge
              :label="approvalStatusLabels[row.original.approval_status]"
              :color="approvalStatusColors[row.original.approval_status]"
              variant="subtle"
              size="sm"
            />
          </template>
          <template #actions-cell="{ row }">
            <div class="flex justify-end">
              <UDropdownMenu :items="menuItems(row.original)" :content="{ align: 'end' }">
                <UButton
                  icon="i-lucide-more-vertical"
                  color="neutral"
                  variant="ghost"
                  square
                  :aria-label="`Actions for ${row.original.laboratory_name}`"
                />
              </UDropdownMenu>
            </div>
          </template>
        </UTable>
      </UContextMenu>
      <TablePagination
        v-model:page="view.page"
        v-model:page-size="view.pageSize"
        :total="view.total"
      />
    </div>

    <UModal
      v-model:open="dialogVisible"
      :title="editingLaboratory ? 'Edit laboratory' : 'Add laboratory'"
      :ui="{ content: 'max-w-lg', footer: 'justify-end' }"
    >
      <template #body>
        <div class="flex flex-col gap-4">
          <div class="flex flex-col gap-2">
            <label for="name" class="font-medium text-sm">Laboratory name *</label>
            <UInput
              id="name"
              v-model="laboratoryName"
              :color="errors.laboratory_name ? 'error' : undefined"
              class="w-full"
              autofocus
            />
            <UAlert
              v-if="errors.laboratory_name"
              color="error"
              variant="subtle"
              :description="errors.laboratory_name"
            />
          </div>
          <div class="flex flex-col gap-2">
            <label for="affiliation" class="font-medium text-sm">Institutional affiliation *</label>
            <UInput
              id="affiliation"
              v-model="institutionalAffiliation"
              :color="errors.institutional_affiliation ? 'error' : undefined"
              class="w-full"
            />
            <UAlert
              v-if="errors.institutional_affiliation"
              color="error"
              variant="subtle"
              :description="errors.institutional_affiliation"
            />
          </div>
          <div class="flex flex-col gap-2">
            <label for="director" class="font-medium text-sm">Director / head of laboratory</label>
            <UInput id="director" v-model="directorHeadOfLaboratory" class="w-full" />
          </div>
          <div class="flex flex-col gap-2">
            <label for="street" class="font-medium text-sm">Street address</label>
            <UInput id="street" v-model="streetAddress" class="w-full" />
          </div>
          <div class="grid grid-cols-2 gap-4">
            <div class="flex flex-col gap-2">
              <label for="postal" class="font-medium text-sm">Postal code</label>
              <UInput id="postal" v-model="postalCode" class="w-full" />
            </div>
            <div class="flex flex-col gap-2">
              <label for="city" class="font-medium text-sm">City *</label>
              <UInput
                id="city"
                v-model="city"
                :color="errors.city ? 'error' : undefined"
                class="w-full"
              />
              <UAlert
                v-if="errors.city"
                color="error"
                variant="subtle"
                :description="errors.city"
              />
            </div>
            <div class="flex flex-col gap-2">
              <label for="state" class="font-medium text-sm">State</label>
              <UInput id="state" v-model="state" class="w-full" />
            </div>
            <div class="flex flex-col gap-2">
              <label for="country" class="font-medium text-sm">Country *</label>
              <USelect
                id="country"
                v-model="country"
                :items="countryItems"
                placeholder="Select country"
                :color="errors.country ? 'error' : undefined"
                class="w-full"
              />
              <UAlert
                v-if="errors.country"
                color="error"
                variant="subtle"
                :description="errors.country"
              />
            </div>
          </div>
          <div class="flex flex-col gap-2">
            <label for="lab-email" class="font-medium text-sm">Contact email</label>
            <UInput
              id="lab-email"
              v-model="email"
              type="email"
              :color="errors.email ? 'error' : undefined"
              class="w-full"
            />
            <UAlert
              v-if="errors.email"
              color="error"
              variant="subtle"
              :description="errors.email"
            />
          </div>
          <UAlert v-if="submitError" color="error" variant="outline" :description="submitError" />
        </div>
      </template>
      <template #footer>
        <UButton label="Cancel" icon="i-lucide-x" variant="ghost" @click="dialogVisible = false" />
        <UButton
          :label="editingLaboratory ? 'Save' : 'Add laboratory'"
          :icon="editingLaboratory ? 'i-lucide-save' : 'i-lucide-plus'"
          :loading="submitting"
          @click="submitLaboratory"
        />
      </template>
    </UModal>
  </div>
</template>
