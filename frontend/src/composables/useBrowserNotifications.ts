import { ref } from 'vue'

const supported = typeof window !== 'undefined' && 'Notification' in window

// Whether this browser lets the app show notifications. Kept in a ref so the
// profile page updates after the user answers the browser's prompt.
const permission = ref<NotificationPermission>(supported ? Notification.permission : 'denied')

export function useBrowserNotifications() {
  function refreshPermission() {
    if (supported) permission.value = Notification.permission
  }

  async function requestPermission(): Promise<NotificationPermission> {
    if (!supported) return 'denied'
    permission.value = await Notification.requestPermission()
    return permission.value
  }

  // Shows a notification; `tag` keeps several open tabs from showing the
  // same one twice. Clicking it focuses the app and runs `onClick`.
  function show(title: string, options: { body?: string; tag?: string; onClick?: () => void } = {}) {
    refreshPermission()
    if (permission.value !== 'granted') return
    const notification = new Notification(title, {
      body: options.body,
      tag: options.tag,
      icon: '/transact_logo_dark.png',
    })
    notification.onclick = () => {
      window.focus()
      options.onClick?.()
      notification.close()
    }
  }

  return { supported, permission, refreshPermission, requestPermission, show }
}
