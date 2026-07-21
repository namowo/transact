<script setup lang="ts">
import { onMounted, ref } from 'vue'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Checkbox from 'primevue/checkbox'
import Button from 'primevue/button'
import Message from 'primevue/message'
import IconField from 'primevue/iconfield'
import InputIcon from 'primevue/inputicon'
import InputText from 'primevue/inputtext'
import Select from 'primevue/select'
import ConfirmDialog from 'primevue/confirmdialog'
import { useConfirm } from 'primevue/useconfirm'
import { FilterMatchMode } from '@primevue/core/api'
import { grantLabAdmin, listLabUsers, removeFromLaboratory, revokeLabAdmin } from '@/api/users'
import {
  approveMembershipRequest,
  denyMembershipRequest,
  listPendingForMyLab,
} from '@/api/labMembershipRequests'
import type { LabMembershipRequest, User } from '@/api/types'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
const confirm = useConfirm()
const users = ref<User[]>([])
const loading = ref(false)
const loadError = ref('')
const actionError = ref('')

function canRemove(target: User) {
  if (target.id === auth.user?.id) return false
  if (target.can_manage_lab_users && !auth.isSuperuser) return false
  return true
}

const booleanOptions = [
  { label: 'Yes', value: true },
  { label: 'No', value: false },
]

function initFilters() {
  return {
    global: { value: null, matchMode: FilterMatchMode.CONTAINS },
    first_name: { value: null, matchMode: FilterMatchMode.CONTAINS },
    last_name: { value: null, matchMode: FilterMatchMode.CONTAINS },
    email: { value: null, matchMode: FilterMatchMode.CONTAINS },
    can_manage_lab_users: { value: null, matchMode: FilterMatchMode.EQUALS },
    can_quality_check: { value: null, matchMode: FilterMatchMode.EQUALS },
    is_superuser: { value: null, matchMode: FilterMatchMode.EQUALS },
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
const actingOnId = ref<number | null>(null)

async function load() {
  if (!auth.user?.laboratory_id) return
  loading.value = true
  loadError.value = ''
  try {
    users.value = await listLabUsers(auth.user.laboratory_id)
  } catch {
    loadError.value = 'Could not load laboratory users.'
  } finally {
    loading.value = false
  }
}

async function loadRequests() {
  requestsLoading.value = true
  requestsLoadError.value = ''
  try {
    requests.value = await listPendingForMyLab()
  } catch {
    requestsLoadError.value = 'Could not load membership requests.'
  } finally {
    requestsLoading.value = false
  }
}

onMounted(() => {
  load()
  loadRequests()
})

async function applyLabAdmin(user: User) {
  actionError.value = ''
  try {
    const updated = user.can_manage_lab_users
      ? await revokeLabAdmin(user.id)
      : await grantLabAdmin(user.id)
    users.value = users.value.map((u) => (u.id === updated.id ? updated : u))
  } catch {
    actionError.value = 'Could not update this user. Please try again.'
  }
}

function toggleLabAdmin(user: User) {
  const verb = user.can_manage_lab_users ? 'Revoke' : 'Grant'
  confirm.require({
    message: `${verb} lab admin access for ${user.first_name} ${user.last_name}?`,
    header: `${verb} lab admin`,
    icon: 'pi pi-exclamation-triangle',
    rejectProps: { label: 'Cancel', severity: 'secondary', text: true },
    acceptProps: { label: verb, severity: user.can_manage_lab_users ? 'danger' : 'primary' },
    accept: () => applyLabAdmin(user),
  })
}

async function removeUser(user: User) {
  actionError.value = ''
  try {
    await removeFromLaboratory(user.id)
    users.value = users.value.filter((u) => u.id !== user.id)
  } catch {
    actionError.value = 'Could not remove this user from the laboratory. Please try again.'
  }
}

function confirmRemoveUser(user: User) {
  confirm.require({
    message: `Remove ${user.first_name} ${user.last_name} from this laboratory?`,
    header: 'Remove user',
    icon: 'pi pi-exclamation-triangle',
    rejectProps: { label: 'Cancel', severity: 'secondary', text: true },
    acceptProps: { label: 'Remove', severity: 'danger' },
    accept: () => removeUser(user),
  })
}

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
</script>

<template>
  <div class="flex flex-col gap-6">
    <ConfirmDialog />

    <h1 class="text-2xl font-bold text-surface-900 dark:text-surface-0">Manage Lab Users</h1>

    <div v-if="requests.length || requestsLoading" class="flex flex-col gap-3">
      <h2 class="text-lg font-semibold text-surface-900 dark:text-surface-0">
        Pending requests
      </h2>

      <Message v-if="requestsLoadError" severity="error" size="small">
        {{ requestsLoadError }}
      </Message>
      <Message v-if="requestsActionError" severity="error" size="small">
        {{ requestsActionError }}
      </Message>

      <div class="overflow-x-auto">
        <DataTable :value="requests" :loading="requestsLoading" data-key="id">
          <Column header="Requester">
            <template #body="{ data }">
              {{ data.user.first_name }} {{ data.user.last_name }}
            </template>
          </Column>
          <Column header="Email">
            <template #body="{ data }">{{ data.user.email }}</template>
          </Column>
          <Column header="Requested">
            <template #body="{ data }">
              {{ new Date(data.created_at).toLocaleDateString() }}
            </template>
          </Column>
          <Column header="" style="width: 14rem">
            <template #body="{ data }">
              <div class="flex gap-1 justify-end">
                <Button
                  label="Approve"
                  size="small"
                  :loading="actingOnId === data.id"
                  @click="approve(data)"
                />
                <Button
                  label="Deny"
                  severity="danger"
                  text
                  size="small"
                  :loading="actingOnId === data.id"
                  @click="deny(data)"
                />
              </div>
            </template>
          </Column>
        </DataTable>
      </div>
    </div>

    <div class="flex flex-col gap-3">
      <h2 class="text-lg font-semibold text-surface-900 dark:text-surface-0">Users</h2>

      <Message v-if="loadError" severity="error" size="small">{{ loadError }}</Message>
      <Message v-if="actionError" severity="error" size="small">{{ actionError }}</Message>

      <div class="overflow-x-auto">
        <div class="mb-3 flex items-center justify-between gap-3">
          <Button type="button" variant="outlined" size="small" @click="clearFilters()">
            <i class="pi pi-filter-slash" />
            Clear Filters
          </Button>
          <IconField iconPosition="left">
            <InputIcon class="pi pi-search" />
            <InputText v-model="filters['global'].value" type="text" placeholder="Keyword Search" />
          </IconField>
        </div>

        <DataTable
          v-model:filters="filters"
          :value="users"
          :loading="loading"
          data-key="id"
          filterDisplay="menu"
          removableSort
          paginator
          :rows="10"
          :rowsPerPageOptions="[10, 25, 50]"
          :globalFilterFields="['first_name', 'last_name', 'email']"
        >
          <template #empty>No users found.</template>

          <Column
            field="first_name"
            header="First name"
            sortable
            :showFilterOperator="false"
            :showAddButton="false"
          >
            <template #filter="{ filterModel }">
              <InputText v-model="filterModel.value" type="text" placeholder="Search by first name" />
            </template>
          </Column>

          <Column
            field="last_name"
            header="Last name"
            sortable
            :showFilterOperator="false"
            :showAddButton="false"
          >
            <template #filter="{ filterModel }">
              <InputText v-model="filterModel.value" type="text" placeholder="Search by last name" />
            </template>
          </Column>

          <Column
            field="email"
            header="Email"
            sortable
            :showFilterOperator="false"
            :showAddButton="false"
          >
            <template #filter="{ filterModel }">
              <InputText v-model="filterModel.value" type="text" placeholder="Search by email" />
            </template>
          </Column>

          <Column
            field="can_manage_lab_users"
            header="Lab admin"
            dataType="boolean"
            sortable
            :showFilterMatchModes="false"
            :showFilterOperator="false"
            :showAddButton="false"
          >
            <template #body="{ data }">
              <Checkbox
                :model-value="data.can_manage_lab_users"
                :binary="true"
                @update:model-value="toggleLabAdmin(data)"
              />
            </template>
            <template #filter="{ filterModel }">
              <Select
                v-model="filterModel.value"
                :options="booleanOptions"
                optionLabel="label"
                optionValue="value"
                placeholder="Any"
                showClear
                class="w-full"
              />
            </template>
          </Column>

          <Column
            field="can_quality_check"
            header="Quality check"
            dataType="boolean"
            sortable
            :showFilterMatchModes="false"
            :showFilterOperator="false"
            :showAddButton="false"
          >
            <template #body="{ data }">
              <Checkbox :model-value="data.can_quality_check" :binary="true" :disabled="true" />
            </template>
            <template #filter="{ filterModel }">
              <Select
                v-model="filterModel.value"
                :options="booleanOptions"
                optionLabel="label"
                optionValue="value"
                placeholder="Any"
                showClear
                class="w-full"
              />
            </template>
          </Column>

          <Column
            field="is_superuser"
            header="Superuser"
            dataType="boolean"
            sortable
            :showFilterMatchModes="false"
            :showFilterOperator="false"
            :showAddButton="false"
          >
            <template #body="{ data }">
              <Checkbox :model-value="data.is_superuser" :binary="true" :disabled="true" />
            </template>
            <template #filter="{ filterModel }">
              <Select
                v-model="filterModel.value"
                :options="booleanOptions"
                optionLabel="label"
                optionValue="value"
                placeholder="Any"
                showClear
                class="w-full"
              />
            </template>
          </Column>

          <Column header="" style="width: 6rem">
            <template #body="{ data }">
              <Button
                v-if="canRemove(data)"
                icon="pi pi-user-minus"
                text
                rounded
                severity="danger"
                aria-label="Remove from laboratory"
                @click="confirmRemoveUser(data)"
              />
            </template>
          </Column>
        </DataTable>
      </div>
    </div>
  </div>
</template>
