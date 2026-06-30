# Mapadata DonWeb Worker

Worker externo para procesos largos de Mapadata.

Responsabilidades:

- tomar runs pendientes desde Supabase
- consultar Google Places API oficial
- normalizar y deduplicar leads
- guardar resultados en `mapadata.leads`
- relacionar leads con `mapadata.run_leads`
- generar CSV/XLSX
- subir archivos a Supabase Storage
- actualizar `mapadata.search_runs` y `mapadata.exports`

No debe ejecutarse en el frontend.
No debe exponer `SUPABASE_SERVICE_ROLE_KEY`.
No toca Likay.
