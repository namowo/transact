import type { RouteLocationNormalizedLoaded } from 'vue-router'
import type { useAuthStore } from '@/stores/auth'

// Interactive guides; must match the ids the backend accepts for
// POST /users/me/completed-tours/{tour}.
export type TourId = 'onboarding' | 'new-study' | 'data-entry'

export interface TourContext {
  auth: ReturnType<typeof useAuthStore>
  route: RouteLocationNormalizedLoaded
  // Name of the page the guide was started on.
  startRoute: string | null
}

export interface TourStepRoute {
  name: string
  // Query values the route must have too, e.g. { step: 'planning' }.
  query?: Record<string, string>
}

export interface TourStep {
  id: string
  title: string
  description: string | ((ctx: TourContext) => string)
  icon?: string
  // CSS selector of the element to highlight. Without one (or when it can't
  // be found) the step is shown centered on the screen.
  target?: string
  side?: 'top' | 'right' | 'bottom' | 'left'
  // Page(s) the step belongs to. Steps without a route show on any page.
  route?: TourStepRoute | TourStepRoute[]
  // Leave the step out when this returns false (e.g. admin-only areas).
  when?: (ctx: TourContext) => boolean
  // Page on which `when` is decided (default: the step's own route); the
  // result is kept for the rest of the tour, e.g. the study purpose read
  // from the form's query still applies on the planning page.
  whenRoute?: TourStepRoute | TourStepRoute[]
  // Skip the step instead of centering it when its target doesn't show up.
  optional?: boolean
  // The step waits for the user to act (e.g. submit a form) instead of
  // showing a "Next" button; the tour moves on once a later step's route is
  // reached.
  waitForRoute?: boolean
  // The step waits for the user to act on the page (e.g. open a dialog or
  // click "Continue" in it) and moves on once an element appears or
  // disappears. Like waitForRoute, it hides the "Next" button.
  waitFor?: { appears?: string; disappears?: string }
  // Lets the user skip ahead on a waiting step: "Next" clicks this element
  // for them (a tab, a dialog's "Continue", the button opening a dialog).
  // If it's disabled, "Next" jumps to `skip.to` (or the next step) instead.
  nextClicks?: string
  // Container the step lives in, e.g. a dialog. While it's open the guide
  // stays visible on top of it; if it closes, the guide goes to `onClose`.
  within?: string
  onClose?: string
  // A secondary button that jumps ahead, e.g. past the steps of a dialog
  // the user doesn't want to open right now.
  skip?: { label: string; to: string }
  // Tells the user what to do on an interactive step.
  hint?: string
  nextLabel?: string
  // An extra primary button, e.g. "Add a study" on the last onboarding step.
  action?: { label: string; icon?: string; run: () => void }
}

export interface TourDefinition {
  id: TourId
  steps: TourStep[]
}
