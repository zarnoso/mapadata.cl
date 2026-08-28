# Mapadata.cl - Arquitectura Final

## Objetivo

Unificar el producto en una sola base de código y evitar que frontend, API y worker compitan entre sí.

## Decisión principal

- **Frontend**: `www.mapadata.cl` en Cloudflare Pages
- **API pública**: `api.mapadata.cl` en FastAPI
- **Worker**: proceso aparte, en tu servidor o VPS
- **DB**: Neon PostgreSQL
- **Storage**: Cloudflare R2

## Flujo exacto

```text
Usuario -> www.mapadata.cl
         -> GET https://api.mapadata.cl/api/comunas
         -> POST https://api.mapadata.cl/api/jobs
         -> API guarda job en Neon
         -> Worker consulta jobs pendientes
         -> Worker llama Google Places
         -> Worker enriquece datos
         -> Worker genera CSV
         -> Worker sube CSV a R2
         -> API expone estado y URL final
         -> Frontend muestra progreso / descarga
```

## Qué vive en cada capa

### Frontend

- landing
- explorador
- checkout MercadoPago
- consulta de estado del job
- descarga final

### API

- `GET /api/health`
- `GET /api/comunas`
- `GET /api/regiones`
- `POST /api/jobs`
- `GET /api/jobs`
- `GET /api/jobs/{id}`
- `DELETE /api/jobs/{id}`
- `GET /api/stats`

### Worker

- toma jobs con bloqueo seguro
- consulta Google Places
- enriquece teléfono, web y emails
- deduplica resultados
- genera CSV
- sube a R2
- actualiza el job en DB

## Lo que se debe evitar

- frontend hablando con `localhost` en producción
- duplicar lógica de jobs en Next y FastAPI
- dejar rutas demo en producción
- guardar CSV solo en `/tmp`
- mezclar funciones Deno/Supabase con el build del frontend si no se van a desplegar juntas

## Hosting recomendado

### DonWeb Web Hosting Plan Emprendedor

Sirve para:

- alojar frontend estático
- servir páginas HTML/CSS/JS simples
- correo y web básico

No lo recomiendo como hogar del backend productivo si necesitas:

- procesos permanentes
- worker de scraping corriendo siempre
- tareas largas
- jobs en cola
- control fino de procesos

### Recomendación realista

- usar Cloudflare Pages para frontend
- usar un VPS o Cloud Server para `api.mapadata.cl` y el worker
- usar DonWeb hosting solo si confirmas que tienes SSH, Python, procesos persistentes y cron suficientes

## Variables críticas

- `NEXT_PUBLIC_API_BASE_URL=https://api.mapadata.cl`
- `DATABASE_URL=...`
- `GOOGLE_PLACES_API_KEY=...`
- `R2_ACCOUNT_ID=...`
- `R2_ACCESS_KEY_ID=...`
- `R2_SECRET_ACCESS_KEY=...`
- `MAPADATA_WORKER_SECRET=...`

## Estado actual del repo

- frontend ya adaptado para consumir API externa
- build de Next validado
- documentación alineada con la arquitectura final
- siguiente paso: endurecer backend y eliminar duplicados innecesarios
