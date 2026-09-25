# GeoQuebradas — Guía para replicar y escalar el visor

> **Qué es este archivo:** el "manual de replicación" de todo lo construido el 2026-09-25 para el visor **GeoQuebradas** (MINAM · SENAMHI):
> diseño (colores, formas, botones), frontend, capa GOES en vivo con Google Earth Engine (backend), despliegue (GitHub → Easypanel → Cloudflare),
> **todos los errores que aparecieron y cómo se resolvieron**, y cómo escalar. Está pensado para retomar el proyecto sin haber estado en la conversación.
>
> - Estado final documentado: **`quebrada_francesa/v3/`** (visor) + **`gee_backend/`** (servicio GOES) + **`geoquebradas_deploy/`** (lo que se sube a GitHub).
> - Repositorio: https://github.com/oimas/geoquebradas (rama `main`). Visor en producción: https://geoquebradas.oimas.online · servicio GOES: https://gee.oimas.online
> - Otros documentos de la carpeta: `DECISIONES.md` (bitácora cronológica), `VISOR_V1.md` (primer visor congelado), `../replica_sit/FUNCIONALIDADES.md` (análisis del visor original que se replicó).
> - **Nunca guardar en GitHub ni en el chat la clave JSON de la cuenta de servicio de Earth Engine.**

---

## 1. Qué es y cómo está organizado

Visor de **prioridad territorial por activación de quebradas (IPT-AQ)**: muestra las quebradas con aviso de SENAMHI, su nivel de prioridad y lo expuesto (población, viviendas, vías, colegios…), más una capa satelital **GOES-19 en vivo** hecha con Earth Engine.

```
Navegador ──► visor (nginx, HTML estático)  ──► servicios ArcGIS de MINAM (datos)   [por /geo/ o directo en localhost]
                    │
                    └─► servicio GOES (FastAPI en Easypanel) ──► Google Earth Engine (teselas GOES-19)
```

### Carpetas (en `C:\Users\hp\Desktop\MINAM\8_QUEBRADAS\`)
| Carpeta | Qué es |
|---|---|
| `replica_sit/` | Copia del visor original (minam.sittecnologic.com) + `FUNCIONALIDADES.md`. Solo referencia. |
| `quebrada_francesa/v1/` | Primer visor con estética tipo Géoportail. Congelado. |
| `quebrada_francesa/v2/` | Rediseño (3 bloques, análisis, capas tipo IGN). Punto de retorno. |
| `quebrada_francesa/v3/` | **Versión final**: paleta verde/petróleo, cabecera nueva, detalle según mockups, iconos, GOES. Respaldos `index.bak_*.html`. |
| `quebrada_francesa/esqueleto.html`, `maqueta_capas.html` | Maquetas aprobadas antes de construir. |
| `quebrada_francesa/gee_backend/` | Servicio GOES (FastAPI + earthengine-api). |
| `geoquebradas_deploy/` | Lo que se sube a GitHub: `visor/` (v3 + nginx + Dockerfile + `config.js`) y `gee_backend/`. **Si cambia `v3/index.html`, recopiarlo a `visor/index.html`** (este lleva además `<script src="config.js">`). |

### Ejecutar en local (Windows, PowerShell)
```powershell
cd C:\Users\hp\Desktop\MINAM\8_QUEBRADAS\quebrada_francesa\v3
python -m http.server 8083            # visor: http://localhost:8083
# servicio GOES (otra ventana), con tu cuenta personal ya autenticada (earthengine authenticate):
cd ..\gee_backend
$env:EE_PROJECT="ee-oimas854"
python -m uvicorn goes_tiles:app --port 8090
```
En localhost el visor consulta directo `https://geoservidorperu.minam.gob.pe/...` y el servicio en `http://localhost:8090`. Fuera de localhost usa `/geo` (proxy nginx) y `window.GEE_API_URL` (`config.js`).

---

## 2. Sistema de diseño (colores, formas, botones)

**Reglas acordadas:** interfaz sobria, **solo 4 familias** (verde, azul petróleo, blanco, gris); **sin emoticones**; nada de franjas o líneas de color en las tarjetas; el color fuerte **solo donde informa** (niveles de prioridad, semáforo del aviso).

### Paleta (variables CSS `:root` en `index.html`)
| Variable | Valor | Uso |
|---|---|---|
| `--navy` | `#145044` | **Verde bosque**: menú, pestaña activa, títulos, texto de acento |
| `--teal` | `#22876A` | **Verde de acento**: botones primarios, interruptores, barras, enlaces activos |
| `--teal-d` | `#1a6d55` | hover del verde |
| `--blue` | `#1F5C78` | **Azul petróleo**: riel de botones, enlaces, 2 de los 4 bloques de cabecera |
| `--blue-d` | `#174a61` | hover del azul |
| `--txt` | `#14261F` | texto (casi negro verdoso) |
| `--muted` | `#5F6E68` | texto secundario |
| `--line` | `#DCE3E0` | bordes |
| `--bg` | `#F1F5F3` | fondos suaves (tarjetas de indicadores, botones redondos) |
| tintes | `#E4F0EB` (verde suave), `#E6EEF2` (azul suave) | tarjetas de orientación, etiqueta de ubicación, banner de lectura |

**Colores con significado (no se cambian):** Sin prioridad `#6b7e96` · Bajo `#2fbf71` · Medio `#ffd400` (texto `#3a3000`) · Alto `#f97316` · Muy Alto `#c1121f`. Semáforo del aviso SENAMHI (`nivel`): 3 `#c1121f`, 2 `#f97316`, 1 `#ffd400`, sin aviso `#d5dae1`.

### Tipografía y medidas
- Fuente: `Arial, "Segoe UI", Helvetica, sans-serif`, base 14 px. (Pendiente decidir: Inter.)
- Títulos de panel y de bloque en **formato oración, negrita** (16 px panel, 24 px secciones). Etiquetas pequeñas en mayúsculas 10–11 px con `letter-spacing`.
- Cabecera **76 px**, pie **44 px**, panel derecho **400 px** (`--top`, `--foot`, `--side`). El mapa ocupa todo el alto entre cabecera y pie.
- Radios: tarjetas 12 px · botones `.btn` 8 px · botón grande del panel 22 px · pestañas 6 px · píldoras de la barra del mapa 19 px · bloques de cabecera **0 px (cuadrados)**.

### Cabecera (una fila)
`[☰ menú 60 px verde] [logo MINAM + wordmark "geoquebradas"] [pestañas Situación | Detalle | Acerca de] [buscador central con filtro dep›prov›dist] [4 bloques cuadrados a la derecha]`
- Wordmark: `linear-gradient(90deg,#1F5C78,#22876A)` como texto (background-clip). Logo: `img/logominam.png`.
- **4 bloques cuadrados** de alto completo (56 px de ancho, borde izquierdo blanco al 35 %): Ayuda y Imprimir en `--blue`; Favoritos y Compartir en `--teal`. Iconos SVG blancos.
- Buscador: al enfocarse abre la ventana con Departamento → Provincia → Distrito (cascada; el mapa se acerca en cada nivel). La ubicación elegida queda dentro del buscador como etiqueta `#E4F0EB` con ✕.

### Sobre el mapa
- Arriba-izquierda: zoom +/−, **2D/3D** (vertical), y a su derecha la barra `[‹ Fecha dd/mm/aaaa ›] [Limpiar]`. Los niveles NO van aquí (van en la leyenda).
- Abajo-izquierda: **panel GOES** (200 px, `bottom:154px`) encima del **minimapa** (128 px) + escala numérica y gráfica.
- Abajo-centro: **línea de tiempo** (últimos 30 días con datos, botón Reproducir/Pausa, flechas).
- Abajo-derecha: localizar y pantalla completa.
- Borde del panel: **riel** de botones (plegar `›`, Capas con contador, Herramientas, Análisis), cada uno con icono arriba y etiqueta debajo.

### Panel derecho (3 bloques apilados)
1. **Bloque 1:** título, descripción corta, fecha y ámbito (con iconos), nota si se muestra otra fecha, botón «Ver detalle →».
2. **Bloque 2 – Indicadores:** 5 tarjetas grises sin franjas (quebradas con su desglose, población, viviendas, red vial, superficie agrícola). Con una quebrada seleccionada muestran sus cifras.
3. **Bloque 3 – Leyenda:** niveles con conteo; **cada fila filtra** mapa/cifras/listas al hacer clic; se oculta solo si el usuario quiere (se recuerda en `localStorage`); debajo, leyenda de las capas ArcGIS encendidas.
- Vistas alternativas del panel: **Capas** (categorías tipo IGN, buscador, «Solo activas», interruptores, menú ⋮), **Herramientas**, **Análisis** (según la selección: país / departamento / distrito / quebrada), **Favoritos**.

### Secciones debajo del mapa (scroll)
- **Detalle por quebrada:** recorrido + línea de fuente, acciones con icono, nombre + caja «IPT-AQ | Percentil» + medidor, **lectura rápida** generada con los datos (banner), tres tarjetas (¿Por qué? · Orientación en dos tarjetas entidades/población · Elementos expuestos en 2 columnas), Avisos 7 días + persistencia junto a Comportamiento reciente. Sin selección: «Las más urgentes del día».
- **Comparar con otras quebradas:** ranking de departamentos + tabla ordenable/paginada con buscador propio y exportar CSV.
- **Acerca de:** cuadrícula (¿Qué es?, fórmula y tabla IPT-AQ, Recursos con icono y flecha, Fuentes).

### Botones y componentes (clases)
`.btn` (8 px, negrita 12.5 px) · `.btn-teal` (fondo `--teal`, texto blanco) · `.btn-line` (borde `--line`, texto `--blue`) · `.btn-block` (ancho completo, 22 px, flex con icono) · `.pill`/`.seg` (barra sobre el mapa, 38 px alto) · `.chip` (etiqueta de nivel coloreada) · `.fcard` (tarjeta blanca 12 px con sombra `0 1px 3px rgba(20,80,68,.08)`) · `.kp div` (tarjeta gris de indicador) · `.ic` (icono de línea).
**Iconos:** ~20 SVG propios de línea (viewBox 24, `stroke:currentColor`, ancho 1.8) definidos en el objeto `ICONS` y la función `ic('nombre')`. Solo en títulos de tarjeta, acciones, riel y cabecera; **no** en tablas, leyenda ni indicadores.

---

## 3. Frontend (un solo `index.html`)

**Tecnologías:** ArcGIS Maps SDK JS **4.29** (tema claro) + Chart.js 4.4. **Chart.js va ANTES del loader AMD de ArcGIS** (si no, su UMD se registra como AMD y rompe `esri/Map`).

### Puntos de edición rápida (arriba del `<script>`)
| Constante | Qué controla |
|---|---|
| `TEXTOS` | Todo texto visible editable (título, descripciones, «Acerca de», textos del panel GOES…) |
| `GEO_BASE`, `URL_ACTUAL`, `URL_HIST`, `URL_REPORTES` | Servicios ArcGIS de MINAM (directo en localhost, `/geo` en producción) |
| `PRI` / `ORDEN_LV` / `NIVEL_COL` | Colores y orden de los niveles y del semáforo |
| `CATS` | Árbol de capas del panel (categoría › subgrupo › `[url, título, where?, colorLínea?, pesada?]`). Las que empiezan por `gee:` son capas GEE |
| `BASEMAPS` | Mapas base disponibles |
| `GEE_API`, `window.GEE_API_URL` | Dirección del servicio GOES (`http://localhost:8090` en local; `config.js` en producción) |
| `ICONS` | Iconos SVG |

### Datos y reglas de negocio
- **Capa vigente** `MapServer/0`; **histórico** `MapServer/1` (`fecha = date 'AAAA-MM-DD'`); **reportes** `.../geoquebradas_prcesamiento/MapServer/2`.
- Si la capa vigente está **vacía** (ocurrió el 2026-09-25) se carga la **última fecha con datos del histórico** y se avisa. Consulta paginada de 1 000 en 1 000 (`resultOffset`).
- **Clave de la quebrada = `quebrada_uid`** (estable entre fechas). `eval_id` NO sirve: se reinicia cada día.
- La prioridad se lee del campo `prioridad` (no se recalcula). IPT-AQ = 0,40·Aᵈ + 0,40·E + 0,20·Gᵃ; niveles por percentiles P25/P60/P85 (calculados por el ETL de MINAM).
- Series por día: `outStatistics` con `groupByFieldsForStatistics=fecha` (gráfico del panel Análisis y línea de tiempo).
- Campos usados: `nombdep, nombprov, nombdist, quebrada_uid, fecha, prioridad, ipt_aq, percentil_ipt, ad, e, ga, aaviso, apersistencia_7d, arecurrencia_7d, dias_persist_7d, aviso_nivel, nivel, pob_exp, viv_exp, salud_exp, educ_exp, redvial_km_exp, agricola_ha_exp, puentes_exp, pam_exp, ph_exp, irs_exp, canales_km_exp, bancos_exp, pozos_exp, presas_exp, bocatomas_exp, reservorios_exp, recomendacion_entidad, recomendacion_publico, observacion_metodologica, criterio_zona_analisis`.

### Enlaces con estado (hash de la URL)
`#f=AAAA-MM-DD` fecha · `d=` `p=` `t=` departamento/provincia/distrito · `n=Muy Alto,Alto` niveles · `q=<quebrada_uid>` quebrada · `v=capas|tools|an|fav` vista del panel · `s=sec-detalle|sec-acerca` sección · `w=0` omitir bienvenida · `pop=1` abrir ventana de ubicación · `gee=vis,pp` encender capas GOES · `ext=sa` ir a Sudamérica. **Sirven para compartir y para tomar capturas de prueba.**

### Otras funciones
Favoritos (`localStorage qf_fav`), exportar CSV, reporte imprimible (ventana con captura del mapa y del gráfico), copiar enlace, 2D/3D (MapView↔SceneView compartiendo el mismo `Map`), buscador por texto, ventana de bienvenida (`localStorage qf2_welcome`), leyenda con clic-para-filtrar.

---

## 4. Backend GOES con Earth Engine (`gee_backend/goes_tiles.py`)

**Por qué existe:** las credenciales de Earth Engine no pueden ir en el HTML. El servicio se autentica, genera la imagen y entrega **la URL de teselas**; el navegador dibuja las teselas directo desde Google.

### Lo que reproduce del script de Code Editor
| Script GEE | Servicio |
|---|---|
| `NOAA/GOES/19/MCMIPF`, imagen más reciente | `GET /goes/{pp|vis}` (ordenada por `system:time_start`) |
| **GOES PP**: banda `CMI_C13`, máscara `<= 2800`, `clip(area)`, paleta de 19 colores, min 1300 / max 3000 | `/goes/pp` |
| **GOES VIS**: RGB `CMI_C02, CMI_C03, CMI_C01`, min 64, max 5454, gamma 1,8 | `/goes/vis` |
| Fecha mostrada = `system:time_start` + 20 min, hora de Lima | campo `fecha_lima` (`SUMA_MINUTOS`) |
| `opacity: 0.8` | opacidad 0,8 en el visor |

Respuesta: `{ "url": ".../tiles/{z}/{x}/{y}", "time_start_ms": ..., "fecha_lima": "25/09/2026 11:40", "leyenda": { "tipo":"rampa", "paleta":[...], "min":1300, "max":3000, "nota":"..." } }`.
Endpoints extra: `/salud`. Caché de 10 min por capa (`CACHE_SEGUNDOS`).

### Variables de entorno
| Variable | Valor |
|---|---|
| `EE_PROJECT` | `ee-oimas854` (proyecto de Cloud registrado en Earth Engine) |
| `EE_SERVICE_ACCOUNT` | `geoquebradas-gee@ee-oimas854.iam.gserviceaccount.com` |
| `EE_KEY_JSON` | contenido **completo del JSON de la clave, en UNA línea** (secreto) |
| `EE_KEY_FILE` | alternativa: ruta al JSON (local) |
| `CORS_ORIGINS` | `https://geoquebradas.oimas.online` (sin barra final; en local `*`) |
| `EE_AREA_ASSET` / `EE_AREA_BBOX` | recorte: asset con la geometría de `area`, o rectángulo `O,S,E,N` (defecto `-130,-65,-20,30`) |
| `PORT` | lo fija Easypanel (**3000**) |

Sin `EE_SERVICE_ACCOUNT`, usa las credenciales locales (`earthengine authenticate`), útil para pruebas.

### Conectar las teselas en ArcGIS (lo aprendido)
- Earth Engine da `url_format` con `{z}/{x}/{y}`; `WebTileLayer` de ArcGIS necesita `{level}/{col}/{row}` → `url.replace('{z}','{level}').replace('{x}','{col}').replace('{y}','{row}')`.
- **Las URL de teselas caducan** (horas): el visor las pide al encender la capa y las **renueva cada 10 min** reemplazando la capa (`geoLoad`/`toggleGee`), conservando visibilidad y opacidad.
- Orden: el **canal 13 va encima del RGB** (en `CATS` se agrega después). Recorte amplio para que no se vea el borde de la imagen.
- El **minimapa** muestra la miniatura GOES y se aleja a Sudamérica (escala 1:150 000 000) mientras haya capa GOES encendida.
- Panel GOES compacto: nombre corto de cada capa, barra de colores 1300–3000, hora «dd/mm hh:mm · Lima», ×.

### Permisos de Earth Engine (aprendido a golpes)
La cuenta de servicio necesita en el proyecto: **Consumidor de Service Usage** + **Escritor de recursos de Earth Engine** (*Earth Engine Resource Writer*). Con solo el rol de **lector** falla con `Permission 'earthengine.maps.create' denied on resource 'projects/ee-oimas854'` (crear mapas exige escritor). Los roles se editan en **IAM (menú izquierdo) → lápiz de la fila**, NO en «Administrar permisos» de la lista de cuentas de servicio (eso decide quién puede usar la cuenta).

---

## 5. Despliegue paso a paso (GitHub → Easypanel → Cloudflare)

1. **GitHub:** repo `oimas/geoquebradas` con `visor/` y `gee_backend/`. `.gitignore` bloquea `*.json`, `.env`, `*.key`, `*.log`.
   ```powershell
   cd ...\geoquebradas_deploy
   git init -b main; git add .; git commit -m "..."; git remote add origin https://github.com/oimas/geoquebradas.git; git push -u origin main
   ```
2. **Cuenta de servicio:** Google Cloud (proyecto `ee-oimas854`) → IAM → Cuentas de servicio → crear `geoquebradas-gee` → roles (arriba) → Claves → JSON. Convertir a una línea y copiar:
   ```powershell
   python -c "import json;print(json.dumps(json.load(open(r'C:\ruta\clave.json'))))" | Set-Clipboard
   ```
   Pegar en Easypanel como `EE_KEY_JSON=`. **Borrar el archivo de Descargas después.**
3. **Cloudflare (DNS):** registro **A**, nombre `geoquebradas` (visor) y `gee` (servicio), IP del VPS `2.24.120.117`, **Proxied**.
4. **Easypanel – App del visor** (`geoquebradas`): Fuente GitHub `oimas/geoquebradas`, rama `main`, **Ruta de compilación `/visor`**; Compilación **Dockerfile**, archivo `Dockerfile`; Dominio `geoquebradas.oimas.online`, HTTPS activado, destino HTTP puerto **80**. Implementar.
5. **Easypanel – App del servicio** (`geoquebradas-gee`): Fuente igual pero **Ruta de compilación `/gee_backend`**; Dockerfile; Entorno con las variables de la sección 4; Dominio `gee.oimas.online`, HTTPS, destino HTTP puerto **3000** (¡no 8090!). Implementar.
6. **Conectar:** en `visor/config.js` dejar `window.GEE_API_URL = "https://gee.oimas.online";`, push y **Implementar** el visor.
7. **Comprobar:** `https://gee.oimas.online/salud` → `{"ok":true,...}`; `/goes/pp` → JSON con `url`; visor → Capas → «Imágenes satelitales en vivo».

`visor/nginx.conf` sirve el HTML sin caché (`no-cache`), imágenes 7 días y hace **proxy `/geo/` → `https://geoservidorperu.minam.gob.pe/arcgis/rest/services/`** (evita el CORS intermitente del servicio de MINAM).

**Riesgos de infraestructura anotados:** el VPS Hostinger **vence el 2026-10-02**; `oimas.online` respondió «Not Found» de Easypanel el 2026-09-21; la red institucional del MINAM bloquea `oimas.online` por nombre de dominio (afectaría también a los subdominios); revisar cuotas y condiciones de uso de Earth Engine para un visor público (proyecto registrado como no comercial).

---

## 6. Catálogo de errores y soluciones

| # | Síntoma / error | Causa | Solución |
|---|---|---|---|
| 1 | El visor original no daba datos / mapa vacío el 2026-09-25 | La capa vigente (`MapServer/0`) tenía 0 registros; el histórico llegaba al 22/09 | Fallback a la última fecha con datos del histórico + aviso en el panel |
| 2 | Historial de una quebrada con un solo punto | `eval_id` se reinicia cada día | Usar `quebrada_uid` |
| 3 | `Uncaught … multipleDefine` de ArcGIS | Chart.js cargado después del loader AMD | Cargar Chart.js **antes** de `js.arcgis.com/4.29/` |
| 4 | Capturas de prueba con el mapa en blanco | Edge headless sin WebGL | Flags `--use-angle=swiftshader --enable-unsafe-swiftshader --ignore-gpu-blocklist` y `--virtual-time-budget=40000+` |
| 5 | Captura de las secciones de abajo saliendo blanca | El screenshot tras hacer scroll en headless falla | Copia de prueba con `#screen{height:200px!important}` para ver las secciones sin scroll |
| 6 | Botones sin estilo (texto suelto) | Al reescribir un bloque de CSS entre marcadores se borraron `.btn*` | **Añadir overrides al final** en vez de reemplazar bloques; revisar con captura tras cada cambio |
| 7 | Botón MENÚ desplazado en la maqueta | Clase `.menu` chocaba con el popover | Renombrar a `.pop` (prefijos únicos por componente) |
| 8 | Cuadro por nivel mostraba «Alto · 1» | Etiqueta usaba el `flex` en vez del conteo | Separar `n` (etiqueta) de `flex` |
| 9 | Script Python con `\U…` en la ruta falla (`unicodeescape`) | Heredoc con rutas de Windows | Guardar el parche en un `.py` y ejecutarlo; usar `r'C:\...'` |
| 10 | GOES tardaba > 90 s | Ordenar toda `NOAA/GOES/19/MCMIPF` | `filterDate` de las últimas 6 h (48 h de respaldo) antes de `sort().first()` → ~3 s |
| 11 | Imagen GOES cortada con un borde | Recorte a un rectángulo justo sobre Sudamérica | Ampliar `EE_AREA_BBOX` (`-130,-65,-20,30`) o no recortar |
| 12 | Canal 13 no se veía | Quedaba debajo del RGB | Agregar la capa PP **después** de la visible (orden en `CATS`) |
| 13 | Easypanel: compilación fallando por Dockerfile | Ruta de compilación `/` con monorepo | **Ruta de compilación `/visor` o `/gee_backend`** y archivo `Dockerfile` |
| 14 | `502` en `https://gee.oimas.online` | Easypanel inyecta `PORT=3000`; el dominio apuntaba a 8090 | Dominio → puerto **3000** |
| 15 | Página «Bad gateway» de Cloudflare ocultando el error | Cloudflare reemplaza los 502/504 del origen | El servicio devuelve **500** con `detail` y escribe el traceback en los registros |
| 16 | `KeyError: 'EE_PROJECT'` al arrancar | Se arrancó antes de guardar las variables | Guardar Entorno y reimplementar |
| 17 | `Permission 'earthengine.maps.create' denied` | Cuenta de servicio solo con rol de lector | Añadir **Escritor de recursos de Earth Engine** en IAM (lápiz de la fila) |
| 18 | «Administrar permisos» no daba roles | Esa opción es para «quién usa la cuenta» | Ir a **IAM** del proyecto y editar la fila |
| 19 | Visor: «HTTP 404» al pedir la capa | `config.js` sin la URL → usa `/gee-api` inexistente | Activar `window.GEE_API_URL` en `config.js` y reimplementar el visor |
| 20 | Visor en el navegador del usuario: «Failed to fetch / No 'Access-Control-Allow-Origin'» | Con un navegador limpio SÍ funciona (servidor y CORS correctos) → algo del perfil (extensión, caché) o de la red | Probar en InPrivate; desactivar extensiones/borrar datos del sitio. Solución robusta pendiente: proxy `/gee-api/` en el nginx del visor (mismo origen, sin CORS) |
| 21 | `git init` en una carpeta dentro del HOME | El HOME ya es un repositorio | Crear la carpeta de despliegue aparte (`geoquebradas_deploy/`) y hacer `git init` ahí |
| 22 | Avisos `LF will be replaced by CRLF` al hacer commit | Windows | Inofensivo (el commit guarda LF) |
| 23 | Peticiones raras `/console/`, `/server-status`, `/login.action` en los registros | Escáneres automáticos de internet | Ignorar (responden 404) |
| 24 | Fallo de la clave pegada en Easypanel | JSON con saltos de línea | Pegar el JSON **en una sola línea** (`json.dumps`), sin comillas extra |

---

## 7. Cómo verificar cambios sin abrir el navegador a mano

Servir la carpeta y tomar una captura con Edge headless (usar los enlaces con hash de la sección 3):
```powershell
python -m http.server 8083   # en v3/
& "C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe" --headless=new --use-angle=swiftshader `
  --enable-unsafe-swiftshader --ignore-gpu-blocklist --virtual-time-budget=90000 --window-size=1910,920 `
  --screenshot=captura.png "http://localhost:8083/#w=0&gee=vis,pp&ext=sa"
node --check archivo.js      # revisar sintaxis del <script> extraído (sin ejecutar el visor)
```
Comprobar el servicio publicado sin navegador: `curl https://gee.oimas.online/salud` y `curl -H "Origin: https://geoquebradas.oimas.online" -D - https://gee.oimas.online/goes/pp` (debe traer `access-control-allow-origin`).

---

## 8. Cómo replicar o escalar

**Otra variante del visor (otros colores/textos):** copiar `v3/` a `vN/`; cambiar las variables de `:root`, `TEXTOS`, el logo y la etiqueta del wordmark; mantener `PRI` (los colores de nivel significan algo). Probar con capturas.
**Otro tema/otros datos:** cambiar `URL_*` y los campos de `renderB2`, `renderDetalle`, `renderAn`, la tabla y el CSV; ajustar `CATS` con las capas nuevas.
**Nueva capa ArcGIS:** añadir `[url, título]` en `CATS` (la leyenda con símbolos sale sola de `MapServer/legend`). Si es pesada, marcar el 5.º elemento en `1` (se dibuja solo al acercar).
**Nueva capa de Earth Engine:** en `goes_tiles.py` añadir un caso en `_construir(nombre)` (colección, máscara, `vis`, `leyenda`) y en `CATS` un elemento `['gee:nombre','Título']` + su entrada en `TEXTOS.gee`. Mismo flujo de teselas.
**Enlazar GEE con la línea de tiempo:** pedir la imagen de una ventana de ±10 días alrededor de `S.fecha` (por ejemplo Sentinel-2) en vez de la última.
**Producción estable:** proxy `/gee-api/` en `visor/nginx.conf`, cuenta de servicio dedicada, `CORS_ORIGINS` explícito, monitoreo de `/salud`, renovar el VPS antes del 2026-10-02, y decidir el dominio (la red MINAM bloquea `oimas.online`).
**Ideas no implementadas:** alertas por correo/WhatsApp por departamento, versión en inglés, comparar quebradas, portada con curvas de nivel o foto, tipografía Inter, miniaturas por quebrada (`getThumbURL` + `MediaLayer`), export de teselas a Cloud Storage para producción sin cuota de GEE.

---

## 9. Pendientes conocidos al cierre (2026-09-25)
- Cerrar el punto 20 del catálogo (falla de la capa GOES solo en el navegador del usuario): resultado del InPrivate o aplicar el proxy `/gee-api/`.
- Verificar con clics reales: cascada dep→prov→dist con zoom, buscador por texto, encender capas ArcGIS y sus leyendas, menú ⋮, reproducir la línea de tiempo, flechas de día, 3D, favoritos, imprimir, CSV, buscador de la tabla, vista móvil, cierre del panel GOES.
- Decisiones abiertas: tipografía (Arial/Inter), portada, redondeo de las píldoras Fecha/Limpiar.
- Borrar de Descargas el `.json` de la clave de la cuenta de servicio.
