import { computed, ref } from 'vue'
import { acceptHMRUpdate, defineStore } from 'pinia'
import router from '@/router'
import { completeTour } from '@/api/users'
import { useAuthStore } from '@/stores/auth'
import { tours, type TourContext, type TourId, type TourStep, type TourStepRoute } from '@/tours'

// Drives the interactive guides rendered by <TourGuide />. Steps are kept in
// their full list and inapplicable ones (`when`) are skipped while moving,
// so the index stays stable when e.g. the route changes mid-tour.
export const useTourStore = defineStore('tour', () => {
  const auth = useAuthStore()

  const tourId = ref<TourId | null>(null)
  const index = ref(0)
  // A one-off message for the current step, e.g. why saving didn't work.
  const notice = ref<string | null>(null)
  // Where the tour started; "Skip tour" is only offered there.
  const startIndex = ref(0)

  const startRoute = ref<string | null>(null)
  const context = (): TourContext => ({ auth, route: router.currentRoute.value, startRoute: startRoute.value })

  const allSteps = computed<TourStep[]>(() => (tourId.value ? tours[tourId.value].steps : []))
  const isActive = computed(() => tourId.value !== null)
  const currentStep = computed<TourStep | null>(() => allSteps.value[index.value] ?? null)

  // A step's `when` may read its own page (e.g. the study purpose from the
  // form's query), so once evaluated there the result is kept for the rest
  // of the tour - otherwise the "3 of 8" total would shift on other pages.
  const whenCache = new Map<string, boolean>()

  function applies(step: TourStep) {
    if (!step.when) return true
    const page = step.whenRoute ?? step.route
    const onItsPage = !!page && isOnRoute(page)
    if (!onItsPage && whenCache.has(step.id)) return whenCache.get(step.id)!
    const result = step.when(context())
    if (onItsPage) whenCache.set(step.id, result)
    return result
  }

  function matchesRoute(step: TourStep) {
    return !step.route || isOnRoute(step.route)
  }

  function isOnRoute(target: TourStepRoute | TourStepRoute[]) {
    const route = router.currentRoute.value
    const routes = Array.isArray(target) ? target : [target]
    return routes.some(
      (r) =>
        r.name === route.name &&
        Object.entries(r.query ?? {}).every(([key, value]) => route.query[key] === value),
    )
  }

  // Position among the steps that apply, for the "3 of 8" counter.
  const progress = computed(() => {
    const applicable = allSteps.value.map((step, i) => ({ step, i })).filter(({ step }) => applies(step))
    return {
      current: applicable.findIndex(({ i }) => i === index.value) + 1,
      total: applicable.length,
    }
  })

  function isCompleted(id: TourId) {
    return !!auth.user?.completed_tours?.includes(id)
  }

  function findStep(from: number, direction: 1 | -1, predicate: (step: TourStep) => boolean) {
    for (let i = from; i >= 0 && i < allSteps.value.length; i += direction) {
      const step = allSteps.value[i]
      if (step && applies(step) && predicate(step)) return i
    }
    return -1
  }

  // Starts a guide at its first step that fits the current page. Unless
  // forced, guides the user already finished or skipped are not shown again;
  // forcing also restarts a guide that's running (or paused) from this page.
  function start(id: TourId, { force = false } = {}) {
    if (!auth.user || (!force && isCompleted(id))) return
    if (!force && tourId.value === id) return
    whenCache.clear()
    startRoute.value = String(router.currentRoute.value.name ?? '')
    tourId.value = id
    const first = findStep(0, 1, matchesRoute)
    if (first === -1) {
      tourId.value = null
      return
    }
    setIndex(first)
    startIndex.value = first
  }

  // Ends the guide without remembering it, e.g. when the user leaves the
  // pages it covers - it's offered again next time.
  function stop() {
    tourId.value = null
    setIndex(0)
  }

  async function markCompleted(id: TourId) {
    if (!auth.user || isCompleted(id)) return
    auth.user.completed_tours = [...(auth.user.completed_tours ?? []), id]
    try {
      auth.user = await completeTour(id)
    } catch {
      // Not critical - at worst the guide is offered once more.
    }
  }

  async function finish() {
    const id = tourId.value
    stop()
    if (id) await markCompleted(id)
  }

  const skip = finish

  // Earlier steps of this page, nearest first. <TourGuide /> picks the first
  // one it can actually show (its dialog/panel may be gone by now).
  function previousCandidates() {
    const result: number[] = []
    for (let i = index.value - 1; i >= 0; i--) {
      const step = allSteps.value[i]!
      if (applies(step) && matchesRoute(step) && !step.waitForRoute) result.push(i)
    }
    return result
  }

  // Set when the user goes back to a step that waits for an action they've
  // already done (e.g. "open the Contacts tab" while it's open): the step
  // then stays until "Next" instead of moving on by itself.
  const holdWait = ref(false)

  function goBackTo(target: number, hold: boolean) {
    setIndex(target)
    holdWait.value = hold
  }

  // Moves to the next step on this page; steps meant for another page (e.g.
  // "Add study & continue" while editing an existing study) are skipped.
  function next() {
    const onThisPage = findStep(index.value + 1, 1, matchesRoute)
    const following = onThisPage !== -1 ? onThisPage : findStep(index.value + 1, 1, () => true)
    if (following === -1) return finish()
    setIndex(following)
  }

  function setIndex(value: number) {
    index.value = value
    notice.value = null
    holdWait.value = false
  }

  // Jumps to a step of the running tour, e.g. back to a form field that
  // still needs to be filled in.
  function goTo(stepId: string, message?: string) {
    const target = allSteps.value.findIndex((step) => step.id === stepId)
    if (target === -1) return
    setIndex(target)
    notice.value = message ?? null
  }

  // Whether the current step belongs to the page that's open. When it
  // doesn't (e.g. the user switched to another step of the same study),
  // the guide is paused and hidden until they come back.
  const isOnStepPage = computed(() => !!currentStep.value && matchesRoute(currentStep.value))

  // Called on navigation: stay if the current step belongs to the new page,
  // jump ahead to the first later step that does, pause while still on a
  // page the tour covers (same route, other query), or stop otherwise.
  function syncWithRoute() {
    const step = currentStep.value
    if (!step || matchesRoute(step)) return
    const ahead = findStep(index.value + 1, 1, matchesRoute)
    if (ahead !== -1) return setIndex(ahead)
    const routeName = router.currentRoute.value.name
    const stillOnTourPage = allSteps.value.some((s) =>
      (Array.isArray(s.route) ? s.route : s.route ? [s.route] : []).some((r) => r.name === routeName),
    )
    if (!stillOnTourPage) stop()
  }

  return {
    tourId,
    index,
    notice,
    startIndex,
    isActive,
    currentStep,
    allStepsList: allSteps,
    progress,
    holdWait,
    previousCandidates,
    goBackTo,
    context,
    isCompleted,
    start,
    stop,
    finish,
    skip,
    next,
    goTo,
    syncWithRoute,
    isOnStepPage,
  }
})

// Swap the store's functions on hot reload during development; without
// this an open tab keeps the old store and misses newly added actions.
if (import.meta.hot) {
  import.meta.hot.accept(acceptHMRUpdate(useTourStore, import.meta.hot))
}
