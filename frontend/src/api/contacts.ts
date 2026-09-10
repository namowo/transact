import apiClient from './client'
import type {
  Contact,
  ContactInput,
  ConditionDuringContact,
  ConditionDuringContactInput,
} from './types'

export function listContacts() {
  return apiClient.get<Contact[]>('/contacts').then((r) => r.data)
}

export function getContact(id: string) {
  return apiClient.get<Contact>(`/contacts/${id}`).then((r) => r.data)
}

export function createContact(payload: ContactInput) {
  return apiClient.post<Contact>('/contacts', payload).then((r) => r.data)
}

export function updateContact(id: string, payload: ContactInput) {
  return apiClient.patch<Contact>(`/contacts/${id}`, payload).then((r) => r.data)
}

export function deleteContact(id: string) {
  return apiClient.delete(`/contacts/${id}`)
}

export function createConditionDuringContact(payload: ConditionDuringContactInput) {
  return apiClient
    .post<ConditionDuringContact>('/conditions-during-contact', payload)
    .then((r) => r.data)
}

export function updateConditionDuringContact(id: string, payload: ConditionDuringContactInput) {
  return apiClient
    .patch<ConditionDuringContact>(`/conditions-during-contact/${id}`, payload)
    .then((r) => r.data)
}
