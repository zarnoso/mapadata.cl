import { cleanPhone } from '../utils/text.js';
import { isValparaisoAddress } from '../utils/chile.js';
import { inferRubroFromQuery } from './planner.js';

export function normalizePlace(place, query) {
  const name = place.displayName?.text || '';
  const address = place.formattedAddress || '';
  const category = place.primaryTypeDisplayName?.text || place.primaryType || (place.types || []).slice(0, 3).join(', ');

  return {
    name,
    rut: null,
    rubro: inferRubroFromQuery(query),
    category,
    commune: 'Valparaíso',
    region: 'Valparaíso',
    address,
    phone: cleanPhone(place.nationalPhoneNumber),
    email: null,
    website: place.websiteUri || null,
    google_place_id: place.id || null,
    google_maps_uri: place.googleMapsUri || null,
    business_status: place.businessStatus || null,
    rating: place.rating || null,
    user_rating_count: place.userRatingCount || null,
    source: 'google_places_api',
    source_url: place.googleMapsUri || null,
    raw_json: place,
    last_query: query,
    is_target_commune: isValparaisoAddress(address)
  };
}
