# quebrada_francesa — Decisiones de diseño (rediseño V2)

> **Qué es este archivo:** registro de las decisiones que se tomaron con el usuario el 2026-09-25 para rediseñar
> el visor "quebrada_francesa". Sirve para retomar si se pierde la sesión.
> - Visor anterior (congelado): `v1/index.html` y su documentación `VISOR_V1.md`.
> - Referencia visual aprobada del rediseño: `esqueleto.html` (distribución) y `maqueta_capas.html` (formato de capas). Respaldos `esqueleto.bak*.html`.
> - El código del rediseño se construye en `v2/` (no sobrescribe V1).
> - **Regla del usuario:** antes de ejecutar/abrir la última versión, preguntar.

## Fuentes de inspiración
1. **Géoportail (Francia)** — imagen de referencia del usuario: cabecera con MENÚ, buscador, iconos; panel derecho con título y botón; minimapa y escala; botón de capas con contador.
2. **Mapping Global China** (`mapglobalchina.com/maps/investment`) — vista real: título arriba, barra de chips flotante sobre el mapa, herramientas arriba a la derecha, ventana de bienvenida con consejos, línea de tiempo, y un panel de detalle por selección (nombre, tarjetas, gráfico de área, variación, treemap, tarjetas paginadas).
3. **IGN Argentina** — modelo de capas: categorías en bloque que se expanden con la leyenda dentro, buscador de capas, contador, menú de tres puntos.
4. **Dibujo del usuario** (imagen 2): dos bloques a la derecha, leyenda abajo, 2D/3D junto al zoom.

## Decisiones tomadas
1. **Nombre:** `quebrada_francesa`. Es la primera de varias versiones/variantes del visor.
2. **El mapa manda:** ocupa todo el alto entre cabecera (76 px) y pie (44 px) y todo el ancho menos el panel. Nada lo tapa salvo controles pequeños.
3. **Panel a la DERECHA** (como Géoportail y como ya estaba construido; se descartó moverlo a la izquierda). 400 px, plegable con flecha.
4. **Panel en 3 bloques apilados:**
   - Bloque 1: título, fecha, ámbito, aviso, botón "Ver detalle".
   - Bloque 2: **Indicadores** (5 tarjetas con franja de color: quebradas, población, viviendas, red vial, superficie agrícola).
   - Bloque 3: **Leyenda** (niveles con conteo). Cambió de posición: originalmente era el 2.
5. **Leyenda:** compacta; cada nivel es un botón que **filtra** mapa, cifras y listas; siempre visible; **solo se oculta si el usuario lo decide** (y se recuerda). Debajo, la leyenda de las capas encendidas.
6. **Chips sobre el mapa:** Filtros (con contador), Fecha, Departamento, Limpiar. **Los niveles NO van en los chips** (están en la leyenda).
7. **Controles del mapa:** zoom y 2D/3D arriba a la izquierda; minimapa + escala abajo a la izquierda; línea de tiempo abajo al centro; localizar y pantalla completa abajo a la derecha.
8. **Cabecera en una sola fila:** MENÚ, logo, pestañas Situación / Detalle / Acerca de, buscador con "+", ayuda, imprimir, Favoritos, Compartir. Sin franja de título ni tarjetas de acceso aparte.
9. **Debajo del mapa (al bajar):** Sección 2 "Detalle por quebrada" (ancho completo, con ranking y tabla) y Sección 3 "Acerca de". Las pestañas Detalle y Acerca de hacen scroll hasta ellas.
10. **Riel de botones al borde del panel:** flecha (plegar), **Capas** (con contador), **Herramientas**, **Análisis** (reemplaza a "Leyen.", que sobraba al existir el bloque 3).
11. **Vista Capas (formato IGN, paleta propia):** 4 categorías (Información de referencia, Zona efectiva de análisis, Exposición directa, Agravamiento ambiental-sanitario), buscador, "Solo activas", interruptores, menú de tres puntos (opacidad, acercar, información de la fuente), símbolos reales tomados de la leyenda de cada servicio, marca "capa pesada" en canales y áreas agrícolas.
12. **Vista Análisis (formato del panel chino):** cambia con la selección (Perú / departamento / distrito / quebrada): ruta, nombre, 3 tarjetas, gráfico de área por día, etiqueta de variación, cuadros proporcionales por nivel, tarjetas de quebradas paginadas.
13. **Paleta:** se mantiene la original (blanco, azul marino `#14213d`, azul `#0f5ca8`, verde azulado `#00a99d`; niveles `#6b7e96 / #2fbf71 / #ffd400 / #f97316 / #c1121f`). No se adopta el azul sólido de IGN. Sin emoticones.
14. **Datos:** si la capa vigente está vacía, cargar la última fecha con datos del histórico y avisarlo. Historial por `quebrada_uid` (no `eval_id`). Textos editables agrupados en `TEXTOS`.
15. **Fuera de alcance por ahora:** alertas por correo/WhatsApp, versión en inglés, comparar quebradas.

## Decisiones pendientes / a confirmar
- Qué hace exactamente "Ver detalle" del bloque 1 (V2 asume: baja a la Sección 2 si hay quebrada seleccionada).
- Contenido final de Herramientas (V2 asume: mapa base, opacidad, vista de todo el Perú, CSV, enlace, limpiar).
- Línea de tiempo: V2 asume últimos 30 días con datos y botón de reproducir (avance de 1,5 s por día).
- Ventana de bienvenida: V2 asume 3 consejos, se muestra la primera vez.

## Orden de construcción acordado
1. Estructura: cabecera, mapa a pantalla completa, panel de 3 bloques, chips.
2. Capas (formato IGN) y Análisis.
3. Secciones 2 y 3 debajo del mapa.
4. Línea de tiempo y ventana de bienvenida.

## Estado (2026-09-25, cierre del día)
`v2/index.html` construido y ejecutado en un navegador automático con datos reales; ver `v2/README.md` para lo verificado y lo pendiente de probar con clics.
Correcciones hechas tras la primera ejecución: rotulado de los cuadros por nivel en Análisis, título largo de quebrada, y parámetros de enlace (`v`, `s`, `w`).

## Ajustes pedidos tras probar V2 (2026-09-25) — aplicados en `v2/index.html`, pendientes de ejecutar/verificar
Respaldo previo a estos ajustes: `v2/index.bak_pre_ajustes.html`.
1. **Paleta homogénea:** solo azul, turquesa, blanco y gris. Se quitaron las líneas/franjas de color de las tarjetas (indicadores, análisis, tarjetas de quebradas, orientación, componentes) y el naranja del logotipo. Se mantienen los colores con significado: niveles de prioridad (leyenda, chips de nivel, cuadros por nivel, ranking, medidor) y semáforo del aviso.
2. **Detalle por quebrada:** panel grande de la quebrada seleccionada (identidad + IPT-AQ + lectura rápida generada, por qué, orientación) y debajo las demás tarjetas del original (elementos expuestos, aviso 7 días, persistencia, gráfico), más "Comparar con otras quebradas" (ranking y tabla). Sin selección: las 6 más urgentes del día.
3. **Acerca de:** ocupa todo el ancho en cuadrícula (qué es / IPT-AQ / recursos / fuentes) con la tipografía del panel.
4. **Filtros en el buscador:** departamento → provincia → distrito dentro de la ventana del buscador ("+"); el mapa se acerca a medida que se elige cada nivel.
5. **Barra de filtros rediseñada:** fecha con flechas de día anterior/siguiente y calendario, chip "Ubicación" con el recorrido elegido, y "Limpiar".

## V3 (2026-09-25): todos los ajustes anteriores aplicados sobre una copia
`v3/` = copia de `v2/` + paleta A, cabecera con buscador central y filtros de ubicación, riel con iconos, detalle y Acerca según los mockups, ~20 iconos.
Volver a `v2/` si algo se daña. Estado: escrito, sintaxis revisada, **sin ejecutar** (regla: preguntar antes). Ver `v3/README.md`.
Pendiente de decidir por el usuario: tipografía (se dejó Arial), franja de portada con curvas de nivel o foto (no incluida).

Estado V3: ejecutada en navegador automático; ver `v3/README.md` (verificado / no verificado). Corregido el bug de estilos de botones también en v2.

## Cierre de sesión (2026-09-25): estado hasta aquí
- **Versión de trabajo actual: `v3/`** (puerto 8083). `v2/` (8082) es el punto de retorno; `v1/` la primera. Respaldos: `v3/index.bak_pre_bloques.html` (antes de los bloques de cabecera).
- **Cabecera V3 (final):** botón de menú (verde bosque) a la izquierda; logo + wordmark; pestañas Situación / Detalle / Acerca de con esquinas poco redondeadas; buscador al centro con filtro dep → prov → dist y etiqueta de ubicación; **4 bloques cuadrados a la derecha** (Ayuda e Imprimir en azul petróleo; Favoritos y Compartir en verde) de alto completo, sin redondeo.
- **Pendiente de decidir:** tipografía (se dejó Arial; alternativa Inter), franja de portada con curvas de nivel o foto, redondeo de los chips Fecha/Limpiar.
- **Pendiente de verificar con clics reales:** cascada dep→prov→dist con zoom, buscador por texto, encender capas + leyendas, menú ⋮, reproducir línea de tiempo, flechas de día, 3D, favoritos, imprimir, CSV, buscador de tabla, móvil.
- **Idea nueva (sin implementar):** imágenes satelitales de Google Earth Engine como capas superpuestas (categoría "Imágenes satelitales" en el panel de Capas), sincronizables con la línea de tiempo. Ver la conversación del 2026-09-25 para las opciones (URL de teselas vía backend / teselas exportadas / miniaturas por quebrada).

## Capa GOES en vivo (2026-09-25) — escrita, NO ejecutada
El usuario quiere en el visor solo su capa en vivo de GEE basada en GOES (script "GOES PP" y "GOES VIS").
- **Servicio:** `gee_backend/goes_tiles.py` (FastAPI + earthengine-api) reproduce esa lógica y devuelve la URL de teselas; ver `gee_backend/README.md`. Necesita credenciales de Earth Engine del usuario (cuenta de servicio). Falta confirmar la variable `area` de su script (no vino en el fragmento pegado).
- **Visor v3:** nueva categoría "Imágenes satelitales en vivo" (primera del panel de Capas) con "GOES-19 · nubes frías (canal 13)" y "GOES-19 · visible (RGB 2-3-1)". Pide la URL al encender la capa, se renueva cada 10 min, muestra la fecha GOES (hora de Lima) y una leyenda con la paleta. Respaldo previo: `v3/index.bak_pre_gee.html`.
- **Sin probar:** todo el flujo (necesita el servicio y las credenciales). Endpoint del visor: `http://localhost:8090` en local, `/gee-api` en producción (const `GEE_API`).

### Resultado de la prueba GOES (2026-09-25, con la cuenta oimas854@gmail.com y proyecto `ee-oimas854`)
- Servicio levantado en `http://localhost:8090` (uvicorn, credenciales locales de `earthengine authenticate`, sin cuenta de servicio). `/goes/vis` y `/goes/pp` responden; fecha GOES 25/09/2026 10:30 (Lima).
- Las teselas de Earth Engine se dibujan dentro de ArcGIS (CORS OK): **GOES visible (RGB)** se ve sobre el mapa (nubes sobre el Pacífico frente a Arequipa/Tacna, lago Titicaca).
- **GOES PP (canal 13, valores <= 2800)**: funciona, pero a esa hora casi no hay nubes frías: 0,1–1,8 % de los píxeles con dato en las teselas de Perú. Es un comportamiento esperado de la máscara, no un fallo.
- Ajuste hecho al servicio: acota la colección a las últimas 6 h (48 h como respaldo) antes de ordenar; sin eso tardaba más de 90 s.
- Parámetro de enlace nuevo en v3: `#gee=pp` o `#gee=vis` enciende la capa al cargar.

### GOES: ajustes del 2026-09-25 (segunda vuelta)
- Canal 13 (PP) ahora se dibuja **encima** del RGB (orden de la categoría: visible primero, PP después).
- Cobertura por defecto: **toda Sudamérica** (`EE_AREA_BBOX=-92,-57,-30,14`); "Acercar a la capa" y `#ext=sa` llevan a esa extensión; `#gee=vis,pp` enciende ambas.
- Servicio reiniciado con el nuevo recorte. Para dejarlo permanente: ver "Dejarlo permanente en tu servidor" en `gee_backend/README.md` (Dockerfile listo, `EE_KEY_JSON`, subdominio, `window.GEE_API_URL`).
- Riesgos anotados: VPS vence 2026-10-02; `oimas.online` "Not Found" desde 2026-09-21; bloqueo de la red MINAM al dominio; cuotas de Earth Engine.

### GOES: panel sobre el mapa y minimapa (2026-09-25, tercera vuelta)
- **Recorte ampliado** a `-130,-65,-20,30` (Sudamérica + océanos vecinos) para que la imagen no termine en un borde visible.
- **Panel "GOES-19 en vivo"** flotante sobre el mapa (arriba a la derecha, junto al riel): título y texto de cada capa activa (textos en `TEXTOS.gee`, tomados del panel de tu visor GEE), **barra de colores** con 1300 / 2150 / 3000, nota de máscara (> 2800 oculto), **fecha GOES (hora de Lima)** y fuente. Se cierra con la ×. La leyenda del panel derecho ya no repite las capas GEE.
- **Minimapa:** al encender una capa GOES muestra su miniatura y se aleja a toda Sudamérica (escala 1:150 000 000); al apagarla vuelve al encuadre de Perú.
- Botón "Limpiar" con fondo blanco para que se lea sobre imágenes. Respaldo previo: `v3/index.bak_pre_panelgoes.html`.

### GOES: panel compacto (2026-09-25, cuarta vuelta)
El panel "GOES-19 en vivo" pasó a ser un cuadro pequeño (200 px) **encima del minimapa**, con pocas palabras: nombre corto de cada capa activa (Visible (RGB) / Canal 13 · nubes frías), barra de colores 1300–3000 y "dd/mm hh:mm · Lima". Se quitaron los textos largos y la fuente (siguen en `gee_backend/README.md`). Se cierra con la ×. Respaldo previo: `v3/index.bak_pre_panelchico.html`.
