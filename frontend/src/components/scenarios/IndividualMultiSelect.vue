<script setup lang="ts">
import { computed, ref } from 'vue'
import DataTable from 'openvue/datatable'
import Column from 'openvue/column'
import { useIndividualOptions, groupIndividuals } from './individualOptions'
import type { IndividualGroup } from './individualOptions'
import type { Individual } from '@/api/types'

// Lets the user pick several individuals at once, e.g. to create one contact
// per individual against a shared item surface. Individuals sharing the same
// traits are grouped (as on the Individuals tab) so a whole group can be
// selected in one click, or expanded to pick just a few of its members.
// Individuals themselves are managed on the Individuals tab, not created
// from here.
const props = defineProps<{ studyId: string }>()
const individualIds = defineModel<string[]>({ default: () => [] })

const { individuals, loading, individualName } = useIndividualOptions(props.studyId)

const groups = computed(() => groupIndividuals(individuals.value))

const selected = computed(() => new Set(individualIds.value))

function groupSelectionState(group: IndividualGroup): boolean | 'indeterminate' {
  const selectedCount = group.members.filter((member) => selected.value.has(member.id)).length
  if (selectedCount === 0) return false
  if (selectedCount === group.members.length) return true
  return 'indeterminate'
}

function toggleGroup(group: IndividualGroup) {
  const allSelected = groupSelectionState(group) === true
  const memberIds = new Set(group.members.map((member) => member.id))
  const next = new Set(selected.value)
  if (allSelected) {
    for (const id of memberIds) next.delete(id)
  } else {
    for (const id of memberIds) next.add(id)
  }
  individualIds.value = [...next]
}

function toggleMember(individual: Individual) {
  const next = new Set(selected.value)
  if (next.has(individual.id)) next.delete(individual.id)
  else next.add(individual.id)
  individualIds.value = [...next]
}

const expandedRows = ref<Record<string, boolean>>({})
</script>

<template>
  <div class="flex flex-col gap-1">
    <div class="border border-default rounded-md overflow-hidden">
      <DataTable
        v-model:expanded-rows="expandedRows"
        :value="groups"
        data-key="key"
        :loading="loading"
        scrollable
        scroll-height="16rem"
      >
        <template #empty>No individuals yet.</template>
        <Column expander style="width: 2.5rem" />
        <Column header="" style="width: 2.5rem">
          <template #body="{ data }">
            <UCheckbox
              :model-value="groupSelectionState(data)"
              @update:model-value="toggleGroup(data)"
            />
          </template>
        </Column>
        <Column header="Count" style="width: 4.5rem">
          <template #body="{ data }">
            <UBadge v-if="data.members.length > 1" color="neutral" variant="subtle">
              {{ data.members.length }}x
            </UBadge>
          </template>
        </Column>
        <Column header="Sex">
          <template #body="{ data }">
            <UBadge v-if="data.sexName" color="neutral" variant="outline">{{ data.sexName }}</UBadge>
            <span v-else>—</span>
          </template>
        </Column>
        <Column header="Age">
          <template #body="{ data }">{{ data.age ?? '—' }}</template>
        </Column>
        <Column header="DNA shedding propensity">
          <template #body="{ data }">
            <UBadge v-if="data.dnaSheddingPropensityCategoryName" color="neutral" variant="outline">
              {{ data.dnaSheddingPropensityCategoryName }}
            </UBadge>
            <span v-else>—</span>
          </template>
        </Column>
        <Column header="Skin disease">
          <template #body="{ data }">
            <UBadge v-if="data.skinDiseaseCategoryName" color="neutral" variant="outline">
              {{ data.skinDiseaseCategoryName }}
            </UBadge>
            <span v-else>—</span>
          </template>
        </Column>
        <Column header="Selected" style="width: 6rem">
          <template #body="{ data }">
            {{ data.members.filter((m: Individual) => selected.has(m.id)).length }} / {{ data.members.length }}
          </template>
        </Column>

        <template #expansion="{ data: group }">
          <DataTable :value="group.members" data-key="id">
            <Column header="" style="width: 2.5rem">
              <template #body="{ data }">
                <UCheckbox
                  :model-value="selected.has(data.id)"
                  @update:model-value="toggleMember(data)"
                />
              </template>
            </Column>
            <Column header="Individual">
              <template #body="{ data }">{{ individualName(data) }}</template>
            </Column>
            <Column header="Sex">
              <template #body="{ data }">
                <UBadge v-if="data.sex?.name" color="neutral" variant="outline">{{ data.sex.name }}</UBadge>
                <span v-else>—</span>
              </template>
            </Column>
            <Column header="Age">
              <template #body="{ data }">{{ data.age ?? '—' }}</template>
            </Column>
            <Column header="DNA shedding propensity">
              <template #body="{ data }">
                <UBadge v-if="data.dna_shedding_propensity_category?.name" color="neutral" variant="outline">
                  {{ data.dna_shedding_propensity_category.name }}
                </UBadge>
                <span v-else>—</span>
              </template>
            </Column>
            <Column header="Skin disease">
              <template #body="{ data }">
                <UBadge v-if="data.skin_disease_category?.name" color="neutral" variant="outline">
                  {{ data.skin_disease_category.name }}
                </UBadge>
                <span v-else>—</span>
              </template>
            </Column>
          </DataTable>
        </template>
      </DataTable>
    </div>
    <p v-if="!loading && !groups.length" class="text-sm text-muted">
      No individuals yet. Add some on the Individuals tab first.
    </p>
  </div>
</template>
