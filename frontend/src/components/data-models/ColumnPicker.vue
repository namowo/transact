<script setup lang="ts">
import { computed, ref } from 'vue'
import type { CatalogField } from '@/api/types'
import { fieldLabel } from './fieldLabel'

// The fields of the joined tables.
const props = defineProps<{ fields: CatalogField[] }>()
const columns = defineModel<string[]>({ required: true })

const search = ref('')

const fieldsByKey = computed(() => new Map(props.fields.map((f) => [f.key, f])))

const groups = computed(() => {
  const byGroup = new Map<string, CatalogField[]>()
  for (const field of props.fields) {
    const list = byGroup.get(field.group) ?? []
    list.push(field)
    byGroup.set(field.group, list)
  }
  return [...byGroup.entries()].map(([group, fields]) => ({ group, fields }))
})

const selected = computed(() => new Set(columns.value))

const accordionItems = computed(() =>
  groups.value.map(({ group, fields }) => ({
    label: group,
    value: group,
    fields,
    count: fields.filter((f) => selected.value.has(f.key)).length,
  })),
)

const searchResults = computed(() => {
  const query = search.value.trim().toLowerCase()
  if (!query) return []
  return props.fields.filter((f) => `${f.group} ${f.label} ${f.key}`.toLowerCase().includes(query))
})

function toggle(key: string, on: boolean) {
  if (on && !selected.value.has(key)) columns.value = [...columns.value, key]
  if (!on) columns.value = columns.value.filter((k) => k !== key)
}

function setGroup(fields: CatalogField[], on: boolean) {
  const keys = fields.map((f) => f.key)
  columns.value = on
    ? [...columns.value, ...keys.filter((k) => !selected.value.has(k))]
    : columns.value.filter((k) => !keys.includes(k))
}

function move(index: number, delta: number) {
  const target = index + delta
  if (target < 0 || target >= columns.value.length) return
  const next = [...columns.value]
  ;[next[index], next[target]] = [next[target]!, next[index]!]
  columns.value = next
}
</script>

<template>
  <div class="grid items-start gap-4 lg:grid-cols-[minmax(0,2fr)_minmax(0,1fr)]">
    <div class="order-1 flex flex-col gap-3 lg:order-2 lg:sticky lg:top-4">
      <div v-if="columns.length" class="flex flex-col gap-1">
        <div class="flex items-center justify-between">
          <span class="text-sm font-medium">Selected columns ({{ columns.length }})</span>
          <UButton
            size="xs"
            variant="link"
            color="neutral"
            label="Clear all"
            @click="columns = []"
          />
        </div>
        <ol
          class="flex flex-col divide-y divide-default rounded-md border border-default max-h-72 overflow-y-auto lg:max-h-[60vh]"
        >
          <li
            v-for="(key, index) in columns"
            :key="key"
            class="flex items-center gap-2 px-2 py-1 text-sm"
          >
            <span class="w-6 shrink-0 text-right text-xs text-muted tabular-nums">{{
              index + 1
            }}</span>
            <span class="min-w-0 flex-1 truncate" :title="fieldsByKey.get(key)?.group">
              {{ fieldsByKey.get(key) ? fieldLabel(fieldsByKey.get(key)!) : key }}
            </span>
            <UButton
              size="xs"
              variant="ghost"
              color="neutral"
              icon="i-lucide-chevron-up"
              aria-label="Move up"
              :disabled="index === 0"
              @click="move(index, -1)"
            />
            <UButton
              size="xs"
              variant="ghost"
              color="neutral"
              icon="i-lucide-chevron-down"
              aria-label="Move down"
              :disabled="index === columns.length - 1"
              @click="move(index, 1)"
            />
            <UButton
              size="xs"
              variant="ghost"
              color="neutral"
              icon="i-lucide-x"
              aria-label="Remove column"
              @click="toggle(key, false)"
            />
          </li>
        </ol>
      </div>
      <UAlert
        v-else
        color="warning"
        variant="subtle"
        icon="i-lucide-columns-3"
        description="Pick at least one column to download."
      />
    </div>

    <div class="order-2 flex flex-col gap-4 lg:order-1">
      <UInput
        v-model="search"
        icon="i-lucide-search"
        placeholder="Search columns…"
        class="w-full"
        :ui="{ trailing: 'pe-1' }"
      >
        <template v-if="search" #trailing>
          <UButton
            size="xs"
            variant="link"
            color="neutral"
            icon="i-lucide-x"
            aria-label="Clear search"
            @click="search = ''"
          />
        </template>
      </UInput>

      <div v-if="search.trim()" class="grid gap-x-4 gap-y-1.5 sm:grid-cols-2 xl:grid-cols-3">
        <p v-if="!searchResults.length" class="text-sm text-muted sm:col-span-full">
          No columns match “{{ search }}”.
        </p>
        <UCheckbox
          v-for="field in searchResults"
          :key="field.key"
          :model-value="selected.has(field.key)"
          :label="fieldLabel(field)"
          :description="field.group"
          @update:model-value="(on: boolean | 'indeterminate') => toggle(field.key, on === true)"
        />
      </div>

      <UAccordion v-else type="multiple" :items="accordionItems" :ui="{ body: 'pb-3' }">
        <template #trailing="{ item }">
          <UBadge
            v-if="item.count"
            :label="`${item.count}/${item.fields.length}`"
            size="sm"
            variant="subtle"
            class="ms-auto me-2"
          />
        </template>
        <template #body="{ item }">
          <div class="flex flex-col gap-1.5">
            <div class="flex gap-2">
              <UButton
                size="xs"
                variant="link"
                color="primary"
                class="px-0"
                label="Select all"
                @click="setGroup(item.fields, true)"
              />
              <UButton
                v-if="item.count"
                size="xs"
                variant="link"
                color="neutral"
                class="px-0"
                label="Clear"
                @click="setGroup(item.fields, false)"
              />
            </div>
            <div class="grid gap-x-4 gap-y-1.5 sm:grid-cols-2 xl:grid-cols-3">
              <UCheckbox
                v-for="field in item.fields"
                :key="field.key"
                :model-value="selected.has(field.key)"
                :label="fieldLabel(field)"
                :description="field.description ?? undefined"
                @update:model-value="
                  (on: boolean | 'indeterminate') => toggle(field.key, on === true)
                "
              />
            </div>
          </div>
        </template>
      </UAccordion>
    </div>
  </div>
</template>
