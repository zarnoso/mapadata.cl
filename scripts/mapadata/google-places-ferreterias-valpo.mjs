import fs from 'node:fs';
import path from 'node:path';
import process from 'node:process';
import { Client } from 'pg';
import xlsx from 'xlsx';

const TARGET_LIMIT = Number(process.env.TARGET_LIMIT || process.argv[2] || 500);
const OUTPUT_DIR = process.env.OUTPUT_DIR || 'exports/mapadata';
const NEON_DATABASE_URL = process.env.NEON_DATABASE_URL;
const GOOGLE_PLACES_API_KEY = process.env.GOOGLE_PLACES_API_KEY;

if (!NEON_DATABASE_URL) {
  console.error('Missing required env: NEON_DATABASE_URL');
  process.exit(1);
}

if (!GOOGLE_PLACES_API_KEY) {
  console.error('Missing required env: GOOGLE_PLACES_API_KEY');
  process.exit(1);
}

fs.mkdirSync(OUTPUT_DIR, { recursive: true });

const QUERIES = [
  'ferretería Valparaíso Chile',
  'ferreterias Valparaiso Chile',
  'ferretería en Valparaíso',
  'tienda de herramientas Valparaíso Chile',
  'herramientas Valparaíso Chile',
  'materiales de construcción Valparaíso Chile',
  'venta materiales de construcción Valparaíso Chile',
  'pinturas ferretería Valparaíso Chile',
  'pernos Valparaíso Chile',
  'quincallería Valparaíso Chile',
  'gasfitería ferretería Valparaíso Chile',
  'electricidad ferretería Valparaíso Chile',
  'ferretería Playa Ancha Valparaíso Chile',
  'ferretería Cerro Alegre Valparaíso Chile',
  'ferretería Cerro Barón Valparaíso Chile',
  'ferretería Cerro Placeres Valparaíso Chile',
  'ferretería Cerro Cordillera Valparaíso Chile',
  'ferretería Cerro Bellavista Valparaíso Chile',
  'ferretería Cerro Cárcel Valparaíso Chile',
  'ferretería Cerro Concepción Valparaíso Chile',
  'ferretería Cerro Florida Valparaíso Chile',
  'ferretería Cerro Mariposas Valparaíso Chile',
  'ferretería Cerro Monjas Valparaíso Chile',
  'ferretería Cerro O Higgins Valparaíso Chile',
  'ferretería Cerro Polanco Valparaíso Chile',
  'ferretería Cerro Ramaditas Valparaíso Chile',
  'ferretería Cerro San Roque Valparaíso Chile',
  'ferretería Cerro Toro Valparaíso Chile',
  'ferretería Cerro Yungay Valparaíso Chile',
  'ferretería Avenida Argentina Valparaíso Chile',
  'ferretería Avenida Pedro Montt Valparaíso Chile',
  'ferretería Barrio Puerto Valparaíso Chile',
  'ferretería El Almendral Valparaíso Chile',
  'ferretería Placilla Valparaíso Chile',
  'ferretería Curauma Valparaíso Chile',
  'herramientas Placilla Valparaíso Chile',
  'materiales construcción Placilla Valparaíso Chile',
  'ferretería Camino La Pólvora Valparaíso Chile',
  'ferretería Rodelillo Valparaíso Chile',
  'ferretería Laguna Verde Valparaíso Chile'
];

const FIELD_MASK = [
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

function normalize(value = '') {
  return String(value)
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .toLowerCase()
    .trim();
}

function isValparaisoAddress(address = '') {
  const normalized = normalize(address);
  if (!normalized.includes('valparaiso')) return false;

  const excluded = [
    'vina del mar',
    'quilpue',
    'villa alemana',
    'concon',
    'quintero',
    'puchuncavi'
  ];

  return !excluded.some((place) => normalized.includes(normalize(place)));
}

function inferRubro(query) {
  const q = normalize(query);
  if (q.includes('herramient')) return 'Herramientas';
  if (q.includes('materiales')) return 'Materiales de construcción';
  if (q.includes('pintura')) return 'Pinturas';
  if (q.includes('perno')) return 'Pernos';
  if (q.includes('quincaller')) return 'Quincallería';
  if (q.includes('gasfiter')) return 'Gasfitería';
  if (q.includes('electric')) return 'Electricidad';
  return 'Ferretería';
}

function scoreLead(lead) {
  let score = 45;
  if (lead.address) score += 10;
  if (lead.phone) score += 20;
  if (lead.website) score += 15;
  if (lead.google_place_id) score += 10;
  return Math.min(score, 100);
}

async function searchPlaces(textQuery, pageToken = null) {
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
      'X-Goog-Api-Key': GOOGLE_PLACES_API_KEY,
      'X-Goog-FieldMask': FIELD_MASK
    },
    body: JSON.stringify(body)
  });

  const data = await response.json();

  if (!response.ok) {
    console.error(JSON.stringify(data, null, 2));
    throw new Error(`Google Places error: HTTP ${response.status}`);
  }

  return data;
}

async function ensureSchema(client) {
  await client.query(`
    CREATE SCHEMA IF NOT EXISTS mapadata;

    CREATE TABLE IF NOT EXISTS mapadata.leads (
      id BIGSERIAL PRIMARY KEY,
      name TEXT NOT NULL,
      rut TEXT NULL,
      rubro TEXT NULL,
      category TEXT NULL,
      commune TEXT NOT NULL DEFAULT 'Valparaíso',
      region TEXT NOT NULL DEFAULT 'Valparaíso',
      address TEXT NULL,
      phone TEXT NULL,
      email TEXT NULL,
      website TEXT NULL,
      google_place_id TEXT NULL,
      google_maps_uri TEXT NULL,
      business_status TEXT NULL,
      rating NUMERIC(3,2) NULL,
      user_rating_count INTEGER NULL,
      source TEXT NOT NULL DEFAULT 'google_places_api',
      source_url TEXT NULL,
      last_query TEXT NULL,
      raw_json JSONB NULL,
      confidence_score INTEGER DEFAULT 50,
      captured_at TIMESTAMPTZ DEFAULT now(),
      updated_at TIMESTAMPTZ DEFAULT now()
    );

    CREATE UNIQUE INDEX IF NOT EXISTS uniq_mapadata_google_place_id
    ON mapadata.leads (google_place_id)
    WHERE google_place_id IS NOT NULL;

    CREATE INDEX IF NOT EXISTS idx_mapadata_commune_rubro
    ON mapadata.leads (commune, rubro);

    CREATE TABLE IF NOT EXISTS mapadata.exports (
      id BIGSERIAL PRIMARY KEY,
      export_name TEXT NOT NULL,
      commune TEXT NOT NULL,
      rubro TEXT NOT NULL,
      requested_limit INTEGER NOT NULL,
      exported_count INTEGER DEFAULT 0,
      file_csv TEXT NULL,
      file_xlsx TEXT NULL,
      created_at TIMESTAMPTZ DEFAULT now()
    );

    CREATE TABLE IF NOT EXISTS mapadata.search_runs (
      id BIGSERIAL PRIMARY KEY,
      run_name TEXT NOT NULL,
      target_rubro TEXT NOT NULL,
      target_commune TEXT NOT NULL,
      target_limit INTEGER NOT NULL DEFAULT 500,
      source TEXT NOT NULL DEFAULT 'google_places_api',
      status TEXT NOT NULL DEFAULT 'pending',
      api_calls INTEGER DEFAULT 0,
      found_count INTEGER DEFAULT 0,
      inserted_count INTEGER DEFAULT 0,
      exported_count INTEGER DEFAULT 0,
      error_message TEXT NULL,
      started_at TIMESTAMPTZ DEFAULT now(),
      finished_at TIMESTAMPTZ NULL
    );
  `);
}

async function createRun(client) {
  const result = await client.query(
    `INSERT INTO mapadata.search_runs
      (run_name, target_rubro, target_commune, target_limit, status)
     VALUES ($1, $2, $3, $4, 'running')
     RETURNING id`,
    [
      `ferreterias_valparaiso_${new Date().toISOString()}`,
      'Ferretería / relacionados',
      'Valparaíso',
      TARGET_LIMIT
    ]
  );
  return result.rows[0].id;
}

async function upsertLead(client, lead) {
  await client.query(
    `INSERT INTO mapadata.leads (
      name,
      rut,
      rubro,
      category,
      commune,
      region,
      address,
      phone,
      email,
      website,
      google_place_id,
      google_maps_uri,
      business_status,
      rating,
      user_rating_count,
      source,
      source_url,
      last_query,
      raw_json,
      confidence_score
    ) VALUES (
      $1, $2, $3, $4, $5, $6, $7, $8, $9, $10,
      $11, $12, $13, $14, $15, $16, $17, $18, $19, $20
    )
    ON CONFLICT (google_place_id) WHERE google_place_id IS NOT NULL
    DO UPDATE SET
      name = EXCLUDED.name,
      rubro = EXCLUDED.rubro,
      category = EXCLUDED.category,
      commune = EXCLUDED.commune,
      region = EXCLUDED.region,
      address = EXCLUDED.address,
      phone = EXCLUDED.phone,
      website = EXCLUDED.website,
      google_maps_uri = EXCLUDED.google_maps_uri,
      business_status = EXCLUDED.business_status,
      rating = EXCLUDED.rating,
      user_rating_count = EXCLUDED.user_rating_count,
      source = EXCLUDED.source,
      source_url = EXCLUDED.source_url,
      last_query = EXCLUDED.last_query,
      raw_json = EXCLUDED.raw_json,
      confidence_score = EXCLUDED.confidence_score,
      updated_at = now()`,
    [
      lead.name,
      lead.rut,
      lead.rubro,
      lead.category,
      lead.commune,
      lead.region,
      lead.address,
      lead.phone,
      lead.email,
      lead.website,
      lead.google_place_id,
      lead.google_maps_uri,
      lead.business_status,
      lead.rating,
      lead.user_rating_count,
      lead.source,
      lead.source_url,
      lead.last_query,
      JSON.stringify(lead.raw_json),
      lead.confidence_score
    ]
  );
}

async function fetchExportRows(client) {
  const result = await client.query(
    `SELECT
      id,
      name AS nombre,
      rut,
      rubro,
      category AS categoria,
      commune AS comuna,
      region,
      address AS direccion,
      phone AS telefono,
      email,
      website AS sitio_web,
      google_maps_uri,
      rating AS rating_google,
      user_rating_count AS cantidad_resenas,
      source AS fuente,
      source_url AS fuente_url,
      confidence_score AS score_dato,
      captured_at AS fecha_captura
    FROM mapadata.leads
    WHERE translate(lower(coalesce(commune, '')), 'áéíóúüñ', 'aeiouun') = 'valparaiso'
    ORDER BY confidence_score DESC, name ASC
    LIMIT $1`,
    [TARGET_LIMIT]
  );
  return result.rows;
}

async function exportFiles(rows, client) {
  const stamp = new Date().toISOString().replace(/[-:]/g, '').replace(/\.\d{3}Z$/, 'Z').replace('T', '_');
  const baseName = `mapadata_ferreterias_valparaiso_${TARGET_LIMIT}_${stamp}`;
  const xlsxPath = path.join(OUTPUT_DIR, `${baseName}.xlsx`);
  const csvPath = path.join(OUTPUT_DIR, `${baseName}.csv`);
  const latestXlsx = path.join(OUTPUT_DIR, `mapadata_ferreterias_valparaiso_${TARGET_LIMIT}_latest.xlsx`);
  const latestCsv = path.join(OUTPUT_DIR, `mapadata_ferreterias_valparaiso_${TARGET_LIMIT}_latest.csv`);

  const workbook = xlsx.utils.book_new();
  const worksheet = xlsx.utils.json_to_sheet(rows);
  xlsx.utils.book_append_sheet(workbook, worksheet, 'Ferreterias Valparaiso');
  xlsx.writeFile(workbook, xlsxPath);
  xlsx.writeFile(workbook, csvPath, { bookType: 'csv' });
  fs.copyFileSync(xlsxPath, latestXlsx);
  fs.copyFileSync(csvPath, latestCsv);

  await client.query(
    `INSERT INTO mapadata.exports
      (export_name, commune, rubro, requested_limit, exported_count, file_csv, file_xlsx)
     VALUES ($1, $2, $3, $4, $5, $6, $7)`,
    [
      baseName,
      'Valparaíso',
      'Ferretería / relacionados',
      TARGET_LIMIT,
      rows.length,
      csvPath,
      xlsxPath
    ]
  );

  return { xlsxPath, csvPath, latestXlsx, latestCsv };
}

async function main() {
  const client = new Client({ connectionString: NEON_DATABASE_URL });
  await client.connect();

  let runId = null;
  let apiCalls = 0;
  let inserted = 0;
  let outside = 0;
  const seen = new Set();

  try {
    await ensureSchema(client);
    runId = await createRun(client);

    console.log(`Run ID: ${runId}`);
    console.log(`Target limit: ${TARGET_LIMIT}`);
    console.log(`Queries: ${QUERIES.length}`);

    for (const query of QUERIES) {
      if (seen.size >= TARGET_LIMIT) break;
      console.log(`\nSearching: ${query}`);

      let pageToken = null;
      let page = 1;

      do {
        if (pageToken) await sleep(2500);
        const data = await searchPlaces(query, pageToken);
        apiCalls++;

        const places = data.places || [];
        console.log(`Page ${page}: ${places.length} results`);

        for (const place of places) {
          if (seen.size >= TARGET_LIMIT) break;

          const placeId = place.id;
          const name = place.displayName?.text || '';
          const address = place.formattedAddress || '';

          if (!placeId || !name) continue;
          if (seen.has(placeId)) continue;

          if (!isValparaisoAddress(address)) {
            outside++;
            continue;
          }

          const category = place.primaryTypeDisplayName?.text || place.primaryType || (place.types || []).slice(0, 3).join(', ');
          const lead = {
            name,
            rut: null,
            rubro: inferRubro(query),
            category,
            commune: 'Valparaíso',
            region: 'Valparaíso',
            address,
            phone: place.nationalPhoneNumber || null,
            email: null,
            website: place.websiteUri || null,
            google_place_id: placeId,
            google_maps_uri: place.googleMapsUri || null,
            business_status: place.businessStatus || null,
            rating: place.rating || null,
            user_rating_count: place.userRatingCount || null,
            source: 'google_places_api',
            source_url: place.googleMapsUri || null,
            last_query: query,
            raw_json: place
          };
          lead.confidence_score = scoreLead(lead);

          await upsertLead(client, lead);
          seen.add(placeId);
          inserted++;
          console.log(`OK ${seen.size}/${TARGET_LIMIT}: ${name}`);
        }

        pageToken = data.nextPageToken || null;
        page++;
      } while (pageToken && seen.size < TARGET_LIMIT);
    }

    const rows = await fetchExportRows(client);
    const files = await exportFiles(rows, client);

    await client.query(
      `UPDATE mapadata.search_runs
       SET status = 'completed', api_calls = $1, found_count = $2, inserted_count = $3, exported_count = $4, finished_at = now()
       WHERE id = $5`,
      [apiCalls, seen.size, inserted, rows.length, runId]
    );

    console.log('\n=== MAPADATA SUMMARY ===');
    console.log(`API calls: ${apiCalls}`);
    console.log(`Detected unique places: ${seen.size}`);
    console.log(`Inserted or updated: ${inserted}`);
    console.log(`Skipped outside Valparaiso: ${outside}`);
    console.log(`Exported rows: ${rows.length}`);
    console.log(`XLSX: ${files.latestXlsx}`);
    console.log(`CSV: ${files.latestCsv}`);

    if (rows.length < TARGET_LIMIT) {
      console.log(`NOTICE: Export has fewer than ${TARGET_LIMIT} rows. This usually means the source did not return enough unique Valparaiso businesses for this niche.`);
    }
  } catch (error) {
    if (runId) {
      await client.query(
        `UPDATE mapadata.search_runs
         SET status = 'failed', api_calls = $1, found_count = $2, inserted_count = $3, error_message = $4, finished_at = now()
         WHERE id = $5`,
        [apiCalls, seen.size, inserted, error.message, runId]
      );
    }
    throw error;
  } finally {
    await client.end();
  }
}

main().catch((error) => {
  console.error('Fatal error:', error);
  process.exit(1);
});
