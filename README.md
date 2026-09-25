# GeoQuebradas (MINAM · SENAMHI)

Visor de prioridad territorial por activación de quebradas + capa GOES-19 en vivo.

- `visor/` — sitio estático (nginx). Consume los servicios ArcGIS de MINAM por `/geo` y, opcionalmente, el servicio GOES (`config.js`).
- `gee_backend/` — servicio FastAPI que entrega teselas GOES-19 desde Google Earth Engine (necesita credenciales; ver su README).

Despliegue: GitHub → Easypanel (dos Apps, una por carpeta). Pasos en la conversación del 2026-09-25 y en `gee_backend/README.md`.
**Nunca subir la clave JSON de la cuenta de servicio**: va solo como variable de entorno `EE_KEY_JSON` en Easypanel.
