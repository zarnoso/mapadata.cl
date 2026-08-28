# Mapadata.cl — Roadmap

## Estado actual (2026-08-28)

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
| Token eliminado del historial de git | 2026-08-28 |
| Repo GitHub limpio (sin secretos) | 2026-08-28 |

### En progreso

| Tarea | Estado | Notas |
|---|---|---|
| Google Places API Key | ⏳ | Pendiente configurar en `.env.mapadata` |
| CORS en bucket R2 | ⏳ | Pendiente |

### Pendiente

| Tarea | Prioridad | Descripción |
|---|---|---|
| Cloudflare Tunnel para api.mapadata.cl | 🔴 Alta | Exponer backend en `api.mapadata.cl` |
| Deploy frontend en Cloudflare Pages | 🔴 Alta | Publicar frontend en la nube |
| Configurar DNS mapadata.cl en Cloudflare | 🔴 Alta | Apuntar dominio a Cloudflare |
| Integrar MercadoPago | 🟡 Media | Procesar pagos |
| Mejorar selector de comunas (mapa) | 🟡 Media | Mapa interactivo de Chile |
| Sistema de notificaciones | 🟡 Media | Email/webhook cuando job termine |
| Rate limiting por cliente | 🟢 Baja | Evitar abuso |
| Tests automatizados | 🟢 Baja | Unit tests y integration tests |
| Dashboard de administración | 🟢 Baja | Ver todos los jobs, estadísticas |

---

## Próximos pasos inmediatos

1. **Configurar Google Places API Key**
   ```bash
   nano /home/chumbeke/mapadata.cl/.env.mapadata
   # Poner: GOOGLE_PLACES_API_KEY=tu_key
   systemctl --user restart mapadata-worker
   ```

2. **Instalar Cloudflare Tunnel**
   ```bash
   cloudflared tunnel login
   cloudflared tunnel create mapadata
   cloudflared tunnel route dns mapadata api.mapadata.cl
   cloudflared tunnel run mapadata
   ```

3. **Deploy frontend en Cloudflare Pages**
   - Ir a dash.cloudflare.com → Workers & Pages
   - Create Application → Pages → Connect to Git
   - Seleccionar repo `zarnoso/mapadata.cl`
   - Build command: `npm run build`
   - Output directory: `.next`

4. **Configurar DNS**
   - Agregar zona `mapadata.cl` en Cloudflare
   - Crear registro CNAME `api` → tunnel
   - Crear registro CNAME `www` → Cloudflare Pages

---

## Notas técnicas

- El worker usa `FOR UPDATE SKIP LOCKED` para concurrencia
- Google Places API tiene límite de 60 resultados por query
- Se recomienda no exceder 2000 queries por job (costo ~$34 USD)
- Los CSVs se generan con UTF-8 BOM para compatibilidad con Excel
- El sistema respeta rate limits de Google (2s entre páginas, 0.1s entre detalles)
