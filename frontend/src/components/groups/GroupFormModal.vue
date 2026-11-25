<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { createUserGroup, updateUserGroup } from '@/api/userGroups'
import { getErrorMessage } from '@/api/errors'
import type { TableColumn } from '@nuxt/ui'
import type { Permission, PermissionInfo, UserGroup } from '@/api/types'
import { useAuthStore } from '@/stores/auth'

// Creates or edits a group. Without `group` a new one is created - for the
// laboratory `laboratoryId`, or platform-wide when that is null.
const props = defineProps<{
  group?: UserGroup | null
  laboratoryId?: string | null
  permissions: PermissionInfo[]
}>()
const open = defineModel<boolean>('open', { default: false })
const emit = defineEmits<{ saved: [group: UserGroup] }>()

const auth = useAuthStore()

const name = ref('')
const description = ref('')
const selected = ref<Permission[]>([])
const saving = ref(false)
const error = ref('')

const isEdit = computed(() => !!props.group)
const isBuiltIn = computed(() => !!props.group?.system_key)
const groupLaboratoryId = computed(() =>
  props.group ? props.group.laboratory_id : (props.laboratoryId ?? null),
)
// Laboratory groups may only hold laboratory permissions.
const available = computed(() =>
  groupLaboratoryId.value
    ? props.permissions.filter((permission) => permission.scope === 'laboratory')
    : props.permissions,
)
// The Administrator group can't give these up (backend enforces it too).
const locked = computed<Permission[]>(() =>
  props.group?.system_key === 'administrator' ? ['users.manage', 'groups.manage'] : [],
)

// Platform permissions first, then the laboratory ones.
const rows = computed(() =>
  [...available.value].sort((a, b) =>
    a.scope === b.scope ? 0 : a.scope === 'global' ? -1 : 1,
  ),
)

const columns: TableColumn<PermissionInfo>[] = [
  { id: 'permission', header: 'Permission' },
  { id: 'scope', header: 'Applies to' },
  { id: 'granted', header: 'Granted' },
]

// Why a permission can't be toggled, if it can't.
function lockReason(key: Permission): string | null {
  if (locked.value.includes(key)) return 'The Administrator group always keeps this permission.'
  // Nobody can grant or revoke what they don't hold themselves.
  if (!auth.can(key)) return "You can't grant or revoke a permission you don't have yourself."
  return null
}

function toggle(key: Permission, granted: boolean) {
  selected.value = granted
    ? [...new Set([...selected.value, key])]
    : selected.value.filter((k) => k !== key)
}

const grantedCount = computed(
  () => rows.value.filter((permission) => selected.value.includes(permission.key)).length,
)

watch(
  open,
  (isOpen) => {
    if (!isOpen) return
    name.value = props.group?.name ?? ''
    description.value = props.group?.description ?? ''
    selected.value = [...(props.group?.permissions ?? [])]
    error.value = ''
  },
  { immediate: true },
)

async function save() {
  if (!name.value.trim()) {
    error.value = 'Please enter a name.'
    return
  }
  saving.value = true
  error.value = ''
  try {
    const payload = {
      ...(isBuiltIn.value ? {} : { name: name.value.trim() }),
      description: description.value.trim() || null,
      permissions: selected.value,
    }
    const saved = props.group
      ? await updateUserGroup(props.group.id, payload)
      : await createUserGroup({
          name: name.value.trim(),
          description: payload.description,
          permissions: payload.permissions,
          laboratory_id: groupLaboratoryId.value,
        })
    emit('saved', saved)
    open.value = false
  } catch (err) {
    error.value = getErrorMessage(err, 'Could not save the group. Please try again.')
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <UModal
    v-model:open="open"
    :title="isEdit ? `Edit group` : 'New group'"
    :description="
      groupLaboratoryId
        ? 'A group of your laboratory. It can only grant permissions within the laboratory.'
        : 'A platform-wide group. It can be given to members of any laboratory.'
    "
    :ui="{ content: 'max-w-4xl', footer: 'justify-end' }"
  >
    <template #body>
      <form class="flex flex-col gap-4" @submit.prevent="save">
        <UAlert v-if="error" color="error" variant="subtle" :description="error" />

        <UFormField label="Name" required :hint="isBuiltIn ? 'Built-in groups keep their name' : undefined">
          <UInput v-model="name" class="w-full" :disabled="isBuiltIn" autofocus />
        </UFormField>

        <UFormField label="Description" hint="Optional">
          <UTextarea v-model="description" :rows="2" class="w-full" />
        </UFormField>

        <div class="flex flex-col gap-2">
          <div class="flex items-baseline justify-between gap-3">
            <p class="text-sm font-medium text-highlighted">Permissions</p>
            <span class="text-xs text-muted">{{ grantedCount }} of {{ rows.length }} granted</span>
          </div>
          <UTable
            :data="rows"
            :columns="columns"
            :get-row-id="(permission: PermissionInfo) => permission.key"
            sticky
            class="max-h-[50vh] rounded-md border border-default"
            :ui="{ th: 'whitespace-nowrap', td: 'py-2 text-sm' }"
          >
            <template #permission-cell="{ row }">
              <div class="flex min-w-56 flex-col gap-0.5 whitespace-normal">
                <span class="font-medium text-highlighted">{{ row.original.label }}</span>
                <span class="text-xs text-muted">{{ row.original.description }}</span>
              </div>
            </template>
            <template #scope-cell="{ row }">
              <UBadge
                :label="row.original.scope === 'global' ? 'Platform' : 'Own lab'"
                :color="row.original.scope === 'global' ? 'primary' : 'neutral'"
                variant="subtle"
                size="sm"
              />
            </template>
            <template #granted-cell="{ row }">
              <UTooltip :text="lockReason(row.original.key) ?? undefined" :disabled="!lockReason(row.original.key)">
                <USwitch
                  :model-value="selected.includes(row.original.key)"
                  :disabled="!!lockReason(row.original.key)"
                  :aria-label="`Grant ${row.original.label}`"
                  @update:model-value="(value: boolean) => toggle(row.original.key, value)"
                />
              </UTooltip>
            </template>
          </UTable>
        </div>

      </form>
    </template>
    <template #footer>
      <UButton label="Save" icon="i-lucide-save" :loading="saving" @click="save" />
    </template>
  </UModal>
</template>
