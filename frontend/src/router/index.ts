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
          component: () => import('@/views/DashboardView.vue'),
          meta: { requiresAuth: true, breadcrumb: 'Dashboard' },
        },
        {
          path: 'studies',
          meta: { breadcrumb: 'Studies' },
          children: [
            { path: '', redirect: { name: 'studies-laboratory' } },
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
          ],
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
                  meta: { requiresAuth: true, breadcrumb: 'Extraction' },
                  children: [
                    {
                      path: '',
                      name: 'settings-methods-extraction',
                      component: () => import('@/views/settings/methods/LabMethodListView.vue'),
                      props: { methodKey: 'extraction' },
                    },
                    {
                      path: 'new',
                      name: 'settings-methods-extraction-new',
                      component: () => import('@/views/settings/methods/LabMethodFormView.vue'),
                      props: { methodKey: 'extraction' },
                      meta: { breadcrumb: 'Add entry' },
                    },
                    {
                      path: ':id/edit',
                      name: 'settings-methods-extraction-edit',
                      component: () => import('@/views/settings/methods/LabMethodFormView.vue'),
                      props: (route) => ({ methodKey: 'extraction', id: route.params.id }),
                      meta: { breadcrumb: 'Edit entry' },
                    },
                  ],
                },
                {
                  path: 'pcr',
                  meta: { requiresAuth: true, breadcrumb: 'PCR' },
                  children: [
                    {
                      path: '',
                      name: 'settings-methods-pcr',
                      component: () => import('@/views/settings/methods/LabMethodListView.vue'),
                      props: { methodKey: 'pcr' },
                    },
                    {
                      path: 'new',
                      name: 'settings-methods-pcr-new',
                      component: () => import('@/views/settings/methods/LabMethodFormView.vue'),
                      props: { methodKey: 'pcr' },
                      meta: { breadcrumb: 'Add entry' },
                    },
                    {
                      path: ':id/edit',
                      name: 'settings-methods-pcr-edit',
                      component: () => import('@/views/settings/methods/LabMethodFormView.vue'),
                      props: (route) => ({ methodKey: 'pcr', id: route.params.id }),
                      meta: { breadcrumb: 'Edit entry' },
                    },
                  ],
                },
                {
                  path: 'ce',
                  meta: { requiresAuth: true, breadcrumb: 'CE' },
                  children: [
                    {
                      path: '',
                      name: 'settings-methods-ce',
                      component: () => import('@/views/settings/methods/LabMethodListView.vue'),
                      props: { methodKey: 'ce' },
                    },
                    {
                      path: 'new',
                      name: 'settings-methods-ce-new',
                      component: () => import('@/views/settings/methods/LabMethodFormView.vue'),
                      props: { methodKey: 'ce' },
                      meta: { breadcrumb: 'Add entry' },
                    },
                    {
                      path: ':id/edit',
                      name: 'settings-methods-ce-edit',
                      component: () => import('@/views/settings/methods/LabMethodFormView.vue'),
                      props: (route) => ({ methodKey: 'ce', id: route.params.id }),
                      meta: { breadcrumb: 'Edit entry' },
                    },
                  ],
                },
                {
                  path: 'quantification',
                  meta: { requiresAuth: true, breadcrumb: 'Quantification' },
                  children: [
                    {
                      path: '',
                      name: 'settings-methods-quantification',
                      component: () => import('@/views/settings/methods/LabMethodListView.vue'),
                      props: { methodKey: 'quantification' },
                    },
                    {
                      path: 'new',
                      name: 'settings-methods-quantification-new',
                      component: () => import('@/views/settings/methods/LabMethodFormView.vue'),
                      props: { methodKey: 'quantification' },
                      meta: { breadcrumb: 'Add entry' },
                    },
                    {
                      path: ':id/edit',
                      name: 'settings-methods-quantification-edit',
                      component: () => import('@/views/settings/methods/LabMethodFormView.vue'),
                      props: (route) => ({ methodKey: 'quantification', id: route.params.id }),
                      meta: { breadcrumb: 'Edit entry' },
                    },
                  ],
                },
                {
                  path: 'epg-analysis',
                  meta: { requiresAuth: true, breadcrumb: 'EPG Analysis' },
                  children: [
                    {
                      path: '',
                      name: 'settings-methods-epg-analysis',
                      component: () => import('@/views/settings/methods/LabMethodListView.vue'),
                      props: { methodKey: 'epg-analysis' },
                    },
                    {
                      path: 'new',
                      name: 'settings-methods-epg-analysis-new',
                      component: () => import('@/views/settings/methods/LabMethodFormView.vue'),
                      props: { methodKey: 'epg-analysis' },
                      meta: { breadcrumb: 'Add entry' },
                    },
                    {
                      path: ':id/edit',
                      name: 'settings-methods-epg-analysis-edit',
                      component: () => import('@/views/settings/methods/LabMethodFormView.vue'),
                      props: (route) => ({ methodKey: 'epg-analysis', id: route.params.id }),
                      meta: { breadcrumb: 'Edit entry' },
                    },
                  ],
                },
                {
                  path: 'epg-interpretation',
                  meta: { requiresAuth: true, breadcrumb: 'EPG Interpretation' },
                  children: [
                    {
                      path: '',
                      name: 'settings-methods-epg-interpretation',
                      component: () => import('@/views/settings/methods/LabMethodListView.vue'),
                      props: { methodKey: 'epg-interpretation' },
                    },
                    {
                      path: 'new',
                      name: 'settings-methods-epg-interpretation-new',
                      component: () => import('@/views/settings/methods/LabMethodFormView.vue'),
                      props: { methodKey: 'epg-interpretation' },
                      meta: { breadcrumb: 'Add entry' },
                    },
                    {
                      path: ':id/edit',
                      name: 'settings-methods-epg-interpretation-edit',
                      component: () => import('@/views/settings/methods/LabMethodFormView.vue'),
                      props: (route) => ({ methodKey: 'epg-interpretation', id: route.params.id }),
                      meta: { breadcrumb: 'Edit entry' },
                    },
                  ],
                },
                {
                  path: 'post-pcr-treatment',
                  meta: { requiresAuth: true, breadcrumb: 'Post-PCR Treatment' },
                  children: [
                    {
                      path: '',
                      name: 'settings-methods-post-pcr-treatment',
                      component: () => import('@/views/settings/methods/LabMethodListView.vue'),
                      props: { methodKey: 'post-pcr-treatment' },
                    },
                    {
                      path: 'new',
                      name: 'settings-methods-post-pcr-treatment-new',
                      component: () => import('@/views/settings/methods/LabMethodFormView.vue'),
                      props: { methodKey: 'post-pcr-treatment' },
                      meta: { breadcrumb: 'Add entry' },
                    },
                    {
                      path: ':id/edit',
                      name: 'settings-methods-post-pcr-treatment-edit',
                      component: () => import('@/views/settings/methods/LabMethodFormView.vue'),
                      props: (route) => ({ methodKey: 'post-pcr-treatment', id: route.params.id }),
                      meta: { breadcrumb: 'Edit entry' },
                    },
                  ],
                },
                {
                  path: 'sampling',
                  meta: { requiresAuth: true, breadcrumb: 'Sampling' },
                  children: [
                    {
                      path: '',
                      name: 'settings-methods-sampling',
                      component: () =>
                        import('@/views/settings/methods/SamplingMethodListView.vue'),
                    },
                    {
                      path: 'new',
                      name: 'settings-methods-sampling-new',
                      component: () =>
                        import('@/views/settings/methods/SamplingMethodFormView.vue'),
                      meta: { breadcrumb: 'Add sampling method' },
                    },
                    {
                      path: ':id/edit',
                      name: 'settings-methods-sampling-edit',
                      component: () =>
                        import('@/views/settings/methods/SamplingMethodFormView.vue'),
                      props: true,
                      meta: { breadcrumb: 'Edit sampling method' },
                    },
                  ],
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
    if (to.name === 'dashboard') {
      return { name: 'docs' }
    }
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
