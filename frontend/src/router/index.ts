import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { startGlobalLoading } from '@/composables/useGlobalLoading'
import { usePrivacyPolicyStore } from '@/stores/privacyPolicy'
import type { Permission } from '@/api/types'

declare module 'vue-router' {
  interface RouteMeta {
    requiresAuth?: boolean
    guestOnly?: boolean
    breadcrumb?: string
    // Any of these permissions (see stores/auth `can`).
    requiresPermission?: Permission | Permission[]
    // The admin area: anything platform-wide to manage.
    requiresAdmin?: boolean
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
              meta: { requiresAuth: true, breadcrumb: 'Study' },
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
          path: 'data',
          name: 'data',
          redirect: { name: 'data-models' },
          meta: { breadcrumb: 'Data download' },
          children: [
            {
              path: 'models',
              name: 'data-models',
              component: () => import('@/views/data-models/DataModelsView.vue'),
            },
            {
              path: 'models/new',
              name: 'data-models-new',
              component: () => import('@/views/data-models/DataModelBuilderView.vue'),
              meta: { breadcrumb: 'New data model' },
            },
            {
              path: 'models/:id',
              name: 'data-models-edit',
              component: () => import('@/views/data-models/DataModelBuilderView.vue'),
              props: true,
              meta: { breadcrumb: 'Data model' },
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
                      component: () =>
                        import('@/views/settings/methods/SamplingMethodListView.vue'),
                      meta: { requiresAuth: true, breadcrumb: 'Sampling' },
                    },
                  ],
                },
                {
                  path: 'users',
                  name: 'lab-users',
                  component: () => import('@/views/settings/laboratory/UsersView.vue'),
                  meta: {
                    requiresAuth: true,
                    requiresPermission: 'lab.manage_members',
                    breadcrumb: 'Users',
                  },
                },
                {
                  path: 'groups',
                  name: 'lab-groups',
                  component: () => import('@/views/settings/laboratory/GroupsView.vue'),
                  meta: {
                    requiresAuth: true,
                    requiresPermission: 'lab.manage_groups',
                    breadcrumb: 'Groups',
                  },
                },
                {
                  path: 'settings',
                  name: 'lab-settings',
                  component: () => import('@/views/settings/laboratory/LabSettingsView.vue'),
                  meta: {
                    requiresAuth: true,
                    requiresPermission: 'lab.manage_settings',
                    breadcrumb: 'Settings',
                  },
                },
              ],
            },
            {
              path: 'admin',
              meta: { requiresAuth: true, requiresAdmin: true, breadcrumb: 'Admin' },
              children: [
                {
                  path: '',
                  // The first admin page the user may open.
                  redirect: () => {
                    const auth = useAuthStore()
                    if (auth.can('users.manage')) return { name: 'admin-users' }
                    if (auth.can('groups.manage')) return { name: 'admin-groups' }
                    if (auth.can('laboratories.manage')) return { name: 'laboratories' }
                    if (auth.canAny('catalog.edit', 'catalog.delete'))
                      return { name: 'admin-item-catalog' }
                    return { name: 'admin-legal' }
                  },
                },
                {
                  path: 'users',
                  name: 'admin-users',
                  component: () => import('@/views/settings/admin/UsersView.vue'),
                  meta: {
                    requiresAuth: true,
                    requiresPermission: 'users.manage',
                    breadcrumb: 'Users',
                  },
                },
                {
                  path: 'groups',
                  name: 'admin-groups',
                  component: () => import('@/views/settings/admin/GroupsView.vue'),
                  meta: {
                    requiresAuth: true,
                    requiresPermission: 'groups.manage',
                    breadcrumb: 'Groups & Permissions',
                  },
                },
                {
                  path: 'laboratories',
                  name: 'laboratories',
                  component: () => import('@/views/settings/admin/LaboratoriesView.vue'),
                  meta: {
                    requiresAuth: true,
                    requiresPermission: 'laboratories.manage',
                    breadcrumb: 'Laboratories',
                  },
                },
                {
                  path: 'item-catalog',
                  name: 'admin-item-catalog',
                  component: () => import('@/views/settings/admin/ItemCatalogView.vue'),
                  meta: {
                    requiresAuth: true,
                    requiresPermission: ['catalog.edit', 'catalog.delete'],
                    breadcrumb: 'Item Catalog',
                  },
                },
                {
                  path: 'legal',
                  name: 'admin-legal',
                  component: () => import('@/views/settings/admin/LegalSettingsView.vue'),
                  meta: {
                    requiresAuth: true,
                    requiresPermission: 'site_settings.manage',
                    breadcrumb: 'Legal Pages',
                  },
                },
              ],
            },
          ],
        },
        {
          path: 'profile',
          component: () => import('@/views/profile/ProfileLayoutView.vue'),
          meta: { requiresAuth: true, breadcrumb: 'Profile' },
          children: [
            {
              path: '',
              name: 'profile',
              component: () => import('@/views/profile/ProfileGeneralView.vue'),
              meta: { requiresAuth: true },
            },
            {
              path: 'sign-in',
              name: 'profile-sign-in',
              component: () => import('@/views/profile/ProfileSignInView.vue'),
              meta: { requiresAuth: true, breadcrumb: 'Email & password' },
            },
            {
              path: 'two-factor',
              name: 'profile-two-factor',
              component: () => import('@/views/profile/ProfileTwoFactorView.vue'),
              meta: { requiresAuth: true, breadcrumb: 'Two-factor authentication' },
            },
            {
              path: 'passkeys',
              name: 'profile-passkeys',
              component: () => import('@/views/profile/ProfilePasskeysView.vue'),
              meta: { requiresAuth: true, breadcrumb: 'Passkeys' },
            },
            {
              path: 'api-keys',
              name: 'profile-api-keys',
              component: () => import('@/views/profile/ProfileApiKeysView.vue'),
              meta: { requiresAuth: true, breadcrumb: 'API keys' },
            },
            {
              path: 'notifications',
              name: 'profile-notifications',
              component: () => import('@/views/profile/ProfileNotificationsView.vue'),
              meta: { requiresAuth: true, breadcrumb: 'Notifications' },
            },
          ],
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
          path: 'accept-invitation',
          name: 'accept-invitation',
          component: () => import('@/views/auth/AcceptInvitationView.vue'),
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
          path: 'two-factor-setup',
          name: 'two-factor-setup',
          component: () => import('@/views/auth/TwoFactorSetupView.vue'),
          meta: { requiresAuth: true },
        },
        {
          path: 'privacy-policy-consent',
          name: 'privacy-policy-consent',
          component: () => import('@/views/auth/PrivacyPolicyConsentView.vue'),
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

// Open while the user still has to set up a second factor.
const TWO_FACTOR_SETUP_ROUTES = ['two-factor-setup', 'site-print', 'privacy-policy']
// Open while the user still has to agree to the privacy policy in force.
const PRIVACY_POLICY_CONSENT_ROUTES = ['privacy-policy-consent', 'site-print', 'privacy-policy']

// Show the global progress bar while a navigation resolves (lazy-loaded
// view chunks, async guards). Registered first so it wraps the other guards.
let stopNavigationLoading: (() => void) | undefined
router.beforeEach(() => {
  stopNavigationLoading?.()
  stopNavigationLoading = startGlobalLoading()
})
router.afterEach(() => stopNavigationLoading?.())
router.onError(() => stopNavigationLoading?.())

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

  // Two-factor authentication is required and the user has no second
  // factor yet: the session is only good for setting one up.
  if (auth.user?.two_factor_setup_required) {
    if (!TWO_FACTOR_SETUP_ROUTES.includes(to.name as string)) {
      return { name: 'two-factor-setup', query: { redirect: to.fullPath } }
    }
    return
  }
  if (to.name === 'two-factor-setup') {
    return { name: 'dashboard' }
  }

  // A privacy policy was published the user hasn't agreed to yet (e.g. a
  // new version): they have to agree before using the app.
  if (auth.user) {
    const privacyPolicy = usePrivacyPolicyStore()
    await privacyPolicy.load()
    if (privacyPolicy.needsConsent(auth.user)) {
      if (!PRIVACY_POLICY_CONSENT_ROUTES.includes(to.name as string)) {
        return { name: 'privacy-policy-consent', query: { redirect: to.fullPath } }
      }
      return
    }
  }
  if (to.name === 'privacy-policy-consent') {
    return { name: 'dashboard' }
  }

  if (to.name === 'register' && !auth.config.registration_enabled) {
    return { name: 'login' }
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

  if (to.meta.requiresAdmin && !auth.isAdmin) {
    return { name: 'dashboard' }
  }

  const required = to.meta.requiresPermission
  if (required && !auth.canAny(...(Array.isArray(required) ? required : [required]))) {
    return { name: 'dashboard' }
  }

  if (to.meta.requiresQualityChecker && !auth.canQualityCheck) {
    return { name: 'dashboard' }
  }
})

export default router
