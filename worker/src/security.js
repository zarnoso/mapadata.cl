import { config } from './config.js';

function safeEqual(a, b) {
  return String(a || '') === String(b || '');
}

export function requireWorkerAuth(req, res, next) {
  const auth = req.headers.authorization || '';
  const bearer = auth.startsWith('Bearer ') ? auth.slice(7) : '';
  const headerSecret = req.headers['x-mapadata-worker-secret'] || req.headers['x-runner-secret'];

  if (safeEqual(bearer, config.workerSecret) || safeEqual(headerSecret, config.workerSecret)) {
    return next();
  }

  return res.status(401).json({ ok: false, error: 'unauthorized_worker_request' });
}
