<script setup lang="ts">
import { onMounted, ref } from 'vue'
import DataTable from 'openvue/datatable'
import Column from 'openvue/column'
import type { DropdownMenuItem } from '@nuxt/ui'
import { useConfirm } from '@/composables/useConfirm'
import { FilterMatchMode } from '@openvue/core/api'
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

const accessDialogVisible = ref(false)
const accessDialogUser = ref<User | null>(null)

function canRemove(target: User) {
  if (target.id === auth.user?.id) return false
  if (target.can_manage_lab_users && !auth.isSuperuser) return false
  return true
}

function initFilters() {
  return {
    global: { value: null, matchMode: FilterMatchMode.CONTAINS },
    first_name: { value: null, matchMode: FilterMatchMode.CONTAINS },
    last_name: { value: null, matchMode: FilterMatchMode.CONTAINS },
    email: { value: null, matchMode: FilterMatchMode.CONTAINS },
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
    if (accessDialogUser.value?.id === updated.id) accessDialogUser.value = updated
  } catch {
    actionError.value = 'Could not update this user. Please try again.'
  }
}

function toggleLabAdmin(user: User) {
  const verb = user.can_manage_lab_users ? 'Revoke' : 'Grant'
  confirm.require({
    message: `${verb} lab admin access for ${user.first_name} ${user.last_name}?`,
    header: `${verb} lab admin`,
    rejectLabel: 'Cancel',
    acceptLabel: verb,
    acceptColor: user.can_manage_lab_users ? 'error' : 'primary',
    accept: () => applyLabAdmin(user),
  })
}

function openAccessDialog(user: User) {
  actionError.value = ''
  accessDialogUser.value = user
  accessDialogVisible.value = true
}

function rowMenuItems(user: User): DropdownMenuItem[] {
  const items: DropdownMenuItem[] = [
    {
      label: 'Manage access',
      icon: 'i-lucide-shield',
      onSelect: () => openAccessDialog(user),
    },
  ]
  if (canRemove(user)) {
    items.push({ type: 'separator' }, {
      label: 'Remove from laboratory',
      icon: 'i-lucide-user-minus',
      color: 'error',
      onSelect: () => confirmRemoveUser(user),
    })
  }
  return items
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
    <h1 class="text-2xl font-bold text-surface-900 dark:text-surface-0">Manage Lab Users</h1>

    <div v-if="requests.length || requestsLoading" class="flex flex-col gap-3">
      <h2 class="text-lg font-semibold text-surface-900 dark:text-surface-0">
        Pending requests
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
                <UButton
                  label="Approve"
                  icon="i-lucide-check"
                  size="sm"
                  :loading="actingOnId === data.id"
                  @click="approve(data)"
                />
                <UButton
                  label="Deny"
                  icon="i-lucide-x"
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

    <div class="flex flex-col gap-3">
      <h2 class="text-lg font-semibold text-surface-900 dark:text-surface-0">Users</h2>

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

          <Column header="Access" style="width: 12rem">
            <template #body="{ data }">
              <div class="flex flex-wrap gap-1">
                <UBadge v-if="data.is_superuser" label="Superuser" color="primary" variant="subtle" size="sm" />
                <UBadge v-if="data.can_manage_lab_users" label="Lab admin" color="neutral" variant="subtle" size="sm" />
                <UBadge v-if="data.can_quality_check" label="Quality check" color="neutral" variant="subtle" size="sm" />
              </div>
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
    </div>

    <UModal
      v-model:open="accessDialogVisible"
      title="Manage access"
      :ui="{ content: 'max-w-md', footer: 'justify-end' }"
    >
      <template #body>
        <div v-if="accessDialogUser" class="flex flex-col gap-4">
          <p class="text-sm text-surface-600 dark:text-surface-300">
            {{ accessDialogUser.first_name }} {{ accessDialogUser.last_name }} ({{ accessDialogUser.email }})
          </p>

          <div class="flex items-center justify-between gap-3">
            <div>
              <p class="text-sm font-medium text-surface-900 dark:text-surface-0">Lab admin</p>
              <p class="text-xs text-surface-500 dark:text-surface-400">Manage users within this laboratory</p>
            </div>
            <USwitch
              :model-value="accessDialogUser.can_manage_lab_users"
              @update:model-value="toggleLabAdmin(accessDialogUser)"
            />
          </div>

          <div class="flex items-center justify-between gap-3">
            <div>
              <p class="text-sm font-medium text-surface-900 dark:text-surface-0">Quality check</p>
              <p class="text-xs text-surface-500 dark:text-surface-400">Managed by a system administrator</p>
            </div>
            <USwitch :model-value="accessDialogUser.can_quality_check" disabled />
          </div>

          <div class="flex items-center justify-between gap-3">
            <div>
              <p class="text-sm font-medium text-surface-900 dark:text-surface-0">Superuser</p>
              <p class="text-xs text-surface-500 dark:text-surface-400">Managed by a system administrator</p>
            </div>
            <USwitch :model-value="accessDialogUser.is_superuser" disabled />
          </div>
        </div>
      </template>
      <template #footer>
        <UButton label="Close" icon="i-lucide-x" variant="ghost" @click="accessDialogVisible = false" />
      </template>
    </UModal>
  </div>
</template>
