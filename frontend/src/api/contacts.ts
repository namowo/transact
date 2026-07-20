import apiClient from './client'
import type {
  Contact,
  ContactInput,
  ConditionDuringContact,
  ConditionDuringContactInput,
} from './types'

export function createContact(payload: ContactInput) {
  return apiClient.post<Contact>('/contacts', payload).then((r) => r.data)
}

export function updateContact(id: number, payload: ContactInput) {
  return apiClient.patch<Contact>(`/contacts/${id}`, payload).then((r) => r.data)
}

export function deleteContact(id: number) {
  return apiClient.delete(`/contacts/${id}`)
}

export function createConditionDuringContact(payload: ConditionDuringContactInput) {
  return apiClient
    .post<ConditionDuringContact>('/conditions-during-contact', payload)
    .then((r) => r.data)
}

export function updateConditionDuringContact(id: number, payload: ConditionDuringContactInput) {
  return apiClient
    .patch<ConditionDuringContact>(`/conditions-during-contact/${id}`, payload)
    .then((r) => r.data)
}
