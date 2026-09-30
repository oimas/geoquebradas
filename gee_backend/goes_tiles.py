"""
Servicio de teselas GOES-19 en vivo para el visor GeoQuebradas.

Reproduce la lógica del script de Code Editor (capas "GOES PP" y "GOES VIS"):
  - toma la imagen más reciente de NOAA/GOES/19/MCMIPF
  - PP : banda CMI_C13, se ocultan los valores > 2800, recorte al área, paleta 1300–3000
  - VIS: composición RGB CMI_C02, CMI_C03, CMI_C01 (min 64, max 5454, gamma 1.8)
y devuelve la URL de teselas ({z}/{x}/{y}) para que el visor la dibuje.

Las credenciales de Earth Engine viven SOLO aquí (nunca en el HTML).

Ejecutar (después de configurar las variables de entorno, ver README.md):
    uvicorn goes_tiles:app --host 0.0.0.0 --port 8090
"""
import json
import logging
import os
import time
import urllib.error
import urllib.request
from urllib.parse import quote
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import ee
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

# ───────────── configuración (variables de entorno) ─────────────
EE_PROJECT = os.environ["EE_PROJECT"]                       # proyecto de Google Cloud registrado en Earth Engine
EE_SERVICE_ACCOUNT = os.environ.get("EE_SERVICE_ACCOUNT")   # correo de la cuenta de servicio
EE_KEY_FILE = os.environ.get("EE_KEY_FILE")                 # ruta al JSON de la clave
EE_AREA_ASSET = os.environ.get("EE_AREA_ASSET")   # opcional: asset FeatureCollection con la geometría de `area`
EE_AREA_BBOX = [float(x) for x in os.environ.get("EE_AREA_BBOX", "-130,-65,-20,30").split(",")]   # O-S-E-N; se usa si no hay asset
#   ^ equivale a la variable `area` de tu script (no vino en el fragmento pegado). Para PROBAR no hace falta:
#     sin asset se recorta a un rectángulo amplio sobre Sudamérica y los océanos vecinos (EE_AREA_BBOX).
CORS_ORIGINS = os.environ.get("CORS_ORIGINS", "*").split(",")   # en producción: el dominio del visor
CACHE_SEGUNDOS = int(os.environ.get("CACHE_SEGUNDOS", "600"))    # GOES full disk publica cada ~10 min
SUMA_MINUTOS = int(os.environ.get("SUMA_MINUTOS", "20"))         # tu script suma 20 min a la hora mostrada

EE_KEY_JSON = os.environ.get("EE_KEY_JSON")                 # alternativa: contenido del JSON de la clave (útil en Easypanel)
if EE_SERVICE_ACCOUNT and EE_KEY_JSON:
    ee.Initialize(ee.ServiceAccountCredentials(EE_SERVICE_ACCOUNT, key_data=EE_KEY_JSON), project=EE_PROJECT)
elif EE_SERVICE_ACCOUNT and EE_KEY_FILE:
    ee.Initialize(ee.ServiceAccountCredentials(EE_SERVICE_ACCOUNT, EE_KEY_FILE), project=EE_PROJECT)
else:
    ee.Initialize(project=EE_PROJECT)   # usa las credenciales locales (earthengine authenticate)

COLECCION = "NOAA/GOES/19/MCMIPF"
AREA = ee.FeatureCollection(EE_AREA_ASSET).geometry() if EE_AREA_ASSET else ee.Geometry.Rectangle(EE_AREA_BBOX, geodesic=False)

PALETA_PP = ["bb16ff", "e241ff", "fd72ff", "ff1212", "ff353e", "ff8989", "2540ff", "4978ff", "45b2ff", "29973b",
             "38e44d", "e4ff50", "ffcf27", "ffc174", "a76238", "b35529", "b3b3b3", "939393", "626262"]
VIS_PP = {"bands": ["CMI_C13"], "min": 1300, "max": 3000, "palette": PALETA_PP}
VIS_VIS = {"bands": ["CMI_C02", "CMI_C03", "CMI_C01"], "min": 64, "max": 5454, "gamma": 1.8}
UMBRAL_PP = 2800   # `seleccion_rango_z`: CMI_C13 <= 2800

# Umbrales de "senamhi" (celdas de posible activacion), iguales a los del
# script GEOMIDAGRI/SSATMI (clases1/classes/senamhi): dos clases sobre
# CMI_C13 (1000,1950] y (1950,2150], vectorizadas a 5000 m y filtradas a
# poligonos con 10 o mas pixeles, para no tomar ruido de 1-2 pixeles.
UMBRAL_SENAMHI_INF = 1000
UMBRAL_SENAMHI_MEDIO = 1950
UMBRAL_SENAMHI_SUP = 2150
ESCALA_SENAMHI = 5000
CONTEO_MINIMO_SENAMHI = 10

# ───────────── terreno de la cuenca activa (piloto A08/D09) ─────────────
# Mismos umbrales y paletas que piloto_dem_divisoria_gee.js (V1, proyecto
# visor_geoquebradas/.claude/EVIDENCIAS/). MERIT Hydro es de libre uso para
# este tipo de visualizacion; revisar terminos de uso antes de redistribuir
# el dato crudo (no solo la tesela renderizada).
MERIT = ee.Image("MERIT/Hydro/v1_0_1")
UMBRAL_DRENAJE_SECUNDARIO_KM2 = 2
UMBRAL_DRENAJE_PRINCIPAL_KM2 = 20
VIS_ELEVACION = {"min": 0, "max": 5000,
                  "palette": ["173b73", "55a6c8", "91bd70", "e3d38b", "8b6b4a", "f2f0e8"]}
VIS_SOMBREADO = {"min": 0, "max": 255}
VIS_DRENAJE = {"min": 1, "max": 2, "palette": ["00bfff", "081a75"]}  # 1=secundario, 2=principal

# Consulta de ANA reusada solo para obtener la geometria de UNA cuenca por
# su CODIGO (misma capa que ya usa el proxy /capas_ana del visor). Solo
# lectura, sin credenciales.
ANA_UNIDADES_HIDRO_QUERY = (
    "https://geosnirh.ana.gob.pe/server/rest/services/ws_UnidadesHidro/"
    "MapServer/1/query"
)
_cache_geom_cuenca = {}   # codigo -> (expira_epoch, geojson_geometry)
CACHE_GEOM_CUENCA_SEGUNDOS = 6 * 3600   # igual que la cache de cuencas del visor

app = FastAPI(title="GeoQuebradas · GOES en vivo")
app.add_middleware(CORSMiddleware, allow_origins=CORS_ORIGINS, allow_methods=["GET"], allow_headers=["*"])
_cache = {}   # nombre -> (expira_epoch, respuesta)


def _ultima_imagen():
    """Imagen GOES más reciente. Se acota a las últimas horas antes de ordenar (la colección completa es enorme y ordenarla entera es lento)."""
    from datetime import timezone
    ahora_ms = int(datetime.now(timezone.utc).timestamp() * 1000)
    for horas in (6, 48):
        col = ee.ImageCollection(COLECCION).filterDate(ee.Date(ahora_ms - horas * 3600 * 1000), ee.Date(ahora_ms))
        if col.size().getInfo() > 0:
            return ee.Image(col.sort("system:time_start", False).first())
    raise RuntimeError("No hay imágenes GOES-19 en las últimas 48 horas")


def _construir(nombre):
    img = _ultima_imagen()
    ts_ms = int(img.get("system:time_start").getInfo())
    if nombre == "pp":
        c13 = img.select("CMI_C13")
        capa = img.updateMask(c13.lte(UMBRAL_PP)).select("CMI_C13").clip(AREA)
        vis = VIS_PP
        leyenda = {"tipo": "rampa", "paleta": PALETA_PP, "min": VIS_PP["min"], "max": VIS_PP["max"],
                   "nota": f"Canal 13 (valor digital). Se ocultan los valores > {UMBRAL_PP}."}
    elif nombre == "vis":
        capa = img.clip(AREA)
        vis = VIS_VIS
        leyenda = {"tipo": "rgb", "nota": "Composición RGB: canales 2, 3 y 1."}
    elif nombre == "senamhi":
        return _construir_senamhi(img, ts_ms)
    else:
        raise HTTPException(404, "Capa desconocida (use 'pp', 'vis' o 'senamhi').")
    url = capa.getMapId(vis)["tile_fetcher"].url_format
    hora = datetime.fromtimestamp(ts_ms / 1000, tz=ZoneInfo("America/Lima")) + timedelta(minutes=SUMA_MINUTOS)
    return {"url": url, "time_start_ms": ts_ms, "fecha_lima": hora.strftime("%d/%m/%Y %H:%M"), "leyenda": leyenda}


def _construir_senamhi(img, ts_ms):
    """Celdas de posible activacion (poligonos), igual que `senamhi` del
    script GEOMIDAGRI/SSATMI: no es una tesela, es una FeatureCollection
    con las celdas ya vectorizadas y filtradas por tamano minimo."""
    c13 = img.select("CMI_C13")
    clases1 = (ee.Image(1)
               .where(c13.gt(UMBRAL_SENAMHI_INF).And(c13.lte(UMBRAL_SENAMHI_MEDIO)), 2)
               .where(c13.gt(UMBRAL_SENAMHI_MEDIO).And(c13.lte(UMBRAL_SENAMHI_SUP)), 3))
    clases = clases1.updateMask(clases1.eq(2).Or(clases1.eq(3)))
    vectores = clases.clip(AREA).reduceToVectors(
        reducer=ee.Reducer.countEvery(),
        geometry=AREA,
        scale=ESCALA_SENAMHI,
        maxPixels=1e8,
    )
    activas = ee.FeatureCollection(vectores).filter(ee.Filter.gte("count", CONTEO_MINIMO_SENAMHI))
    coleccion = activas.getInfo()   # FeatureCollection real (geometria + propiedades)
    hora = datetime.fromtimestamp(ts_ms / 1000, tz=ZoneInfo("America/Lima")) + timedelta(minutes=SUMA_MINUTOS)
    return {
        "type": "FeatureCollection",
        "features": coleccion.get("features", []),
        "time_start_ms": ts_ms,
        "fecha_lima": hora.strftime("%d/%m/%Y %H:%M"),
        "umbral": {"inf": UMBRAL_SENAMHI_INF, "medio": UMBRAL_SENAMHI_MEDIO, "sup": UMBRAL_SENAMHI_SUP,
                   "escala_m": ESCALA_SENAMHI, "conteo_minimo": CONTEO_MINIMO_SENAMHI},
    }


def _geometria_cuenca(codigo):
    """Geometria (GeoJSON) de UNA cuenca de ANA por su CODIGO, en cache por
    CACHE_GEOM_CUENCA_SEGUNDOS. Misma fuente publica que ya consulta el
    proxy /capas_ana del visor; aqui solo se pide una entidad, no toda la
    capa. Sin resultado -> None (no se inventa un recorte)."""
    ahora = time.time()
    hit = _cache_geom_cuenca.get(codigo)
    if hit and hit[0] > ahora:
        return hit[1]
    where = "CODIGO=" + quote("'{}'".format(codigo))
    url = "{}?where={}&outFields=CODIGO&returnGeometry=true&f=geojson".format(
        ANA_UNIDADES_HIDRO_QUERY, where)
    peticion = urllib.request.Request(url, headers={"User-Agent": "geoquebradas-terreno/1.0"})
    with urllib.request.urlopen(peticion, timeout=20) as respuesta:
        coleccion = json.loads(respuesta.read())
    features = coleccion.get("features") or []
    if not features:
        return None
    geometria = features[0]["geometry"]
    _cache_geom_cuenca[codigo] = (ahora + CACHE_GEOM_CUENCA_SEGUNDOS, geometria)
    return geometria


def _construir_terreno(nombre, cuenca_codigo):
    """Elevacion, sombreado o drenaje de MERIT Hydro, recortados a UNA
    cuenca de ANA (piloto A08/D09: terreno de la cuenca activa). Sin
    cuenca_codigo no se sirve nada -- no es una capa nacional de fondo."""
    if not cuenca_codigo:
        raise HTTPException(400, "falta cuenca_codigo (CODIGO de la cuenca ANA activa)")
    geojson = _geometria_cuenca(cuenca_codigo)
    if geojson is None:
        raise HTTPException(404, "no se encontro la cuenca ANA con ese CODIGO")
    geometria = ee.Geometry(geojson)

    if nombre == "elevacion":
        capa = MERIT.select("elv").clip(geometria)
        vis = VIS_ELEVACION
        leyenda = {"tipo": "rampa", "nota": "Elevación MERIT Hydro (m; resolución aprox. 90 m)."}
    elif nombre == "sombreado":
        sombreado = ee.Terrain.hillshade(MERIT.select("elv"))
        capa = sombreado.clip(geometria)
        vis = VIS_SOMBREADO
        leyenda = {"tipo": "rampa", "nota": "Sombreado de relieve (hillshade) sobre MERIT Hydro."}
    elif nombre == "drenaje":
        upa = MERIT.select("upa")
        clases = (ee.Image(0)
                  .where(upa.gte(UMBRAL_DRENAJE_SECUNDARIO_KM2), 1)
                  .where(upa.gte(UMBRAL_DRENAJE_PRINCIPAL_KM2), 2))
        capa = clases.selfMask().clip(geometria)
        vis = VIS_DRENAJE
        leyenda = {"tipo": "clases",
                    "clases": [{"valor": 1, "color": VIS_DRENAJE["palette"][0],
                                "nota": f"Drenaje secundario (UPA {UMBRAL_DRENAJE_SECUNDARIO_KM2}-{UMBRAL_DRENAJE_PRINCIPAL_KM2} km²)"},
                               {"valor": 2, "color": VIS_DRENAJE["palette"][1],
                                "nota": f"Cauce principal (UPA ≥ {UMBRAL_DRENAJE_PRINCIPAL_KM2} km²)"}],
                   "nota": "Red de drenaje MERIT Hydro por umbral de área aguas arriba (UPA), igual que el piloto V1."}
    else:
        raise HTTPException(404, "capa de terreno desconocida (use 'elevacion', 'sombreado' o 'drenaje')")

    url = capa.getMapId(vis)["tile_fetcher"].url_format
    return {"url": url, "cuenca_codigo": cuenca_codigo, "leyenda": leyenda,
            "nota_general": "Terreno de referencia (MERIT Hydro), no es una divisoria de aguas validada."}


@app.get("/goes/{nombre}")
def goes(nombre: str):
    ahora = time.time()
    hit = _cache.get(nombre)
    if hit and hit[0] > ahora:
        return hit[1]
    try:
        resp = _construir(nombre)
    except HTTPException:
        raise
    except Exception as e:   # error de Earth Engine (cuota, permisos, credenciales, colección vacía…)
        logging.exception("Fallo al construir la capa %s", nombre)   # queda en los registros del servidor
        # 500 y no 502: Cloudflare reemplaza los 502/504 por su propia página y oculta el mensaje
        raise HTTPException(500, f"Earth Engine: {e}")
    _cache[nombre] = (ahora + CACHE_SEGUNDOS, resp)
    return resp


@app.get("/terreno/{nombre}")
def terreno(nombre: str, cuenca_codigo: str = ""):
    # Cache propia (clave = nombre + cuenca): el terreno no cambia como GOES,
    # pero igual se evita recalcular en cada clic mientras la cuenca activa
    # no cambie.
    clave = f"{nombre}:{cuenca_codigo}"
    ahora = time.time()
    hit = _cache.get(clave)
    if hit and hit[0] > ahora:
        return hit[1]
    try:
        resp = _construir_terreno(nombre, cuenca_codigo)
    except HTTPException:
        raise
    except Exception as e:
        logging.exception("Fallo al construir terreno %s para cuenca %s", nombre, cuenca_codigo)
        raise HTTPException(500, f"Earth Engine: {e}")
    _cache[clave] = (ahora + CACHE_SEGUNDOS, resp)
    return resp


@app.get("/salud")
def salud():
    return {"ok": True, "coleccion": COLECCION}
