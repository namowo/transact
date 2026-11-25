<script setup lang="ts">
import { onMounted, ref } from 'vue'
import type { DropdownMenuItem, TableColumn } from '@nuxt/ui'
import { useConfirm } from '@/composables/useConfirm'
import LaboratorySelect from '@/components/auth/LaboratorySelect.vue'
import UserGroupsModal from '@/components/groups/UserGroupsModal.vue'
import UserGroupBadges from '@/components/groups/UserGroupBadges.vue'
import { deleteUser, listAllUsers, setLaboratory } from '@/api/users'
import { listLaboratories } from '@/api/laboratories'
import { listUserGroups } from '@/api/userGroups'
import type { Laboratory, User, UserGroup } from '@/api/types'
import { useAuthStore } from '@/stores/auth'
import { manualSorting, useTableView } from '@/composables/useTableView'
import { sortHeader } from '@/composables/tableColumns'
import TableFilterDrawer from '@/components/ui/TableFilterDrawer.vue'
import TablePagination from '@/components/ui/TablePagination.vue'

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

const view = useTableView(users, {
  searchFields: ['first_name', 'last_name', 'email', 'laboratory.laboratory_name'],
  filters: {
    first_name: { field: 'first_name' },
    last_name: { field: 'last_name' },
    email: { field: 'email' },
    laboratory: { field: 'laboratory.laboratory_name', mode: 'equals' },
  },
  sortAccessors: { laboratory: 'laboratory.laboratory_name' },
  pageSize: 10,
})

const columns: TableColumn<User>[] = [
  { id: 'first_name', accessorKey: 'first_name', header: sortHeader('First name') },
  { id: 'last_name', accessorKey: 'last_name', header: sortHeader('Last name') },
  { id: 'email', accessorKey: 'email', header: sortHeader('Email') },
  { id: 'laboratory', header: sortHeader('Laboratory') },
  { id: 'groups', header: 'Groups', meta: { class: { td: 'w-56 whitespace-normal' } } },
  { id: 'actions', header: '', meta: { class: { td: 'w-12' } } },
]

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
    items.push(
      { type: 'separator' },
      {
        label: 'Delete account',
        icon: 'i-lucide-trash-2',
        color: 'error',
        onSelect: () => confirmDeleteUser(user),
      },
    )
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

    <div class="flex flex-col gap-3">
      <div class="flex flex-wrap items-center justify-between gap-3">
        <UInput
          v-model="view.search"
          icon="i-lucide-search"
          placeholder="Keyword Search"
          class="w-full max-w-sm"
        />
        <TableFilterDrawer :active-count="view.activeFilterCount" @reset="view.resetFilters()">
          <UFormField label="First name">
            <UInput
              v-model="view.filters.first_name"
              placeholder="Search by first name"
              class="w-full"
            />
          </UFormField>
          <UFormField label="Last name">
            <UInput
              v-model="view.filters.last_name"
              placeholder="Search by last name"
              class="w-full"
            />
          </UFormField>
          <UFormField label="Email">
            <UInput v-model="view.filters.email" placeholder="Search by email" class="w-full" />
          </UFormField>
          <UFormField label="Laboratory">
            <USelectMenu
              v-model="view.filters.laboratory"
              :items="laboratories"
              label-key="laboratory_name"
              value-key="laboratory_name"
              placeholder="Any laboratory"
              clear
              class="w-full"
            />
          </UFormField>
        </TableFilterDrawer>
      </div>

      <UTable
        v-model:sorting="view.sorting"
        :sorting-options="manualSorting"
        :data="view.rows"
        :columns="columns"
        :loading="loading"
        :get-row-id="(user: User) => user.id"
        empty="No users found."
      >
        <template #laboratory-cell="{ row }">
          {{ row.original.laboratory?.laboratory_name ?? '—' }}
        </template>
        <template #groups-cell="{ row }">
          <UserGroupBadges :user="row.original" />
        </template>
        <template #actions-cell="{ row }">
          <div class="flex justify-end">
            <UDropdownMenu :items="rowMenuItems(row.original)" :content="{ align: 'end' }">
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
      </UTable>
      <TablePagination
        v-model:page="view.page"
        v-model:page-size="view.pageSize"
        :total="view.total"
      />
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
        <UButton
          label="Cancel"
          icon="i-lucide-x"
          variant="ghost"
          @click="labDialogVisible = false"
        />
        <UButton
          label="Save"
          icon="i-lucide-save"
          :loading="labDialogSaving"
          @click="saveLabDialog"
        />
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
