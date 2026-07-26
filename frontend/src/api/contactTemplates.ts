import apiClient from './client'
import type { ContactTemplate, ContactTemplateInput } from './types'

export function listContactTemplates() {
  return apiClient.get<ContactTemplate[]>('/contact-templates').then((r) => r.data)
}

export function getContactTemplate(id: number) {
  return apiClient.get<ContactTemplate>(`/contact-templates/${id}`).then((r) => r.data)
}

export function createContactTemplate(payload: ContactTemplateInput) {
  return apiClient.post<ContactTemplate>('/contact-templates', payload).then((r) => r.data)
}

export function updateContactTemplate(id: number, payload: ContactTemplateInput) {
  return apiClient.patch<ContactTemplate>(`/contact-templates/${id}`, payload).then((r) => r.data)
}

export function deleteContactTemplate(id: number) {
  return apiClient.delete(`/contact-templates/${id}`)
}
