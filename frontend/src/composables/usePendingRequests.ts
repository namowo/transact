import { computed, ref } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { listPendingForMyLab, listPendingNewLabs } from '@/api/labMembershipRequests'
import type { LabMembershipRequest } from '@/api/types'

const labRequests = ref<LabMembershipRequest[]>([])
const newLabRequests = ref<LabMembershipRequest[]>([])
const loaded = ref(false)

export function usePendingRequests() {
  const auth = useAuthStore()

  async function load() {
    const [labResult, newLabResult] = await Promise.all([
      auth.isLabAdmin ? listPendingForMyLab().catch(() => []) : Promise.resolve([]),
      auth.isSuperuser ? listPendingNewLabs().catch(() => []) : Promise.resolve([]),
    ])
    labRequests.value = labResult
    newLabRequests.value = newLabResult
    loaded.value = true
  }

  const labRequestCount = computed(() => labRequests.value.length)
  const newLabRequestCount = computed(() => newLabRequests.value.length)
  const totalCount = computed(() => labRequestCount.value + newLabRequestCount.value)

  return { labRequests, newLabRequests, labRequestCount, newLabRequestCount, totalCount, loaded, load }
}
