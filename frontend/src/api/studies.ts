import apiClient from './client'
import { filenameFrom, saveBlob, unwrapBlobError } from './download'
import type { Study, StudyCreate, StudyUpdate } from './types'

export function listStudies() {
  return apiClient.get<Study[]>('/studies').then((r) => r.data)
}

export function getStudy(id: string) {
  return apiClient.get<Study>(`/studies/${id}`).then((r) => r.data)
}

export function createStudy(payload: StudyCreate) {
  return apiClient.post<Study>('/studies', payload).then((r) => r.data)
}

export function updateStudy(id: string, payload: StudyUpdate) {
  return apiClient.patch<Study>(`/studies/${id}`, payload).then((r) => r.data)
}

export function passQualityCheck(id: string) {
  return apiClient.post<Study>(`/studies/${id}/quality-check`).then((r) => r.data)
}

export function deleteStudy(id: string) {
  return apiClient.delete<void>(`/studies/${id}`).then((r) => r.data)
}

export interface PlanningSheetImport {
  individuals_created: number
  individuals_updated: number
  items_created: number
  items_updated: number
  categories_created: number
  subcategories_created: number
}

/** What the user has to decide before a planning sheet is saved. */
export interface PlanningSheetConfirmation {
  /** Item categories/subcategories the sheet would add to the shared catalog. */
  new_categories: string[]
  new_subcategories: { category: string; name: string }[]
  /** Rows without a scenario - e.g. filled in before scenarios were planned. */
  unassigned_individuals: number
  unassigned_items: number
}

export interface PlanningSheetUploadOptions {
  /** Create the new item categories/subcategories. */
  createCategories?: boolean
  /** Scenarios for the rows that have none. */
  scenarioIds?: string[]
}

/** The planning checklist as .xlsx, with sheets to plan individuals and items. */
export async function downloadPlanningSheet(id: string, studyTitle?: string | null) {
  const response = await apiClient
    .get<Blob>(`/studies/${id}/planning-sheet`, { responseType: 'blob' })
    .catch(unwrapBlobError)
  saveBlob(
    response.data,
    filenameFrom(
      response.headers['content-disposition'],
      `${(studyTitle?.trim() || 'study').replace(/\s+/g, '_')}_planning_checklist.xlsx`,
    ),
  )
}

/** Creates/updates the study's individuals and items from a filled-in planning sheet. */
export function uploadPlanningSheet(id: string, file: File, options: PlanningSheetUploadOptions = {}) {
  return apiClient
    .post<PlanningSheetImport>(`/studies/${id}/planning-sheet`, file, {
      headers: { 'Content-Type': 'application/octet-stream' },
      params: {
        create_categories: options.createCategories || undefined,
        scenario_ids: options.scenarioIds?.length ? options.scenarioIds : undefined,
      },
      // scenario_ids=a&scenario_ids=b, as FastAPI expects (not scenario_ids[]=a).
      paramsSerializer: { indexes: null },
    })
    .then((r) => r.data)
}

/** The per-row problems of a rejected planning sheet, if that's what the error is. */
export function planningSheetErrors(err: unknown): string[] {
  const detail = (err as { response?: { data?: { detail?: unknown } } })?.response?.data?.detail
  if (detail && typeof detail === 'object' && Array.isArray((detail as { errors?: unknown }).errors)) {
    return (detail as { errors: string[] }).errors
  }
  return []
}

export interface ChecklistItem {
  /** Stable id - a study's ticks and notes refer to it. New items leave it out; the server assigns one. */
  id?: string
  text: string
}

export interface ChecklistSection {
  title: string
  items: ChecklistItem[]
}

/** What a study has ticked off its planning checklist, and its notes per item id. */
export interface PlanningChecklistProgress {
  checked: string[]
  notes: Record<string, string>
}

export interface PlanningChecklist extends PlanningChecklistProgress {
  laboratory_id: string | null
  sections: ChecklistSection[]
  /** True while the laboratory hasn't saved its own checklist. */
  is_default: boolean
  /** Whether the current user (a lab admin of the study's laboratory) may edit it. */
  can_edit: boolean
  /** Whether the current user (a member of the study's laboratory) may tick items off. */
  can_check: boolean
}

/** The planning checklist of the study's laboratory, or the default one. */
export function getPlanningChecklist(studyId: string) {
  return apiClient.get<PlanningChecklist>(`/studies/${studyId}/planning-checklist`).then((r) => r.data)
}

/** Replaces the laboratory's planning checklist (lab admins only). */
export function savePlanningChecklist(laboratoryId: string, sections: ChecklistSection[]) {
  return apiClient
    .put<PlanningChecklist>(`/laboratories/${laboratoryId}/planning-checklist`, { sections })
    .then((r) => r.data)
}

/** Goes back to the default planning checklist (lab admins only). */
export function resetPlanningChecklist(laboratoryId: string) {
  return apiClient
    .delete<PlanningChecklist>(`/laboratories/${laboratoryId}/planning-checklist`)
    .then((r) => r.data)
}

/** Saves which checklist items the study has ticked off, and its notes. */
export function savePlanningChecklistProgress(studyId: string, progress: PlanningChecklistProgress) {
  return apiClient
    .put<PlanningChecklistProgress>(`/studies/${studyId}/planning-checklist/progress`, progress)
    .then((r) => r.data)
}

/** What a rejected upload asks the user to decide, if that's what the error is. */
export function planningSheetConfirmation(err: unknown): PlanningSheetConfirmation | null {
  const response = (err as { response?: { status?: number; data?: { detail?: unknown } } })?.response
  const detail = response?.data?.detail as Partial<PlanningSheetConfirmation> | undefined
  if (response?.status !== 409 || !detail || !Array.isArray(detail.new_categories)) return null
  return {
    new_categories: detail.new_categories,
    new_subcategories: detail.new_subcategories ?? [],
    unassigned_individuals: detail.unassigned_individuals ?? 0,
    unassigned_items: detail.unassigned_items ?? 0,
  }
}
