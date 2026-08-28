# Mapadata.cl - Roadmap de Unificación

## Fase 1 - Base final

- [x] Frontend copiado desde el repo original de Lovable
- [x] Frontend apuntando a `NEXT_PUBLIC_API_BASE_URL`
- [x] Build validado
- [x] Documentación alineada a la arquitectura final

## Fase 2 - Backend único

- [ ] Elegir backend único definitivo
- [ ] Consolidar esquemas y eliminar duplicados
- [ ] Agregar `/api/health`
- [ ] Agregar configuración por entorno
- [ ] Estándares de logging y errores

## Fase 3 - Producción

- [ ] Publicar frontend en Cloudflare Pages
- [ ] Publicar backend en `api.mapadata.cl`
- [ ] Publicar worker como proceso dedicado
- [ ] Guardar exports en Cloudflare R2
- [ ] Enlazar dominio y SSL

## Fase 4 - Endurecimiento

- [ ] Autenticación/API keys
- [ ] Rate limiting
- [ ] Webhooks de pago
- [ ] Monitoreo y alertas
- [ ] Pruebas automatizadas
