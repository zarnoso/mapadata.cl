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
| Tabla `comunas_chile` (347 comunas) | 2026-08-28 |
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
| Cloudflare Tunnel creado | 2026-08-28 |
| Registro DNS `api.mapadata.cl` | 2026-08-28 |
| Backend accesible vía tunnel | 2026-08-28 |
| Google Places API Key configurada | 2026-08-28 |
| Worker procesando jobs | 2026-08-28 |
| DNS de DonWeb apuntando a Cloudflare | 2026-08-28 |
| Auditoría de seguridad backend | 2026-08-28 |
| Rate limiting + headers de seguridad | 2026-08-28 |
| Frontend deployado en Cloudflare Pages | 2026-08-28 |
| **Worker v5.0 — Mejoras de conciliación y rendimiento** | 2026-08-28 |

### Mejoras del Worker v5.0

| Mejora | Estado |
|---|---|
| 1. ThreadPoolExecutor con lock para DDG (thread-safe) | ✅ |
| 2. Checkpointing incremental por zona | ✅ |
| 3. Pool de conexiones + reconexión automática | ✅ |
| 4. Dedup en SQL (memoria acotada) | ✅ |
| 5. Errores informativos en DB (traceback) | ✅ |
| 6. Graceful shutdown con signal handling | ✅ |
| 7. Upload real a R2 (S3-compatible) | ✅ |
| 8. Config validation al inicio | ✅ |
| 9. Health check endpoint (puerto 8002) | ✅ |
| 10. Circuit breaker para Places API | ✅ |
| 11. Enriquecimiento paralelizado (3 workers) | ✅ |
| 12. Batch writes (cada 50 zonas) | ✅ |
| 13. Límite de jobs concurrentes (2) | ✅ |
| 14. Alertas Telegram en fallo | ✅ |
| 15. Stale job detector (5 min) | ✅ |

---

## En progreso

| Tarea | Estado | Notas |
|---|---|---|
| Tabla `scraping_resultados` en Neon | ⏳ | Pendiente crear en Neon |
| Configurar Telegram Bot Token | ⏳ | Pendiente |
| Probar worker con job real | ⏳ | Pendiente |

---

## Pendiente

| Tarea | Prioridad | Descripción |
|---|---|---|
| Configurar DNS `www.mapadata.cl` | 🔴 Alta | Apuntar a Cloudflare Pages |
| Integrar MercadoPago | 🟡 Media | Procesar pagos |
| Mejorar selector de comunas (mapa) | 🟡 Media | Mapa interactivo de Chile |
| Sistema de notificaciones | 🟡 Media | Email/webhook cuando job termine |
| Rate limiting por cliente | 🟢 Baja | Evitar abuso |
| Tests automatizados | 🟢 Baja | Unit tests y integration tests |
| Dashboard de administración | 🟢 Baja | Ver todos los jobs, estadísticas |

---

## Próximos pasos inmediatos

1. **Crear tabla `scraping_resultados` en Neon**
   ```bash
   psql $DATABASE_URL -f sql/create_scraping_resultados.sql
   ```

2. **Probar worker con job de prueba**
   ```bash
   curl -X POST https://api.mapadata.cl/api/jobs \
     -H "Content-Type: application/json" \
     -d '{"comunas":["Santiago"],"cliente_id":1}'
   ```

3. **Verificar health check**
   ```bash
   curl http://localhost:8002/health
   ```

4. **Configurar DNS `www.mapadata.cl`**
   - Agregar registro CNAME `www` → `mapadata.pages.dev`

---

## Notas técnicas

- El worker usa `FOR UPDATE SKIP LOCKED` para concurrencia
- Google Places API tiene límite de 60 resultados por query
- Se recomienda no exceder 2000 queries por job (costo ~$34 USD)
- Los CSVs se generan con UTF-8 BOM para compatibilidad con Excel
- El sistema respeta rate limits de Google (2s entre páginas, 0.1s entre detalles)
- El backend corre en Python 3.11 (evita problemas con psycopg2 en 3.13)
- El worker v5.0 incluye: paralelización, checkpointing, circuit breaker, batch writes
- Health check endpoint: http://localhost:8002/health
- Alertas Telegram configurables vía `TELEGRAM_BOT_TOKEN` y `TELEGRAM_CHAT_ID`
