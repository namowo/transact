<script setup lang="ts">
import { computed, ref } from 'vue'
import type { TableColumn } from '@nuxt/ui'
import { expandColumn } from '@/composables/tableColumns'
import { useIndividualOptions, groupIndividuals } from './individualOptions'
import type { IndividualGroup } from './individualOptions'
import type { Individual } from '@/api/types'
import { usePagination } from '@/composables/useTableView'
import TablePagination from '@/components/ui/TablePagination.vue'

// Lets the user pick several individuals at once, e.g. to create one contact
// per individual against a shared item surface. Individuals sharing the same
// traits are grouped (as on the Individuals tab) so a whole group can be
// selected in one click, or expanded to pick just a few of its members.
// Individuals themselves are managed on the Individuals tab, not created
// from here. With a `scenarioId`, only individuals assigned to that scenario
// are offered.
const props = defineProps<{ studyId: string; scenarioId?: string | null }>()
const individualIds = defineModel<string[]>({ default: () => [] })

const { individuals, loading, individualName } = useIndividualOptions(props.studyId)

const scopedIndividuals = computed(() =>
  props.scenarioId
    ? individuals.value.filter((individual) => individual.scenario_ids?.includes(props.scenarioId!))
    : individuals.value,
)

const groups = computed(() => groupIndividuals(scopedIndividuals.value))

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

const groupPages = usePagination(groups)

const groupColumns: TableColumn<IndividualGroup>[] = [
  expandColumn(),
  { id: 'select', header: '', meta: { class: { td: 'w-10' } } },
  { id: 'count', header: 'Count', meta: { class: { td: 'w-18' } } },
  { id: 'sex', header: 'Sex' },
  { id: 'age', accessorKey: 'age', header: 'Age' },
  { id: 'dna', accessorKey: 'dna', header: 'DNA shedding propensity' },
  { id: 'skin', accessorKey: 'skin', header: 'Skin disease' },
  { id: 'selected', accessorKey: 'selected', header: 'Selected', meta: { class: { td: 'w-24' } } },
]

const memberColumns: TableColumn<Individual>[] = [
  { id: 'select', header: '', meta: { class: { td: 'w-10' } } },
  { id: 'name', accessorKey: 'name', header: 'Individual' },
  { id: 'sex', header: 'Sex' },
  { id: 'age', accessorKey: 'age', header: 'Age' },
  { id: 'dna', accessorKey: 'dna', header: 'DNA shedding propensity' },
  { id: 'skin', accessorKey: 'skin', header: 'Skin disease' },
]
</script>

<template>
  <div class="flex flex-col gap-1">
    <div class="border border-default rounded-md overflow-hidden">
      <UTable
        v-model:expanded="expandedRows"
        :data="groupPages.rows"
        :columns="groupColumns"
        :get-row-id="(group: IndividualGroup) => group.key"
        :loading="loading"
        empty="No individuals yet."
        sticky
        class="max-h-64"
      >
        <template #select-cell="{ row: { original: data } }">
          <UCheckbox
            :model-value="groupSelectionState(data)"
            @update:model-value="toggleGroup(data)"
          />
        </template>
        <template #count-cell="{ row: { original: data } }">
          <UBadge v-if="data.members.length > 1" color="neutral" variant="subtle">
            {{ data.members.length }}x
          </UBadge>
        </template>
        <template #sex-cell="{ row: { original: data } }">
          <UBadge v-if="data.sexName" color="neutral" variant="outline">{{ data.sexName }}</UBadge>
          <span v-else>—</span>
        </template>
        <template #age-cell="{ row: { original: data } }">{{ data.age ?? '—' }}</template>
        <template #dna-cell="{ row: { original: data } }">
          <UBadge v-if="data.dnaSheddingPropensityCategoryName" color="neutral" variant="outline">
            {{ data.dnaSheddingPropensityCategoryName }}
          </UBadge>
          <span v-else>—</span>
        </template>
        <template #skin-cell="{ row: { original: data } }">
          <UBadge v-if="data.skinDiseaseCategoryName" color="neutral" variant="outline">
            {{ data.skinDiseaseCategoryName }}
          </UBadge>
          <span v-else>—</span>
        </template>
        <template #selected-cell="{ row: { original: data } }">
          {{ data.members.filter((m: Individual) => selected.has(m.id)).length }} /
          {{ data.members.length }}
        </template>

        <template #expanded="{ row: { original: group } }">
          <UTable
            :data="group.members"
            :columns="memberColumns"
            :get-row-id="(m: Individual) => m.id"
          >
            <template #select-cell="{ row: { original: data } }">
              <UCheckbox
                :model-value="selected.has(data.id)"
                @update:model-value="toggleMember(data)"
              />
            </template>
            <template #name-cell="{ row: { original: data } }">{{ individualName(data) }}</template>
            <template #sex-cell="{ row: { original: data } }">
              <UBadge v-if="data.sex?.name" color="neutral" variant="outline">{{
                data.sex.name
              }}</UBadge>
              <span v-else>—</span>
            </template>
            <template #age-cell="{ row: { original: data } }">{{ data.age ?? '—' }}</template>
            <template #dna-cell="{ row: { original: data } }">
              <UBadge
                v-if="data.dna_shedding_propensity_category?.name"
                color="neutral"
                variant="outline"
              >
                {{ data.dna_shedding_propensity_category.name }}
              </UBadge>
              <span v-else>—</span>
            </template>
            <template #skin-cell="{ row: { original: data } }">
              <UBadge v-if="data.skin_disease_category?.name" color="neutral" variant="outline">
                {{ data.skin_disease_category.name }}
              </UBadge>
              <span v-else>—</span>
            </template>
          </UTable>
        </template>
      </UTable>
    </div>
    <TablePagination
      v-model:page="groupPages.page"
      v-model:page-size="groupPages.pageSize"
      :total="groupPages.total"
    />
    <p v-if="!loading && !groups.length" class="text-sm text-muted">
      {{ scenarioId ? 'No individuals in this scenario yet.' : 'No individuals yet.' }}
      Add some on the Individuals tab first.
    </p>
  </div>
</template>
