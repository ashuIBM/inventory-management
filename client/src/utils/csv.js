// CSV export helpers

// Spreadsheet apps execute cells starting with these as formulas
const FORMULA_PREFIX = /^[=+\-@\t\r]/

function escapeCell(value) {
  if (value === null || value === undefined) return ''
  let text = String(value)
  // Neutralise formula injection for text cells; numbers stay numeric
  if (typeof value === 'string' && FORMULA_PREFIX.test(text)) {
    text = "'" + text
  }
  if (/[",\n\r]/.test(text)) {
    text = '"' + text.replace(/"/g, '""') + '"'
  }
  return text
}

/**
 * Build CSV text from rows.
 * @param {Array<{header: string, value: (row) => any}>} columns
 * @param {Array<object>} rows
 */
export function toCsv(columns, rows) {
  const lines = [columns.map(c => escapeCell(c.header)).join(',')]
  for (const row of rows) {
    lines.push(columns.map(c => escapeCell(c.value(row))).join(','))
  }
  return lines.join('\r\n')
}

export function downloadCsv(filename, csv) {
  // BOM so Excel opens UTF-8 (e.g. Japanese headers) correctly
  const blob = new Blob(['﻿' + csv], { type: 'text/csv;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  document.body.appendChild(link)
  link.click()
  link.remove()
  URL.revokeObjectURL(url)
}
