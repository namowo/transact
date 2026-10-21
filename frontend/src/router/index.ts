import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

declare module 'vue-router' {
  interface RouteMeta {
    requiresAuth?: boolean
    guestOnly?: boolean
    breadcrumb?: string
    requiresSuperuser?: boolean
    requiresLabAdmin?: boolean
    requiresQualityChecker?: boolean
  }
}

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      component: () => import('@/layouts/AppLayout.vue'),
      children: [
        {
          path: '',
          name: 'dashboard',
          component: () => import('@/views/HomeView.vue'),
          meta: { breadcrumb: 'Dashboard' },
        },
        {
          path: 'studies',
          name: 'studies',
          redirect: { name: 'studies-laboratory' },
          meta: { breadcrumb: 'Studies' },
          children: [
            {
              path: 'laboratory',
              name: 'studies-laboratory',
              component: () => import('@/views/studies/StudiesView.vue'),
              props: { scope: 'laboratory' },
              meta: { requiresAuth: true, breadcrumb: 'By Laboratory' },
            },
            {
              path: 'all',
              name: 'studies-all',
              component: () => import('@/views/studies/StudiesView.vue'),
              props: { scope: 'all' },
              meta: { breadcrumb: 'All' },
            },
            {
              path: 'new',
              name: 'studies-new',
              component: () => import('@/views/studies/StudyFormView.vue'),
              meta: { requiresAuth: true, breadcrumb: 'Add study' },
            },
            {
              path: ':id/edit',
              name: 'studies-edit',
              component: () => import('@/views/studies/StudyFormView.vue'),
              props: true,
              meta: { requiresAuth: true, breadcrumb: 'Edit study' },
            },
            {
              path: ':studyId/scenarios',
              props: true,
              meta: { requiresAuth: true, breadcrumb: 'Scenarios' },
              children: [
                {
                  path: '',
                  name: 'scenarios',
                  component: () => import('@/views/scenarios/ScenariosView.vue'),
                  props: true,
                },
                {
                  path: 'new',
                  name: 'scenarios-new',
                  component: () => import('@/views/scenarios/ScenarioFormView.vue'),
                  props: true,
                  meta: { breadcrumb: 'Add scenario' },
                },
                {
                  path: ':id/edit',
                  name: 'scenarios-edit',
                  component: () => import('@/views/scenarios/ScenarioFormView.vue'),
                  props: true,
                  meta: { breadcrumb: 'Edit scenario' },
                },
              ],
            },
            {
              path: ':studyId/data',
              name: 'data-entry',
              component: () => import('@/views/data/DataEntryView.vue'),
              props: true,
              meta: { requiresAuth: true, breadcrumb: 'Data entry' },
            },
          ],
        },
        {
          path: 'quality-check',
          name: 'studies-quality-check',
          component: () => import('@/views/studies/QualityCheckQueueView.vue'),
          meta: {
            requiresAuth: true,
            requiresQualityChecker: true,
            breadcrumb: 'Quality Check',
          },
        },
        {
          path: 'settings',
          meta: { breadcrumb: 'Settings' },
          children: [
            { path: '', redirect: { name: 'settings-methods-extraction' } },
            {
              path: 'laboratory',
              meta: { requiresAuth: true, breadcrumb: 'Laboratory' },
              children: [
                { path: '', redirect: { name: 'settings-methods-extraction' } },
                {
                  path: 'methods',
                  component: () => import('@/views/settings/methods/MethodsLayoutView.vue'),
                  meta: { requiresAuth: true, breadcrumb: 'Methods' },
                  children: [
                    { path: '', redirect: { name: 'settings-methods-extraction' } },
                    {
                  path: 'extraction',
                  name: 'settings-methods-extraction',
                  component: () => import('@/views/settings/methods/LabMethodListView.vue'),
                  props: { methodKey: 'extraction' },
                  meta: { requiresAuth: true, breadcrumb: 'Extraction' },
                },
                {
                  path: 'pcr',
                  name: 'settings-methods-pcr',
                  component: () => import('@/views/settings/methods/LabMethodListView.vue'),
                  props: { methodKey: 'pcr' },
                  meta: { requiresAuth: true, breadcrumb: 'PCR' },
                },
                {
                  path: 'ce',
                  name: 'settings-methods-ce',
                  component: () => import('@/views/settings/methods/LabMethodListView.vue'),
                  props: { methodKey: 'ce' },
                  meta: { requiresAuth: true, breadcrumb: 'CE' },
                },
                {
                  path: 'quantification',
                  name: 'settings-methods-quantification',
                  component: () => import('@/views/settings/methods/LabMethodListView.vue'),
                  props: { methodKey: 'quantification' },
                  meta: { requiresAuth: true, breadcrumb: 'Quantification' },
                },
                {
                  path: 'epg-analysis',
                  name: 'settings-methods-epg-analysis',
                  component: () => import('@/views/settings/methods/LabMethodListView.vue'),
                  props: { methodKey: 'epg-analysis' },
                  meta: { requiresAuth: true, breadcrumb: 'EPG Analysis' },
                },
                {
                  path: 'epg-interpretation',
                  name: 'settings-methods-epg-interpretation',
                  component: () => import('@/views/settings/methods/LabMethodListView.vue'),
                  props: { methodKey: 'epg-interpretation' },
                  meta: { requiresAuth: true, breadcrumb: 'EPG Interpretation' },
                },
                {
                  path: 'post-pcr-treatment',
                  name: 'settings-methods-post-pcr-treatment',
                  component: () => import('@/views/settings/methods/LabMethodListView.vue'),
                  props: { methodKey: 'post-pcr-treatment' },
                  meta: { requiresAuth: true, breadcrumb: 'Post-PCR Treatment' },
                },
                {
                  path: 'sampling',
                  name: 'settings-methods-sampling',
                  component: () => import('@/views/settings/methods/SamplingMethodListView.vue'),
                  meta: { requiresAuth: true, breadcrumb: 'Sampling' },
                },
              ],
            },
                {
                  path: 'users',
                  name: 'lab-users',
                  component: () => import('@/views/settings/laboratory/UsersView.vue'),
                  meta: { requiresAuth: true, requiresLabAdmin: true, breadcrumb: 'Users' },
                },
              ],
            },
            {
              path: 'admin',
              meta: { requiresAuth: true, requiresSuperuser: true, breadcrumb: 'Admin' },
              children: [
                { path: '', redirect: { name: 'admin-users' } },
                {
                  path: 'users',
                  name: 'admin-users',
                  component: () => import('@/views/settings/admin/UsersView.vue'),
                  meta: {
                    requiresAuth: true,
                    requiresSuperuser: true,
                    breadcrumb: 'User Permissions',
                  },
                },
                {
                  path: 'laboratories',
                  name: 'laboratories',
                  component: () => import('@/views/settings/admin/LaboratoriesView.vue'),
                  meta: {
                    requiresAuth: true,
                    requiresSuperuser: true,
                    breadcrumb: 'Laboratories',
                  },
                },
                {
                  path: 'item-catalog',
                  name: 'admin-item-catalog',
                  component: () => import('@/views/settings/admin/ItemCatalogView.vue'),
                  meta: {
                    requiresAuth: true,
                    requiresSuperuser: true,
                    breadcrumb: 'Item Catalog',
                  },
                },
                {
                  path: 'legal',
                  name: 'admin-legal',
                  component: () => import('@/views/settings/admin/LegalSettingsView.vue'),
                  meta: {
                    requiresAuth: true,
                    requiresSuperuser: true,
                    breadcrumb: 'Legal Pages',
                  },
                },
              ],
            },
          ],
        },
        {
          path: 'profile',
          name: 'profile',
          component: () => import('@/views/ProfileView.vue'),
          meta: { requiresAuth: true, breadcrumb: 'Edit profile' },
        },
        {
          path: 'docs/:slug?',
          name: 'docs',
          component: () => import('@/views/docs/DocsView.vue'),
          meta: { breadcrumb: 'Documentation' },
        },
      ],
    },
    {
      path: '/',
      component: () => import('@/layouts/AuthLayout.vue'),
      meta: { guestOnly: true },
      children: [
        { path: 'login', name: 'login', component: () => import('@/views/auth/LoginView.vue') },
        {
          path: 'register',
          name: 'register',
          component: () => import('@/views/auth/RegisterView.vue'),
        },
        {
          path: 'forgot-password',
          name: 'forgot-password',
          component: () => import('@/views/auth/ForgotPasswordView.vue'),
        },
      ],
    },
    {
      path: '/',
      component: () => import('@/layouts/AuthLayout.vue'),
      children: [
        {
          path: 'verify-email',
          name: 'verify-email',
          component: () => import('@/views/auth/VerifyEmailView.vue'),
        },
        {
          path: 'reset-password',
          name: 'reset-password',
          component: () => import('@/views/auth/ResetPasswordView.vue'),
        },
        {
          path: 'setup',
          name: 'setup',
          component: () => import('@/views/auth/SetupView.vue'),
        },
        {
          path: 'select-laboratory',
          name: 'select-laboratory',
          component: () => import('@/views/auth/SelectLaboratoryView.vue'),
          meta: { requiresAuth: true },
        },
        {
          path: 'confirm-email',
          name: 'email-not-verified',
          component: () => import('@/views/auth/EmailNotVerifiedView.vue'),
          meta: { requiresAuth: true },
        },
      ],
    },
    {
      path: '/',
      component: () => import('@/layouts/LegalLayout.vue'),
      children: [
        {
          path: 'site-print',
          name: 'site-print',
          component: () => import('@/views/legal/SitePrintView.vue'),
        },
        {
          path: 'privacy-policy',
          name: 'privacy-policy',
          component: () => import('@/views/legal/PrivacyPolicyView.vue'),
        },
      ],
    },
  ],
})

router.beforeEach(async (to) => {
  const auth = useAuthStore()

  // Checked before anything else - a freshly installed instance has no
  // superuser yet, so every navigation is forced to the setup page until
  // it's completed.
  await auth.ensureSetupStatusLoaded()

  if (auth.needsSetup) {
    if (to.name !== 'setup') {
      return { name: 'setup' }
    }
    return
  }

  if (to.name === 'setup') {
    return { name: 'login' }
  }

  // The session lives in an httpOnly cookie the frontend can't read, so
  // `isAuthenticated` is only known once this resolves. It's memoized, so
  // this only does real work on the first navigation after a page load.
  await auth.ensureUserLoaded()

  if (to.meta.requiresAuth && !auth.isAuthenticated) {
    return { name: 'login', query: { redirect: to.fullPath } }
  }

  if (to.meta.guestOnly && auth.isAuthenticated) {
    return { name: 'dashboard' }
  }

  if (
    to.meta.requiresAuth &&
    to.name !== 'email-not-verified' &&
    auth.isAuthenticated &&
    auth.user &&
    !auth.user.is_verified
  ) {
    return { name: 'email-not-verified' }
  }

  if (
    to.meta.requiresAuth &&
    to.name !== 'select-laboratory' &&
    to.name !== 'email-not-verified' &&
    auth.isAuthenticated &&
    !auth.user?.laboratory_id
  ) {
    return { name: 'select-laboratory' }
  }

  if (to.meta.requiresSuperuser && !auth.isSuperuser) {
    return { name: 'dashboard' }
  }

  if (to.meta.requiresLabAdmin && !auth.isLabAdmin) {
    return { name: 'dashboard' }
  }

  if (to.meta.requiresQualityChecker && !auth.canQualityCheck) {
    return { name: 'dashboard' }
  }
})

export default router
