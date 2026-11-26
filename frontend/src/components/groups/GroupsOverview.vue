<script setup lang="ts">
import { computed } from 'vue'
import type { DropdownMenuItem, TableColumn } from '@nuxt/ui'
import type { Laboratory, UserGroup } from '@/api/types'
import TableLoadingSkeleton from '@/components/ui/TableLoadingSkeleton.vue'
import { usePagination } from '@/composables/useTableView'
import TablePagination from '@/components/ui/TablePagination.vue'

// The groups at a glance: what they are for, where they apply, how many
// permissions and members they have.
const props = defineProps<{
  groups: UserGroup[]
  loading?: boolean
  // Names the laboratory of each laboratory group.
  laboratories?: Laboratory[]
  // Which groups get an edit/delete menu.
  editable?: (group: UserGroup) => boolean
}>()
const emit = defineEmits<{ edit: [group: UserGroup]; delete: [group: UserGroup] }>()

const laboratoryNames = computed(
  () => new Map((props.laboratories ?? []).map((lab) => [lab.id, lab.laboratory_name])),
)

const groupPages = usePagination(() => props.groups)

const columns: TableColumn<UserGroup>[] = [
  { id: 'name', header: 'Group' },
  { id: 'scope', header: 'Available to' },
  { id: 'permissions', header: 'Permissions' },
  { id: 'members', header: 'Members' },
  { id: 'actions', header: '' },
]

function rowMenuItems(group: UserGroup): DropdownMenuItem[] {
  const items: DropdownMenuItem[] = [
    { label: 'Edit', icon: 'i-lucide-pencil', onSelect: () => emit('edit', group) },
  ]
  if (!group.system_key) {
    items.push(
      { type: 'separator' },
      {
        label: 'Delete',
        icon: 'i-lucide-trash-2',
        color: 'error',
        onSelect: () => emit('delete', group),
      },
    )
  }
  return items
}
</script>

<template>
  <div>
    <UTable
      :data="groupPages.rows"
      :columns="columns"
      :loading="loading"
      :get-row-id="(group: UserGroup) => group.id"
      empty="No groups yet."
      class="rounded-md border border-default"
      :ui="{ td: 'py-2 text-sm' }"
    >
      <template #loading>
        <TableLoadingSkeleton />
      </template>
      <template #name-cell="{ row }">
        <div class="flex min-w-56 flex-col gap-0.5 whitespace-normal">
          <div class="flex items-center gap-2">
            <span class="font-medium text-highlighted">{{ row.original.name }}</span>
            <UBadge
              v-if="row.original.system_key"
              label="Built-in"
              color="neutral"
              variant="outline"
              size="sm"
            />
          </div>
          <span v-if="row.original.description" class="text-xs text-muted">
            {{ row.original.description }}
          </span>
        </div>
      </template>

      <template #scope-cell="{ row }">
        <UBadge
          v-if="!row.original.laboratory_id"
          label="All laboratories"
          color="primary"
          variant="subtle"
          size="sm"
        />
        <UBadge
          v-else
          :label="laboratoryNames.get(row.original.laboratory_id) ?? 'This laboratory'"
          color="neutral"
          variant="subtle"
          size="sm"
        />
      </template>

      <template #permissions-cell="{ row }">
        {{ row.original.permissions.length }}
      </template>

      <template #members-cell="{ row }">
        {{ row.original.member_count }}
      </template>

      <template #actions-cell="{ row }">
        <div v-if="editable?.(row.original)" class="flex justify-end">
          <UDropdownMenu :items="rowMenuItems(row.original)" :content="{ align: 'end' }">
            <UButton
              icon="i-lucide-ellipsis-vertical"
              variant="ghost"
              color="neutral"
              square
              :aria-label="`Actions for ${row.original.name}`"
            />
          </UDropdownMenu>
        </div>
      </template>
    </UTable>
    <TablePagination
      v-model:page="groupPages.page"
      v-model:page-size="groupPages.pageSize"
      :total="groupPages.total"
    />
  </div>
</template>
