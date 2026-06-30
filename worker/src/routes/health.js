import { Router } from 'express';
import { mapadata } from '../supabaseAdmin.js';

export const healthRouter = Router();

healthRouter.get('/health', async (_req, res) => {
  try {
    const { error } = await mapadata().from('search_runs').select('id').limit(1);
    return res.json({
      ok: true,
      service: 'mapadata-worker',
      db: error ? 'error' : 'ok',
      error: error?.message || null,
      ts: new Date().toISOString()
    });
  } catch (error) {
    return res.status(500).json({ ok: false, error: error.message });
  }
});
