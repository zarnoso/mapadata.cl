import { toCsv } from '../utils/csv.js';

export function rowsForExport(leads) {
  return leads.map((lead) => ({
    nombre: lead.name,
    rut: lead.rut,
    rubro: lead.rubro,
    categoria: lead.category,
    comuna: lead.commune,
    region: lead.region,
    direccion: lead.address,
    telefono: lead.phone,
    email: lead.email,
    sitio_web: lead.website,
    google_maps_uri: lead.google_maps_uri,
    rating_google: lead.rating,
    cantidad_resenas: lead.user_rating_count,
    fuente: lead.source,
    fuente_url: lead.source_url,
    score_dato: lead.confidence_score,
    fecha_captura: lead.captured_at || new Date().toISOString()
  }));
}

export function buildCsvBuffer(rows) {
  return Buffer.from(toCsv(rows), 'utf8');
}
