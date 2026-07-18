import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

declare module 'vue-router' {
  interface RouteMeta {
    requiresAuth?: boolean
    guestOnly?: boolean
    breadcrumb?: string
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
          path: 'laboratories',
          name: 'laboratories',
          component: () => import('@/views/laboratories/LaboratoriesView.vue'),
          meta: { requiresAuth: true, breadcrumb: 'Laboratories' },
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
              meta: { requiresAuth: true, breadcrumb: 'All' },
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
})

export default router
