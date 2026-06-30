import { Router } from 'express';
import { requireWorkerAuth } from '../security.js';
import { pollPendingRuns } from '../jobs/pollPendingRuns.js';

export const pollRouter = Router();

pollRouter.post('/poll', requireWorkerAuth, async (req, res) => {
  try {
    const limit = Number(req.body?.limit || 1);
    const result = await pollPendingRuns({ limit });
    return res.json(result);
  } catch (error) {
    return res.status(500).json({ ok: false, error: error.message });
  }
});
