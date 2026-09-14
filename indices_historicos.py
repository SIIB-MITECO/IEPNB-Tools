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

Índices Históricos - Consulta la Statistical API de Copernicus Data Space
Ecosystem (CDSE) para un punto y dibuja la serie temporal del índice
espectral elegido (NDVI, NDWI, NBR, EVI) usando Sentinel-2 L2A.
"""

import json
from datetime import datetime, timezone
from functools import partial

from qgis.PyQt.QtCore import Qt, QUrl, QUrlQuery, QByteArray, QEventLoop, QSettings
from qgis.PyQt.QtGui import QDesktopServices
from qgis.PyQt.QtWidgets import (QDialog, QVBoxLayout, QFormLayout, QLineEdit,
                                 QPushButton, QLabel, QMessageBox, QDialogButtonBox,
                                 QHBoxLayout, QMenu, QApplication)
from qgis.PyQt import QtNetwork
from qgis.core import (QgsApplication, QgsAuthMethodConfig, QgsNetworkAccessManager,
                       QgsCoordinateReferenceSystem, QgsCoordinateTransform,
                       QgsProject, QgsPointXY)

from .config import (CDSE_AUTH_URL, CDSE_STATS_URL,
                     CDSE_AUTHCFG_SETTING, INDICE_FORMULAS, CATEGORIAS_INDICES)

# --- Matplotlib embebido: compatible con QGIS3 (Qt5) y QGIS4 (Qt6) ---
try:
    from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
    from matplotlib.backends.backend_qtagg import NavigationToolbar2QT as NavigationToolbar
except ImportError:
    from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
    from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
import matplotlib.dates as mdates


# =====================================================================
# CREDENCIALES (Authentication Manager de QGIS)
# =====================================================================

class DialogoCredencialesCDSE(QDialog):
    """Pide el Client ID / Client Secret de Sentinel Hub (Dashboard de CDSE),
    NO el usuario/contraseña de la cuenta personal."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Copernicus Data Space Ecosystem - Credenciales")
        self.setMinimumWidth(420)
        layout = QVBoxLayout(self)

        layout.addWidget(QLabel(
            "Introduce el Client ID y Client Secret de tu OAuth Client de "
            "Sentinel Hub (no es tu usuario/contraseña de la cuenta). Se "
            "guardan cifrados en el gestor de autenticación de QGIS."))

        instrucciones = QLabel(
            '<b>¿Cómo consigo estas credenciales?</b><br>'
            '1. Entra en tu cuenta de '
            '<a href="https://dataspace.copernicus.eu">dataspace.copernicus.eu</a><br>'
            '2. Pasa el ratón por el icono de perfil → "Sentinel Hub" '
            '(te lleva al Dashboard)<br>'
            '3. Ve a User Settings → OAuth clients → "+ Create"<br>'
            '4. Copia el Client ID y el Client Secret '
            '(el secret solo se muestra una vez)')
        instrucciones.setWordWrap(True)
        instrucciones.setOpenExternalLinks(True)
        instrucciones.setTextFormat(Qt.TextFormat.RichText)
        instrucciones.setStyleSheet(
            "color: #444; font-size: 11px; background-color: #f2f2f2; "
            "padding: 8px; border-radius: 4px; border: 1px solid #e0e0e0;")
        layout.addWidget(instrucciones)

        btn_dashboard = QPushButton("Abrir dataspace.copernicus.eu")
        btn_dashboard.clicked.connect(
            lambda: QDesktopServices.openUrl(QUrl("https://dataspace.copernicus.eu")))
        layout.addWidget(btn_dashboard)

        form = QFormLayout()
        self.txt_client_id = QLineEdit()
        self.txt_client_secret = QLineEdit()
        self.txt_client_secret.setEchoMode(QLineEdit.EchoMode.Password)
        form.addRow("Client ID:", self.txt_client_id)
        form.addRow("Client Secret:", self.txt_client_secret)
        layout.addLayout(form)

        botones = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        botones.accepted.connect(self.accept)
        botones.rejected.connect(self.reject)
        layout.addWidget(botones)

    @property
    def client_id(self):
        return self.txt_client_id.text().strip()

    @property
    def client_secret(self):
        return self.txt_client_secret.text().strip()


def obtener_credenciales_cdse(parent_widget):
    """Devuelve (client_id, client_secret) desde el Authentication Manager de
    QGIS, pidiéndolas al usuario la primera vez y guardándolas cifradas."""
    settings = QSettings()
    authcfg = settings.value(CDSE_AUTHCFG_SETTING, "", type=str)
    auth_manager = QgsApplication.authManager()

    if authcfg:
        config = QgsAuthMethodConfig()
        if auth_manager.loadAuthenticationConfig(authcfg, config, True) and config.isValid():
            return config.config("username"), config.config("password")
        # authcfg guardado pero ya no válido (borrado a mano, etc.) -> repetimos alta
        settings.remove(CDSE_AUTHCFG_SETTING)

    dialogo = DialogoCredencialesCDSE(parent_widget)
    if dialogo.exec() != QDialog.DialogCode.Accepted:
        return None, None
    if not dialogo.client_id or not dialogo.client_secret:
        QMessageBox.warning(parent_widget, "Índice histórico", "Client ID y Client Secret son obligatorios.")
        return None, None

    config = QgsAuthMethodConfig()
    config.setName("CDSE - IEPNB Tools")
    config.setMethod("Basic")
    config.setConfig("username", dialogo.client_id)
    config.setConfig("password", dialogo.client_secret)
    if not auth_manager.storeAuthenticationConfig(config):
        QMessageBox.warning(parent_widget, "Índice histórico",
                            "No se han podido guardar las credenciales en QGIS.")
        return dialogo.client_id, dialogo.client_secret

    settings.setValue(CDSE_AUTHCFG_SETTING, config.id())
    return dialogo.client_id, dialogo.client_secret


def olvidar_credenciales_cdse():
    """Borra el authcfg guardado (botón 'cambiar cuenta' opcional)."""
    settings = QSettings()
    authcfg = settings.value(CDSE_AUTHCFG_SETTING, "", type=str)
    if authcfg:
        QgsApplication.authManager().removeAuthenticationConfig(authcfg)
        settings.remove(CDSE_AUTHCFG_SETTING)


# =====================================================================
# TOKEN OAuth2
# =====================================================================

def obtener_token_cdse(client_id, client_secret):
    """POST síncrono al Identity Provider de CDSE (OAuth2 client_credentials,
    el flujo correcto para Process/Statistical API). Devuelve access_token o
    lanza RuntimeError con un mensaje legible."""
    network_manager = QgsNetworkAccessManager.instance()

    request = QtNetwork.QNetworkRequest(QUrl(CDSE_AUTH_URL))
    request.setHeader(QtNetwork.QNetworkRequest.KnownHeaders.ContentTypeHeader,
                      "application/x-www-form-urlencoded")

    cuerpo = QUrlQuery()
    cuerpo.addQueryItem("grant_type", "client_credentials")
    cuerpo.addQueryItem("client_id", client_id)
    cuerpo.addQueryItem("client_secret", client_secret)
    datos = cuerpo.toString(QUrl.ComponentFormattingOption.FullyEncoded).encode("utf-8")

    loop = QEventLoop()
    reply = network_manager.post(request, QByteArray(datos))
    reply.finished.connect(loop.quit)
    loop.exec()

    raw = bytes(reply.readAll())
    error = reply.error()
    reply.deleteLater()

    if error != QtNetwork.QNetworkReply.NetworkError.NoError:
        try:
            detalle = json.loads(raw).get("error_description", raw.decode("utf-8", "ignore"))
        except Exception:
            detalle = raw.decode("utf-8", "ignore") or str(error)
        raise RuntimeError(f"Autenticación CDSE fallida: {detalle}")

    payload = json.loads(raw)
    if "access_token" not in payload:
        raise RuntimeError(f"CDSE no devolvió token de acceso: {payload}")
    return payload["access_token"]


# =====================================================================
# EVALSCRIPT + GEOMETRÍA
# =====================================================================

def construir_evalscript(indice):
    info = INDICE_FORMULAS[indice]
    bandas_js = ", ".join(f'"{b}"' for b in info["bandas"])
    formula = info["formula"]
    return f"""//VERSION=3
function setup() {{
  return {{
    input: [
      {{ bands: [{bandas_js}, "SCL", "dataMask"], units: "DN" }}
    ],
    output: [
      {{ id: "index", bands: 1, sampleType: "FLOAT32" }},
      {{ id: "dataMask", bands: 1 }}
    ]
  }};
}}

function evaluatePixel(samples) {{
  let valor = {formula};
  let valido = samples.dataMask;
  // SCL: 3=sombra de nube, 8/9=nube media/alta prob., 10=cirro -> descartar
  if (samples.SCL == 3 || samples.SCL == 8 || samples.SCL == 9 || samples.SCL == 10) {{
    valido = 0;
  }}
  return {{
    index: [valor],
    dataMask: [valido]
  }};
}}
"""


def _epsg_utm(lat, lon):
    """Código EPSG de la zona UTM que corresponde a (lat, lon)."""
    zona = int((lon + 180) / 6) + 1
    return (32600 if lat >= 0 else 32700) + zona


def punto_a_poligono(lat, lon, lado_m=20):
    """Cuadrado geojson de ~lado_m de lado, en la UTM que corresponde al
    punto (coordenadas en metros de verdad). La Statistical API interpreta
    resx/resy en las unidades del CRS del polígono, así que en EPSG:4326
    "10" significaría 10 grados, no 10 metros -> hay que ir en UTM.
    Devuelve (geojson_polygon, crs_uri_para_bounds_properties)."""
    epsg_utm = _epsg_utm(lat, lon)
    crs_origen = QgsCoordinateReferenceSystem("EPSG:4326")
    crs_utm = QgsCoordinateReferenceSystem(f"EPSG:{epsg_utm}")
    transform = QgsCoordinateTransform(crs_origen, crs_utm, QgsProject.instance())
    punto_utm = transform.transform(QgsPointXY(lon, lat))
    x, y = punto_utm.x(), punto_utm.y()
    d = lado_m / 2

    poligono = {
        "type": "Polygon",
        "coordinates": [[
            [x - d, y - d],
            [x + d, y - d],
            [x + d, y + d],
            [x - d, y + d],
            [x - d, y - d],
        ]]
    }
    crs_uri = f"http://www.opengis.net/def/crs/EPSG/0/{epsg_utm}"
    return poligono, crs_uri


# =====================================================================
# CONSULTA A LA STATISTICAL API
# =====================================================================

def consultar_historico_indice(token, lat, lon, indice, fecha_inicio, fecha_fin,
                               intervalo="P1M"):
    """Devuelve una lista [(datetime, valor_medio), ...] ordenada por fecha."""
    poligono, crs_uri = punto_a_poligono(lat, lon)
    cuerpo = {
        "input": {
            "bounds": {
                "geometry": poligono,
                "properties": {"crs": crs_uri}
            },
            "data": [{
                "type": "sentinel-2-l2a",
                "dataFilter": {"maxCloudCoverage": 80}
            }]
        },
        "aggregation": {
            "timeRange": {"from": fecha_inicio, "to": fecha_fin},
            "aggregationInterval": {"of": intervalo},
            "evalscript": construir_evalscript(indice),
            "resx": 10,
            "resy": 10
        },
        "calculations": {
            "index": {"statistics": {"default": {}}}
        }
    }

    network_manager = QgsNetworkAccessManager.instance()
    request = QtNetwork.QNetworkRequest(QUrl(CDSE_STATS_URL))
    request.setHeader(QtNetwork.QNetworkRequest.KnownHeaders.ContentTypeHeader, "application/json")
    request.setRawHeader(b"Authorization", f"Bearer {token}".encode("utf-8"))

    loop = QEventLoop()
    reply = network_manager.post(request, QByteArray(json.dumps(cuerpo).encode("utf-8")))
    reply.finished.connect(loop.quit)
    loop.exec()

    raw = bytes(reply.readAll())
    error = reply.error()
    reply.deleteLater()

    if error != QtNetwork.QNetworkReply.NetworkError.NoError:
        try:
            detalle = json.loads(raw)
        except Exception:
            detalle = raw.decode("utf-8", "ignore") or str(error)
        raise RuntimeError(f"Error consultando la Statistical API: {detalle}")

    payload = json.loads(raw)
    return _parsear_respuesta_statistics(payload)


def _parsear_respuesta_statistics(payload):
    serie = []
    for item in payload.get("data", []):
        intervalo = item.get("interval", {})
        fecha_str = intervalo.get("from")
        salida_index = item.get("outputs", {}).get("index", {})
        b0 = salida_index.get("bands", {}).get("B0", {})
        stats = b0.get("stats", {})
        media = stats.get("mean")
        n_muestras = stats.get("sampleCount", 0)
        n_nodata = stats.get("noDataCount", 0)

        if media is None or n_muestras <= n_nodata:
            continue  # intervalo sin píxeles válidos (todo nube, etc.)
        # La API a veces serializa NaN como el string "NaN" (JSON estricto no
        # admite NaN literal) cuando la fórmula degenera en 0/0 para algún
        # píxel del área (frecuente con agua/nieve en zonas de borde). Sin
        # este filtro, ese string se cuela en la serie y rompe la media móvil.
        try:
            media = float(media)
        except (TypeError, ValueError):
            continue
        if media != media or media in (float("inf"), float("-inf")):  # NaN/inf
            continue
        if not fecha_str:
            continue
        try:
            fecha = datetime.fromisoformat(fecha_str.replace("Z", "+00:00"))
        except ValueError:
            continue
        serie.append((fecha, media))

    serie.sort(key=lambda par: par[0])
    return serie


# =====================================================================
# GRÁFICA
# =====================================================================

COLOR_POR_INDICE = {
    "NDVI": "#2e7d32",   # verde - vegetación
    "NDWI": "#1565c0",   # azul - agua
    "NBR": "#d84315",    # naranja quemado - área quemada
    "EVI": "#00897b",    # verde azulado - vegetación mejorado
    "NDMI": "#6a1b9a",   # morado - humedad de vegetación
    "GNDVI": "#7cb342",  # verde lima - clorofila
    "SAVI": "#8d6e63",   # marrón - corrección de suelo
    "BAI": "#bf360c",    # rojo carbón - cicatriz de quemado
    "NDSI": "#00acc1",   # cian hielo - nieve
    "BSI": "#a1887f",    # tierra - suelo desnudo
    "CIRE": "#558b2f",   # verde oliva - clorofila borde rojo
}


def _media_movil(valores, ventana):
    """Media móvil centrada de 'ventana' puntos (suaviza sin depender de
    numpy/scipy). Con ventana<=1 o pocos datos, devuelve la serie tal cual."""
    n = len(valores)
    if ventana <= 1 or n < ventana:
        return list(valores)
    mitad = ventana // 2
    return [
        sum(valores[max(0, i - mitad):min(n, i + mitad + 1)]) /
        len(valores[max(0, i - mitad):min(n, i + mitad + 1)])
        for i in range(n)
    ]


class GraficaIndiceDialog(QDialog):
    def __init__(self, indice, lat, lon, serie, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Histórico {indice} - {lat:.5f}, {lon:.5f}")
        self.resize(820, 640)
        self.setStyleSheet("background-color: white;")
        self.serie_completa = serie
        self.indice = indice
        self.lat, self.lon = lat, lon
        self.color = COLOR_POR_INDICE.get(indice, "#2e7d32")
        self.indice2 = None
        self.serie2_completa = None
        self.color2 = None
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 10)

        if not serie:
            layout.addWidget(QLabel(
                "No se han obtenido observaciones válidas (probablemente cobertura "
                "de nubes constante en el rango de fechas consultado)."))
            return

        # --- Filtro temporal: botones rápidos ---
        fila_rango = QHBoxLayout()
        fila_rango.addWidget(QLabel("Periodo:"))
        self.botones_rango = {}
        for etiqueta, anios in [("1 año", 1), ("3 años", 3), ("5 años", 5), ("Todo", None)]:
            btn = QPushButton(etiqueta)
            btn.setCheckable(True)
            btn.setStyleSheet(
                "QPushButton { padding: 3px 12px; border-radius: 4px; border: 1px solid #ccc; }"
                "QPushButton:checked { background-color: %s; color: white; border: none; }" % self.color)
            btn.clicked.connect(partial(self._aplicar_rango, anios))
            fila_rango.addWidget(btn)
            self.botones_rango[anios] = btn
        fila_rango.addStretch()

        self.btn_comparar = QPushButton("+ Añadir índice")
        self.btn_comparar.setStyleSheet(
            "QPushButton { padding: 3px 12px; border-radius: 4px; border: 1px solid #ccc; }")
        self.btn_comparar.clicked.connect(self._menu_anadir_indice)
        fila_rango.addWidget(self.btn_comparar)

        self.btn_quitar_comparar = QPushButton("✕")
        self.btn_quitar_comparar.setToolTip("Quitar el segundo índice")
        self.btn_quitar_comparar.setFixedWidth(28)
        self.btn_quitar_comparar.setStyleSheet(
            "QPushButton { padding: 3px; border-radius: 4px; border: 1px solid #ccc; }")
        self.btn_quitar_comparar.clicked.connect(self._quitar_segundo_indice)
        self.btn_quitar_comparar.setVisible(False)
        fila_rango.addWidget(self.btn_quitar_comparar)

        layout.addLayout(fila_rango)

        # --- Figura ---
        self.fig = Figure(figsize=(8.2, 4.6), dpi=100)
        self.fig.patch.set_facecolor("white")
        self.canvas = FigureCanvas(self.fig)
        self.ax = self.fig.add_subplot(111)

        # Barra de herramientas de matplotlib: incluye zoom de lupa (arrastrar
        # para hacer zoom a un rectángulo), pan, y "Home" para volver a la
        # vista completa. Quitamos el botón de guardar/editar-ejes para no
        # saturar, dejando solo pan/zoom/home.
        self.toolbar = NavigationToolbar(self.canvas, self)
        acciones_permitidas = {"Home", "Pan", "Zoom", "Back", "Forward"}
        for accion in self.toolbar.actions():
            if accion.text() not in acciones_permitidas and not accion.isSeparator():
                self.toolbar.removeAction(accion)
        self.toolbar.setStyleSheet("QToolBar { border: none; spacing: 2px; }")
        layout.addWidget(self.toolbar)
        layout.addWidget(self.canvas)

        # Etiqueta que muestra fecha/valor del punto más cercano al ratón
        self.lbl_hover = QLabel(" ")
        self.lbl_hover.setStyleSheet(
            "color: #222; font-size: 11px; font-weight: bold; padding-top: 2px;")
        layout.addWidget(self.lbl_hover)
        self.canvas.mpl_connect("motion_notify_event", self._al_mover_raton)
        self.canvas.mpl_connect("axes_leave_event", self._al_salir_raton)

        self.info = QLabel()
        self.info.setStyleSheet("color: #888; font-size: 11px; padding-top: 4px;")
        layout.addWidget(self.info)

        # --- Ficha explicativa del índice: qué es, fórmula y cómo leerlo ---
        meta = INDICE_FORMULAS.get(indice, {})
        if meta:
            ficha = self._crear_ficha(indice, meta, self.color)
            layout.addWidget(ficha)

        self.layout_principal = layout
        self.ficha2 = None  # se crea/destruye al activar/quitar la comparación

        # --- Disclaimer de fuente y licencia ---
        anio_actual = datetime.now().year
        disclaimer = QLabel(
            f"Fuente: Copernicus Sentinel-2 L2A (ESA), procesado vía Copernicus Data Space "
            f"Ecosystem. Acceso libre y gratuito según la Legal Notice on the use of Copernicus "
            f"Sentinel Data — atribución requerida al redistribuir: "
            f"<i>«Copernicus Sentinel data {anio_actual}»</i>. Datos entregados sin garantía "
            f"expresa ni implícita de exactitud.")
        disclaimer.setWordWrap(True)
        disclaimer.setTextFormat(Qt.TextFormat.RichText)
        disclaimer.setStyleSheet(
            "color: #999; font-size: 9.5px; padding-top: 6px;")
        layout.addWidget(disclaimer)
        self.disclaimer_widget = disclaimer

        fila_botones = QHBoxLayout()
        fila_botones.addStretch()
        btn_cerrar = QPushButton("Cerrar")
        btn_cerrar.setStyleSheet(
            "QPushButton { padding: 5px 18px; border-radius: 4px; }")
        btn_cerrar.clicked.connect(self.accept)
        fila_botones.addWidget(btn_cerrar)
        layout.addLayout(fila_botones)

        self.rango_activo = None
        self.botones_rango[None].setChecked(True)
        self._dibujar(serie)

    def _crear_ficha(self, indice, meta, color):
        texto_ficha = (
            f"<b>{indice}</b> — {meta.get('descripcion', '')}<br>"
            f"<b>Fórmula:</b> {meta.get('formula_legible', '')}<br>"
            f"<b>Rango:</b> {meta.get('rango', '')}<br>"
            f"<b>Cómo leerlo:</b> {meta.get('interpretacion', '')}"
        )
        ficha = QLabel(texto_ficha)
        ficha.setWordWrap(True)
        ficha.setTextFormat(Qt.TextFormat.RichText)
        ficha.setStyleSheet(
            f"color: #444; font-size: 11px; background-color: #f7f7f7; "
            f"border-left: 3px solid {color}; border-radius: 3px; "
            f"padding: 8px 10px; margin-top: 4px;")
        return ficha

    def _filtrar_por_rango(self, serie_completa, anios):
        if not serie_completa:
            return serie_completa
        if anios is None:
            return serie_completa
        fecha_max = serie_completa[-1][0]
        fecha_min = fecha_max.replace(year=fecha_max.year - anios)
        return [(f, v) for f, v in serie_completa if f >= fecha_min]

    def _aplicar_rango(self, anios):
        for a, btn in self.botones_rango.items():
            btn.setChecked(a == anios)
        self.rango_activo = anios

        serie_filtrada = self._filtrar_por_rango(self.serie_completa, anios)
        serie2_filtrada = (self._filtrar_por_rango(self.serie2_completa, anios)
                           if self.serie2_completa else None)
        self._dibujar(serie_filtrada, serie2_filtrada)

    def _menu_anadir_indice(self):
        menu = QMenu(self)
        menu.setToolTipsVisible(True)
        for categoria, indices in CATEGORIAS_INDICES.items():
            submenu = menu.addMenu(categoria)
            submenu.setToolTipsVisible(True)
            for indice in indices:
                if indice == self.indice:
                    continue  # no tiene sentido comparar un índice consigo mismo
                accion = submenu.addAction(indice)
                meta = INDICE_FORMULAS.get(indice, {})
                if meta:
                    accion.setToolTip(
                        f"{meta.get('descripcion', '')}\nFórmula: {meta.get('formula_legible', '')}")
                accion.triggered.connect(partial(self._seleccionar_segundo_indice, indice))
        menu.exec(self.btn_comparar.mapToGlobal(self.btn_comparar.rect().bottomLeft()))

    def _seleccionar_segundo_indice(self, indice2):
        client_id, client_secret = obtener_credenciales_cdse(self)
        if not client_id:
            return

        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        try:
            token = obtener_token_cdse(client_id, client_secret)
            hoy = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
            serie2 = consultar_historico_indice(
                token, self.lat, self.lon, indice2,
                fecha_inicio="2017-01-01T00:00:00Z", fecha_fin=hoy, intervalo="P5D")
        except Exception as exc:
            QApplication.restoreOverrideCursor()
            QMessageBox.critical(self, "Añadir índice", str(exc))
            return
        QApplication.restoreOverrideCursor()

        if not serie2:
            QMessageBox.information(self, "Añadir índice",
                                    f"No se han obtenido observaciones válidas de {indice2} "
                                    f"en este punto.")
            return

        self.indice2 = indice2
        self.serie2_completa = serie2
        self.color2 = COLOR_POR_INDICE.get(indice2, "#e65100")
        self.btn_quitar_comparar.setVisible(True)
        self.btn_comparar.setText(f"Comparando con {indice2}")
        self.btn_comparar.setEnabled(False)

        # Ficha explicativa del segundo índice, insertada justo antes del disclaimer
        meta2 = INDICE_FORMULAS.get(indice2, {})
        if meta2:
            self.ficha2 = self._crear_ficha(indice2, meta2, self.color2)
            indice_insercion = self.layout_principal.indexOf(self.disclaimer_widget)
            self.layout_principal.insertWidget(indice_insercion, self.ficha2)

        serie_filtrada = self._filtrar_por_rango(self.serie_completa, self.rango_activo)
        serie2_filtrada = self._filtrar_por_rango(self.serie2_completa, self.rango_activo)
        self._dibujar(serie_filtrada, serie2_filtrada)

    def _quitar_segundo_indice(self):
        self.indice2 = None
        self.serie2_completa = None
        self.color2 = None
        self.btn_quitar_comparar.setVisible(False)
        self.btn_comparar.setText("+ Añadir índice")
        self.btn_comparar.setEnabled(True)
        if self.ficha2 is not None:
            self.layout_principal.removeWidget(self.ficha2)
            self.ficha2.deleteLater()
            self.ficha2 = None
        serie_filtrada = self._filtrar_por_rango(self.serie_completa, self.rango_activo)
        self._dibujar(serie_filtrada)

    def _dibujar(self, serie, serie2=None):
        self.ax.clear()
        if getattr(self, "ax2", None) is not None:
            self.ax2.remove()
            self.ax2 = None
        indice, color = self.indice, self.color
        fechas = [f for f, _ in serie]
        valores = [v for _, v in serie]
        n = len(valores)

        self.ax.set_facecolor("#fbfbfb")

        if not serie:
            self.ax.text(0.5, 0.5, "Sin observaciones en este periodo",
                         ha="center", va="center", color="#888", transform=self.ax.transAxes)
            self.canvas.draw()
            self.info.setText("0 observaciones en el periodo seleccionado")
            self._fechas_num = []
            self._valores_brutos = []
            self._valores_linea = []
            self.hover_marker = None
            return

        # Con muchos puntos (P5D puede dar cientos) los marcadores grandes
        # saturan la gráfica: los reducimos según la densidad de datos.
        tam_marcador = 4 if n < 80 else (2.5 if n < 250 else 0)
        grosor_linea = 1.3 if n < 250 else 0.9

        # Media móvil para suavizar el ruido de nubes residual; ventana más
        # ancha cuantos más puntos haya.
        ventana = 9 if n >= 200 else (5 if n >= 60 else (3 if n >= 20 else 1))
        suavizado = _media_movil(valores, ventana)

        if ventana > 1:
            # Datos crudos: puntos finos y atenuados, de fondo
            self.ax.scatter(fechas, valores, s=6, color=color, alpha=0.25, zorder=2, linewidths=0)
            # Curva suavizada: la que se lee de verdad
            self.ax.plot(fechas, suavizado, linewidth=2.0, color=color, alpha=0.95, zorder=3,
                        solid_capstyle="round")
            self.ax.fill_between(fechas, suavizado, min(suavizado), color=color, alpha=0.12, zorder=1)
            valores_linea = suavizado
        else:
            self.ax.plot(fechas, valores, marker="o", markersize=tam_marcador,
                        markerfacecolor=color, markeredgecolor="none",
                        linewidth=grosor_linea, color=color, alpha=0.9, zorder=3)
            self.ax.fill_between(fechas, valores, min(valores), color=color, alpha=0.12, zorder=1)
            valores_linea = valores

        # Marcador que se mueve al pasar el ratón (invisible hasta el primer hover)
        self.hover_marker, = self.ax.plot([], [], "o", color="#222", markersize=7,
                                          markeredgecolor="white", markeredgewidth=1.2,
                                          zorder=6, visible=False)

        titulo = f"{indice} histórico — Sentinel-2 L2A"
        self.ax.set_ylabel(indice, fontsize=10, color=color, fontweight="bold")
        self.ax.tick_params(axis="y", labelcolor=color)

        # --- Segundo índice (comparación), en un eje Y independiente ---
        fechas2, valores2, valores2_linea = [], [], []
        if serie2:
            fechas2 = [f for f, _ in serie2]
            valores2 = [v for _, v in serie2]
            n2 = len(valores2)
            ventana2 = 9 if n2 >= 200 else (5 if n2 >= 60 else (3 if n2 >= 20 else 1))
            valores2_linea = _media_movil(valores2, ventana2)

            self.ax2 = self.ax.twinx()
            self.ax2.plot(fechas2, valores2_linea, linewidth=1.8, color=self.color2,
                         alpha=0.9, zorder=4, linestyle="--")
            self.ax2.set_ylabel(self.indice2, fontsize=10, color=self.color2, fontweight="bold")
            self.ax2.tick_params(axis="y", labelcolor=self.color2, labelsize=9)
            for lado in ("top", "left"):
                self.ax2.spines[lado].set_visible(False)
            self.ax2.spines["right"].set_color(self.color2)
            self.ax2.grid(False)

            # Leyenda combinando las líneas de ambos ejes (lines[0] es la curva
            # de datos real; el marcador de hover se añade después y no cuenta aquí)
            linea1 = self.ax.lines[0]
            linea2 = self.ax2.lines[0]
            self.ax.legend([linea1, linea2], [indice, self.indice2],
                          loc="upper left", fontsize=8, frameon=False)
            titulo = f"{indice} vs {self.indice2} — Sentinel-2 L2A"

        self.ax.set_title(titulo, fontsize=13, fontweight="bold", color="#222", pad=12)

        self.ax.grid(True, axis="y", linestyle="--", linewidth=0.6, alpha=0.35, color="#999")
        self.ax.grid(False, axis="x")
        for lado in ("top", "right"):
            self.ax.spines[lado].set_visible(False)
        for lado in ("left", "bottom"):
            self.ax.spines[lado].set_color("#bbb")
        self.ax.tick_params(axis="x", labelsize=9, colors="#555")

        self.fig.autofmt_xdate()

        # Formateador adaptativo: a escala de años muestra solo el año, pero
        # al hacer zoom (con la lupa) pasa a mostrar mes/día automáticamente
        # en vez de dejar el eje lleno de años apretados y confusos.
        locator = mdates.AutoDateLocator(minticks=4, maxticks=9)
        formatter = mdates.ConciseDateFormatter(locator, show_offset=False)
        self.ax.xaxis.set_major_locator(locator)
        self.ax.xaxis.set_major_formatter(formatter)

        self.fig.tight_layout()
        self.canvas.draw()

        self.info.setText(f"{n} observaciones válidas · "
                          f"{fechas[0].strftime('%d/%m/%Y')} a {fechas[-1].strftime('%d/%m/%Y')}")

        # Datos para la inspección al pasar el ratón
        self._fechas_dt = fechas
        self._fechas_num = mdates.date2num(fechas)
        self._valores_brutos = valores
        self._valores_linea = valores_linea

        # Datos del segundo índice (vacío si no hay comparación activa)
        if serie2:
            self._fechas_num2 = mdates.date2num(fechas2)
            self._valores_linea2 = valores2_linea
        else:
            self._fechas_num2 = []
            self._valores_linea2 = []

    def _al_mover_raton(self, event):
        ejes_validos = (self.ax, self.ax2) if getattr(self, "ax2", None) is not None else (self.ax,)
        if event.inaxes not in ejes_validos or not len(self._fechas_num) or event.xdata is None:
            self._al_salir_raton()
            return

        # Punto más cercano al cursor (distancia en el eje X, que es el que importa aquí)
        diffs = [abs(x - event.xdata) for x in self._fechas_num]
        i = diffs.index(min(diffs))

        fecha = self._fechas_dt[i]
        valor_linea = self._valores_linea[i]
        valor_bruto = self._valores_brutos[i]

        self.hover_marker.set_data([self._fechas_num[i]], [valor_linea])
        self.hover_marker.set_visible(True)
        self.canvas.draw_idle()

        if abs(valor_linea - valor_bruto) > 1e-9:
            texto = (f"{fecha.strftime('%d/%m/%Y')}  ·  {self.indice} (suavizado): {valor_linea:.3f}"
                    f"  ·  bruto: {valor_bruto:.3f}")
        else:
            texto = f"{fecha.strftime('%d/%m/%Y')}  ·  {self.indice}: {valor_bruto:.3f}"

        # Si hay un segundo índice activo, buscamos su valor en esa misma fecha
        if len(self._fechas_num2):
            diffs2 = [abs(x - self._fechas_num[i]) for x in self._fechas_num2]
            j = diffs2.index(min(diffs2))
            # Solo lo mostramos si la fecha encontrada está razonablemente
            # cerca (± 3 días); si no, es que ese índice no tiene dato ahí.
            if diffs2[j] <= 3:
                texto += f"  ·  {self.indice2}: {self._valores_linea2[j]:.3f}"

        self.lbl_hover.setText(texto)

    def _al_salir_raton(self, event=None):
        if getattr(self, "hover_marker", None) is not None:
            self.hover_marker.set_visible(False)
            self.canvas.draw_idle()
        self.lbl_hover.setText(" ")
