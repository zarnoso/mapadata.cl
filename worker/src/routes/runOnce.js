import { Router } from 'express';
import { requireWorkerAuth } from '../security.js';
import { processRun } from '../jobs/processRun.js';

export const runOnceRouter = Router();

runOnceRouter.post('/run-once', requireWorkerAuth, async (req, res) => {
  try {
    const runId = req.body?.run_id || req.body?.runId;
    if (!runId) return res.status(400).json({ ok: false, error: 'missing_run_id' });
    const result = await processRun(runId);
    return res.json(result);
  } catch (error) {
    return res.status(500).json({ ok: false, error: error.message });
  }
});
