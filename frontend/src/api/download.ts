// Helpers for file downloads via axios (responseType: 'blob').

// Prefers `filename*` (UTF-8, keeps umlauts in study titles) over the
// ASCII-only `filename`.
export function filenameFrom(disposition: string | undefined, fallback: string) {
  const encoded = disposition?.match(/filename\*=UTF-8''([^;]+)/i)?.[1]
  if (encoded) {
    try {
      return decodeURIComponent(encoded)
    } catch {
      // Malformed - fall through to the plain filename.
    }
  }
  const match = disposition?.match(/filename="?([^";]+)"?/)
  return match?.[1] ?? fallback
}

export function saveBlob(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  document.body.appendChild(link)
  link.click()
  link.remove()
  setTimeout(() => URL.revokeObjectURL(url), 1000)
}

// Error bodies of blob requests arrive as Blobs too; turn them back into
// JSON so getErrorMessage() can read `detail`.
export async function unwrapBlobError(err: unknown): Promise<never> {
  const data = (err as { response?: { data?: unknown } })?.response?.data
  if (data instanceof Blob) {
    try {
      ;(err as { response: { data: unknown } }).response.data = JSON.parse(await data.text())
    } catch {
      // Leave the original error as is.
    }
  }
  throw err
}
