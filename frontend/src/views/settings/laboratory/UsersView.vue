<script setup lang="ts">
import { onMounted, ref } from 'vue'
import type { DropdownMenuItem, TableColumn } from '@nuxt/ui'
import { useToast } from '@nuxt/ui/composables'
import { useConfirm } from '@/composables/useConfirm'
import { deleteUser, listLabUsers, removeFromLaboratory, resendInvitation } from '@/api/users'
import { getErrorMessage } from '@/api/errors'
import InviteUserModal from '@/components/users/InviteUserModal.vue'
import { listUserGroups } from '@/api/userGroups'
import UserGroupsModal from '@/components/groups/UserGroupsModal.vue'
import UserGroupBadges from '@/components/groups/UserGroupBadges.vue'
import {
  approveMembershipRequest,
  denyMembershipRequest,
  listPendingForMyLab,
} from '@/api/labMembershipRequests'
import type { LabMembershipRequest, User, UserGroup } from '@/api/types'
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
const loading = ref(false)
const loadError = ref('')
const actionError = ref('')

const groups = ref<UserGroup[]>([])
const inviteDialogVisible = ref(false)

const groupsDialogVisible = ref(false)
const groupsDialogUser = ref<User | null>(null)

// Only user managers may remove a fellow lab admin (backend enforces it too).
function canRemove(target: User) {
  if (target.id === auth.user?.id) return false
  if (target.permissions.includes('lab.manage_members') && !auth.can('users.manage')) return false
  return true
}

const view = useTableView(users, {
  searchFields: ['first_name', 'last_name', 'email'],
  filters: {
    first_name: { field: 'first_name' },
    last_name: { field: 'last_name' },
    email: { field: 'email' },
  },
})

const columns: TableColumn<User>[] = [
  { id: 'first_name', accessorKey: 'first_name', header: sortHeader('First name') },
  { id: 'last_name', accessorKey: 'last_name', header: sortHeader('Last name') },
  { id: 'email', accessorKey: 'email', header: sortHeader('Email') },
  { id: 'groups', header: 'Groups', meta: { class: { td: 'w-56 whitespace-normal' } } },
  { id: 'actions', header: '', meta: { class: { td: 'w-12' } } },
]

const requestColumns: TableColumn<LabMembershipRequest>[] = [
  { id: 'requester', header: 'Requester' },
  { id: 'email', accessorKey: 'email', header: 'Email' },
  { id: 'created_at', accessorKey: 'created_at', header: 'Requested' },
  { id: 'actions', header: '', meta: { class: { td: 'w-56' } } },
]

const requests = ref<LabMembershipRequest[]>([])
const requestsLoading = ref(false)
const requestsLoadError = ref('')
const requestsActionError = ref('')
const actingOnId = ref<string | null>(null)

async function load() {
  if (!auth.user?.laboratory_id) return
  loading.value = true
  loadError.value = ''
  try {
    const [loadedUsers, loadedGroups] = await Promise.all([
      listLabUsers(auth.user.laboratory_id),
      listUserGroups(auth.user.laboratory_id),
    ])
    users.value = loadedUsers
    groups.value = loadedGroups
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
  ]
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
  } else if (canRemove(user)) {
    items.push(
      { type: 'separator' },
      {
        label: 'Remove from laboratory',
        icon: 'i-lucide-user-minus',
        color: 'error',
        onSelect: () => confirmRemoveUser(user),
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
    rejectLabel: 'Cancel',
    acceptLabel: 'Remove',
    acceptColor: 'error',
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
    <div class="flex flex-wrap items-start justify-between gap-3">
      <h1 class="text-2xl font-bold text-surface-900 dark:text-surface-0">Manage Lab Users</h1>
      <UButton
        v-if="auth.config.invitations_enabled"
        label="Invite user"
        icon="i-lucide-user-plus"
        @click="inviteDialogVisible = true"
      />
    </div>

    <div v-if="requests.length || requestsLoading" class="flex flex-col gap-3">
      <h2 class="text-lg font-semibold text-surface-900 dark:text-surface-0">Pending requests</h2>

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
        <template #loading>
          <TableLoadingSkeleton />
        </template>
        <template #requester-cell="{ row }">
          {{ row.original.user.first_name }} {{ row.original.user.last_name }}
        </template>
        <template #email-cell="{ row }">{{ row.original.user.email }}</template>
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
      <h2 class="text-lg font-semibold text-surface-900 dark:text-surface-0">Users</h2>

      <UAlert v-if="loadError" color="error" variant="outline" :description="loadError" />
      <UAlert v-if="actionError" color="error" variant="outline" :description="actionError" />

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
          </div>
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

    <InviteUserModal
      v-model:open="inviteDialogVisible"
      :groups="groups"
      :laboratory-id="auth.user?.laboratory_id"
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
