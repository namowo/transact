import { computed, type Ref, type WritableComputedRef } from 'vue'

// Fields like humidity are stored as a 0-1 decimal fraction, but edited and
// displayed as a whole percentage (0.65 <-> 65).
export function usePercentModel(decimal: Ref<number | null>): WritableComputedRef<number | null> {
  return computed({
    get: () => (decimal.value == null ? null : decimal.value * 100),
    set: (percent) => {
      decimal.value = percent == null ? null : percent / 100
    },
  })
}

export function formatPercent(value: number): string {
  return new Intl.NumberFormat(undefined, { style: 'percent' }).format(value)
}
