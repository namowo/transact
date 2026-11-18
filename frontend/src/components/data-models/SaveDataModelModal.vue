<script setup lang="ts">
import { ref, watch } from 'vue'

export interface SaveDetails {
  name: string
  description: string | null
  is_public: boolean
}

const props = defineProps<{
  title: string
  initial: SaveDetails
  // Guests save to this browser, so there's nothing to make public.
  canPublish: boolean
  saving: boolean
}>()

const open = defineModel<boolean>('open', { required: true })
const emit = defineEmits<{ save: [details: SaveDetails] }>()

const name = ref('')
const description = ref('')
const isPublic = ref(false)

watch(open, (value) => {
  if (!value) return
  name.value = props.initial.name
  description.value = props.initial.description ?? ''
  isPublic.value = props.initial.is_public
})

function submit() {
  if (!name.value.trim()) return
  emit('save', {
    name: name.value.trim(),
    description: description.value.trim() || null,
    is_public: props.canPublish && isPublic.value,
  })
}
</script>

<template>
  <UModal v-model:open="open" :title="title">
    <template #body>
      <form id="save-data-model" class="flex flex-col gap-4" @submit.prevent="submit">
        <UFormField label="Name" required>
          <UInput v-model="name" class="w-full" autofocus maxlength="200" />
        </UFormField>
        <UFormField label="Description" hint="Optional">
          <UTextarea
            v-model="description"
            class="w-full"
            :rows="3"
            placeholder="What this data is for, how it was filtered…"
          />
        </UFormField>
        <USwitch
          v-if="canPublish"
          v-model="isPublic"
          label="Share with the community"
          description="Public models are listed for everyone. Each viewer only downloads data from the studies available to them."
        />
        <UAlert
          v-else
          color="info"
          variant="subtle"
          icon="i-lucide-info"
          description="Without an account, data models are saved in this browser only. Sign in to keep them in your account and share them."
        />
      </form>
    </template>
    <template #footer>
      <div class="flex w-full justify-end gap-2">
        <UButton color="neutral" variant="ghost" label="Cancel" @click="open = false" />
        <UButton
          type="submit"
          form="save-data-model"
          label="Save"
          icon="i-lucide-save"
          :loading="saving"
          :disabled="!name.trim()"
        />
      </div>
    </template>
  </UModal>
</template>
