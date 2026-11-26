import { computed, ref } from 'vue'

// Number of API requests and route navigations in flight. Drives the
// progress bar under the dashboard header.
const pending = ref(0)

export const isGlobalLoading = computed(() => pending.value > 0)

/** Marks one unit of work as started; call the returned function when it ends. */
export function startGlobalLoading(): () => void {
  pending.value++
  let done = false
  return () => {
    if (done) return
    done = true
    pending.value = Math.max(0, pending.value - 1)
  }
}
