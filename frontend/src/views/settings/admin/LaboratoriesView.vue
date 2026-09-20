<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useForm } from 'vee-validate'
import * as yup from 'yup'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import { FilterMatchMode } from '@primevue/core/api'
import { createLaboratory, listLaboratories } from '@/api/laboratories'
import {
  approveMembershipRequest,
  denyMembershipRequest,
  listPendingNewLabs,
} from '@/api/labMembershipRequests'
import type { Laboratory, LabMembershipRequest } from '@/api/types'
import { COUNTRIES } from '@/constants/countries'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
const laboratories = ref<Laboratory[]>([])
const loading = ref(false)

const approvalStatusOptions = [
  { label: 'Pending', value: 'pending' },
  { label: 'Approved', value: 'approved' },
  { label: 'Denied', value: 'denied' },
]

function initFilters() {
  return {
    global: { value: null, matchMode: FilterMatchMode.CONTAINS },
    laboratory_name: { value: null, matchMode: FilterMatchMode.CONTAINS },
    institutional_affiliation: { value: null, matchMode: FilterMatchMode.CONTAINS },
    city: { value: null, matchMode: FilterMatchMode.CONTAINS },
    country: { value: null, matchMode: FilterMatchMode.CONTAINS },
    approval_status: { value: null, matchMode: FilterMatchMode.EQUALS },
  }
}

const filters = ref(initFilters())

function clearFilters() {
  filters.value = initFilters()
}

const requests = ref<LabMembershipRequest[]>([])
const requestsLoading = ref(false)
const requestsLoadError = ref('')
const requestsActionError = ref('')
const actingOnId = ref<string | null>(null)

const dialogVisible = ref(false)
const submitting = ref(false)
const submitError = ref('')

// Mirrors the schema in components/auth/LaboratorySelect.vue's inline
// add-laboratory dialog, so both entry points enforce the same rules.
const schema = yup.object({
  laboratory_name: yup.string().trim().required('Laboratory name is required.'),
  institutional_affiliation: yup
    .string()
    .trim()
    .required('Institutional affiliation is required.'),
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
  resetForm()
  submitError.value = ''
  dialogVisible.value = true
}

const submitNewLaboratory = handleSubmit(async (values) => {
  submitting.value = true
  submitError.value = ''
  try {
    const created = await createLaboratory({
      laboratory_name: values.laboratory_name.trim(),
      institutional_affiliation: values.institutional_affiliation.trim(),
      director_head_of_laboratory: values.director_head_of_laboratory.trim() || null,
      street_address: values.street_address.trim() || null,
      city: values.city.trim(),
      state: values.state.trim() || null,
      postal_code: values.postal_code.trim() || null,
      country: values.country.trim(),
      email: values.email.trim() || null,
    })
    laboratories.value.push(created)
    dialogVisible.value = false
  } catch {
    submitError.value = 'Could not create the laboratory. Please try again.'
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
        v-if="auth.isSuperuser"
        label="Add laboratory"
        icon="i-lucide-plus"
        @click="openDialog"
      />
    </div>

    <div v-if="requests.length || requestsLoading" class="flex flex-col gap-3">
      <h2 class="text-lg font-semibold text-surface-900 dark:text-surface-0">
        Pending approvals
      </h2>

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

      <div class="overflow-x-auto">
        <DataTable :value="requests" :loading="requestsLoading" data-key="id">
          <Column header="Laboratory">
            <template #body="{ data }">{{ data.laboratory.laboratory_name }}</template>
          </Column>
          <Column header="Affiliation">
            <template #body="{ data }">{{ data.laboratory.institutional_affiliation }}</template>
          </Column>
          <Column header="City">
            <template #body="{ data }">{{ data.laboratory.city }}</template>
          </Column>
          <Column header="Country">
            <template #body="{ data }">{{ data.laboratory.country }}</template>
          </Column>
          <Column header="Requester">
            <template #body="{ data }">
              {{ data.user.first_name }} {{ data.user.last_name }} ({{ data.user.email }})
            </template>
          </Column>
          <Column header="Requested">
            <template #body="{ data }">
              {{ new Date(data.created_at).toLocaleDateString() }}
            </template>
          </Column>
          <Column header="" style="width: 14rem">
            <template #body="{ data }">
              <div class="flex gap-1 justify-end">
                <UButton
                  label="Approve"
                  size="sm"
                  :loading="actingOnId === data.id"
                  @click="approve(data)"
                />
                <UButton
                  label="Deny"
                  color="error"
                  variant="ghost"
                  size="sm"
                  :loading="actingOnId === data.id"
                  @click="deny(data)"
                />
              </div>
            </template>
          </Column>
        </DataTable>
      </div>
    </div>

    <div class="overflow-x-auto">
      <div class="mb-3 flex items-center justify-between gap-3">
        <UButton type="button" icon="i-lucide-filter-x" variant="outline" size="sm" @click="clearFilters()">
          Clear Filters
        </UButton>
        <UInput
          v-model="filters['global'].value"
          type="text"
          icon="i-lucide-search"
          placeholder="Keyword Search"
        />
      </div>

      <DataTable
        v-model:filters="filters"
        :value="laboratories"
        :loading="loading"
        data-key="id"
        filterDisplay="menu"
        removableSort
        paginator
        :rows="10"
        :rowsPerPageOptions="[10, 25, 50]"
        :globalFilterFields="[
          'laboratory_name',
          'institutional_affiliation',
          'city',
          'country',
        ]"
      >
        <template #empty>No laboratories found.</template>

        <Column
          field="laboratory_name"
          header="Name"
          sortable
          :showFilterOperator="false"
          :showAddButton="false"
        >
          <template #filter="{ filterModel }">
            <UInput v-model="filterModel.value" type="text" placeholder="Search by name" />
          </template>
        </Column>

        <Column
          field="institutional_affiliation"
          header="Affiliation"
          sortable
          :showFilterOperator="false"
          :showAddButton="false"
        >
          <template #filter="{ filterModel }">
            <UInput v-model="filterModel.value" type="text" placeholder="Search by affiliation" />
          </template>
        </Column>

        <Column field="city" header="City" sortable :showFilterOperator="false" :showAddButton="false">
          <template #filter="{ filterModel }">
            <UInput v-model="filterModel.value" type="text" placeholder="Search by city" />
          </template>
        </Column>

        <Column
          field="country"
          header="Country"
          sortable
          :showFilterOperator="false"
          :showAddButton="false"
        >
          <template #filter="{ filterModel }">
            <UInput v-model="filterModel.value" type="text" placeholder="Search by country" />
          </template>
        </Column>

        <Column
          v-if="auth.isSuperuser"
          field="approval_status"
          header="Status"
          sortable
          :showFilterMatchModes="false"
          :showFilterOperator="false"
          :showAddButton="false"
        >
          <template #filter="{ filterModel }">
            <USelectMenu
              v-model="filterModel.value"
              :items="approvalStatusOptions"
              placeholder="Any status"
              clear
              class="w-full"
            />
          </template>
        </Column>
      </DataTable>
    </div>

    <UModal
      v-model:open="dialogVisible"
      title="Add laboratory"
      :ui="{ content: 'max-w-lg' }"
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
            <UAlert v-if="errors.city" color="error" variant="subtle" :description="errors.city" />
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
              :items="COUNTRIES"
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
          <UAlert v-if="errors.email" color="error" variant="subtle" :description="errors.email" />
        </div>
        <UAlert v-if="submitError" color="error" variant="outline" :description="submitError" />
      </div>
      </template>
      <template #footer>
        <UButton label="Cancel" variant="ghost" @click="dialogVisible = false" />
        <UButton label="Add laboratory" :loading="submitting" @click="submitNewLaboratory" />
      </template>
    </UModal>
  </div>
</template>
