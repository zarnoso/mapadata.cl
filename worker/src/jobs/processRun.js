import { config } from '../config.js';
import { logger } from '../logger.js';
import { mapadata } from '../supabaseAdmin.js';
import { buildFerreteriaValparaisoPlan } from '../engine/planner.js';
import { collectPlacesForQuery } from '../engine/googlePlacesAdapter.js';
import { normalizePlace } from '../engine/normalizer.js';
import { DedupeSet } from '../engine/dedupe.js';
import { scoreLead } from '../engine/quality.js';
import { rowsForExport, buildCsvBuffer } from '../engine/exportBuilder.js';

async function updateRun(runId, patch) {
  const { error } = await mapadata().from('search_runs').update(patch).eq('id', runId);
  if (error) throw error;
}

async function claimRun(runId) {
  const { data, error } = await mapadata()
    .from('search_runs')
    .update({
      status: 'running',
      worker_id: config.workerId,
      locked_at: new Date().toISOString(),
      heartbeat_at: new Date().toISOString(),
      started_at: new Date().toISOString()
    })
    .eq('id', runId)
    .in('status', ['pending', 'failed'])
    .select('*')
    .single();

  if (error) throw error;
  return data;
}

async function insertSearchQuery(runId, query) {
  await mapadata().from('search_queries').insert({
    run_id: runId,
    query,
    commune: 'Valparaíso',
    rubro: 'Ferretería',
    source: 'google_places_api'
  });
}

async function findExistingLead(lead) {
  if (lead.google_place_id) {
    const { data, error } = await mapadata()
      .from('leads')
      .select('id')
      .eq('google_place_id', lead.google_place_id)
      .limit(1);
    if (error) throw error;
    if (data && data[0]) return data[0].id;
  }
  return null;
}

async function saveLead(run, lead) {
  const existingId = await findExistingLead(lead);
  const payload = {
    user_id: run.user_id,
    run_id: run.id,
    name: lead.name,
    rut: lead.rut,
    rubro: lead.rubro,
    category: lead.category,
    commune: lead.commune,
    region: lead.region,
    address: lead.address,
    phone: lead.phone,
    email: lead.email,
    website: lead.website,
    google_place_id: lead.google_place_id,
    google_maps_uri: lead.google_maps_uri,
    business_status: lead.business_status,
    rating: lead.rating,
    user_rating_count: lead.user_rating_count,
    source: lead.source,
    source_url: lead.source_url,
    raw_json: lead.raw_json,
    confidence_score: lead.confidence_score
  };

  if (existingId) {
    const { error } = await mapadata().from('leads').update(payload).eq('id', existingId);
    if (error) throw error;
    await mapadata().from('run_leads').insert({ run_id: run.id, lead_id: existingId }).select();
    return existingId;
  }

  const { data, error } = await mapadata().from('leads').insert(payload).select('id').single();
  if (error) throw error;
  await mapadata().from('run_leads').insert({ run_id: run.id, lead_id: data.id }).select();
  return data.id;
}

async function createCsvExportRecord(run, rows) {
  const filename = `mapadata_ferreterias_valparaiso_${rows.length}_${Date.now()}.csv`;
  buildCsvBuffer(rows);

  const { data, error } = await mapadata()
    .from('exports')
    .insert({
      user_id: run.user_id,
      run_id: run.id,
      format: 'csv',
      file_name: filename,
      row_count: rows.length,
      status: 'generated_pending_storage'
    })
    .select('*')
    .single();

  if (error) throw error;
  return data;
}

export async function processRun(runId, options = {}) {
  const run = options.directRun || await claimRun(runId);
  const limit = Math.min(Number(options.limit || run.target_limit || run.limit || config.defaultLimit), config.maxLimit);
  const plan = buildFerreteriaValparaisoPlan({ limit });
  const dedupe = new DedupeSet();
  const collectedLeads = [];
  let apiCalls = 0;
  let insertedCount = 0;
  let skippedOutside = 0;

  logger.info('processing_run_started', { runId: run.id, limit });

  try {
    for (const query of plan.queries) {
      if (collectedLeads.length >= limit) break;
      await insertSearchQuery(run.id, query);

      const result = await collectPlacesForQuery({
        query,
        targetLimit: limit,
        onPage: async () => {
          await updateRun(run.id, { heartbeat_at: new Date().toISOString() });
        }
      });

      apiCalls += result.apiCalls;

      for (const place of result.places) {
        if (collectedLeads.length >= limit) break;
        const lead = normalizePlace(place, query);
        if (!lead.is_target_commune) {
          skippedOutside += 1;
          continue;
        }
        if (dedupe.has(lead)) continue;
        lead.confidence_score = scoreLead(lead);
        const leadId = await saveLead(run, lead);
        dedupe.add(lead);
        collectedLeads.push({ ...lead, id: leadId, captured_at: new Date().toISOString() });
        insertedCount += 1;
      }

      await updateRun(run.id, {
        heartbeat_at: new Date().toISOString(),
        api_calls: apiCalls,
        found_count: collectedLeads.length,
        inserted_count: insertedCount
      });
    }

    const rows = rowsForExport(collectedLeads);
    const exportRecord = await createCsvExportRecord(run, rows);
    const finalStatus = collectedLeads.length >= limit ? 'completed' : 'partial_result';

    await updateRun(run.id, {
      status: finalStatus,
      api_calls: apiCalls,
      found_count: collectedLeads.length,
      inserted_count: insertedCount,
      exported_count: rows.length,
      finished_at: new Date().toISOString(),
      error_message: null
    });

    logger.info('processing_run_completed', {
      runId: run.id,
      status: finalStatus,
      apiCalls,
      insertedCount,
      skippedOutside,
      exportId: exportRecord.id
    });

    return {
      ok: true,
      run_id: run.id,
      status: finalStatus,
      api_calls: apiCalls,
      found_count: collectedLeads.length,
      inserted_count: insertedCount,
      export_id: exportRecord.id,
      note: 'CSV buffer generated; Lovable must wire Supabase Storage upload in storageUploader helper.'
    };
  } catch (error) {
    await updateRun(run.id, {
      status: 'failed',
      error_message: error.message,
      finished_at: new Date().toISOString()
    });
    logger.error('processing_run_failed', { runId: run.id, error: error.message });
    throw error;
  }
}

if (import.meta.url === `file://${process.argv[1]}`) {
  const runId = process.argv[2];
  if (!runId) {
    console.error('Usage: node src/jobs/processRun.js <run_id>');
    process.exit(1);
  }
  processRun(runId).catch((error) => {
    console.error(error);
    process.exit(1);
  });
}
