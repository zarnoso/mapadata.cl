import { normalizeText } from './text.js';

const excludedValparaisoPlaces = [
  'vina del mar',
  'quilpue',
  'villa alemana',
  'concon',
  'quintero',
  'puchuncavi'
];

export function isValparaisoAddress(address = '') {
  const normalized = normalizeText(address);
  if (!normalized.includes('valparaiso')) return false;
  return !excludedValparaisoPlaces.some((place) => normalized.includes(place));
}

export function canonicalCommune(value = '') {
  const normalized = normalizeText(value);
  if (normalized.includes('valparaiso')) return 'Valparaíso';
  return value || null;
}
