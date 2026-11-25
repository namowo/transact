<script setup lang="ts">
import { onMounted, ref } from 'vue'
import DataTable from 'openvue/datatable'
import Column from 'openvue/column'
import type { DropdownMenuItem } from '@nuxt/ui'
import { useConfirm } from '@/composables/useConfirm'
import { FilterMatchMode } from '@openvue/core/api'
import LaboratorySelect from '@/components/auth/LaboratorySelect.vue'
import UserGroupsModal from '@/components/groups/UserGroupsModal.vue'
import UserGroupBadges from '@/components/groups/UserGroupBadges.vue'
import { deleteUser, listAllUsers, setLaboratory } from '@/api/users'
import { listLaboratories } from '@/api/laboratories'
import { listUserGroups } from '@/api/userGroups'
import type { Laboratory, User, UserGroup } from '@/api/types'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
const confirm = useConfirm()
const users = ref<User[]>([])
const laboratories = ref<Laboratory[]>([])
const groups = ref<UserGroup[]>([])
const loading = ref(false)
const loadError = ref('')
const actionError = ref('')

const labDialogVisible = ref(false)
const labDialogUser = ref<User | null>(null)
const labDialogValue = ref<string | null>(null)
const labDialogSaving = ref(false)

const groupsDialogVisible = ref(false)
const groupsDialogUser = ref<User | null>(null)

function initFilters() {
  return {
    global: { value: null, matchMode: FilterMatchMode.CONTAINS },
    first_name: { value: null, matchMode: FilterMatchMode.CONTAINS },
    last_name: { value: null, matchMode: FilterMatchMode.CONTAINS },
    email: { value: null, matchMode: FilterMatchMode.CONTAINS },
    'laboratory.laboratory_name': { value: null, matchMode: FilterMatchMode.EQUALS },
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
    const [loadedUsers, loadedLabs, loadedGroups] = await Promise.all([
      listAllUsers(),
      listLaboratories(),
      listUserGroups(),
    ])
    users.value = loadedUsers
    laboratories.value = loadedLabs
    groups.value = loadedGroups
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

function openGroupsDialog(user: User) {
  actionError.value = ''
  groupsDialogUser.value = user
  groupsDialogVisible.value = true
}

function rowMenuItems(user: User): DropdownMenuItem[] {
  const items: DropdownMenuItem[] = [
    {
      label: 'Groups',
      icon: 'i-lucide-shield',
      onSelect: () => openGroupsDialog(user),
    },
    {
      label: 'Edit lab',
      icon: 'i-lucide-building-2',
      onSelect: () => openLabDialog(user),
    },
  ]
  if (user.id !== auth.user?.id) {
    items.push({ type: 'separator' }, {
      label: 'Delete account',
      icon: 'i-lucide-trash-2',
      color: 'error',
      onSelect: () => confirmDeleteUser(user),
    })
  }
  return items
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
      rejectLabel: 'Cancel',
      acceptLabel: 'Remove',
      acceptColor: 'error',
      accept: perform,
    })
    return
  }

  confirm.require({
    message: `Change ${user.first_name} ${user.last_name}'s laboratory?`,
    header: 'Change laboratory',
    rejectLabel: 'Cancel',
    acceptLabel: 'Change',
    accept: perform,
  })
}

function confirmDeleteUser(user: User) {
  confirm.require({
    message: `Permanently delete ${user.first_name} ${user.last_name} (${user.email})? This cannot be undone.`,
    header: 'Delete account',
    rejectLabel: 'Cancel',
    acceptLabel: 'Delete',
    acceptColor: 'error',
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
    <div>
      <h1 class="text-2xl font-bold text-surface-900 dark:text-surface-0">Manage Users</h1>
      <p class="text-sm text-muted">
        What users may do comes from their groups. Define groups under Groups &amp; Permissions.
      </p>
    </div>

    <UAlert v-if="loadError" color="error" variant="outline" :description="loadError" />
    <UAlert v-if="actionError" color="error" variant="outline" :description="actionError" />

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
            <UInput v-model="filterModel.value" type="text" placeholder="Search by first name" />
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
            <UInput v-model="filterModel.value" type="text" placeholder="Search by last name" />
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
            <UInput v-model="filterModel.value" type="text" placeholder="Search by email" />
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
            {{ data.laboratory?.laboratory_name ?? '—' }}
          </template>
          <template #filter="{ filterModel }">
            <USelectMenu
              v-model="filterModel.value"
              :items="laboratories"
              label-key="laboratory_name"
              value-key="laboratory_name"
              placeholder="Any laboratory"
              clear
              class="w-full"
            />
          </template>
        </Column>

        <Column header="Groups" style="width: 14rem">
          <template #body="{ data }">
            <UserGroupBadges :user="data" />
          </template>
        </Column>

        <Column header="" style="width: 3rem">
          <template #body="{ data }">
            <div class="flex justify-end">
              <UDropdownMenu :items="rowMenuItems(data)" :content="{ align: 'end' }">
                <UButton
                  icon="i-lucide-ellipsis-vertical"
                  variant="ghost"
                  color="neutral"
                  square
                  aria-label="User actions"
                />
              </UDropdownMenu>
            </div>
          </template>
        </Column>
      </DataTable>
    </div>

    <UModal
      v-model:open="labDialogVisible"
      title="Edit lab"
      :ui="{ content: 'max-w-md', footer: 'justify-end' }"
    >
      <template #body>
      <div v-if="labDialogUser" class="flex flex-col gap-4">
        <p class="text-sm text-surface-600 dark:text-surface-300">
          {{ labDialogUser.first_name }} {{ labDialogUser.last_name }} ({{ labDialogUser.email }})
        </p>
        <LaboratorySelect v-model="labDialogValue" />
      </div>
      </template>
      <template #footer>
        <UButton label="Cancel" icon="i-lucide-x" variant="ghost" @click="labDialogVisible = false" />
        <UButton label="Save" icon="i-lucide-save" :loading="labDialogSaving" @click="saveLabDialog" />
      </template>
    </UModal>

    <UserGroupsModal
      v-model:open="groupsDialogVisible"
      :user="groupsDialogUser"
      :groups="groups"
      @saved="applyUpdate"
    />
  </div>
</template>
