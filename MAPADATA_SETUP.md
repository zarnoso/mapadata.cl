# Mapadata / Prospexa

Proyecto separado de Likay.

BD oficial: Neon Postgres, schema `mapadata`.

## Objetivo operativo

Generar una base segmentada para cliente:

- Rubro: ferretería y relacionados directos.
- Comuna: Valparaíso.
- Salida: Excel y CSV.
- Persistencia: `mapadata.leads` en Neon.

## Secrets necesarios en GitHub Actions

Crear en `Settings -> Secrets and variables -> Actions`:

- `NEON_DATABASE_URL`
- `GOOGLE_PLACES_API_KEY`

No pegar esos valores en issues, commits, README públicos ni chats.

## Script creado

```txt
scripts/mapadata/google-places-ferreterias-valpo.mjs
```

El script:

1. Consulta Google Places API oficial por búsquedas segmentadas.
2. Filtra resultados por dirección en Valparaíso.
3. Deduplica por `google_place_id`.
4. Inserta/actualiza en `mapadata.leads`.
5. Registra corrida en `mapadata.search_runs`.
6. Genera archivos `.xlsx` y `.csv`.

## Ejecución local o en runner

```bash
npm install --no-audit --no-fund --no-save pg xlsx
NEON_DATABASE_URL="postgresql://..." \
GOOGLE_PLACES_API_KEY="..." \
TARGET_LIMIT=500 \
OUTPUT_DIR=exports/mapadata \
node scripts/mapadata/google-places-ferreterias-valpo.mjs 500
```

## Workflow manual sugerido

El conector bloqueó la creación directa de archivos dentro de `.github/workflows`. Crear manualmente este archivo:

```txt
.github/workflows/mapadata-ferreterias-valpo.yml
```

Contenido:

```yaml
name: Mapadata Ferreterias Valparaiso

on:
  workflow_dispatch:
    inputs:
      target_limit:
        description: "Cantidad maxima a exportar"
        required: true
        default: "500"
      output_dir:
        description: "Carpeta de salida"
        required: true
        default: "exports/mapadata"

jobs:
  build-export:
    name: Generate Mapadata export
    runs-on: ubuntu-latest
    timeout-minutes: 30

    env:
      TARGET_LIMIT: ${{ github.event.inputs.target_limit }}
      OUTPUT_DIR: ${{ github.event.inputs.output_dir }}
      NEON_DATABASE_URL: ${{ secrets.NEON_DATABASE_URL }}
      GOOGLE_PLACES_API_KEY: ${{ secrets.GOOGLE_PLACES_API_KEY }}

    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: "20"

      - name: Install runtime dependencies
        run: npm install --no-audit --no-fund --no-save pg xlsx

      - name: Validate required secrets
        run: |
          test -n "$NEON_DATABASE_URL" || (echo "Missing NEON_DATABASE_URL" && exit 1)
          test -n "$GOOGLE_PLACES_API_KEY" || (echo "Missing GOOGLE_PLACES_API_KEY" && exit 1)

      - name: Generate Excel and CSV
        run: node scripts/mapadata/google-places-ferreterias-valpo.mjs "$TARGET_LIMIT"

      - name: Upload Mapadata export
        uses: actions/upload-artifact@v4
        with:
          name: mapadata-ferreterias-valparaiso-${{ github.run_id }}
          path: |
            ${{ github.event.inputs.output_dir }}/*.xlsx
            ${{ github.event.inputs.output_dir }}/*.csv
          if-no-files-found: error
          retention-days: 14
```

## Consultas Neon útiles

```sql
SELECT COUNT(*) FROM mapadata.leads;

SELECT *
FROM mapadata.v_ferreterias_valparaiso_export
LIMIT 500;

SELECT *
FROM mapadata.search_runs
ORDER BY started_at DESC
LIMIT 10;
```
