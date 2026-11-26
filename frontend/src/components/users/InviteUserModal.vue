<script setup lang="ts">
import { computed, reactive, ref, watch } from 'vue'
import * as yup from 'yup'
import LaboratorySelect from '@/components/auth/LaboratorySelect.vue'
import { inviteUser } from '@/api/users'
import { getErrorMessage } from '@/api/errors'
import type { User, UserGroup } from '@/api/types'
import { useAuthStore } from '@/stores/auth'

// Invites someone by email. Admins pick any laboratory (or none); lab
// admins always invite to `laboratoryId`, their own.
const props = defineProps<{
  groups: UserGroup[]
  laboratoryId?: string | null
  chooseLaboratory?: boolean
}>()
const open = defineModel<boolean>('open', { default: false })
const emit = defineEmits<{ invited: [user: User] }>()

const auth = useAuthStore()
const saving = ref(false)
const error = ref('')

const state = reactive({
  email: '',
  first_name: '',
  last_name: '',
  laboratory_id: null as string | null,
  group_ids: [] as string[],
})

const schema = yup.object({
  email: yup.string().trim().required('Email is required.').email('Enter a valid email address.'),
  first_name: yup.string().trim().required('First name is required.'),
  last_name: yup.string().trim().required('Last name is required.'),
})

watch(open, (isOpen) => {
  if (!isOpen) return
  Object.assign(state, {
    email: '',
    first_name: '',
    last_name: '',
    laboratory_id: props.laboratoryId ?? null,
    group_ids: [],
  })
  error.value = ''
})

// Mirrors the backend rule (app/crud/user_group.py `may_assign`).
function mayAssign(group: UserGroup) {
  if (auth.can('users.manage')) return true
  return group.permissions.every((permission) => auth.can(permission))
}

const groupItems = computed(() =>
  props.groups
    .filter((group) => !group.laboratory_id || group.laboratory_id === state.laboratory_id)
    .map((group) => ({
      label: group.name,
      value: group.id,
      disabled: !mayAssign(group),
    })),
)

// Laboratory groups of another laboratory don't apply once it changes.
watch(
  () => state.laboratory_id,
  () => {
    const available = new Set(groupItems.value.map((item) => item.value))
    state.group_ids = state.group_ids.filter((id) => available.has(id))
  },
)

async function onSubmit() {
  saving.value = true
  error.value = ''
  try {
    const invited = await inviteUser({
      email: state.email.trim(),
      first_name: state.first_name.trim(),
      last_name: state.last_name.trim(),
      laboratory_id: state.laboratory_id,
      group_ids: state.group_ids,
    })
    emit('invited', invited)
    open.value = false
  } catch (err) {
    error.value = getErrorMessage(err, 'Could not invite this user. Please try again.')
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <UModal
    v-model:open="open"
    title="Invite user"
    description="They get an email with a link to choose a password and activate their account."
    :ui="{ content: 'max-w-lg' }"
  >
    <template #body>
      <UForm :schema="schema" :state="state" class="flex flex-col gap-4" @submit="onSubmit">
        <UAlert v-if="error" color="error" variant="subtle" :description="error" />
        <UFormField label="Email" name="email" required>
          <UInput v-model="state.email" type="email" autocomplete="off" class="w-full" />
        </UFormField>
        <div class="grid gap-4 sm:grid-cols-2">
          <UFormField label="First name" name="first_name" required>
            <UInput v-model="state.first_name" class="w-full" />
          </UFormField>
          <UFormField label="Last name" name="last_name" required>
            <UInput v-model="state.last_name" class="w-full" />
          </UFormField>
        </div>
        <UFormField
          v-if="chooseLaboratory"
          label="Laboratory"
          name="laboratory_id"
          hint="Optional"
        >
          <LaboratorySelect v-model="state.laboratory_id" />
        </UFormField>
        <UFormField
          v-if="groupItems.length"
          label="Groups"
          name="group_ids"
          hint="Optional"
          help="Leave empty for a regular member without extra permissions. You can change groups later."
        >
          <USelectMenu
            v-model="state.group_ids"
            :items="groupItems"
            value-key="value"
            multiple
            placeholder="No group (regular member)"
            :search-input="{ placeholder: 'Search groups…' }"
            class="w-full"
          />
        </UFormField>
        <div class="flex justify-end gap-2">
          <UButton label="Cancel" variant="ghost" color="neutral" @click="open = false" />
          <UButton type="submit" label="Send invitation" icon="i-lucide-send" :loading="saving" />
        </div>
      </UForm>
    </template>
  </UModal>
</template>
