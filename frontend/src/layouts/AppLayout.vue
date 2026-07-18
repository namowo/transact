<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { RouterLink, RouterView, useRoute, useRouter } from 'vue-router'
import Avatar from 'primevue/avatar'
import Menu from 'primevue/menu'
import Breadcrumb from 'primevue/breadcrumb'
import SidebarLayout from 'primevue/sidebarlayout'
import Sidebar from 'primevue/sidebar'
import SidebarBackdrop from 'primevue/sidebarbackdrop'
import SidebarMain from 'primevue/sidebarmain'
import SidebarAside from 'primevue/sidebaraside'
import SidebarPanel from 'primevue/sidebarpanel'
import SidebarSpacer from 'primevue/sidebarspacer'
import SidebarHeader from 'primevue/sidebarheader'
import SidebarContent from 'primevue/sidebarcontent'
import SidebarFooter from 'primevue/sidebarfooter'
import SidebarGroup from 'primevue/sidebargroup'
import SidebarGroupLabel from 'primevue/sidebargrouplabel'
import SidebarGroupContent from 'primevue/sidebargroupcontent'
import SidebarMenu from 'primevue/sidebarmenu'
import SidebarMenuItem from 'primevue/sidebarmenuitem'
import SidebarMenuButton from 'primevue/sidebarmenubutton'
import SidebarMenuSub from 'primevue/sidebarmenusub'
import SidebarMenuSubItem from 'primevue/sidebarmenusubitem'
import SidebarMenuSubButton from 'primevue/sidebarmenusubbutton'
import SidebarRail from 'primevue/sidebarrail'
import SidebarTrigger from 'primevue/sidebartrigger'
import ThemeToggle from '@/components/ThemeToggle.vue'
import { useAuthStore } from '@/stores/auth'
import { useThemeStore } from '@/stores/theme'
import { useUiStore } from '@/stores/ui'
import { defaultDocSlug, docPages } from '@/data/docs'

const router = useRouter()
const route = useRoute()
const auth = useAuthStore()
const theme = useThemeStore()
const ui = useUiStore()

const userMenu = ref()

interface NavLink {
  label: string
  icon?: string
  to: { name: string; params?: Record<string, string> }
  children?: undefined
}

interface NavGroupLink {
  label: string
  icon: string
  to: { name: string }
  children: { label: string; to: { name: string } }[]
}

const navGroups = computed<{ label: string; items: (NavLink | NavGroupLink)[] }[]>(() =>
  auth.isAuthenticated
    ? [
        {
          label: 'Application',
          items: [
            { label: 'Dashboard', icon: 'pi pi-home', to: { name: 'dashboard' } },
            {
              label: 'Studies',
              icon: 'pi pi-book',
              to: { name: 'studies-laboratory' },
              children: [
                { label: 'By Laboratory', to: { name: 'studies-laboratory' } },
                { label: 'All', to: { name: 'studies-all' } },
              ],
            },
            { label: 'Laboratories', icon: 'pi pi-building', to: { name: 'laboratories' } },
          ],
        },
      ]
    : [
        {
          label: 'Documentation',
          items: docPages.map((page) => ({
            label: page.title,
            icon: 'pi pi-book',
            to: { name: 'docs', params: { slug: page.slug } },
          })),
        },
      ],
)

function isItemActive(item: { to: { name: string; params?: Record<string, string> } }) {
  if (route.name !== item.to.name) return false
  return !item.to.params || route.params.slug === item.to.params.slug
}

function isGroupActive(item: {
  to?: { name: string }
  children?: { to: { name: string } }[]
}) {
  if (item.children?.some((child) => child.to.name === route.name)) return true
  return !!item.to && isItemActive(item as { to: { name: string } })
}

const userMenuItems = [
  {
    label: 'Edit profile',
    icon: 'pi pi-user-edit',
    command: () => router.push({ name: 'profile' }),
  },
  {
    label: 'Log out',
    icon: 'pi pi-sign-out',
    command: async () => {
      await auth.logout()
      router.push({ name: 'login' })
    },
  },
]

function toggleUserMenu(event: Event) {
  userMenu.value?.toggle(event)
}

function initials(firstName?: string, lastName?: string) {
  return `${firstName?.[0] ?? ''}${lastName?.[0] ?? ''}`.toUpperCase()
}

const homeCrumb = { icon: 'pi pi-home', command: () => router.push({ name: 'dashboard' }) }

const breadcrumbItems = computed(() => {
  const items = route.matched
    .filter((r) => r.meta.breadcrumb)
    .map((r) => ({ label: r.meta.breadcrumb as string, name: r.name as string | undefined }))

  if (route.name === 'docs') {
    const slug = (route.params.slug as string | undefined) ?? defaultDocSlug
    const page = docPages.find((p) => p.slug === slug)
    if (page) items[items.length - 1] = { label: page.title, name: 'docs' }
  }

  return items.map((item, index) => ({
    label: item.label,
    command: index < items.length - 1 && item.name ? () => router.push({ name: item.name }) : undefined,
  }))
})

const isMobile = ref(false)
const mobileOpen = ref(false)
let mql: MediaQueryList | null = null
let onMqlChange: ((event: MediaQueryListEvent) => void) | null = null

const sidebarOpen = computed({
  get: () => (isMobile.value ? mobileOpen.value : ui.sidebarOpen),
  set: (value: boolean) => {
    if (isMobile.value) {
      mobileOpen.value = value
    } else {
      ui.sidebarOpen = value
    }
  },
})

onMounted(() => {
  if (typeof window === 'undefined') return

  mql = window.matchMedia('(max-width: 1023px)')
  isMobile.value = mql.matches
  onMqlChange = (event) => {
    isMobile.value = event.matches
    mobileOpen.value = false
  }
  mql.addEventListener('change', onMqlChange)
})

onBeforeUnmount(() => {
  if (mql && onMqlChange) {
    mql.removeEventListener('change', onMqlChange)
  }
})

function handleNavClick() {
  if (isMobile.value) sidebarOpen.value = false
}
</script>

<template>
  <SidebarLayout class="min-h-full!">
    <SidebarBackdrop v-if="isMobile && sidebarOpen" />

    <Sidebar
      id="app-sidebar"
      collapsible="icon"
      side="left"
      :overlay="isMobile"
      v-model:open="sidebarOpen"
    >
      <SidebarSpacer />
      <SidebarAside>
        <SidebarPanel>
          <SidebarHeader>
            <SidebarMenu>
              <SidebarMenuItem>
                <SidebarMenuButton asChild class="px-1!" v-slot="brandSlot">
                  <RouterLink :to="{ name: 'dashboard' }" v-bind="brandSlot?.a11yAttrs" :class="brandSlot?.class">
                    <img
                      :src="theme.isDark ? '/transact_logo_light.png' : '/transact_logo_dark.png'"
                      alt="TransAct"
                      class="size-6 shrink-0"
                    />
                    <span class="font-semibold text-sm">TransAct Repository</span>
                  </RouterLink>
                </SidebarMenuButton>
              </SidebarMenuItem>
            </SidebarMenu>
          </SidebarHeader>

          <SidebarContent>
            <SidebarGroup v-for="group in navGroups" :key="group.label">
              <SidebarGroupLabel>{{ group.label }}</SidebarGroupLabel>
              <SidebarGroupContent>
                <SidebarMenu>
                  <SidebarMenuItem
                    v-for="item in group.items"
                    :key="item.label"
                    :collapsible="!!item.children"
                    :open="isGroupActive(item)"
                  >
                    <template v-if="item.children">
                      <SidebarMenuButton asChild :isActive="isGroupActive(item)" v-slot="groupSlot">
                        <RouterLink
                          :to="item.to"
                          v-bind="groupSlot?.a11yAttrs"
                          :class="groupSlot?.class"
                          @click="handleNavClick"
                        >
                          <i :class="item.icon" />
                          <span>{{ item.label }}</span>
                          <i class="pi pi-angle-down ml-auto" />
                        </RouterLink>
                      </SidebarMenuButton>
                      <SidebarMenuSub>
                        <SidebarMenuSubItem v-for="child in item.children" :key="child.label">
                          <SidebarMenuSubButton
                            asChild
                            :isActive="isItemActive(child)"
                            v-slot="subSlot"
                          >
                            <RouterLink
                              :to="child.to"
                              v-bind="subSlot?.a11yAttrs"
                              :class="subSlot?.class"
                              @click="handleNavClick"
                            >
                              <span>{{ child.label }}</span>
                            </RouterLink>
                          </SidebarMenuSubButton>
                        </SidebarMenuSubItem>
                      </SidebarMenuSub>
                    </template>
                    <SidebarMenuButton v-else asChild :isActive="isItemActive(item)" v-slot="navSlot">
                      <RouterLink
                        :to="item.to"
                        v-bind="navSlot?.a11yAttrs"
                        :class="navSlot?.class"
                        @click="handleNavClick"
                      >
                        <i :class="item.icon" />
                        <span>{{ item.label }}</span>
                      </RouterLink>
                    </SidebarMenuButton>
                  </SidebarMenuItem>
                </SidebarMenu>
              </SidebarGroupContent>
            </SidebarGroup>
          </SidebarContent>

          <SidebarFooter>
            <SidebarMenu>
              <SidebarMenuItem v-if="auth.isAuthenticated">
                <SidebarMenuButton class="p-1!" @click="toggleUserMenu">
                  <Avatar
                    :label="initials(auth.user?.first_name, auth.user?.last_name)"
                    shape="circle"
                    class="size-6 shrink-0 text-xs"
                  />
                  <span>{{ auth.user?.first_name }} {{ auth.user?.last_name }}</span>
                </SidebarMenuButton>
                <Menu ref="userMenu" :model="userMenuItems" :popup="true" />
              </SidebarMenuItem>
              <SidebarMenuItem v-else>
                <SidebarMenuButton asChild v-slot="loginSlot">
                  <RouterLink
                    :to="{ name: 'login' }"
                    v-bind="loginSlot?.a11yAttrs"
                    :class="[loginSlot?.class, 'justify-center! bg-primary! text-primary-contrast! font-medium hover:bg-primary-emphasis!']"
                  >
                    <i class="pi pi-sign-in" />
                    <span>Log in</span>
                  </RouterLink>
                </SidebarMenuButton>
              </SidebarMenuItem>
            </SidebarMenu>
          </SidebarFooter>

          <SidebarRail />
        </SidebarPanel>
      </SidebarAside>
    </Sidebar>

    <SidebarMain>
      <header
        class="h-16 shrink-0 flex items-center justify-between gap-4 px-4 sm:px-6 bg-surface-0 dark:bg-surface-900 border-b border-surface-200 dark:border-surface-700"
      >
        <div class="flex items-center gap-3 min-w-0">
          <SidebarTrigger target="app-sidebar" severity="secondary" text rounded aria-label="Toggle navigation">
            <i class="pi pi-bars" />
          </SidebarTrigger>
          <Breadcrumb :home="homeCrumb" :model="breadcrumbItems" class="border-0! bg-transparent! p-0!" />
        </div>

        <div class="flex items-center gap-2 shrink-0">
          <ThemeToggle />
        </div>
      </header>

      <main class="flex-1 p-4 sm:p-6 max-w-6xl w-full mx-auto">
        <RouterView />
      </main>
    </SidebarMain>
  </SidebarLayout>
</template>
