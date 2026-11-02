// Minimal CSV helpers for round-tripping tables through a spreadsheet.

export function toCsv(rows: (string | number | null | undefined)[][], delimiter = ','): string {
  const escape = (value: string | number | null | undefined) => {
    const text = value == null ? '' : String(value)
    return /["\n\r]/.test(text) || text.includes(delimiter) ? `"${text.replace(/"/g, '""')}"` : text
  }
  return rows.map((row) => row.map(escape).join(delimiter)).join('\r\n')
}

// Parses CSV text with quoted fields. The delimiter (',' or ';' - German
// spreadsheets write ';') is detected from the header line.
export function parseCsv(text: string): string[][] {
  const source = text.replace(/^\uFEFF/, '')
  const firstLine = source.split(/\r?\n/, 1)[0] ?? ''
  const delimiter =
    (firstLine.match(/;/g)?.length ?? 0) > (firstLine.match(/,/g)?.length ?? 0) ? ';' : ','

  const rows: string[][] = []
  let row: string[] = []
  let field = ''
  let quoted = false
  for (let i = 0; i < source.length; i++) {
    const char = source[i]
    if (quoted) {
      if (char === '"' && source[i + 1] === '"') {
        field += '"'
        i++
      } else if (char === '"') {
        quoted = false
      } else {
        field += char
      }
    } else if (char === '"') {
      quoted = true
    } else if (char === delimiter) {
      row.push(field)
      field = ''
    } else if (char === '\n' || char === '\r') {
      if (char === '\r' && source[i + 1] === '\n') i++
      row.push(field)
      rows.push(row)
      row = []
      field = ''
    } else {
      field += char
    }
  }
  if (field !== '' || row.length) {
    row.push(field)
    rows.push(row)
  }
  return rows.filter((r) => r.some((cell) => cell.trim() !== ''))
}

export type DecimalSeparator = '.' | ','

// Parses a number; null for empty, NaN for anything unparsable. A lone point or
// comma is read as the decimal separator whichever style was chosen, because
// spreadsheets often mix both in one file. The chosen style only matters when a
// number has both, e.g. "1.234,5": there the other character is a thousands mark.
export function parseNumber(value: string, decimal: DecimalSeparator = '.'): number | null {
  // Drop whitespace, quotes and invisible characters (BOM, zero-width spaces) that spreadsheets add.
  let cleaned = value.replace(/[\s\u00A0\u202F\u200B-\u200D\u2060\uFEFF"'`]/g, '')
  if (cleaned === '') return null
  const thousands = decimal === '.' ? ',' : '.'
  if (cleaned.includes('.') && cleaned.includes(',')) {
    if (cleaned.lastIndexOf(decimal) < cleaned.indexOf(thousands)) return Number.NaN
    cleaned = cleaned.split(thousands).join('')
  }
  if (cleaned.split(',').length > 2 || cleaned.split('.').length > 2) return Number.NaN
  const normalized = cleaned.replace(',', '.')
  return /^[+-]?(\d+\.?\d*|\.\d+)(e[+-]?\d+)?$/i.test(normalized) ? Number(normalized) : Number.NaN
}

export function downloadTextFile(filename: string, content: string, mime = 'text/csv') {
  // The BOM makes Excel read the file as UTF-8 (µ, umlauts).
  const blob = new Blob(['\uFEFF', content], { type: `${mime};charset=utf-8` })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  document.body.appendChild(link)
  link.click()
  link.remove()
  URL.revokeObjectURL(url)
}
