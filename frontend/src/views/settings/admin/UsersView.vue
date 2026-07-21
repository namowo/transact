<script setup lang="ts">
import { onMounted, ref } from 'vue'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Checkbox from 'primevue/checkbox'
import Message from 'primevue/message'
import Button from 'primevue/button'
import Dialog from 'primevue/dialog'
import IconField from 'primevue/iconfield'
import InputIcon from 'primevue/inputicon'
import InputText from 'primevue/inputtext'
import Select from 'primevue/select'
import ConfirmDialog from 'primevue/confirmdialog'
import { useConfirm } from 'primevue/useconfirm'
import { FilterMatchMode } from '@primevue/core/api'
import LaboratorySelect from '@/components/auth/LaboratorySelect.vue'
import {
  deleteUser,
  grantLabAdmin,
  grantQualityCheck,
  grantSuperuser,
  listAllUsers,
  revokeLabAdmin,
  revokeQualityCheck,
  revokeSuperuser,
  setLaboratory,
} from '@/api/users'
import { listLaboratories } from '@/api/laboratories'
import type { Laboratory, User } from '@/api/types'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
const confirm = useConfirm()
const users = ref<User[]>([])
const laboratories = ref<Laboratory[]>([])
const loading = ref(false)
const loadError = ref('')
const actionError = ref('')

const labDialogVisible = ref(false)
const labDialogUser = ref<User | null>(null)
const labDialogValue = ref<number | null>(null)
const labDialogSaving = ref(false)

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
    'laboratory.laboratory_name': { value: null, matchMode: FilterMatchMode.EQUALS },
    is_superuser: { value: null, matchMode: FilterMatchMode.EQUALS },
    can_quality_check: { value: null, matchMode: FilterMatchMode.EQUALS },
    can_manage_lab_users: { value: null, matchMode: FilterMatchMode.EQUALS },
  }
}

const filters = ref(initFilters())

function clearFilters() {
  filters.value = initFilters()
}

async function load() {
  loading.value = true
  loadError.value = ''
  try {
    const [loadedUsers, loadedLabs] = await Promise.all([listAllUsers(), listLaboratories()])
    users.value = loadedUsers
    laboratories.value = loadedLabs
  } catch {
    loadError.value = 'Could not load users.'
  } finally {
    loading.value = false
  }
}

onMounted(load)

function applyUpdate(updated: User) {
  users.value = users.value.map((u) => (u.id === updated.id ? updated : u))
}

async function applySuperuser(user: User) {
  actionError.value = ''
  try {
    const updated = user.is_superuser
      ? await revokeSuperuser(user.id)
      : await grantSuperuser(user.id)
    applyUpdate(updated)
  } catch {
    actionError.value = 'Could not update this user. Please try again.'
  }
}

function toggleSuperuser(user: User) {
  const verb = user.is_superuser ? 'Revoke' : 'Grant'
  confirm.require({
    message: `${verb} superuser access for ${user.first_name} ${user.last_name}?`,
    header: `${verb} superuser`,
    icon: 'pi pi-exclamation-triangle',
    rejectProps: { label: 'Cancel', severity: 'secondary', text: true },
    acceptProps: { label: verb, severity: user.is_superuser ? 'danger' : 'primary' },
    accept: () => applySuperuser(user),
  })
}

async function applyQualityCheck(user: User) {
  actionError.value = ''
  try {
    const updated = user.can_quality_check
      ? await revokeQualityCheck(user.id)
      : await grantQualityCheck(user.id)
    applyUpdate(updated)
  } catch {
    actionError.value = 'Could not update this user. Please try again.'
  }
}

function toggleQualityCheck(user: User) {
  const verb = user.can_quality_check ? 'Revoke' : 'Grant'
  confirm.require({
    message: `${verb} quality check access for ${user.first_name} ${user.last_name}?`,
    header: `${verb} quality check`,
    icon: 'pi pi-exclamation-triangle',
    rejectProps: { label: 'Cancel', severity: 'secondary', text: true },
    acceptProps: { label: verb, severity: user.can_quality_check ? 'danger' : 'primary' },
    accept: () => applyQualityCheck(user),
  })
}

async function applyLabAdmin(user: User) {
  actionError.value = ''
  try {
    const updated = user.can_manage_lab_users
      ? await revokeLabAdmin(user.id)
      : await grantLabAdmin(user.id)
    applyUpdate(updated)
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

function openLabDialog(user: User) {
  actionError.value = ''
  labDialogUser.value = user
  labDialogValue.value = user.laboratory_id
  labDialogVisible.value = true
}

async function saveLabDialog() {
  const user = labDialogUser.value
  if (!user) return
  const nextLaboratoryId = labDialogValue.value
  const isReset = nextLaboratoryId === null

  const perform = async () => {
    labDialogSaving.value = true
    actionError.value = ''
    try {
      const updated = await setLaboratory(user.id, nextLaboratoryId)
      applyUpdate(updated)
      labDialogVisible.value = false
    } catch {
      actionError.value = 'Could not update this user. Please try again.'
    } finally {
      labDialogSaving.value = false
    }
  }

  if (isReset && user.laboratory_id !== null) {
    confirm.require({
      message: `Remove ${user.first_name} ${user.last_name} from ${user.laboratory?.laboratory_name ?? 'their laboratory'}?`,
      header: 'Reset laboratory',
      icon: 'pi pi-exclamation-triangle',
      rejectProps: { label: 'Cancel', severity: 'secondary', text: true },
      acceptProps: { label: 'Remove', severity: 'danger' },
      accept: perform,
    })
    return
  }

  confirm.require({
    message: `Change ${user.first_name} ${user.last_name}'s laboratory?`,
    header: 'Change laboratory',
    icon: 'pi pi-exclamation-triangle',
    rejectProps: { label: 'Cancel', severity: 'secondary', text: true },
    acceptProps: { label: 'Change', severity: 'primary' },
    accept: perform,
  })
}

function confirmDeleteUser(user: User) {
  confirm.require({
    message: `Permanently delete ${user.first_name} ${user.last_name} (${user.email})? This cannot be undone.`,
    header: 'Delete account',
    icon: 'pi pi-exclamation-triangle',
    rejectProps: { label: 'Cancel', severity: 'secondary', text: true },
    acceptProps: { label: 'Delete', severity: 'danger' },
    accept: () => deleteUserConfirmed(user),
  })
}

async function deleteUserConfirmed(user: User) {
  actionError.value = ''
  try {
    await deleteUser(user.id)
    users.value = users.value.filter((u) => u.id !== user.id)
  } catch {
    actionError.value = 'Could not delete this user. Please try again.'
  }
}
</script>

<template>
  <div class="flex flex-col gap-6">
    <ConfirmDialog />

    <h1 class="text-2xl font-bold text-surface-900 dark:text-surface-0">Manage Users</h1>

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
        :globalFilterFields="[
          'first_name',
          'last_name',
          'email',
          'laboratory.laboratory_name',
        ]"
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
          header="Laboratory"
          filterField="laboratory.laboratory_name"
          sortField="laboratory.laboratory_name"
          sortable
          :showFilterMatchModes="false"
          :showFilterOperator="false"
          :showAddButton="false"
        >
          <template #body="{ data }">
            <Button
              :label="data.laboratory?.laboratory_name ?? 'Assign laboratory'"
              text
              size="small"
              @click="openLabDialog(data)"
            />
          </template>
          <template #filter="{ filterModel }">
            <Select
              v-model="filterModel.value"
              :options="laboratories"
              optionLabel="laboratory_name"
              optionValue="laboratory_name"
              placeholder="Any laboratory"
              filter
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
            <Checkbox
              :model-value="data.is_superuser"
              :binary="true"
              :disabled="data.id === auth.user?.id"
              @update:model-value="toggleSuperuser(data)"
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
            <Checkbox
              :model-value="data.can_quality_check"
              :binary="true"
              @update:model-value="toggleQualityCheck(data)"
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

        <Column header="" style="width: 6rem">
          <template #body="{ data }">
            <div class="flex gap-1 justify-end">
              <Button
                v-if="data.id !== auth.user?.id"
                icon="pi pi-trash"
                text
                rounded
                severity="danger"
                aria-label="Delete account"
                @click="confirmDeleteUser(data)"
              />
            </div>
          </template>
        </Column>
      </DataTable>
    </div>

    <Dialog
      v-model:visible="labDialogVisible"
      header="Change laboratory"
      modal
      :style="{ width: '28rem' }"
    >
      <div v-if="labDialogUser" class="flex flex-col gap-4">
        <p class="text-sm text-surface-600 dark:text-surface-300">
          {{ labDialogUser.first_name }} {{ labDialogUser.last_name }} ({{ labDialogUser.email }})
        </p>
        <LaboratorySelect v-model="labDialogValue" />
      </div>
      <template #footer>
        <Button label="Cancel" text @click="labDialogVisible = false" />
        <Button label="Save" :loading="labDialogSaving" @click="saveLabDialog" />
      </template>
    </Dialog>
  </div>
</template>
