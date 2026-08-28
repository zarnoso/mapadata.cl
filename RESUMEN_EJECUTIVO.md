# Proyecto Mapadata.cl — Resumen Ejecutivo

## Descripción del Proyecto

**Mapadata.cl** es una plataforma web que permite a clientes empresariales (B2B) buscar y descargar bases de datos de empresas en Chile. El cliente selecciona comunas y áreas de interés, y la plataforma genera un archivo CSV con datos de contacto de empresas verificadas de Google Places.

**Propuesto de valor:** "Convierte Google Maps en tu motor de ventas."

---

## Entorno Actual

| Parámetro | Valor |
|---|---|
| **Hostname** | h |
| **OS** | Debian GNU/Linux 13 (trixie) |
| **Kernel** | 6.12.101+deb13-amd64 |
| **CPU** | 4 cores (i5-3230M) |
| **RAM** | 7.2 GB |
| **Disco** | 18 GB (61% usado) |
| **IP local** | 192.168.100.23 |
| **Uptime** | 5+ días |

---

## Arquitectura del Sistema

```
┌─────────────────────────────────────────────────────────────────┐
│                        FRONTEND (Next.js)                        │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  - Selector de comunas (mapa/checklist)                   │  │
│  │  - Selector de áreas de búsqueda (términos)              │  │
│  │  - Tabla de resultados con descarga CSV                  │  │
│  │  - Integración con MercadoPago (pagos)                   │  │
│  └──────────────────────────────────────────────────────────┘  │
└──────────────────────────┬──────────────────────────────────────┘
                           │ POST /api/jobs
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                     BACKEND (FastAPI)                            │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  GET  /api/comunas          → Lista comunas de Chile     │  │
│  │  POST /api/jobs             → Crear job de scraping      │  │
│  │  GET  /api/jobs/:id         → Estado de un job           │  │
│  │  GET  /api/jobs             → Listar jobs                │  │
│  └──────────────────────────────────────────────────────────┘  │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                   BASE DE DATOS (Neon PostgreSQL)                │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  scraping_jobs   → Cola de trabajos pendientes           │  │
│  │  comunas_chile   → 82 comunas de Chile                   │  │
│  └──────────────────────────────────────────────────────────┘  │
└──────────────────────────┬──────────────────────────────────────┘
                           │ FOR UPDATE SKIP LOCKED
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                      WORKER (Python)                             │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  1. Lee job pendiente de Neon                            │  │
│  │  2. Consulta Google Places API (textsearch)              │  │
│  │  3. Enriquece datos (teléfono, web) via Place Details   │  │
│  │  4. Extrae emails desde webs (regex + mailto)            │  │
│  │  5. Deduplica resultados                                 │  │
│  │  6. Genera CSV                                           │  │
│  │  7. Sube a Cloudflare R2                                │  │
│  │  8. Actualiza estado en Neon                             │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Componentes Detallados

### Frontend (`app/page.tsx`)

- **Framework:** Next.js 16.2.4 + React 19.2.4 + Tailwind CSS 4
- **Funcionalidad:**
  - Selector de comunas por región (filtro cascada)
  - Selector de términos de búsqueda (tags editables)
  - Tabla de resultados con nombre, dirección, teléfono, web, email
  - Botón de descarga CSV
  - Indicador de carga animado
- **Diseño:** Colores `#1a1a2e` (azul oscuro), Geist font, responsive
- **Legal:** Incluye aviso de presunción de inocencia y fuente de datos

### Backend (`backend.py`)

- **Framework:** FastAPI 0.141.1 + Uvicorn 0.30.6
- **Puerto:** 8001
- **Endpoints:**
  - `GET /api/comunas` — Lista comunas (filtro por región opcional)
  - `POST /api/jobs` — Crea job de scraping
  - `GET /api/jobs/{id}` — Estado de un job
  - `GET /api/jobs` — Listar jobs por cliente

### Worker (`worker.py`)

- **Loop infinito** con `FOR UPDATE SKIP LOCKED`
- **Google Places API:**
  - `textsearch` — Búsqueda por término + zona (máx 60 resultados)
  - `place details` — Enriquecimiento (teléfono, web)
- **Extracción de emails:**
  - Regex en HTML de webs (páginas: /contacto, /contact, /quienes-somos, etc.)
  - Links `mailto:`
  - Filtro de dominios no válidos (wixpress.com, sentry.io, etc.)
- **Deduplicación:** Por `place_id` y por nombre+dirección normalizados
- **Salida:** CSV UTF-8 con BOM, separado por comas
- **Subida a R2:** Automática después de generar CSV

### Base de Datos (Neon PostgreSQL)

**Tabla `scraping_jobs`:**

| Columna | Tipo | Descripción |
|---------|------|-------------|
| id | SERIAL PK | Identificador único |
| status | TEXT | queued / running / done / failed / cancelled |
| comunas | TEXT[] | Array de comunas seleccionadas |
| terminos | TEXT[] | Términos de búsqueda |
| modo | TEXT | enriched (con teléfono/web/email) |
| resultado_csv_url | TEXT | URL pública del CSV en R2 |
| total_empresas | INT | Total de empresas encontradas |
| con_email | INT | Cantidad con email |
| creado_en | TIMESTAMPTZ | Fecha de creación |
| terminado_en | TIMESTAMPTZ | Fecha de finalización |
| cliente_id | INT | ID del cliente |
| error_message | TEXT | Mensaje de error si falla |

**Tabla `comunas_chile`:**

| Columna | Tipo | Descripción |
|---------|------|-------------|
| id | SERIAL PK | Identificador |
| nombre | VARCHAR | Nombre de la comuna |
| region | VARCHAR | Región |
| region_number | VARCHAR | Número romano de región |

**Datos:** 82 comunas insertadas (muestra representativa de todas las regiones)

---

## Almacenamiento (Cloudflare R2)

- **Bucket:** `mapadata`
- **Account ID:** `7976da0811374c03128e815940af652a`
- **Endpoint:** `https://7976da0811374c03128e815940af652a.r2.cloudflarestorage.com/mapadata`
- **Location:** Eastern North America (ENAM)
- **API Token:** Configurado (no incluido en este documento por seguridad)
- **CORS:** Pendiente configuración
- **URLs públicas:** `https://pub-7976da0811374c03128e815940af652a.r2.dev/{archivo}`

---

## Variables de Entorno

```bash
# Base de datos Neon
DATABASE_URL=postgresql://neondb_owner:***@ep-dark-sunset-ah922o3v-pooler.c-3.us-east-1.aws.neon.tech/neondb?sslmode=require

# Google Places API
GOOGLE_PLACES_API_KEY=AIza... (RELLENAR)

# Cloudflare R2
R2_ACCOUNT_ID=7976da0811374c03128e815940af652a
R2_API_TOKEN=cfut_... (CONFIGURADO LOCALMENTE)
R2_BUCKET_NAME=mapadata
R2_PUBLIC_URL=https://pub-7976da0811374c03128e815940af652a.r2.dev
```

---

## Seguridad y Legalidad

- **Fuente de datos:** Google Places API (datos públicos verificados)
- **Legalidad:** Los datos son de acceso público. No se almacenan datos de terceros sin consentimiento.
- **Términos de servicio:** Los clientes aceptan uso responsable de los datos.
- **Protección de datos:** No se incluyen datos de personas naturales, solo empresas.
- **Disclaimer:** Incluye presunción de inocencia y fuente de datos.
- **Rate limiting:** Respeto a servidores destino (0.3s entre requests)
- **Límites de API:** Máximo 60 resultados por query, 5 términos por defecto
- **Cumplimiento:** Ley 19.628 (protección de datos Chile)

---

## Estado del Proyecto

### Completado

| Tarea | Fecha |
|---|---|
| Frontend Next.js básico | 2026-08-26 |
| Frontend profesional UX/UI | 2026-08-26 |
| Backend FastAPI (endpoints) | 2026-08-26 |
| Worker Google Places | 2026-08-26 |
| Tabla `scraping_jobs` en Neon | 2026-08-26 |
| Tabla `comunas_chile` (82 comunas) | 2026-08-26 |
| API endpoints funcionales | 2026-08-26 |
| Worker loop con `FOR UPDATE SKIP LOCKED` | 2026-08-26 |
| Extracción de emails desde webs | 2026-08-26 |
| Deduplicación de resultados | 2026-08-26 |
| Generación de CSV | 2026-08-26 |
| Bucket R2 creado | 2026-08-27 |
| Token R2 configurado | 2026-08-27 |
| Backend corriendo en systemd | 2026-08-27 |
| Worker corriendo en systemd | 2026-08-27 |
| Documentación (ARCHITECTURE, README, ROADMAP) | 2026-08-27 |

### En progreso

| Tarea | Estado |
|---|---|
| Google Places API Key | Pendiente configurar |
| CORS en bucket R2 | Pendiente |

### Pendiente

| Tarea | Prioridad |
|---|---|
| Deploy frontend en Cloudflare Pages | Alta |
| Conectar dominio mapadata.cl a Cloudflare | Alta |
| Configurar HTTPS para backend | Alta |
| Integración MercadoPago | Media |
| Mejorar selector de comunas (mapa interactivo) | Media |
| Sistema de notificaciones (email/webhook) | Media |
| Rate limiting por cliente | Baja |
| Tests automatizados | Baja |
| Dashboard de administración | Baja |

---

## Problemas Conocidos

1. **API Key de Google Places no configurada:** El worker falla sin `GOOGLE_PLACES_API_KEY`
2. **Frontend no deployado:** Solo funciona en localhost:3001, no hay URL pública
3. **Backend en PC local:** No es accesible desde internet sin IP pública o tunnel
4. **CORS no configurado en R2:** Puede causar errores en navegador
5. **Sin HTTPS:** El backend corre en HTTP, no seguro para producción
6. **MercadoPago no integrado:** No se pueden procesar pagos

---

## Mejoras Futuras

1. **Dockerizar el proyecto:** Facilitar deploy en cualquier servidor
2. **Migrar a VPS:** DigitalOcean/Hetzner ($4-6/mes) para tener backend siempre online
3. **Cloudflare Workers:** Reescribir backend en JavaScript para serverless
4. **Mapa interactivo:** Selector visual de comunas con mapa de Chile
5. **Notificaciones en tiempo real:** WebSockets o SSE para progreso del job
6. **Cache de resultados:** No repetir búsquedas de comunas recientes
7. **Panel de administración:** Ver todos los jobs, estadísticas, gestión de clientes
8. **API key por cliente:** Autenticación y rate limiting por usuario
9. **Tests automatizados:** Unit tests y integration tests
10. **Monitoreo:** Logs centralizados, alertas de errores

---

## Contacto

- **Desarrollo:** Andrés Bravo (andres_bv@live.cl)
- **GitHub:** https://github.com/zarnoso/mapadata.cl
- **Dominio:** mapadata.cl (pendiente deploy)
- **Deploy objetivo:** Cloudflare Pages (frontend) + VPS/Cloudflare Workers (backend)

---

*Última actualización: 2026-08-27*
