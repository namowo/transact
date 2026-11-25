<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { deleteUserGroup, listPermissions, listUserGroups } from '@/api/userGroups'
import { listLaboratories } from '@/api/laboratories'
import { getErrorMessage } from '@/api/errors'
import type { Laboratory, PermissionInfo, UserGroup } from '@/api/types'
import { useConfirm } from '@/composables/useConfirm'
import GroupFormModal from './GroupFormModal.vue'
import GroupsOverview from './GroupsOverview.vue'

// With `laboratoryId`: that laboratory's own groups (editable) and the
// platform-wide groups for reference. Without: every group, for admins.
const props = defineProps<{ laboratoryId?: string | null }>()

const confirm = useConfirm()
const permissions = ref<PermissionInfo[]>([])
const groups = ref<UserGroup[]>([])
const laboratories = ref<Laboratory[]>([])
const loading = ref(false)
const loadError = ref('')
const actionError = ref('')

const formOpen = ref(false)
const editing = ref<UserGroup | null>(null)
// Laboratory of a new group; null creates a platform-wide one.
const newGroupLaboratoryId = ref<string | null>(null)

const platformGroups = computed(() => groups.value.filter((group) => !group.laboratory_id))
const laboratoryGroups = computed(() => groups.value.filter((group) => !!group.laboratory_id))
// The laboratory's own groups first on its page; platform groups first for admins.
const orderedGroups = computed(() =>
  props.laboratoryId
    ? [...laboratoryGroups.value, ...platformGroups.value]
    : [...platformGroups.value, ...laboratoryGroups.value],
)
// On a laboratory's page only its own groups can be changed.
const canEdit = (group: UserGroup) => !props.laboratoryId || !!group.laboratory_id

async function load() {
  loading.value = true
  loadError.value = ''
  try {
    const [loadedPermissions, loadedGroups, loadedLabs] = await Promise.all([
      listPermissions(),
      listUserGroups(props.laboratoryId),
      props.laboratoryId ? Promise.resolve([]) : listLaboratories(),
    ])
    permissions.value = loadedPermissions
    groups.value = loadedGroups
    laboratories.value = loadedLabs
  } catch {
    loadError.value = 'Could not load groups.'
  } finally {
    loading.value = false
  }
}

onMounted(load)

function openCreate() {
  editing.value = null
  newGroupLaboratoryId.value = props.laboratoryId ?? null
  formOpen.value = true
}

function openEdit(group: UserGroup) {
  editing.value = group
  formOpen.value = true
}

function onSaved(saved: UserGroup) {
  const exists = groups.value.some((group) => group.id === saved.id)
  groups.value = exists
    ? groups.value.map((group) => (group.id === saved.id ? saved : group))
    : [...groups.value, saved]
}

function confirmDelete(group: UserGroup) {
  confirm.require({
    header: 'Delete group',
    message: `Delete the group "${group.name}"? Its ${group.member_count} member(s) lose the permissions it grants.`,
    rejectLabel: 'Cancel',
    acceptLabel: 'Delete',
    acceptColor: 'error',
    accept: async () => {
      actionError.value = ''
      try {
        await deleteUserGroup(group.id)
        groups.value = groups.value.filter((g) => g.id !== group.id)
      } catch (err) {
        actionError.value = getErrorMessage(err, 'Could not delete the group.')
      }
    },
  })
}
</script>

<template>
  <div class="flex flex-col gap-8">
    <UAlert v-if="loadError" color="error" variant="outline" :description="loadError" />
    <UAlert v-if="actionError" color="error" variant="outline" :description="actionError" />

    <div class="flex items-center justify-between gap-3">
      <p class="text-sm text-muted">
        {{
          laboratoryId
            ? "Your laboratory's own groups and the platform-wide groups defined by the platform admins. Assign groups to members on the Users page."
            : 'Platform groups are available to members of every laboratory; laboratory groups were defined by a laboratory for its own members. "Own lab" permissions apply to the member\'s own laboratory.'
        }}
      </p>
      <UButton label="New group" icon="i-lucide-plus" class="shrink-0" @click="openCreate" />
    </div>

    <GroupsOverview
      :groups="orderedGroups"
      :laboratories="laboratories"
      :loading="loading"
      :editable="canEdit"
      @edit="openEdit"
      @delete="confirmDelete"
    />

    <GroupFormModal
      v-model:open="formOpen"
      :group="editing"
      :laboratory-id="newGroupLaboratoryId"
      :permissions="permissions"
      @saved="onSaved"
    />
  </div>
</template>
