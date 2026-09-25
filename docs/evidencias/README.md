# Evidencia de trabajo — GeoQuebradas (2026-09-25)

Carpeta para **mostrar el proceso**: de las referencias y bocetos, pasando por las maquetas (esqueletos) aprobadas, hasta el visor final y su despliegue.
Las maquetas `.html` se abren con doble clic (son páginas estáticas sin datos); las capturas son del visor funcionando con datos reales del 22/09/2026.

## Cronología
| Etapa | Qué se hizo | Evidencia |
|---|---|---|
| 0. Análisis del visor original | Se clonó el frontend de minam.sittecnologic.com y se documentó cada botón, capa y servicio | `../../replica_sit/FUNCIONALIDADES.md`, `referencias/06_visor_original_detalle_quebrada.png` |
| 1. Referencias de diseño | Géoportail (Francia), boceto propio con bloques y leyenda, capas tipo IGN, panel de detalle de Mapping Global China | `referencias/01`–`05` |
| 2. Primer visor (v1) | Visor con estética Géoportail, panel de una sola columna | `capturas/05_v1_primer_visor.png` · código `../v1/` · doc `../VISOR_V1.md` |
| 3. Esqueleto de distribución | Panel de 3 bloques, chips sobre el mapa, minimapa, línea de tiempo, secciones debajo | `maquetas/esqueleto.html` · `capturas/01`–`03` (las versiones `.bak*` muestran la evolución) |
| 4. Maqueta del panel de Capas | Formato de categorías expandibles (inspirado en IGN) con paleta propia | `maquetas/maqueta_capas.html` · `capturas/04` |
| 5. Visor v2 | Construcción del rediseño con datos reales, vista Análisis, capas, detalle | `capturas/06`, `07` · código `../v2/` |
| 6. Mockups y paleta | Mockups de detalle/Acerca de y muestra de verde aportados por el usuario | `referencias/07`–`09` |
| 7. Visor v3 (final) | Paleta verde/petróleo, cabecera con 4 bloques, detalle según mockups, ~20 iconos | `capturas/08`, `10` · código `../v3/` |
| 8. Capa GOES en vivo | Servicio FastAPI + Earth Engine; capas visible y canal 13 sobre Sudamérica, panel y miniatura | `capturas/09` · código `../gee_backend/` · `despliegue/08_goes_pp_json_ok.png` |
| 9. Despliegue | GitHub → Easypanel → Cloudflare, cuenta de servicio y permisos | `despliegue/01`–`09` |

## Documentos que lo respaldan
- `../DECISIONES.md` — bitácora cronológica de decisiones.
- `../GUIA_REPLICA_Y_ESCALADO.md` — manual para replicar y escalar (diseño, frontend, backend GEE, despliegue, 24 errores resueltos).

## Notas
- Las capturas se tomaron con un navegador automático; en algunas el mapa base aparece a medio cargar por el tiempo de espera, no es un defecto del visor.
- `despliegue/` contiene pantallas de Easypanel, Cloudflare y Google Cloud: **no se sube a GitHub** (solo se guarda localmente).
