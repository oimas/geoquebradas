# Servicio GOES en vivo (Earth Engine → visor GeoQuebradas)

> **Qué es:** un servicio muy pequeño (FastAPI) que ejecuta en Earth Engine la lógica de tu script GOES y le entrega al visor
> la URL de teselas. **Está escrito pero NO se ha ejecutado** (necesita tus credenciales de Earth Engine).
> El visor (`../v3/index.html`, categoría "Imágenes satelitales en vivo" del panel Capas) lo consume en `GET /goes/pp` y `GET /goes/vis`.

## Por qué hace falta un servicio
Las credenciales de Earth Engine no pueden ir en el HTML. El servicio se autentica con una cuenta de servicio, genera la
imagen (`getMapId`) y devuelve solo la URL de teselas + la fecha + la leyenda. Las URL de teselas **caducan** (horas), por eso
el servicio las cachea 10 min y el visor las renueva cada 10 min mientras la capa esté encendida.

## Qué reproduce de tu script
| Tu script | Servicio |
|---|---|
| `NOAA/GOES/19/MCMIPF`, imagen más reciente | igual (ordenada por `system:time_start`) |
| "GOES PP": `CMI_C13`, máscara `<= 2800`, `clip(area)`, paleta 1300–3000 | `GET /goes/pp` |
| "GOES VIS": RGB `CMI_C02, CMI_C03, CMI_C01`, min 64, max 5454, gamma 1.8 | `GET /goes/vis` |
| Fecha mostrada = `system:time_start` + 20 min, hora de Lima | `fecha_lima` (variable `SUMA_MINUTOS`) |
| `opacity: 0.8` | opacidad inicial 0,8 en el visor |

**Sobre `area`:** en el fragmento pegado no aparece la variable `area` (la de `.clip(area)`). Para probar no hace falta: sin asset el servicio recorta a un
rectángulo amplio sobre Sudamérica y los océanos vecinos (`EE_AREA_BBOX`, por defecto `-130,-65,-20,30`; el disco de GOES-19 llega a ~-156°/+6°). Si `area` era un asset, ponlo en `EE_AREA_ASSET`
(y comprueba que tu cuenta tenga permiso de lectura sobre él).

## Puesta en marcha (cuando quieras probarlo)
1. Un proyecto de Google Cloud registrado en Earth Engine y una **cuenta de servicio** con acceso a los assets usados
   (registrarla en Earth Engine y compartirle los assets si son privados). Descargar su clave JSON.
2. `pip install -r requirements.txt`
3. Variables de entorno: `EE_PROJECT`, `EE_SERVICE_ACCOUNT`, `EE_KEY_FILE`, y opcionalmente `EE_AREA_ASSET`, `CORS_ORIGINS`.
4. `uvicorn goes_tiles:app --host 0.0.0.0 --port 8090`
5. Comprobar: `http://localhost:8090/salud` y `http://localhost:8090/goes/pp`.
6. En producción, publicar tras el mismo dominio del visor como `/gee-api` (proxy inverso) y poner `CORS_ORIGINS` con ese dominio.

## Pendiente de verificar
- Que las teselas de `earthengine.googleapis.com` se carguen bien dentro de ArcGIS (CORS) — debería, pero no está probado.
- Cuotas y condiciones de uso de Earth Engine para un visor público.
- Que `area` sea la geometría correcta.

## Prueba rápida con tu cuenta personal (sin cuenta de servicio ni proyecto nuevo)
El proyecto de Cloud que ya tienes registrado en Earth Engine (`ee-oimas854`) sirve. No hay que crear otro ni publicar una "app" de Earth Engine.
1. `pip install -r requirements.txt`
2. `earthengine authenticate` (abre el navegador; entra con tu cuenta) — solo la primera vez.
3. PowerShell: `$env:EE_PROJECT="ee-oimas854"` (sin las variables de cuenta de servicio, usa tus credenciales locales).
4. `uvicorn goes_tiles:app --port 8090`
5. Abrir el visor v3 → Capas → "Imágenes satelitales en vivo".
La cuenta de servicio solo hará falta al publicar el visor para otras personas.

## Dejarlo permanente en tu servidor (Easypanel / Hostinger, como el portal y el visor de incendios)
Qué falta, en orden:
1. **Cuenta de servicio de Earth Engine** (recomendado en vez de tu cuenta personal): en Google Cloud del proyecto `ee-oimas854`
   crear una cuenta de servicio, descargar su clave JSON y registrarla en Earth Engine
   (https://signup.earthengine.google.com/#!/service_accounts). Rol sugerido en el proyecto: *Service Usage Consumer* y *Earth Engine Resource Viewer*.
   *(Para salir del paso, se podría copiar `~/.config/earthengine/credentials` al servidor, pero queda atado a tu cuenta personal y no se recomienda.)*
2. **Subir `gee_backend/` a GitHub** (mejor un repositorio propio, sin la clave). El `Dockerfile` ya está listo.
3. **Easypanel → Create → App** desde ese repositorio (Build: Dockerfile). Variables de entorno:
   `EE_PROJECT=ee-oimas854`, `EE_SERVICE_ACCOUNT=<correo de la cuenta de servicio>`, `EE_KEY_JSON=<contenido completo del JSON>`,
   `CORS_ORIGINS=https://<dominio del visor>` (no dejar `*`), opcional `EE_AREA_BBOX`.
4. **Dominio:** un subdominio para el servicio (por ejemplo `gee.oimas.online`) apuntando al puerto **8090**, con HTTPS.
5. **Visor:** definir `window.GEE_API_URL = "https://gee.oimas.online"` antes del script del visor (o servir el servicio bajo `/gee-api` en el mismo dominio).
6. Comprobar `https://gee.oimas.online/salud` y encender la capa en el visor.

Cosas a vigilar (según las notas del portal): el **VPS Hostinger vence el 2026-10-02**, `oimas.online` respondía "Not Found" de Easypanel desde el 2026-09-21,
y la red institucional del MINAM bloquea `oimas.online` por nombre de dominio (esto también afectaría a un subdominio del servicio).
Además: revisar cuotas y condiciones de uso de Earth Engine para un visor público (proyecto registrado como no comercial).

> **Nota Easypanel:** Easypanel asigna el puerto interno **3000** (variable `PORT`); el dominio del servicio debe apuntar al puerto 3000, no al 8090.
> Los errores de Earth Engine se devuelven como HTTP 500 y se escriben en los registros (Cloudflare oculta los 502/504).
