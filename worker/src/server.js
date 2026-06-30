import express from 'express';
import cors from 'cors';
import { config } from './config.js';
import { logger } from './logger.js';
import { healthRouter } from './routes/health.js';
import { runOnceRouter } from './routes/runOnce.js';
import { pollRouter } from './routes/poll.js';

const app = express();

app.use(cors({ origin: true }));
app.use(express.json({ limit: '2mb' }));

app.use(healthRouter);
app.use(runOnceRouter);
app.use(pollRouter);

app.get('/', (_req, res) => {
  res.json({ ok: true, service: 'mapadata-worker' });
});

app.use((err, _req, res, _next) => {
  logger.error('unhandled_error', { error: err.message });
  res.status(500).json({ ok: false, error: 'internal_error' });
});

app.listen(config.port, () => {
  logger.info('worker_started', { port: config.port, workerId: config.workerId });
});
