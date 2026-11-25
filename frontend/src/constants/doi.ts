import * as yup from 'yup'

// Shared DOI rules, so every DOI field (studies, shedding propensity
// references, ...) accepts and stores DOIs the same way: a pasted
// https://doi.org/ or "doi:" prefix is stripped and the rest must look like
// 10.1234/abc.
const DOI_PREFIX = /^(?:https?:\/\/(?:dx\.)?doi\.org\/|doi:\s*)/i
const DOI_PATTERN = /^10\.\d{4,9}\/\S+$/

export const normalizeDoi = (value: string) => value.trim().replace(DOI_PREFIX, '')

// Optional DOI field: empty is fine, anything else must be a valid DOI.
export function doiSchema() {
  return yup
    .string()
    .trim()
    .transform((value) => (typeof value === 'string' ? normalizeDoi(value) : value))
    .defined()
    .test(
      'doi-format',
      'Invalid DOI. Expected format: 10.1234/abc (a https://doi.org/ prefix is removed automatically).',
      (value) => !value || DOI_PATTERN.test(value),
    )
}
