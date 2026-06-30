import { config } from '../config.js';
import { logger } from '../logger.js';
import { mapadata } from '../supabaseAdmin.js';
import { processRun } from './processRun.js';

export async function pollPendingRuns({ limit = config.pollBatchSize } = {}) {
  const { data, error } = await mapadata()
    .from('search_runs')
    .select('*')
    .eq('status', 'pending')
    .order('created_at', { ascending: true })
    .limit(limit);

  if (error) throw error;

  const results = [];
  for (const run of data || []) {
    try {
      const result = await processRun(run.id);
      results.push(result);
    } catch (error) {
      logger.error('poll_run_failed', { runId: run.id, error: error.message });
      results.push({ ok: false, run_id: run.id, error: error.message });
    }
  }

  return { ok: true, count: results.length, results };
}

if (import.meta.url === `file://${process.argv[1]}`) {
  pollPendingRuns().then((result) => {
    console.log(JSON.stringify(result, null, 2));
  }).catch((error) => {
    console.error(error);
    process.exit(1);
  });
}
