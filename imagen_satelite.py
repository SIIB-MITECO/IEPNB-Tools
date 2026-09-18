"""
/***************************************************************************
 * IEPNB Tools - Herramientas para el Inventario Español (MITECO)        *
 * *
 * Copyright (C) 2026 Rodrigo Saz-Orozco Maier (IEPNB - MITECO)          *
 * Email: rsazorozco@miteco.es                                           *
 * *
 * This program is free software; you can redistribute it and/or modify  *
 * it under the terms of the GNU General Public License as published by  *
 * the Free Software Foundation; either version 3 of the License, or     *
 * (at your option) any later version.                                   *
 ***************************************************************************/

Ver Imagen - Para un punto (2x2 km fijos) o un área dibujada a mano (con
límite de superficie), y una fecha aproximada, localiza la adquisición
Sentinel-2 L2A real más despejada de nubes (reutilizando la misma búsqueda
que la Firma Espectral) y descarga la imagen real de la zona -- color real,
falso color infrarrojo, o un índice coloreado -- como GeoTIFF, cargándola
directamente como capa ráster en el proyecto de QGIS.
"""

import json
import tempfile
import os

from qgis.PyQt.QtCore import Qt, QUrl, QByteArray, QEventLoop, pyqtSignal
from qgis.PyQt.QtGui import QColor
from qgis.PyQt import QtNetwork
from qgis.core import (QgsNetworkAccessManager, QgsRasterLayer, QgsProject,
                       QgsCoordinateReferenceSystem, QgsCoordinateTransform, QgsPointXY,
                       QgsGeometry, QgsWkbTypes, QgsRasterShader, QgsColorRampShader,
                       QgsSingleBandPseudoColorRenderer)
from qgis.gui import QgsMapTool, QgsRubberBand

from .config import CDSE_PROCESS_URL, VER_IMAGEN_MAX_PX, INDICE_FORMULAS
from .indices_historicos import _epsg_utm, COLOR_POR_INDICE

# Valor centinela para píxeles inválidos (nube/sombra/fuera de escena) en los
# GeoTIFF de índice de una sola banda -- muy por debajo de cualquier valor
# real de estos índices, para poder marcarlo como NoData al cargar la capa.
_VALOR_NODATA_INDICE = -9999.0

# Rango de visualización por defecto para el estilo de QGIS. La mayoría de
# índices van de -1 a 1; BAI y CIRE no tienen techo fijo, así que usamos un
# rango práctico basado en valores habituales en vez de su rango teórico.
_RANGO_VISUAL_INDICE = {
    "BAI": (0, 3),
    "CIRE": (0, 8),
}


# =====================================================================
# HERRAMIENTAS DE MAPA
# =====================================================================

class ImagenPuntoTool(QgsMapTool):
    """Clic único -> callback(lat, lon). Usa el cuadrado fijo de 2x2 km."""

    def __init__(self, canvas, callback):
        super().__init__(canvas)
        self.canvas = canvas
        self.callback = callback
        self.setCursor(Qt.CursorShape.CrossCursor)

    def canvasReleaseEvent(self, event):
        point = self.toMapCoordinates(event.pos())
        crs_src = self.canvas.mapSettings().destinationCrs()
        crs_dest = QgsCoordinateReferenceSystem("EPSG:4326")
        transform = QgsCoordinateTransform(crs_src, crs_dest, QgsProject.instance())
        point_wgs = transform.transform(point)
        self.callback(point_wgs.y(), point_wgs.x())


class ImagenAreaTool(QgsMapTool):
    """Dibuja un polígono a mano: clic izquierdo añade vértices, clic derecho
    (con 3+ vértices) termina y emite polygon_finished con la geometría ya en
    EPSG:4326. Mismo patrón que ManualPolygonTool en identify.py."""
    polygon_finished = pyqtSignal(object)

    def __init__(self, canvas):
        super().__init__(canvas)
        self.canvas = canvas
        self.points = []
        self.rubber = QgsRubberBand(canvas, QgsWkbTypes.GeometryType.PolygonGeometry)
        self.rubber.setColor(QColor(30, 136, 229, 180))
        self.rubber.setWidth(2)
        self.setCursor(Qt.CursorShape.CrossCursor)

    def canvasPressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            p = self.toMapCoordinates(event.pos())
            self.points.append(QgsPointXY(p))
            if len(self.points) == 1:
                self.rubber.addPoint(p, True)
            self.rubber.addPoint(p, True)
            self.rubber.show()
        elif event.button() == Qt.MouseButton.RightButton and len(self.points) > 2:
            crs_src = self.canvas.mapSettings().destinationCrs()
            crs_dest = QgsCoordinateReferenceSystem("EPSG:4326")
            transform = QgsCoordinateTransform(crs_src, crs_dest, QgsProject.instance())
            puntos_wgs = [transform.transform(p) for p in self.points]
            geom_wgs = QgsGeometry.fromPolygonXY([puntos_wgs])
            self.polygon_finished.emit(geom_wgs)
            self.deactivate()

    def canvasMoveEvent(self, event):
        if len(self.points) > 0:
            self.rubber.movePoint(self.toMapCoordinates(event.pos()))

    def deactivate(self):
        self.points = []
        self.rubber.reset(QgsWkbTypes.GeometryType.PolygonGeometry)
        super().deactivate()


# =====================================================================
# GEOMETRÍA / LÍMITE DE ÁREA
# =====================================================================

def _bbox_utm(lat, lon, lado_m=2000):
    """Cuadrado de lado_m metros centrado en (lat, lon), en la UTM que le
    corresponde. Devuelve (bbox=[minx,miny,maxx,maxy], crs_uri)."""
    epsg_utm = _epsg_utm(lat, lon)
    crs_origen = QgsCoordinateReferenceSystem("EPSG:4326")
    crs_utm = QgsCoordinateReferenceSystem(f"EPSG:{epsg_utm}")
    transform = QgsCoordinateTransform(crs_origen, crs_utm, QgsProject.instance())
    punto_utm = transform.transform(QgsPointXY(lon, lat))
    x, y = punto_utm.x(), punto_utm.y()
    d = lado_m / 2
    bbox = [x - d, y - d, x + d, y + d]
    crs_uri = f"http://www.opengis.net/def/crs/EPSG/0/{epsg_utm}"
    return bbox, crs_uri


def calcular_area_km2(geom_wgs84):
    """Área real del polígono (dibujado en EPSG:4326) en km², calculada
    reproyectando a la UTM de su centroide -- igual que hacemos para el
    cuadrado del punto, para tener metros de verdad y no grados."""
    centroide = geom_wgs84.centroid().asPoint()
    epsg_utm = _epsg_utm(centroide.y(), centroide.x())
    crs_origen = QgsCoordinateReferenceSystem("EPSG:4326")
    crs_utm = QgsCoordinateReferenceSystem(f"EPSG:{epsg_utm}")
    transform = QgsCoordinateTransform(crs_origen, crs_utm, QgsProject.instance())
    geom_utm = QgsGeometry(geom_wgs84)
    geom_utm.transform(transform)
    return geom_utm.area() / 1_000_000.0


def _geojson_y_tamano_area(geom_wgs84):
    """Para un polígono ya validado (dentro del límite de área): devuelve
    (geometria_geojson, ancho_px, alto_px), con el tamaño de píxel
    aproximando 10 m/píxel (resolución nativa de Sentinel-2) hasta el tope
    VER_IMAGEN_MAX_PX por lado."""
    poligono = geom_wgs84.asPolygon()
    anillo_exterior = [[p.x(), p.y()] for p in poligono[0]]
    geojson = {"type": "Polygon", "coordinates": [anillo_exterior]}

    centroide = geom_wgs84.centroid().asPoint()
    epsg_utm = _epsg_utm(centroide.y(), centroide.x())
    crs_origen = QgsCoordinateReferenceSystem("EPSG:4326")
    crs_utm = QgsCoordinateReferenceSystem(f"EPSG:{epsg_utm}")
    transform = QgsCoordinateTransform(crs_origen, crs_utm, QgsProject.instance())
    bbox_utm = transform.transformBoundingBox(geom_wgs84.boundingBox())
    ancho_m, alto_m = bbox_utm.width(), bbox_utm.height()

    ancho_px = min(VER_IMAGEN_MAX_PX, max(64, round(ancho_m / 10)))
    alto_px = min(VER_IMAGEN_MAX_PX, max(64, round(alto_m / 10)))
    return geojson, ancho_px, alto_px


# =====================================================================
# EVALSCRIPTS DE VISUALIZACIÓN (Process API, no Statistical)
# =====================================================================

def _evalscript_color_real():
    return """//VERSION=3
function setup() {
  return { input: ["B02", "B03", "B04", "dataMask"], output: { bands: 4 } };
}
function evaluatePixel(s) {
  return [2.5 * s.B04, 2.5 * s.B03, 2.5 * s.B02, s.dataMask];
}
"""


def _evalscript_falso_color():
    return """//VERSION=3
function setup() {
  return { input: ["B03", "B04", "B08", "dataMask"], output: { bands: 4 } };
}
function evaluatePixel(s) {
  return [2.5 * s.B08, 2.5 * s.B04, 2.5 * s.B03, s.dataMask];
}
"""


def _evalscript_indice_valor(nombre_indice):
    """Evalscript genérico para CUALQUIER índice de INDICE_FORMULAS (misma
    fórmula que usa el Índice Histórico): devuelve el VALOR real del índice
    en una sola banda FLOAT32 -- no un color ya cocinado -- para que QGIS
    pueda mostrarlo con su propio estilo y, a la vez, se pueda inspeccionar
    el valor exacto de cada píxel o reclasificarlo más tarde."""
    info = INDICE_FORMULAS[nombre_indice]
    bandas_js = ", ".join(f'"{b}"' for b in info["bandas"])
    formula = info["formula"]
    return f"""//VERSION=3
function setup() {{
  return {{
    input: [{{ bands: [{bandas_js}, "SCL", "dataMask"], units: "DN" }}],
    output: {{ bands: 1, sampleType: "FLOAT32" }}
  }};
}}
function evaluatePixel(samples) {{
  let valido = samples.dataMask;
  if (samples.SCL == 3 || samples.SCL == 8 || samples.SCL == 9 || samples.SCL == 10) {{
    valido = 0;
  }}
  if (!valido) {{
    return [{_VALOR_NODATA_INDICE}];
  }}
  let valor = {formula};
  return [valor];
}}
"""


ESTILOS_RGB = {
    "Color real": _evalscript_color_real,
    "Falso color infrarrojo": _evalscript_falso_color,
}

# Los estilos de índice reutilizan exactamente las mismas 11 fórmulas (y
# categorías) que ya tiene el Índice Histórico -- no se duplican a mano.
ESTILOS_INDICE = list(INDICE_FORMULAS.keys())

# Diccionario único para poder resolver el evalscript de cualquier estilo
# (RGB o índice) desde un solo sitio.
ESTILOS_IMAGEN = dict(ESTILOS_RGB)
ESTILOS_IMAGEN.update({nombre: (lambda n=nombre: _evalscript_indice_valor(n)) for nombre in ESTILOS_INDICE})


def es_estilo_indice(estilo):
    return estilo in ESTILOS_INDICE


# =====================================================================
# DESCARGA
# =====================================================================

def _peticion_process_api(token, cuerpo):
    network_manager = QgsNetworkAccessManager.instance()
    request = QtNetwork.QNetworkRequest(QUrl(CDSE_PROCESS_URL))
    request.setHeader(QtNetwork.QNetworkRequest.KnownHeaders.ContentTypeHeader, "application/json")
    request.setRawHeader(b"Authorization", f"Bearer {token}".encode("utf-8"))
    request.setRawHeader(b"Accept", b"image/tiff")

    loop = QEventLoop()
    reply = network_manager.post(request, QByteArray(json.dumps(cuerpo).encode("utf-8")))
    reply.finished.connect(loop.quit)
    loop.exec()

    raw = bytes(reply.readAll())
    error = reply.error()
    content_type = bytes(reply.rawHeader(b"Content-Type")).decode("utf-8", "ignore")
    reply.deleteLater()

    if error != QtNetwork.QNetworkReply.NetworkError.NoError or "image" not in content_type:
        # En error, la Process API devuelve JSON legible en vez de la imagen
        try:
            detalle = json.loads(raw)
        except Exception:
            detalle = raw.decode("utf-8", "ignore") or str(error)
        raise RuntimeError(f"Error consultando la Process API: {detalle}")
    return raw


def _guardar_tiff(raw, estilo, fecha, etiqueta_ubicacion):
    carpeta = os.path.join(tempfile.gettempdir(), "iepnb_tools_imagenes")
    os.makedirs(carpeta, exist_ok=True)
    limpio = estilo.replace(" ", "_").replace("(", "").replace(")", "")
    nombre = f"s2_{limpio}_{fecha.strftime('%Y%m%d')}_{etiqueta_ubicacion}.tif"
    ruta = os.path.join(carpeta, nombre)
    with open(ruta, "wb") as f:
        f.write(raw)
    return ruta


def descargar_imagen_punto(token, lat, lon, estilo, fecha, lado_m=2000, tam_px=512):
    """Descarga la imagen (GeoTIFF RGBA) del día exacto dado, cuadrado fijo
    de lado_m metros centrado en el punto."""
    bbox, crs_uri = _bbox_utm(lat, lon, lado_m)
    desde = fecha.strftime("%Y-%m-%dT00:00:00Z")
    hasta = fecha.strftime("%Y-%m-%dT23:59:59Z")

    cuerpo = {
        "input": {
            "bounds": {"bbox": bbox, "properties": {"crs": crs_uri}},
            "data": [{
                "type": "sentinel-2-l2a",
                "dataFilter": {"timeRange": {"from": desde, "to": hasta}, "maxCloudCoverage": 100}
            }]
        },
        "output": {
            "width": tam_px, "height": tam_px,
            "responses": [{"identifier": "default", "format": {"type": "image/tiff"}}]
        },
        "evalscript": ESTILOS_IMAGEN[estilo]()
    }
    raw = _peticion_process_api(token, cuerpo)
    return _guardar_tiff(raw, estilo, fecha, f"{lat:.5f}_{lon:.5f}")


def descargar_imagen_area(token, geom_wgs84, estilo, fecha):
    """Descarga la imagen (GeoTIFF RGBA) recortada al polígono dibujado
    (no solo su rectángulo envolvente). El área ya debe haberse validado
    contra VER_IMAGEN_MAX_AREA_KM2 antes de llamar a esta función."""
    geojson, ancho_px, alto_px = _geojson_y_tamano_area(geom_wgs84)
    desde = fecha.strftime("%Y-%m-%dT00:00:00Z")
    hasta = fecha.strftime("%Y-%m-%dT23:59:59Z")

    cuerpo = {
        "input": {
            "bounds": {
                "geometry": geojson,
                "properties": {"crs": "http://www.opengis.net/def/crs/EPSG/0/4326"}
            },
            "data": [{
                "type": "sentinel-2-l2a",
                "dataFilter": {"timeRange": {"from": desde, "to": hasta}, "maxCloudCoverage": 100}
            }]
        },
        "output": {
            "width": ancho_px, "height": alto_px,
            "responses": [{"identifier": "default", "format": {"type": "image/tiff"}}]
        },
        "evalscript": ESTILOS_IMAGEN[estilo]()
    }
    raw = _peticion_process_api(token, cuerpo)
    centroide = geom_wgs84.centroid().asPoint()
    return _guardar_tiff(raw, estilo, fecha, f"area_{centroide.y():.5f}_{centroide.x():.5f}")


def _aplicar_estilo_indice(capa, estilo):
    """Estilo de QGIS (pseudocolor de banda única) para que un ráster de
    índice se vea coloreado igual que antes, pero sin cocinar el color en
    el propio dato -- el valor real de cada píxel sigue ahí, consultable
    con "Identificar" o reclasificable más tarde."""
    capa.dataProvider().setNoDataValue(1, _VALOR_NODATA_INDICE)

    minimo, maximo = _RANGO_VISUAL_INDICE.get(estilo, (-1, 1))
    color_bajo = QColor("#8d6e63")             # tono neutro (tierra) para valores bajos, en todos los índices
    color_medio = QColor("#fff9c4")            # amarillo pálido, punto medio
    color_alto = QColor(COLOR_POR_INDICE.get(estilo, "#2e7d32"))  # color propio del índice para valores altos

    shader = QgsRasterShader()
    rampa = QgsColorRampShader()
    rampa.setColorRampType(QgsColorRampShader.Type.Interpolated)
    rampa.setColorRampItemList([
        QgsColorRampShader.ColorRampItem(minimo, color_bajo, f"{minimo}"),
        QgsColorRampShader.ColorRampItem((minimo + maximo) / 2, color_medio, "medio"),
        QgsColorRampShader.ColorRampItem(maximo, color_alto, f"{maximo}"),
    ])
    shader.setRasterShaderFunction(rampa)
    renderizador = QgsSingleBandPseudoColorRenderer(capa.dataProvider(), 1, shader)
    capa.setRenderer(renderizador)
    capa.triggerRepaint()


def cargar_capa_imagen(ruta, estilo, fecha, etiqueta_ubicacion):
    """Carga el GeoTIFF descargado como capa ráster del proyecto QGIS actual.
    Si el estilo es un índice (no RGB), aplica además el pseudocolor de
    QGIS conservando el valor real subyacente."""
    nombre_capa = f"Sentinel-2 {estilo} - {fecha.strftime('%d-%m-%Y')} ({etiqueta_ubicacion})"
    capa = QgsRasterLayer(ruta, nombre_capa)
    if not capa.isValid():
        raise RuntimeError("El GeoTIFF descargado no es una capa ráster válida.")
    if es_estilo_indice(estilo):
        _aplicar_estilo_indice(capa, estilo)
    QgsProject.instance().addMapLayer(capa)
    return capa
