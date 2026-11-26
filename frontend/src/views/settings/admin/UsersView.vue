<script setup lang="ts">
import { onMounted, ref } from 'vue'
import type { DropdownMenuItem, TableColumn } from '@nuxt/ui'
import { useToast } from '@nuxt/ui/composables'
import { useConfirm } from '@/composables/useConfirm'
import LaboratorySelect from '@/components/auth/LaboratorySelect.vue'
import UserGroupsModal from '@/components/groups/UserGroupsModal.vue'
import UserGroupBadges from '@/components/groups/UserGroupBadges.vue'
import {
  deleteUser,
  listAllUsers,
  resendInvitation,
  resetTwoFactor,
  setLaboratory,
  unlockUser,
} from '@/api/users'
import { getErrorMessage } from '@/api/errors'
import InviteUserModal from '@/components/users/InviteUserModal.vue'
import { listLaboratories } from '@/api/laboratories'
import { listUserGroups } from '@/api/userGroups'
import type { Laboratory, User, UserGroup } from '@/api/types'
import { useAuthStore } from '@/stores/auth'
import { manualSorting, useTableView } from '@/composables/useTableView'
import { sortHeader } from '@/composables/tableColumns'
import TableFilterDrawer from '@/components/ui/TableFilterDrawer.vue'
import TablePagination from '@/components/ui/TablePagination.vue'
import TableLoadingSkeleton from '@/components/ui/TableLoadingSkeleton.vue'

const auth = useAuthStore()
const confirm = useConfirm()
const toast = useToast()
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

const inviteDialogVisible = ref(false)

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
  if (user.is_locked) {
    items.push({
      label: 'Unlock account',
      icon: 'i-lucide-lock-open',
      onSelect: () => unlock(user),
    })
  }
  if (!user.invitation_pending && user.id !== auth.user?.id) {
    items.push({
      label: 'Reset two-factor',
      icon: 'i-lucide-shield-off',
      onSelect: () => confirmResetTwoFactor(user),
    })
  }
  if (user.invitation_pending && auth.config.invitations_enabled) {
    items.push({
      label: 'Resend invitation',
      icon: 'i-lucide-send',
      onSelect: () => resendInvitationTo(user),
    })
  }
  if (user.invitation_pending) {
    items.push(
      { type: 'separator' },
      {
        label: 'Withdraw invitation',
        icon: 'i-lucide-user-x',
        color: 'error',
        onSelect: () => confirmWithdrawInvitation(user),
      },
    )
  } else if (user.id !== auth.user?.id) {
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

async function resendInvitationTo(user: User) {
  actionError.value = ''
  try {
    applyUpdate(await resendInvitation(user.id))
    toast.add({
      color: 'success',
      title: 'Invitation sent',
      description: `We emailed a new link to ${user.email}.`,
    })
  } catch (err) {
    actionError.value = getErrorMessage(err, 'Could not resend the invitation. Please try again.')
  }
}

async function unlock(user: User) {
  actionError.value = ''
  try {
    applyUpdate(await unlockUser(user.id))
    toast.add({
      color: 'success',
      title: 'Account unlocked',
      description: `${user.email} can sign in again.`,
    })
  } catch (err) {
    actionError.value = getErrorMessage(err, 'Could not unlock this account.')
  }
}

function confirmResetTwoFactor(user: User) {
  confirm.require({
    message: `Remove the authenticator app and all passkeys of ${user.first_name} ${user.last_name} (${user.email})? Use this when they lost them. They sign in with their password alone${auth.config.two_factor_required ? ' and then have to set up a new second factor' : ''}.`,
    header: 'Reset two-factor authentication',
    rejectLabel: 'Cancel',
    acceptLabel: 'Reset',
    acceptColor: 'error',
    accept: () => resetTwoFactorConfirmed(user),
  })
}

async function resetTwoFactorConfirmed(user: User) {
  actionError.value = ''
  try {
    applyUpdate(await resetTwoFactor(user.id))
    toast.add({
      color: 'success',
      title: 'Two-factor authentication reset',
      description: `${user.email} can now set up a new second factor.`,
    })
  } catch (err) {
    actionError.value = getErrorMessage(err, 'Could not reset two-factor authentication.')
  }
}

function confirmWithdrawInvitation(user: User) {
  confirm.require({
    message: `Withdraw the invitation for ${user.first_name} ${user.last_name} (${user.email})? Their invitation link stops working.`,
    header: 'Withdraw invitation',
    rejectLabel: 'Cancel',
    acceptLabel: 'Withdraw',
    acceptColor: 'error',
    accept: () => withdrawInvitation(user),
  })
}

async function withdrawInvitation(user: User) {
  actionError.value = ''
  try {
    await deleteUser(user.id)
    users.value = users.value.filter((u) => u.id !== user.id)
  } catch (err) {
    actionError.value = getErrorMessage(err, 'Could not withdraw the invitation. Please try again.')
  }
}

function onInvited(user: User) {
  users.value = [...users.value, user]
  toast.add({
    color: 'success',
    title: 'Invitation sent',
    description: `${user.first_name} ${user.last_name} gets an email to activate their account.`,
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
    <div class="flex flex-wrap items-start justify-between gap-3">
      <div>
        <h1 class="text-2xl font-bold text-surface-900 dark:text-surface-0">Manage Users</h1>
        <p class="text-sm text-muted">
          What users may do comes from their groups. Define groups under Groups &amp; Permissions.
        </p>
      </div>
      <UButton
        v-if="auth.config.invitations_enabled"
        label="Invite user"
        icon="i-lucide-user-plus"
        @click="inviteDialogVisible = true"
      />
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
        <template #loading>
          <TableLoadingSkeleton />
        </template>
        <template #email-cell="{ row }">
          <div class="flex items-center gap-2">
            <span>{{ row.original.email }}</span>
            <UBadge
              v-if="row.original.invitation_pending"
              label="Invited"
              color="warning"
              variant="subtle"
              size="sm"
            />
            <UBadge
              v-if="row.original.is_locked"
              label="Locked"
              icon="i-lucide-lock"
              color="error"
              variant="subtle"
              size="sm"
            />
          </div>
        </template>
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

    <InviteUserModal
      v-model:open="inviteDialogVisible"
      :groups="groups"
      choose-laboratory
      @invited="onInvited"
    />

    <UserGroupsModal
      v-model:open="groupsDialogVisible"
      :user="groupsDialogUser"
      :groups="groups"
      @saved="applyUpdate"
    />
  </div>
</template>
