function csvCell(value) {
  if (value === null || value === undefined) return '';
  const text = String(value).replace(/\r?\n/g, ' ');
  const escaped = text.split('"').join('""');
  return `"${escaped}"`;
}

export function toCsv(rows) {
  if (!rows.length) return '';
  const headers = Object.keys(rows[0]);
  const lines = [headers.map(csvCell).join(',')];
  for (const row of rows) {
    lines.push(headers.map((header) => csvCell(row[header])).join(','));
  }
  return lines.join('\n');
}
