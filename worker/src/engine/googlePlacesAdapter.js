import { config } from '../config.js';

const BASIC_FIELD_MASK = [
  'places.id',
  'places.displayName',
  'places.formattedAddress',
  'places.googleMapsUri',
  'places.types',
  'places.primaryType',
  'places.primaryTypeDisplayName',
  'nextPageToken'
].join(',');

const ENRICHED_FIELD_MASK = [
  'places.id',
  'places.displayName',
  'places.formattedAddress',
  'places.nationalPhoneNumber',
  'places.websiteUri',
  'places.businessStatus',
  'places.googleMapsUri',
  'places.types',
  'places.primaryType',
  'places.primaryTypeDisplayName',
  'places.rating',
  'places.userRatingCount',
  'nextPageToken'
].join(',');

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

export function getFieldMask() {
  return config.placesMode === 'enriched' ? ENRICHED_FIELD_MASK : BASIC_FIELD_MASK;
}

export async function searchText({ textQuery, pageToken = null }) {
  const body = {
    textQuery,
    languageCode: 'es',
    regionCode: 'CL',
    maxResultCount: 20
  };

  if (pageToken) body.pageToken = pageToken;

  const response = await fetch('https://places.googleapis.com/v1/places:searchText', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-Goog-Api-Key': config.googlePlacesApiKey,
      'X-Goog-FieldMask': getFieldMask()
    },
    body: JSON.stringify(body)
  });

  const data = await response.json();

  if (!response.ok) {
    throw new Error(`Google Places error ${response.status}: ${JSON.stringify(data)}`);
  }

  return data;
}

export async function collectPlacesForQuery({ query, targetLimit, onPage }) {
  let pageToken = null;
  let page = 1;
  let apiCalls = 0;
  const places = [];

  do {
    if (pageToken) await sleep(2500);
    const data = await searchText({ textQuery: query, pageToken });
    apiCalls += 1;

    const pagePlaces = data.places || [];
    places.push(...pagePlaces);

    if (onPage) {
      await onPage({ query, page, count: pagePlaces.length, apiCalls });
    }

    pageToken = data.nextPageToken || null;
    page += 1;
  } while (pageToken && places.length < targetLimit);

  return { places, apiCalls };
}
