import { ref, watch } from 'vue'
import { defineStore } from 'pinia'

const STORAGE_KEY = 'transact-sidebar-open'

function getInitialSidebarOpen() {
  const stored = localStorage.getItem(STORAGE_KEY)
  return stored === null ? true : stored === 'true'
}

export const useUiStore = defineStore('ui', () => {
  const sidebarOpen = ref(getInitialSidebarOpen())

  watch(sidebarOpen, (value) => {
    localStorage.setItem(STORAGE_KEY, String(value))
  })

  function toggleSidebar() {
    sidebarOpen.value = !sidebarOpen.value
  }

  return { sidebarOpen, toggleSidebar }
})
