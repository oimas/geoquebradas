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
import logging
import os
import time
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
    else:
        raise HTTPException(404, "Capa desconocida (use 'pp' o 'vis').")
    url = capa.getMapId(vis)["tile_fetcher"].url_format
    hora = datetime.fromtimestamp(ts_ms / 1000, tz=ZoneInfo("America/Lima")) + timedelta(minutes=SUMA_MINUTOS)
    return {"url": url, "time_start_ms": ts_ms, "fecha_lima": hora.strftime("%d/%m/%Y %H:%M"), "leyenda": leyenda}


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


@app.get("/salud")
def salud():
    return {"ok": True, "coleccion": COLECCION}
