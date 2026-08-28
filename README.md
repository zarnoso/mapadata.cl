# Mapadata.cl — Motor de Ventas B2B

> Plataforma web que permite a empresas buscar y descargar bases de datos de empresas verificadas en Chile bajo la nuea ley de protección de datos.

## Estado del Proyecto

| Componente | Estado |
|---|---|
| **Backend FastAPI** | ✅ Corriendo en `localhost:8001` con systemd |
| **Worker Google Places** | ✅ Corriendo con systemd (falta API Key) |
| **Cloudflare R2** | ✅ Bucket `mapadata` creado |
| **Cloudflare Tunnel** | ✅ Configurado para `api.mapadata.cl` |
| **Base de Datos Neon** | ✅ Conectado con 347 comunas |
| **Frontend Next.js** | ✅ En GitHub (pendiente deploy) |
| **Repo GitHub** | ✅ Limpio (sin secretos en historial) |

---

## Arquitectura Final

```
┌─────────────────────────────────────────────┐
│  www.mapadata.cl (Cloudflare Pages)         │
│  - Selector de comunas                      │
│  - Selector de términos                     │
│  - Tabla de resultados                      │
│  - Descarga CSV                             │
└──────────────────┬──────────────────────────┘
                   │ API REST
                   ▼
┌─────────────────────────────────────────────┐
│  api.mapadata.cl (Cloudflare Tunnel)        │
│  - Backend FastAPI en tu servidor           │
│  - PostgreSQL Neon                          │
└──────────────────┬──────────────────────────┘
                   │ Cola de jobs
                   ▼
┌─────────────────────────────────────────────┐
│  Worker Python                              │
│  1. Lee job pendiente (FOR UPDATE SKIP)     │
│  2. Google Places API → datos básicos      │
│  3. Place Details → teléfono, web          │
│  4. Scraping webs → emails                 │
│  5. Deduplicación                          │
│  6. Genera CSV                              │
│  7. Sube a R2                               │
└─────────────────────────────────────────────┘
```

---

## Tecnologías

| Componente | Tecnología |
|---|---|
| Frontend | Next.js 16 + React 19 + Tailwind CSS |
| Backend | FastAPI + Uvicorn |
| Base de datos | Neon PostgreSQL |
| Almacenamiento | Cloudflare R2 |
| Tunel | Cloudflare Tunnel |
| Scraping | Google Places API |

---

## Instalación

```bash
# Clonar repositorio
git clone https://github.com/zarnoso/mapadata.cl.git
cd mapadata.cl

# Instalar dependencias del frontend
npm install

# Instalar dependencias del backend (Python 3.11)
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements-mapadata.txt

# Configurar variables de entorno
cp .env.example .env.mapadata
# Editar .env.mapadata con tus credenciales
```

---

## Uso

### Iniciar frontend (desarrollo)
```bash
npm run dev
```

### Iniciar backend
```bash
source .venv/bin/activate
python backend.py
```

### Iniciar worker
```bash
source .venv/bin/activate
export GOOGLE_PLACES_API_KEY=***
python worker.py
```

### Iniciar todo (producción)
```bash
./start.sh
```

---

## API Endpoints

| Método | Endpoint | Descripción |
|---|---|---|
| GET | `/api/comunas` | Lista comunas de Chile |
| GET | `/api/regiones` | Lista regiones |
| POST | `/api/jobs` | Crear job de scraping |
| GET | `/api/jobs/{id}` | Estado de un job |
| GET | `/api/jobs` | Listar jobs |
| DELETE | `/api/jobs/{id}` | Cancelar job |

---

## Variables de Entorno

Ver `.env.mapadata`:

```bash
DATABASE_URL=postgresql://...
GOOGLE_PLACES_API_KEY=***
R2_ACCOUNT_ID=7976da0811374c03128e815940af652a
R2_API_TOKEN=***
R2_BUCKET_NAME=mapadata
R2_PUBLIC_URL=https://pub-7976da0811374c03128e815940af652a.r2.dev
```

---

## Desarrollo

Este proyecto usa:
- **Next.js 16** con Turbopack
- **Python 3.11** (evita problemas con psycopg2 en 3.13)
- **Cloudflare Tunnel** para exponer el backend

---

## Contacto

- **Desarrollo:** Andrés Bravo
- **GitHub:** https://github.com/zarnoso/mapadata.cl
- **Dominio:** mapadata.cl
