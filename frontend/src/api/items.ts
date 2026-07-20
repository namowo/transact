import apiClient from './client'
import type { Item, ItemInput } from './types'

export function listItems() {
  return apiClient.get<Item[]>('/items').then((r) => r.data)
}

export function createItem(payload: ItemInput) {
  return apiClient.post<Item>('/items', payload).then((r) => r.data)
}

export function updateItem(id: number, payload: ItemInput) {
  return apiClient.patch<Item>(`/items/${id}`, payload).then((r) => r.data)
}
