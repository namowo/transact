<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import InputNumber from 'primevue/inputnumber'
import Textarea from 'primevue/textarea'
import ToggleSwitch from 'primevue/toggleswitch'
import Button from 'primevue/button'
import Message from 'primevue/message'
import ProgressSpinner from 'primevue/progressspinner'
import Tabs from 'primevue/tabs'
import TabList from 'primevue/tablist'
import Tab from 'primevue/tab'
import TabPanels from 'primevue/tabpanels'
import TabPanel from 'primevue/tabpanel'
import CategorySelect from '@/components/scenarios/CategorySelect.vue'
import ContactCard from '@/components/scenarios/ContactCard.vue'
import DurationInput from '@/components/scenarios/DurationInput.vue'
import {
  scenarioCategoryApi,
  disturbanceCategoryApi,
  geographicLocationCategoryApi,
} from '@/api/categories'
import { getScenario, createScenario, updateScenario } from '@/api/scenarios'
import {
  emptyPersistenceDraft,
  persistenceDraftFromPersistence,
  savePersistenceDraft,
} from '@/components/scenarios/persistenceDraft'
import type { PersistenceDraft } from '@/components/scenarios/persistenceDraft'
import {
  contactDraftFromContact,
  emptyContactDraft,
  saveContactDraft,
} from '@/components/scenarios/contactDraft'
import type { ContactDraft } from '@/components/scenarios/contactDraft'

const props = defineProps<{ studyId: string; id?: string }>()

const router = useRouter()

const studyId = computed(() => Number(props.studyId))
const editingId = computed(() => (props.id ? Number(props.id) : null))

const loading = ref(false)
const loadError = ref('')
const submitting = ref(false)
const submitError = ref('')

const realistic = ref(true)
const scenarioCategoryId = ref<number | null>(null)
const persistence = ref<PersistenceDraft>(emptyPersistenceDraft())
const contacts = ref<ContactDraft[]>([emptyContactDraft()])
const collapsedContacts = ref<boolean[]>([false])

onMounted(async () => {
  if (editingId.value === null) return

  loading.value = true
  try {
    const scenario = await getScenario(editingId.value)
    realistic.value = !!scenario.realistic
    scenarioCategoryId.value = scenario.scenario_category_id ?? null
    persistence.value = persistenceDraftFromPersistence(scenario.persistence)
    contacts.value = scenario.contacts.length
      ? scenario.contacts.map(contactDraftFromContact)
      : [emptyContactDraft()]
    // Existing contacts start collapsed so the form doesn't open on a wall
    // of fields; a single freshly-added contact starts expanded.
    collapsedContacts.value = contacts.value.map(() => scenario.contacts.length > 0)
  } catch {
    loadError.value = 'Could not load this scenario.'
  } finally {
    loading.value = false
  }
})

function addContact() {
  collapsedContacts.value = collapsedContacts.value.map(() => true)
  contacts.value.push(emptyContactDraft())
  collapsedContacts.value.push(false)
}

function removeContact(index: number) {
  contacts.value.splice(index, 1)
  collapsedContacts.value.splice(index, 1)
}

async function onSubmit() {
  submitting.value = true
  submitError.value = ''
  try {
    const persistenceId = await savePersistenceDraft(persistence.value)

    const payload = {
      realistic: realistic.value,
      scenario_category_id: scenarioCategoryId.value,
      study_id: studyId.value,
      persistence_id: persistenceId,
    }

    const scenario = editingId.value
      ? await updateScenario(editingId.value, payload)
      : await createScenario(payload)

    for (const contact of contacts.value) {
      await saveContactDraft(contact, scenario.id)
    }

    router.push({ name: 'scenarios', params: { studyId: studyId.value } })
  } catch {
    submitError.value = 'Could not save the scenario. Please try again.'
  } finally {
    submitting.value = false
  }
}

function onCancel() {
  router.push({ name: 'scenarios', params: { studyId: studyId.value } })
}
</script>

<template>
  <div class="flex flex-col gap-6 max-w-3xl">
    <h1 class="text-2xl font-bold text-surface-900 dark:text-surface-0">
      {{ editingId === null ? 'Add scenario' : 'Edit scenario' }}
    </h1>

    <div v-if="loading" class="flex justify-center py-12">
      <ProgressSpinner style="width: 3rem; height: 3rem" />
    </div>

    <Message v-else-if="loadError" severity="error" size="small">{{ loadError }}</Message>

    <form v-else class="flex flex-col gap-4" @submit.prevent="onSubmit">
      <Tabs value="details">
        <TabList>
          <Tab value="details">Details</Tab>
          <Tab value="persistence">Persistence</Tab>
          <Tab value="contacts">Contacts ({{ contacts.length }})</Tab>
        </TabList>
        <TabPanels>
          <TabPanel value="details">
            <div class="flex flex-col gap-4">
              <CategorySelect
                v-model="scenarioCategoryId"
                label="Scenario category"
                :api="scenarioCategoryApi"
              />

              <div class="flex items-center gap-2">
                <ToggleSwitch v-model="realistic" input-id="realistic" />
                <label for="realistic" class="text-sm">Realistic scenario</label>
              </div>
            </div>
          </TabPanel>

          <TabPanel value="persistence">
            <div class="flex flex-col gap-4">
              <div class="flex flex-col gap-2">
                <label class="font-medium text-sm">Interval of persistence (Optional)</label>
                <DurationInput v-model="persistence.intervalOfPersistence" />
              </div>
              <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div class="flex flex-col gap-2">
                  <label class="font-medium text-sm">Temperature (°C)</label>
                  <InputNumber v-model="persistence.temperature" fluid />
                </div>
                <div class="flex flex-col gap-2">
                  <label class="font-medium text-sm">Humidity (%)</label>
                  <InputNumber v-model="persistence.humidity" fluid />
                </div>
              </div>
              <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div class="flex flex-col gap-2">
                  <label class="font-medium text-sm">UV irradiation (Optional)</label>
                  <InputNumber v-model="persistence.uvIrradiation" fluid />
                </div>
                <div class="flex flex-col gap-2">
                  <label class="font-medium text-sm"
                    >Duration of disturbance (seconds, Optional)</label
                  >
                  <InputNumber v-model="persistence.durationOfDisturbance" fluid />
                </div>
              </div>
              <div class="flex flex-wrap gap-6">
                <div class="flex items-center gap-2">
                  <ToggleSwitch v-model="persistence.indoors" input-id="indoors" />
                  <label for="indoors" class="text-sm">Indoors</label>
                </div>
                <div class="flex items-center gap-2">
                  <ToggleSwitch v-model="persistence.changeOverTime" input-id="change-over-time" />
                  <label for="change-over-time" class="text-sm">Changes over time</label>
                </div>
              </div>
              <CategorySelect
                v-model="persistence.disturbanceCategoryId"
                label="Disturbance"
                :api="disturbanceCategoryApi"
              />
              <CategorySelect
                v-model="persistence.geographicLocationCategoryId"
                label="Geographic location"
                :api="geographicLocationCategoryApi"
              />
              <div class="flex flex-col gap-2">
                <label class="font-medium text-sm">Description of disturbance (Optional)</label>
                <Textarea v-model="persistence.descriptionOfDisturbance" rows="2" fluid />
              </div>
            </div>
          </TabPanel>

          <TabPanel value="contacts">
            <div class="flex flex-col gap-4">
              <ContactCard
                v-for="(contact, index) in contacts"
                :key="index"
                :model-value="contact"
                :collapsed="collapsedContacts[index]"
                :index="index"
                :removable="contacts.length > 1"
                @update:model-value="contacts[index] = $event"
                @update:collapsed="collapsedContacts[index] = $event"
                @remove="removeContact(index)"
              />

              <Button
                label="Add contact"
                icon="pi pi-plus"
                outlined
                class="self-start"
                @click="addContact"
              />
            </div>
          </TabPanel>
        </TabPanels>
      </Tabs>

      <Message v-if="submitError" severity="error" size="small">{{ submitError }}</Message>

      <div class="flex gap-2 mt-2">
        <Button
          type="submit"
          :label="editingId === null ? 'Add scenario' : 'Save changes'"
          :loading="submitting"
        />
        <Button label="Cancel" text type="button" @click="onCancel" />
      </div>
    </form>
  </div>
</template>
