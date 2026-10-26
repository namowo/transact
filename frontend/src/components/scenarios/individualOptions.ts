import { computed, onMounted, ref } from 'vue'
import { listIndividuals } from '@/api/individuals'
import type { Individual } from '@/api/types'

// Individuals have no name of their own, so label them by creation order
// (not their database id, which is an implementation detail) plus whatever
// traits are known, e.g. "Individual 3 (m, 34y)".
export function useIndividualOptions(studyId: string) {
  const individuals = ref<Individual[]>([])
  const loading = ref(false)

  function individualPosition(individual: Individual): number {
    return individuals.value.findIndex((candidate) => candidate.id === individual.id)
  }

  function individualName(individual: Individual): string {
    return `Individual ${individualPosition(individual) + 1}`
  }

  function describeIndividual(individual: Individual): string {
    const parts = [
      individual.sex?.name,
      individual.age != null ? `${individual.age}y` : null,
    ].filter(Boolean)
    const name = individualName(individual)
    return parts.length ? `${name} (${parts.join(', ')})` : name
  }

  async function load() {
    loading.value = true
    try {
      individuals.value = await listIndividuals(studyId)
    } finally {
      loading.value = false
    }
  }

  onMounted(load)

  const individualOptions = computed(() =>
    individuals.value.map((individual) => ({ ...individual, label: describeIndividual(individual) })),
  )

  return { individuals, individualOptions, loading, describeIndividual, individualName, load }
}

export interface IndividualGroup {
  key: string
  sexName: string | null
  age: number | null
  dnaSheddingPropensityCategoryName: string | null
  skinDiseaseCategoryName: string | null
  members: Individual[]
}

// Individuals sharing the same sex/age/shedding-propensity/skin-disease are
// grouped into one row, mirroring how the Individuals tab displays them, so
// "all individuals that look alike" can be selected as a unit.
function groupKey(individual: Individual): string {
  return [
    individual.sex_id,
    individual.age,
    individual.dna_shedding_propensity_category_id,
    individual.skin_disease_category_id,
    individual.determination_of_shedding_propensity_category_id,
  ]
    .map((value) => value ?? '')
    .join('::')
}

export function groupIndividuals(individuals: Individual[]): IndividualGroup[] {
  const groups = new Map<string, IndividualGroup>()
  for (const individual of individuals) {
    const key = groupKey(individual)
    const existing = groups.get(key)
    if (existing) {
      existing.members.push(individual)
    } else {
      groups.set(key, {
        key,
        sexName: individual.sex?.name ?? null,
        age: individual.age ?? null,
        dnaSheddingPropensityCategoryName: individual.dna_shedding_propensity_category?.name ?? null,
        skinDiseaseCategoryName: individual.skin_disease_category?.name ?? null,
        members: [individual],
      })
    }
  }
  return [...groups.values()]
}
