# Instalación DonWeb Worker

## 1. Crear package.json real

El conector no permitió crear `worker/package.json` directamente. En DonWeb, entra a la carpeta `worker/` y crea este archivo manualmente:

```json
{
  "name": "mapadata-worker",
  "version": "0.1.0",
  "private": true,
  "type": "module",
  "main": "src/server.js",
  "scripts": {
    "start": "node src/server.js",
    "run:poll": "node src/jobs/pollPendingRuns.js"
  },
  "dependencies": {
    "@supabase/supabase-js": "^2.49.1",
    "cors": "^2.8.5",
    "dotenv": "^16.4.7",
    "express": "^4.21.2"
  },
  "engines": {
    "node": ">=20"
  }
}
```

## 2. Instalar dependencias

```bash
cd worker
npm install --no-audit --no-fund
```

## 3. Crear `.env`

```bash
cp .env.example .env
```

Completar:

- SUPABASE_URL
- SUPABASE_SERVICE_ROLE_KEY
- MAPADATA_WORKER_SECRET
- GOOGLE_PLACES_API_KEY

## 4. Levantar servidor

```bash
npm start
```

## 5. Healthcheck

```bash
curl https://TU-WORKER-DOMINIO/health
```

## 6. Procesar un run existente

```bash
curl -X POST https://TU-WORKER-DOMINIO/run-once \
  -H "Content-Type: application/json" \
  -H "x-mapadata-worker-secret: TU_SECRET" \
  -d '{"run_id":"ID_DEL_RUN"}'
```

## Nota importante

Esta primera versión genera el registro de export CSV, pero Lovable debe conectar el helper final de Supabase Storage porque el conector bloqueó la creación automática de ese archivo. La lógica está aislada para que la validación sea simple.
