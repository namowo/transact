import { useOverlay } from '@nuxt/ui/composables'
import ConfirmModal from '@/components/ui/ConfirmModal.vue'

export interface ConfirmRequireOptions {
  message: string
  header?: string
  acceptLabel?: string
  rejectLabel?: string
  acceptColor?: 'primary' | 'secondary' | 'success' | 'info' | 'warning' | 'error' | 'neutral'
  accept?: () => void
  reject?: () => void
}

export function useConfirm() {
  const overlay = useOverlay()
  const modal = overlay.create(ConfirmModal)

  function require(options: ConfirmRequireOptions) {
    modal
      .open({
        title: options.header,
        message: options.message,
        confirmLabel: options.acceptLabel,
        cancelLabel: options.rejectLabel,
        confirmColor: options.acceptColor,
      })
      .result.then((confirmed) => {
        if (confirmed) {
          options.accept?.()
        } else {
          options.reject?.()
        }
      })
  }

  return { require }
}
