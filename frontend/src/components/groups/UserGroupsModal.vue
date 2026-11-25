<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { setUserGroups } from '@/api/users'
import { getErrorMessage } from '@/api/errors'
import type { User, UserGroup } from '@/api/types'
import { useAuthStore } from '@/stores/auth'

// Picks the groups of `user` among `groups` (platform-wide groups and the
// groups of the user's laboratory).
const props = defineProps<{
  user: User | null
  groups: UserGroup[]
}>()
const open = defineModel<boolean>('open', { default: false })
const emit = defineEmits<{ saved: [user: User] }>()

const auth = useAuthStore()
const selected = ref<string[]>([])
const saving = ref(false)
const error = ref('')

// Mirrors the backend rule (app/crud/user_group.py `may_assign`): user
// managers assign anything; lab admins only groups whose permissions they
// hold themselves.
function mayAssign(group: UserGroup) {
  if (auth.can('users.manage')) return true
  return group.permissions.every((permission) => auth.can(permission))
}

const items = computed(() => {
  const relevant = props.groups.filter(
    (group) => !group.laboratory_id || group.laboratory_id === props.user?.laboratory_id,
  )
  return relevant.map((group) => ({
    label: group.name,
    description:
      (group.laboratory_id ? 'Laboratory group' : 'Platform group') +
      (group.description ? ` · ${group.description}` : ''),
    value: group.id,
    disabled: !mayAssign(group),
  }))
})

watch(
  open,
  (isOpen) => {
    if (!isOpen) return
    selected.value = props.user?.groups.map((group) => group.id) ?? []
    error.value = ''
  },
  { immediate: true },
)

async function save() {
  if (!props.user) return
  saving.value = true
  error.value = ''
  try {
    const updated = await setUserGroups(props.user.id, selected.value)
    emit('saved', updated)
    open.value = false
  } catch (err) {
    error.value = getErrorMessage(err, 'Could not update the groups. Please try again.')
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <UModal
    v-model:open="open"
    title="Groups"
    :description="user ? `${user.first_name} ${user.last_name} (${user.email})` : undefined"
    :ui="{ content: 'max-w-lg', footer: 'justify-end' }"
  >
    <template #body>
      <div class="flex flex-col gap-4">
        <UAlert v-if="error" color="error" variant="subtle" :description="error" />
        <UCheckboxGroup
          v-if="items.length"
          v-model="selected"
          :items="items"
          variant="card"
          :ui="{ fieldset: 'flex-col' }"
        />
        <UEmpty v-else icon="i-lucide-users" title="No groups yet" />
        <p v-if="items.some((item) => item.disabled)" class="text-xs text-muted">
          Groups granting permissions you don't have yourself can't be changed.
        </p>
      </div>
    </template>
    <template #footer>
      <UButton label="Save" icon="i-lucide-save" :loading="saving" @click="save" />
    </template>
  </UModal>
</template>
