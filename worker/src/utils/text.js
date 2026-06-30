export function normalizeText(value = '') {
  return String(value)
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .toLowerCase()
    .trim();
}

export function cleanPhone(value = '') {
  const raw = String(value || '').trim();
  return raw || null;
}

export function slug(value = '') {
  return normalizeText(value).split(' ').filter(Boolean).join('-');
}
