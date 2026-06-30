import dotenv from 'dotenv';

dotenv.config();

function required(name) {
  const value = process.env[name];
  if (!value) throw new Error(`Missing required env: ${name}`);
  return value;
}

function numberEnv(name, fallback) {
  const raw = process.env[name];
  if (!raw) return fallback;
  const value = Number(raw);
  return Number.isFinite(value) ? value : fallback;
}

export const config = {
  port: numberEnv('PORT', 8787),
  nodeEnv: process.env.NODE_ENV || 'development',
  supabaseUrl: required('SUPABASE_URL'),
  supabaseServiceRoleKey: required('SUPABASE_SERVICE_ROLE_KEY'),
  workerSecret: required('MAPADATA_WORKER_SECRET'),
  googlePlacesApiKey: required('GOOGLE_PLACES_API_KEY'),
  workerId: process.env.WORKER_ID || `donweb-worker-${process.pid}`,
  placesMode: process.env.MAPADATA_PLACES_MODE || 'basic',
  defaultLimit: numberEnv('MAPADATA_DEFAULT_LIMIT', 20),
  maxLimit: numberEnv('MAPADATA_MAX_LIMIT', 500),
  storageBucket: process.env.MAPADATA_STORAGE_BUCKET || 'mapadata-exports',
  pollBatchSize: numberEnv('MAPADATA_POLL_BATCH_SIZE', 1),
  heartbeatStaleMinutes: numberEnv('MAPADATA_HEARTBEAT_STALE_MINUTES', 10)
};
