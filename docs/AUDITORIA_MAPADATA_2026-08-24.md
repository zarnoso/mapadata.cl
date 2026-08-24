# Auditoría técnica — Prospexa / Mapadata

**Fecha:** 2026-08-24  
**Repositorio auditado:** `zarnoso/mapadata.cl`  
**Branch base:** `main`  
**Branch de auditoría:** `audit/mapadata-2026-08-24`  

## 1. Resumen ejecutivo

Hay una diferencia importante entre el estado descrito en las conversaciones anteriores y lo que actualmente está comprobable en GitHub.

El `main` actual del repositorio es un proyecto **Next.js 16 + React 19** muy básico. El `package.json` confirma Next.js y los scripts `next dev`, `next build` y `next start`. La página principal consume `/api/empresas` y `/api/contactos`, pero en el repositorio auditado no se encontraron esas rutas API mediante búsqueda de código.

El worker DonWeb **sí fue desarrollado**, pero está en la branch `feat/donweb-mapadata-worker` dentro del PR #1 y **el PR sigue abierto/no mergeado**. Por lo tanto, el worker no forma parte del `main` auditado.

No se encontraron en GitHub archivos de `supabase/functions`, migraciones SQL de `mapadata`, referencias a `mapadata-*`, ni código de Edge Functions. Esto no demuestra que Lovable/Supabase no tenga esos recursos: significa que **no están versionados en este repositorio y no pueden auditarse desde GitHub**.

La conclusión operativa es clara: antes de programar más frontend, hay que reconciliar tres fuentes de verdad: **GitHub, Supabase/Lovable y DonWeb**.

---

## 2. Backend que existe realmente en GitHub

### `main`

El backend visible en el repositorio es, conceptualmente, un proyecto Next.js. Sin embargo, está incompleto como backend productivo.

`package.json` contiene:

- `next: 16.2.4`
- `react: 19.2.4`
- `react-dom: 19.2.4`
- scripts `dev`, `build`, `start`, `lint`

No aparecen dependencias de Supabase, PostgreSQL, Neon, Google Places, MercadoPago, Express ni SDKs equivalentes en ese `package.json`.

La página `app/page.tsx` intenta llamar:

- `/api/empresas`
- `/api/contactos?rut=...`

Pero esas rutas no aparecen en la búsqueda del repositorio auditado.

**Diagnóstico:** el `main` actual no contiene un backend Mapadata funcional para generación de leads.

---

## 3. Edge Functions de Lovable

### Lo que se afirmó en conversaciones anteriores

En el historial proporcionado en la conversación se indicó que Lovable había creado estas Edge Functions:

- `mapadata-health`
- `mapadata-runs-create`
- `mapadata-runs-list`
- `mapadata-runs-status`
- `mapadata-leads-list`
- `mapadata-exports-create`
- `mapadata-exports-list`
- `mapadata-exports-download`
- `mapadata-import`
- `mapadata-billing-status`
- `mapadata-billing-webhook`

También se indicó que existirían helpers compartidos como:

- `_shared/cors.ts`
- `_shared/auth.ts`
- `_shared/worker.ts`

Y que existiría un secret `MAPADATA_WORKER_SECRET`.

### Verificación contra GitHub

No se encontraron en el repositorio:

- `supabase/functions/`
- archivos con nombres `mapadata-*`
- migraciones SQL de Supabase
- referencias de código a `supabase/functions`
- referencias a `mapadata-health`, `mapadata-runs-create`, etc.

**Conclusión:** esas Edge Functions pueden existir en el proyecto Supabase/Lovable, pero **no están presentes en GitHub y no deben considerarse auditadas/confirmadas por este repositorio**.

La siguiente auditoría debe hacerse directamente contra el proyecto Supabase/Lovable.

---

## 4. Schema y tablas `mapadata`

### Estado comprobable en GitHub

No hay migraciones SQL ni archivos de schema `mapadata` visibles en el repositorio `main`.

Por conversaciones anteriores se definió este modelo esperado:

- `mapadata.search_queries`
- `mapadata.search_runs`
- `mapadata.leads`
- `mapadata.run_leads`
- `mapadata.exports`
- `mapadata.entitlements`
- `mapadata.billing_events`
- `mapadata.industry_keywords`
- vista `mapadata.v_ferreterias_valparaiso_export`

También se indicó un bucket privado:

- `mapadata-exports`

Pero **ninguno de estos elementos puede confirmarse desde el repositorio GitHub actual**.

### Conclusión

El schema real debe consultarse en Supabase. No recomiendo crear otra base ni migrar a Neon hasta hacer esa comprobación.

---

## 5. Google Places

### Worker

La branch `feat/donweb-mapadata-worker` sí contiene integración con **Google Places API (New)**.

El worker define dos modos de Field Mask:

- `basic`
- `enriched`

El modo enriched solicita, entre otros:

- nombre
- dirección
- teléfono
- sitio web
- estado comercial
- Google Maps URI
- tipos
- rating
- cantidad de reseñas

El worker utiliza `GOOGLE_PLACES_API_KEY` como variable de entorno.

También existe paginación mediante `nextPageToken` y espera entre páginas.

### Planner existente

El worker tiene un planner específico para **ferreterías en Valparaíso**, con múltiples queries, incluyendo ferretería, herramientas, materiales de construcción, pernos, quincallería y búsquedas por sectores.

Esto significa que la arquitectura de búsqueda ya fue parcialmente preparada para el caso original de 500 ferreterías.

### Falta

Para el nuevo caso de **500 comercializadoras en Santiago**, el worker actualmente no muestra un planner específico equivalente. El planner comprobado en la branch está orientado a ferreterías/Valparaíso.

Por lo tanto hay que agregar un planner configurable por:

```text
industry
commune
region
limit
keywords
```

No conviene duplicar el código creando un segundo worker.

---

## 6. Worker DonWeb

### Existe

El PR #1 se llama:

`feat: add DonWeb Mapadata worker`

El PR está abierto y no mergeado a `main`.

La branch contiene:

```text
worker/
├── .env.example
├── INSTALL.md
├── README.md
├── package.template.json
└── src/
    ├── config.js
    ├── engine/
    │   ├── billingGatekeeper.js
    │   ├── dedupe.js
    │   ├── exportBuilder.js
    │   ├── googlePlacesAdapter.js
    │   ├── normalizer.js
    │   ├── planner.js
    │   └── quality.js
    ├── jobs/
    │   ├── pollPendingRuns.js
    │   └── processRun.js
    ├── logger.js
    ├── routes/
    │   ├── health.js
    │   ├── poll.js
    │   └── runOnce.js
    ├── security.js
    ├── server.js
    ├── supabaseAdmin.js
    └── utils/
        ├── chile.js
        ├── csv.js
        └── text.js
```

### Qué hace

El worker está diseñado para:

1. tomar runs pendientes desde Supabase;
2. reclamar el run;
3. consultar Google Places;
4. normalizar resultados;
5. filtrar la comuna objetivo;
6. deduplicar por `google_place_id` y otros campos;
7. guardar leads;
8. relacionarlos mediante `run_leads`;
9. generar CSV;
10. actualizar el estado del run.

### Problemas pendientes

#### A. No está en `main`

El primer problema es de integración: el worker existe solamente en la branch del PR #1.

#### B. Exportación incompleta

`processRun.js` genera el buffer CSV y crea el registro en `exports`, pero deja explícitamente pendiente la subida a Supabase Storage.

El resultado actual crea un estado similar a:

`generated_pending_storage`

Por tanto, el flujo de descarga todavía no está completo.

#### C. XLSX no está implementado en esta versión

El `exportBuilder.js` comprobado construye CSV. No existe en el worker auditado una implementación equivalente de XLSX.

#### D. Planner rígido

El proceso usa directamente `buildFerreteriaValparaisoPlan`.

Eso hace que el worker todavía esté acoplado al primer caso de uso.

#### E. Billing gatekeeper no está integrado claramente al procesamiento

Existe `billingGatekeeper.js`, pero el flujo visible de `processRun.js` no muestra un consumo transaccional de créditos antes de insertar/exportar. Esto debe revisarse antes de cobrar por generación.

#### F. Seguridad CORS demasiado abierta

`server.js` usa:

```js
cors({ origin: true })
```

Para producción conviene restringir los orígenes permitidos.

#### G. Falta confirmar el despliegue real en DonWeb

El repositorio contiene instrucciones y código, pero GitHub no demuestra que el worker esté actualmente ejecutándose en DonWeb.

Hay que comprobar:

- Node activo;
- proceso/Passenger activo;
- URL pública;
- `/health` respondiendo;
- variables de entorno cargadas;
- conexión a Supabase funcionando;
- Google Places funcionando;
- polling funcionando.

---

## 7. Arquitectura real reconstruida

El estado más coherente con todo lo auditado es:

```text
                    ┌─────────────────────┐
                    │     Frontend        │
                    │ Next.js en main     │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │ API / Supabase      │
                    │ Edge Functions      │
                    │ NO VERSIONADAS AQUÍ │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │ Supabase Postgres   │
                    │ schema mapadata ?   │
                    └──────────┬──────────┘
                               │
                         runs pending
                               │
                               ▼
                    ┌─────────────────────┐
                    │ DonWeb Worker       │
                    │ PR #1 / branch     │
                    └──────────┬──────────┘
                               │
                    Google Places API
                               │
                               ▼
                    ┌─────────────────────┐
                    │ leads / exports     │
                    │ Supabase Storage ?  │
                    └─────────────────────┘
```

El signo `?` es intencional: GitHub no permite confirmar esos componentes externos.

---

## 8. Auditoría de conversaciones de Codex

No tengo acceso directo a una base de datos privada de conversaciones de Codex ni puedo recuperar conversaciones que no estén expuestas a esta sesión.

Sí puedo auditar la evidencia que quedó materializada en GitHub.

La evidencia más importante encontrada es el PR #1, que contiene una implementación sustancial del worker DonWeb. Por eso podemos afirmar que **hubo avance real del worker**, aunque no podamos reconstruir cada conversación de Codex que produjo esos cambios.

No debe confundirse:

```text
conversación de Codex
        ≠
commit/PR verificable
```

Para efectos de continuidad técnica, el código versionado debe ser nuestra fuente de verdad.

---

## 9. Estado por componente

| Componente | Estado | Evidencia |
|---|---|---|
| Frontend Next.js | Existe | `package.json`, `app/page.tsx` |
| Backend Next.js productivo | Incompleto | `/api/empresas` y `/api/contactos` son llamados, pero no aparecen implementados en búsqueda |
| Supabase/Lovable | No verificable desde GitHub | Sin archivos Supabase en repo |
| Edge Functions Mapadata | No verificables desde GitHub | No aparecen en repo |
| Schema `mapadata` | No verificable desde GitHub | No hay migraciones |
| Google Places adapter | Existe en worker | PR #1 |
| Worker DonWeb | Existe en branch | PR #1 |
| Worker en `main` | No | PR #1 abierto |
| Planner ferretería Valparaíso | Existe | worker branch |
| Planner comercializadoras Santiago | No | No encontrado |
| Deduplicación | Existe | `dedupe.js` |
| Normalización | Existe | `normalizer.js` |
| Quality score | Existe | `quality.js` |
| CSV | Parcialmente implementado | `exportBuilder.js` |
| XLSX | No confirmado / no implementado | No encontrado en worker |
| Supabase Storage upload | Pendiente | `processRun.js` lo deja explícitamente pendiente |
| Billing gate transaccional | Pendiente de integración/verificación | helper existe, flujo no lo muestra integrado |
| DonWeb deployment | No verificable desde GitHub | requiere comprobación en servidor |
| 500 comercializadoras Santiago | No implementado | falta planner/configuración |

---

## 10. Prioridad inmediata

No seguir construyendo otra arquitectura.

El siguiente orden recomendado es:

### Paso 1 — Auditar Supabase/Lovable

Confirmar directamente:

- proyecto Supabase;
- schema `mapadata`;
- tablas;
- RLS;
- Storage bucket;
- Edge Functions;
- secrets;
- billing/entitlements;
- URL del worker configurada.

### Paso 2 — Auditar DonWeb

Confirmar:

```text
worker instalado
npm install ejecutado
.env configurado
Node >= 20
proceso activo
/health OK
Supabase OK
Google Places OK
```

### Paso 3 — Completar worker

Antes de usarlo comercialmente:

1. Storage uploader;
2. XLSX;
3. planner genérico;
4. billing gate real/transaccional;
5. manejo de errores/reintentos;
6. observabilidad;
7. CORS restringido;
8. validación de payloads;
9. evitar duplicación concurrente;
10. prueba end-to-end.

### Paso 4 — Merge controlado del PR #1

No mergear a ciegas.

Primero validar Supabase y DonWeb. Después revisar el PR y mergearlo cuando el worker esté probado.

### Paso 5 — Caso Santiago

Agregar una configuración como:

```json
{
  "industry": "comercializadoras",
  "commune": "Santiago",
  "region": "Metropolitana",
  "limit": 500
}
```

con múltiples keywords de descubrimiento y deduplicación centralizada.

---

## 11. Veredicto

**Mapadata no está empezando desde cero.**

Hay tres piezas de trabajo distintas:

1. un frontend Next.js básico en `main`;
2. una arquitectura Supabase/Lovable descrita y aparentemente construida fuera del repositorio;
3. un worker DonWeb bastante avanzado en el PR #1, pero todavía incompleto y sin mergear.

El mayor riesgo ahora no es programar más código. Es **desalineación entre GitHub, Lovable/Supabase y DonWeb**.

La prioridad debe ser comprobar esos tres sistemas y convertirlos en una única arquitectura verificable antes de seguir.

---

## Evidencia principal

- `package.json` de `main`: Next.js 16 + React 19.
- `app/page.tsx`: llamadas a `/api/empresas` y `/api/contactos`.
- PR #1: `feat: add DonWeb Mapadata worker`, abierto/no mergeado.
- Branch `feat/donweb-mapadata-worker`: contiene adapter Google Places, planner, normalizer, dedupe, quality, polling y procesamiento de runs.
- `processRun.js`: confirma que Storage y XLSX todavía no están terminados en esta versión.

**Esta auditoría no modifica la arquitectura de producción ni mergea el worker.**
