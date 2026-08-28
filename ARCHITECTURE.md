# Mapadata.cl — Documentación de Arquitectura

## Descripción del Producto

**Mapadata.cl** es una plataforma web que permite a clientes empresariales (B2B) buscar y descargar bases de datos de empresas en Chile. El cliente selecciona comunas y áreas de interés, y la plataforma genera un archivo CSV con los datos de contacto de empresas verificadas.

**Propuesto de valor:** "Convierte Google Maps en tu motor de ventas."

---

## Arquitectura del Sistema

```
┌─────────────────────────────────────────────────────────────────┐
│  www.mapadata.cl (Cloudflare Pages)                              │
│  - Selector de comunas (mapa/checklist)                          │
│  - Selector de áreas de búsqueda (términos)                      │
│  - Tabla de resultados con descarga CSV                          │
└──────────────────────────┬──────────────────────────────────────┘
                           │ POST /api/jobs
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│  api.mapadata.cl (Cloudflare Tunnel)                             │
│  - Backend FastAPI en tu servidor Debian 13                      │
│  - PostgreSQL Neon                                               │
└──────────────────────────┬──────────────────────────────────────┘
                           │ FOR UPDATE SKIP LOCKED
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│  Worker Python                                                   │
│  1. Lee job pendiente de Neon                                   │
│  2. Consulta Google Places API (textsearch)                     │
│  3. Enriquece datos (teléfono, web) via Place Details          │
│  4. Extrae emails desde webs (regex + mailto)                   │
│  5. Deduplica resultados                                        │
│  6. Genera CSV                                                   │
│  7. Sube a Cloudflare R2                                        │
└─────────────────────────────────────────────────────────────────┘
```

---

## Componentes

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
- **Deploy:** Cloudflare Pages (pendiente)

### Backend (`backend.py`)

- **Framework:** FastAPI 0.141.1 + Uvicorn 0.30.6
- **Puerto:** 8001
- **EndPoints:**
  - `GET /api/comunas` — Lista comunas (filtro por región opcional)
  - `POST /api/jobs` — Crea job de scraping
  - `GET /api/jobs/{id}` — Estado de un job
  - `GET /api/jobs` — Listar jobs por cliente
- **Acceso:** `api.mapadata.cl` vía Cloudflare Tunnel

### Worker (`worker.py`)

- **Loop infinito** con `FOR UPDATE SKIP LOCKED`
- **Google Places API:**
  - `textsearch` — Búsqueda por término + zona (máx 60 resultados)
  - `place details` — Enriquecimiento (teléfono, web)
- **Extracción de emails:**
  - Regex en HTML de webs
  - Links `mailto:`
  - Filtro de dominios no válidos
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
- **URLs públicas:** `https://pub-7976da0811374c03128e815940af652a.r2.dev/{archivo}`

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

## Variables de Entorno

```bash
# Base de datos Neon
DATABASE_URL=postgresql://neondb_owner:***@ep-dark-sunset-ah922o3v-pooler.c-3.us-east-1.aws.neon.tech/neondb?sslmode=require

# Google Places API
GOOGLE_PLACES_API_KEY=AIza... (RELLENAR)

# Cloudflare R2
R2_ACCOUNT_ID=7976da0811374c03128e815940af652a
R2_API_TOKEN=*** (CONFIGURADO LOCALMENTE)
R2_BUCKET_NAME=mapadata
R2_PUBLIC_URL=https://pub-7976da0811374c03128e815940af652a.r2.dev
```

---

## Flujo de Uso

1. Cliente entra a mapadata.cl
2. Selecciona comunas (o "Todo Chile")
3. Selecciona áreas de búsqueda (o usa las por defecto)
4. Paga vía MercadoPago
5. Se crea un job (status: queued)
6. Worker toma el job y ejecuta scraping
7. Se genera CSV y se sube a R2
8. Cliente recibe notificación con enlace de descarga
9. Cliente descarga el CSV

---

## Contacto

- **Desarrollo:** Andrés Bravo (andres_bv@live.cl)
- **GitHub:** https://github.com/zarnoso/mapadata.cl
- **Dominio:** mapadata.cl (pendiente deploy)
- **Deploy objetivo:** Cloudflare Pages (frontend) + VPS/Cloudflare Workers (backend)

---

*Última actualización: 2026-08-28*
