<script setup lang="ts">
import { computed, onBeforeUnmount, ref, shallowRef, watch } from 'vue'
import { useRoute } from 'vue-router'
import { useEventListener } from '@vueuse/core'
import { useTourStore } from '@/stores/tour'
import type { TourStep } from '@/tours'

// Renders the active interactive guide: a spotlight around the step's
// target plus a popover with the explanation. Clicks are never blocked on
// target steps, so the user can fill in the highlighted field right away.
// While another overlay (select menu, dropdown, modal) is open the guide
// steps aside, since those overlays have no z-index to stack above it.

const TARGET_TIMEOUT_MS = 2500
const SPOTLIGHT_PADDING = 6
// Room the narrow dialog card needs beside a dialog: 17rem + offset + margin.
const DIALOG_CARD_SPACE = 17 * 16 + 14 + 12

type Side = 'top' | 'right' | 'bottom' | 'left'

const tour = useTourStore()
const route = useRoute()

const step = computed(() => tour.currentStep)
const description = computed(() => {
  const value = step.value?.description
  return typeof value === 'function' ? value(tour.context()) : value
})

const targetEl = shallowRef<HTMLElement | null>(null)
const rect = ref<{ top: number; left: number; width: number; height: number } | null>(null)
const resolved = ref(false)
const otherOverlayOpen = ref(false)
// Collapsed to a small pill so it doesn't hide what the user works on.
const minimized = ref(false)
// The user started working on the page (typing, picking a value): the card
// collapses and the page isn't dimmed any more, only the ring stays.
const interacting = ref(false)
// Nearest earlier step that can be shown right now, or -1.
const previousIndex = ref(-1)
// Where to show a step that points at a whole dialog: beside it when
// there's room, otherwise docked inside it above its buttons.
const dialogPlacement = shallowRef<{ reference: HTMLElement; side: Side; docked: boolean } | null>(null)

function placeBesideDialog(dialog: HTMLElement) {
  const r = dialog.getBoundingClientRect()
  const footer = dialog.querySelector<HTMLElement>('[data-slot="footer"]')
  const next =
    window.innerWidth - r.right >= DIALOG_CARD_SPACE
      ? { reference: dialog, side: 'right' as const, docked: false }
      : r.left >= DIALOG_CARD_SPACE
        ? { reference: dialog, side: 'left' as const, docked: false }
        : { reference: footer ?? dialog, side: 'top' as const, docked: true }
  const current = dialogPlacement.value
  // Only replace it when it changes - this runs on every animation frame.
  if (current?.reference !== next.reference || current.side !== next.side) dialogPlacement.value = next
}

let searchStartedAt = 0
let foundOnce = false
let frame = 0

function isVisible(el: HTMLElement) {
  const r = el.getBoundingClientRect()
  return r.width > 0 && r.height > 0 && r.right > 0 && r.left < window.innerWidth
}

// Whether what a waiting step waits for has already happened.
function waitSatisfied(s: TourStep) {
  const wait = s.waitFor
  if (!wait) return false
  const appeared = wait.appears ? document.querySelector<HTMLElement>(wait.appears) : null
  return !!((appeared && isVisible(appeared)) || (wait.disappears && !document.querySelector(wait.disappears)))
}

// Whether a step could be shown as things are now - its dialog still open,
// its target on screen and not covered by some other dialog.
function isShowable(s: TourStep) {
  if (s.within && !document.querySelector(s.within)) return false
  if (!s.target) return !hasOtherOverlay(null)
  const el = document.querySelector<HTMLElement>(s.target)
  return !!el && isVisible(el) && !hasOtherOverlay(el)
}

function findPreviousIndex() {
  return tour.previousCandidates().find((i) => isShowable(tour.allStepsList[i]!)) ?? -1
}

// Overlays other than the guide itself and the one the step lives in.
function hasOtherOverlay(home: Element | null) {
  return Array.from(
    document.querySelectorAll('[role="dialog"], [role="alertdialog"], [role="menu"], [role="listbox"]'),
  ).some(
    (el) =>
      !el.querySelector('[data-tour-popover]') &&
      !el.closest('[data-tour-popover]') &&
      !(home && el.contains(home)) &&
      // e.g. the dashboard's mobile sidebar stays mounted but hidden
      el.checkVisibility() &&
      el.getBoundingClientRect().width > 0,
  )
}

function tick() {
  frame = 0
  const current = step.value
  if (!current) return

  // Steps that wait for the user: move on once the page has changed -
  // unless the user came back to this step after doing it already.
  if (!tour.holdWait && waitSatisfied(current)) {
    tour.next()
    return
  }

  previousIndex.value = findPreviousIndex()

  const home = current.within ? document.querySelector(current.within) : null
  if (current.within && !home) {
    // The dialog the step lives in was closed.
    if (current.onClose) tour.goTo(current.onClose)
    else tour.next()
    return
  }

  otherOverlayOpen.value = hasOtherOverlay(home)

  if (current.target) {
    const el = document.querySelector<HTMLElement>(current.target)
    if (el && isVisible(el)) {
      if (el !== targetEl.value) {
        targetEl.value = el
        if (!foundOnce) {
          const r = el.getBoundingClientRect()
          if (r.top < 0 || r.bottom > window.innerHeight) {
            el.scrollIntoView({ block: 'center', behavior: 'smooth' })
          }
        }
      }
      foundOnce = true
      if (el.getAttribute('role') === 'dialog') placeBesideDialog(el)
      else dialogPlacement.value = null
      const r = el.getBoundingClientRect()
      rect.value = { top: r.top, left: r.left, width: r.width, height: r.height }
      resolved.value = true
    } else {
      targetEl.value = null
      rect.value = null
      // Present but hidden (e.g. the desktop sidebar on a phone): show the
      // step centered right away instead of waiting for it to appear.
      if (el && !foundOnce && !current.optional) resolved.value = true
      else if (!foundOnce && performance.now() - searchStartedAt > TARGET_TIMEOUT_MS) {
        if (current.optional) {
          tour.next()
        } else {
          // Never showed up - explain it centered instead.
          resolved.value = true
        }
      }
    }
  } else {
    targetEl.value = null
    rect.value = null
    resolved.value = true
  }

  frame = requestAnimationFrame(tick)
}

watch(
  () => [tour.tourId, tour.index] as const,
  () => {
    targetEl.value = null
    rect.value = null
    resolved.value = false
    minimized.value = false
    interacting.value = false
    previousIndex.value = -1
    dialogPlacement.value = null
    foundOnce = false
    searchStartedAt = performance.now()
    if (frame) cancelAnimationFrame(frame)
    frame = tour.isActive ? requestAnimationFrame(tick) : 0
  },
  { immediate: true },
)

onBeforeUnmount(() => {
  if (frame) cancelAnimationFrame(frame)
})

watch(
  () => route.fullPath,
  () => tour.syncWithRoute(),
)

useEventListener(window, 'keydown', (event: KeyboardEvent) => {
  // Escape inside a dialog closes that dialog, not the guide.
  if (event.key === 'Escape' && tour.isActive && !hasOtherOverlay(null)) tour.skip()
})

const visible = computed(
  () => tour.isActive && tour.isOnStepPage && resolved.value && !otherOverlayOpen.value,
)
const centered = computed(() => visible.value && !targetEl.value)

// Steps without a target hang below a point in the upper third of the screen.
const centerReference = {
  getBoundingClientRect: () => {
    const x = window.innerWidth / 2
    const y = window.innerHeight * 0.3
    return new DOMRect(x, y, 0, 0)
  },
}

const reference = computed(() => dialogPlacement.value?.reference ?? targetEl.value ?? centerReference)
const side = computed<Side>(() =>
  centered.value ? 'bottom' : (dialogPlacement.value?.side ?? step.value?.side ?? 'bottom'),
)

// Once the user starts working - clicking into a field, typing, picking a
// value - the guide steps back: the card collapses to a pill and the dimming
// lifts.
const FORM_CONTROL =
  'input, textarea, select, [contenteditable="true"], [role="combobox"], [role="radio"], [role="switch"], [role="checkbox"]'

function startInteracting(target: EventTarget | null) {
  if (!tour.isActive || !(target instanceof Element) || target.closest('[data-tour-popover]')) return
  // Clicks in the highlighted area count too (e.g. "Add new persistence"),
  // except in a dialog the card sits beside rather than on top of.
  const besideDialog = dialogPlacement.value && !dialogPlacement.value.docked
  const inTarget = !besideDialog && !!targetEl.value?.contains(target)
  if (!inTarget && !target.closest(FORM_CONTROL)) return
  minimized.value = true
  interacting.value = true
}

useEventListener(document, 'pointerdown', (event: PointerEvent) => startInteracting(event.target), { capture: true })
useEventListener(document, 'input', (event: Event) => startInteracting(event.target), { capture: true })

function onBack() {
  const target = previousIndex.value
  if (target < 0) return
  // Going back to "open the tab" while it's open must not bounce forward.
  tour.goBackTo(target, waitSatisfied(tour.allStepsList[target]!))
}

const hasNext = computed(
  () => !!step.value && ((!step.value.waitForRoute && !step.value.waitFor) || !!step.value.nextClicks),
)

const spotlightStyle = computed(() => {
  if (!rect.value) return undefined
  return {
    top: `${rect.value.top - SPOTLIGHT_PADDING}px`,
    left: `${rect.value.left - SPOTLIGHT_PADDING}px`,
    width: `${rect.value.width + SPOTLIGHT_PADDING * 2}px`,
    height: `${rect.value.height + SPOTLIGHT_PADDING * 2}px`,
  }
})

const isLast = computed(() => tour.progress.current === tour.progress.total)

// Some controls react to the press rather than the click (tabs switch on
// mousedown), so replay the whole sequence a real mouse click produces.
function pressLikeAMouse(el: HTMLElement) {
  const init = { bubbles: true, cancelable: true, composed: true, button: 0, view: window }
  el.dispatchEvent(new PointerEvent('pointerdown', { ...init, pointerType: 'mouse', isPrimary: true }))
  el.dispatchEvent(new MouseEvent('mousedown', init))
  el.dispatchEvent(new PointerEvent('pointerup', { ...init, pointerType: 'mouse', isPrimary: true }))
  el.dispatchEvent(new MouseEvent('mouseup', init))
  el.click()
}

// "Next" on a step that waits for the user does the click for them (open
// the tab, press "Continue", open the dialog); the step then moves on by
// itself. A disabled button can't help, so skip past that part instead.
function onNext() {
  const current = step.value
  // Revisited a waiting step whose action is already done: just continue.
  if (current && waitSatisfied(current)) return tour.next()
  if (!current?.nextClicks) return tour.next()
  const el = document.querySelector<HTMLElement>(current.nextClicks)
  const disabled = !el || el.matches(':disabled, [aria-disabled="true"], [data-disabled]')
  if (!disabled) return pressLikeAMouse(el)
  if (current.skip) tour.goTo(current.skip.to)
  else tour.next()
}
</script>

<template>
  <Teleport to="body">
    <div
      v-if="visible && spotlightStyle"
      class="fixed z-55 rounded-lg ring-2 ring-primary pointer-events-none transition-shadow duration-300"
      :class="interacting ? '' : 'shadow-[0_0_0_9999px_rgb(0_0_0/0.4)]'"
      :style="spotlightStyle"
    />
    <div v-else-if="centered" class="fixed inset-0 z-55 bg-black/40" />
  </Teleport>

  <!-- Remounted for every step: a popover opened before a dialog ends up
       below the dialog's layer, which turns off its pointer events. -->
  <UPopover
    v-if="step"
    :key="`${tour.tourId}-${tour.index}`"
    :open="visible"
    :dismissible="false"
    :reference="reference"
    :arrow="!centered && !dialogPlacement?.docked"
    :content="{
      side,
      align: dialogPlacement?.docked ? 'end' : 'center',
      sideOffset: centered ? 0 : dialogPlacement?.docked ? 8 : 14,
      collisionPadding: 12,
      // Stay on screen even when there's no room beside a wide dialog.
      sticky: 'always',
      onOpenAutoFocus: (event: Event) => event.preventDefault(),
      onCloseAutoFocus: (event: Event) => event.preventDefault(),
    }"
    :ui="{
      content: minimized
        ? 'z-60 max-w-[calc(100vw-2rem)]'
        : step.within
          ? 'z-60 w-[min(17rem,calc(100vw-2rem))]'
          : 'z-60 w-[min(24rem,calc(100vw-2rem))]',
    }"
  >
    <template #content>
      <div
        v-if="minimized"
        data-tour-popover
        class="flex items-center gap-2 py-1.5 pl-3 pr-1.5"
        role="group"
        :aria-label="step.title"
      >
        <UIcon :name="step.icon ?? 'i-lucide-sparkles'" class="size-4 text-primary shrink-0" />
        <span class="text-sm truncate">{{ tour.notice ?? step.hint ?? step.title }}</span>
        <UButton
          v-if="hasNext"
          :label="step.nextLabel ?? (isLast ? 'Finish' : 'Next')"
          :trailing-icon="isLast ? undefined : 'i-lucide-arrow-right'"
          size="xs"
          @click="onNext"
        />
        <UButton
          icon="i-lucide-maximize-2"
          size="xs"
          color="neutral"
          variant="ghost"
          aria-label="Expand guide"
          @click="minimized = false"
        />
      </div>
      <div v-else data-tour-popover class="flex flex-col gap-3 p-4" role="group" :aria-label="step.title">
        <div class="flex items-start gap-3">
          <div class="flex items-center justify-center size-9 rounded-lg bg-primary/10 text-primary shrink-0">
            <UIcon :name="step.icon ?? 'i-lucide-sparkles'" class="size-5" />
          </div>
          <div class="flex-1 min-w-0">
            <p class="font-semibold text-highlighted">{{ step.title }}</p>
            <p class="text-sm text-muted mt-1">{{ description }}</p>
          </div>
          <div class="flex shrink-0">
            <UButton
              v-if="!centered"
              icon="i-lucide-minimize-2"
              size="xs"
              color="neutral"
              variant="ghost"
              aria-label="Collapse guide"
              @click="minimized = true"
            />
            <UButton
              icon="i-lucide-x"
              size="xs"
              color="neutral"
              variant="ghost"
              aria-label="Close guide"
              @click="tour.skip()"
            />
          </div>
        </div>

        <UAlert
          v-if="tour.notice"
          :description="tour.notice"
          icon="i-lucide-circle-alert"
          color="warning"
          variant="subtle"
          :ui="{ root: 'py-2' }"
        />
        <UAlert
          v-else-if="step.hint"
          :description="step.hint"
          icon="i-lucide-mouse-pointer-click"
          color="primary"
          variant="subtle"
          :ui="{ root: 'py-2' }"
        />

        <UProgress
          v-if="tour.progress.total > 1"
          :model-value="tour.progress.current"
          :max="tour.progress.total"
          size="xs"
        />

        <div class="flex items-center justify-between gap-2">
          <span class="text-xs text-muted">
            <template v-if="tour.progress.total > 1">{{ tour.progress.current }} of {{ tour.progress.total }}</template>
          </span>
          <div class="flex flex-wrap justify-end gap-2">
            <UButton
              v-if="tour.index === tour.startIndex && previousIndex < 0 && !isLast"
              label="Skip tour"
              color="neutral"
              variant="ghost"
              size="sm"
              @click="tour.skip()"
            />
            <UButton
              v-else
              label="Back"
              icon="i-lucide-arrow-left"
              color="neutral"
              variant="ghost"
              size="sm"
              :disabled="previousIndex < 0"
              @click="onBack"
            />
            <UButton
              v-if="step.skip"
              :label="step.skip.label"
              color="neutral"
              variant="ghost"
              size="sm"
              @click="tour.goTo(step.skip.to)"
            />
            <UButton
              v-if="hasNext"
              :label="step.nextLabel ?? (isLast ? 'Finish' : 'Next')"
              :trailing-icon="isLast || step.action ? undefined : 'i-lucide-arrow-right'"
              :color="step.action ? 'neutral' : 'primary'"
              :variant="step.action ? 'outline' : 'solid'"
              size="sm"
              @click="onNext"
            />
            <UButton
              v-if="step.action"
              :label="step.action.label"
              :icon="step.action.icon"
              size="sm"
              @click="step.action.run()"
            />
          </div>
        </div>
      </div>
    </template>
  </UPopover>
</template>
