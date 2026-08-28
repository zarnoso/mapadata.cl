# Mapadata.cl

Mapadata.cl es una plataforma B2B para buscar y descargar bases de datos de empresas en Chile.

## Arquitectura final

- `www.mapadata.cl`: frontend estático en Cloudflare Pages
- `api.mapadata.cl`: backend principal en FastAPI
- `worker.mapadata.cl` o proceso separado: worker de scraping y enriquecimiento
- `Neon PostgreSQL`: cola, runs, leads, exportaciones y facturación
- `Cloudflare R2`: almacenamiento de CSVs generados

## Variables de entorno

Ver [.env.example](/home/chumbeke/mapadata.cl/.env.example).

## Flujo

1. El usuario entra a `www.mapadata.cl`
2. El frontend consulta `https://api.mapadata.cl/api/comunas`
3. El usuario crea un job en `POST /api/jobs`
4. El backend persiste el job en Neon
5. El worker toma el job, busca en Google Places y enriquece los datos
6. El worker genera CSV y lo sube a R2
7. El backend expone el estado y la URL final del export

## Desarrollo local

```bash
npm install
npm run dev
```

Backend:

```bash
pip install -r requirements-mapadata.txt
python backend.py
```

Worker:

```bash
python worker.py
```
