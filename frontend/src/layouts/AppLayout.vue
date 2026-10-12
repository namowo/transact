<script setup lang="ts">
import { computed } from 'vue'
import { RouterLink, RouterView, useRoute, useRouter } from 'vue-router'
import type { NavigationMenuItem } from '@nuxt/ui'
import NotificationCenter from '@/components/NotificationCenter.vue'
import ThemeToggle from '@/components/ThemeToggle.vue'
import { useAuthStore } from '@/stores/auth'
import { useUiStore } from '@/stores/ui'
import { defaultDocSlug, docPages } from '@/data/docs'
import { usePendingRequests } from '@/composables/usePendingRequests'

const router = useRouter()
const route = useRoute()
const auth = useAuthStore()
const ui = useUiStore()
const { labRequestCount, newLabRequestCount, load: loadPendingRequests } = usePendingRequests()

if (auth.isAuthenticated) loadPendingRequests()

const navGroups = computed<NavigationMenuItem[][]>(() =>
  auth.isAuthenticated
    ? [
        [
          { label: 'Dashboard', icon: 'i-lucide-layout-dashboard', to: { name: 'dashboard' } },
          {
            label: 'Studies',
            icon: 'i-lucide-book-open',
            type: 'trigger',
            defaultOpen: route.name?.toString().startsWith('studies-'),
            children: [
              { label: 'By Laboratory', to: { name: 'studies-laboratory' } },
              { label: 'All', to: { name: 'studies-all' } },
            ],
          },
          ...(auth.canQualityCheck
            ? [
                {
                  label: 'Quality Check',
                  icon: 'i-lucide-square-check',
                  to: { name: 'studies-quality-check' },
                },
              ]
            : []),
        ],
        [
          {
            label: 'Laboratory',
            icon: 'i-lucide-building-2',
            type: 'trigger',
            defaultOpen: route.name?.toString().startsWith('settings-methods-') || route.name === 'lab-users',
            badge: labRequestCount.value > 0 ? labRequestCount.value : undefined,
            children: [
              { label: 'Methods', to: { name: 'settings-methods-extraction' } },
              ...(auth.isLabAdmin
                ? [
                    {
                      label: 'Users',
                      to: { name: 'lab-users' },
                      badge: labRequestCount.value > 0 ? labRequestCount.value : undefined,
                    },
                  ]
                : []),
            ],
          },
          ...(auth.isSuperuser
            ? [
                {
                  label: 'Admin',
                  icon: 'i-lucide-shield',
                  type: 'trigger' as const,
                  defaultOpen:
                    route.name === 'admin-users' ||
                    route.name === 'laboratories' ||
                    route.name === 'admin-item-catalog' ||
                    route.name === 'admin-legal',
                  badge: newLabRequestCount.value > 0 ? newLabRequestCount.value : undefined,
                  children: [
                    { label: 'User Permissions', to: { name: 'admin-users' } },
                    {
                      label: 'Laboratories',
                      to: { name: 'laboratories' },
                      badge: newLabRequestCount.value > 0 ? newLabRequestCount.value : undefined,
                    },
                    { label: 'Item Catalog', to: { name: 'admin-item-catalog' } },
                    { label: 'Legal Pages', to: { name: 'admin-legal' } },
                  ],
                },
              ]
            : []),
        ],
        [
          ...docPages.map((page) => ({
            label: page.title,
            icon: 'i-lucide-file-text',
            to: { name: 'docs', params: { slug: page.slug } },
          })),
        ],
      ]
    : [
        [{ label: 'Studies', icon: 'i-lucide-book-open', to: { name: 'studies-all' } }],
        [
          ...docPages.map((page) => ({
            label: page.title,
            icon: 'i-lucide-file-text',
            to: { name: 'docs', params: { slug: page.slug } },
          })),
        ],
      ],
)

const userMenuItems = computed(() => [
  [
    {
      label: 'Edit profile',
      icon: 'i-lucide-user-pen',
      onSelect: () => router.push({ name: 'profile' }),
    },
  ],
  [
    {
      label: 'Log out',
      icon: 'i-lucide-log-out',
      onSelect: async () => {
        await auth.logout()
        router.push({ name: 'login' })
      },
    },
  ],
])

function initials(firstName?: string, lastName?: string) {
  return `${firstName?.[0] ?? ''}${lastName?.[0] ?? ''}`.toUpperCase()
}

const breadcrumbItems = computed(() => {
  const items = route.matched
    .filter((r) => r.meta.breadcrumb)
    .map((r) => ({ label: r.meta.breadcrumb as string, name: r.name as string | undefined }))

  if (route.name === 'docs') {
    const slug = (route.params.slug as string | undefined) ?? defaultDocSlug
    const page = docPages.find((p) => p.slug === slug)
    if (page) items[items.length - 1] = { label: page.title, name: 'docs' }
  }

  if (route.name === 'dashboard' && !auth.isAuthenticated) {
    items[items.length - 1] = { label: 'Startpage', name: 'dashboard' }
  }

  return [
    { label: '', icon: 'i-lucide-house', to: { name: 'dashboard' } },
    ...items.map((item) => ({
      label: item.label,
      to: item.name ? { name: item.name } : undefined,
    })),
  ]
})

const secondaryNavGroup = [
  {
    label: 'Report a bug',
    icon: 'i-lucide-message-circle',
    to: 'https://github.com/namowo/transact/issues',
    target: '_blank',
  },
]

const appVersion = __APP_VERSION__

const footerLinks = [
  {
    label: 'Site Print',
    to: { name: 'site-print' },
  },
  {
    label: 'Privacy Policy',
    to: { name: 'privacy-policy' },
  },
]
</script>

<template>
  <UDashboardGroup unit="rem" storage="local">
    <UDashboardSidebar
      id="app-sidebar"
      v-model:open="ui.sidebarOpen"
      collapsible
      resizable
      class="bg-elevated/25"
      :ui="{ root: 'transition-[width] duration-200 ease-in-out data-[dragging=true]:transition-none' }"
    >
      <template #header="{ collapsed }">
        <RouterLink
          :to="{ name: 'dashboard' }"
          class="flex items-center gap-2 px-1 min-w-0"
        >
          <img
            src="/transact_logo_dark.png"
            alt="TransAct"
            class="size-6 shrink-0 dark:hidden"
          />
          <img
            src="/transact_logo_light.png"
            alt="TransAct"
            class="size-6 shrink-0 hidden dark:block"
          />
          <span v-if="!collapsed" class="font-semibold text-sm truncate">TransAct Repository</span>
        </RouterLink>
      </template>

      <template #default="{ collapsed }">
        <UNavigationMenu
          v-for="(group, index) in navGroups"
          :key="index"
          :collapsed="collapsed"
          :items="group"
          orientation="vertical"
          tooltip
          popover
          :class="index > 0 && 'mt-4'"
        />

        <UNavigationMenu
          :collapsed="collapsed"
          :items="[secondaryNavGroup]"
          orientation="vertical"
          tooltip
          popover
          class="mt-auto"
        />
      </template>

      <template #footer="{ collapsed }">
        <UDropdownMenu v-if="auth.isAuthenticated" :items="userMenuItems" :content="{ align: 'center' }">
          <UButton
            color="neutral"
            variant="ghost"
            block
            :square="collapsed"
            class="data-[state=open]:bg-elevated"
          >
            <UAvatar
              :text="initials(auth.user?.first_name, auth.user?.last_name)"
              size="xs"
            />
            <span v-if="!collapsed" class="truncate">{{ auth.user?.first_name }} {{ auth.user?.last_name }}</span>
          </UButton>
        </UDropdownMenu>
        <UButton
          v-else
          :label="collapsed ? undefined : 'Log in'"
          icon="i-lucide-log-in"
          color="primary"
          block
          :square="collapsed"
          :to="{ name: 'login' }"
        />
      </template>
    </UDashboardSidebar>

    <UDashboardPanel id="app-content">
      <template #header>
        <UDashboardNavbar :ui="{ right: 'gap-2' }">
          <template #leading>
            <UDashboardSidebarCollapse />
          </template>

          <template #default>
            <UBreadcrumb :items="breadcrumbItems" />
          </template>

          <template #right>
            <NotificationCenter v-if="auth.isAuthenticated" />
            <ThemeToggle />
          </template>
        </UDashboardNavbar>
      </template>

      <template #body>
        <div class="max-w-6xl w-full mx-auto flex flex-col flex-1">
          <RouterView />
        </div>

        <UFooter :ui="{ root: 'border-t border-default mt-8' }">
          <template #left>
            <span class="text-sm text-muted">&copy; {{ new Date().getFullYear() }} namowo GmbH</span>
          </template>

          <UNavigationMenu :items="footerLinks" variant="link" />

          <template #right>
            <span class="text-sm text-muted">v{{ appVersion }}</span>
          </template>
        </UFooter>
      </template>
    </UDashboardPanel>
  </UDashboardGroup>
</template>
