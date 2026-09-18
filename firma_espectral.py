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

Firma Espectral - Para un punto y una fecha aproximada, localiza la
adquisición Sentinel-2 L2A real más despejada de nubes cercana a esa fecha
y consulta la reflectancia de todas sus bandas, mostrándola como una
gráfica clásica de firma espectral (reflectancia vs longitud de onda).
"""

import json
from datetime import datetime, timedelta, timezone
from functools import partial

from qgis.PyQt.QtCore import Qt, QUrl, QByteArray, QEventLoop, QDate
from qgis.PyQt.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                                 QPushButton, QDateEdit, QDialogButtonBox, QMenu)
from qgis.PyQt import QtNetwork
from qgis.gui import QgsMapTool
from qgis.core import (QgsProject, QgsCoordinateReferenceSystem,
                       QgsCoordinateTransform, QgsNetworkAccessManager)

from .config import (CDSE_STATS_URL, BANDAS_S2, REGIONES_ESPECTRO, FIRMA_VENTANA_DIAS_BUSQUEDA,
                     GAP_DESDE_NM, GAP_HASTA_NM, GAP_COMPRESION, REFERENCIAS_FIRMA)
from .indices_historicos import punto_a_poligono

# --- Matplotlib embebido: compatible con QGIS3 (Qt5) y QGIS4 (Qt6) ---
try:
    from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
    from matplotlib.backends.backend_qtagg import NavigationToolbar2QT as NavigationToolbar
except ImportError:
    from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
    from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
from matplotlib.ticker import PercentFormatter

try:
    from scipy.interpolate import PchipInterpolator
    _TIENE_SCIPY = True
except ImportError:
    _TIENE_SCIPY = False


def _nm_a_x(nm):
    """Transforma una longitud de onda real (nm) a la posición X que se
    dibuja, comprimiendo el hueco vacío 945-1610nm (sin bandas) para no
    desperdiciar la mitad del ancho del gráfico en un tramo sin datos.
    Todo lo demás mantiene proporción real de verdad."""
    if nm <= GAP_DESDE_NM:
        return nm
    if nm >= GAP_HASTA_NM:
        return GAP_DESDE_NM + (GAP_HASTA_NM - GAP_DESDE_NM) / GAP_COMPRESION + (nm - GAP_HASTA_NM)
    frac = (nm - GAP_DESDE_NM) / (GAP_HASTA_NM - GAP_DESDE_NM)
    return GAP_DESDE_NM + frac * (GAP_HASTA_NM - GAP_DESDE_NM) / GAP_COMPRESION


# =====================================================================
# HERRAMIENTA DE MAPA
# =====================================================================

class FirmaEspectralTool(QgsMapTool):
    """Herramienta de mapa: clic -> callback(lat, lon)."""

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


# =====================================================================
# DIÁLOGO: FECHA APROXIMADA
# =====================================================================

class DialogoFechaAproximada(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Firma espectral - Fecha aproximada")
        self.setMinimumWidth(380)
        layout = QVBoxLayout(self)

        lbl_intro = QLabel(
            "Elige una fecha aproximada. Buscaremos la adquisición de "
            "Sentinel-2 real más despejada de nubes cerca de esa fecha "
            f"(± {FIRMA_VENTANA_DIAS_BUSQUEDA} días) — puede que el resultado "
            "no sea exactamente el día pedido.")
        lbl_intro.setWordWrap(True)
        layout.addWidget(lbl_intro)

        self.fecha_edit = QDateEdit()
        self.fecha_edit.setCalendarPopup(True)
        self.fecha_edit.setDisplayFormat("dd/MM/yyyy")
        self.fecha_edit.setDate(QDate.currentDate())
        self.fecha_edit.setMaximumDate(QDate.currentDate())
        self.fecha_edit.setMinimumDate(QDate(2017, 1, 1))
        layout.addWidget(self.fecha_edit)

        botones = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        botones.accepted.connect(self.accept)
        botones.rejected.connect(self.reject)
        layout.addWidget(botones)

    def fecha_seleccionada(self):
        qd = self.fecha_edit.date()
        return datetime(qd.year(), qd.month(), qd.day(), tzinfo=timezone.utc)


# =====================================================================
# EVALSCRIPTS
# =====================================================================

def _evalscript_busqueda():
    """Evalscript ligero (una banda + máscara) para explorar qué días de la
    ventana tienen mejor cobertura despejada en el punto exacto. La cobertura
    despejada va en una salida propia ("cobertura"), separada de "dataMask"
    (que se deja con su significado nativo: dentro/fuera de escena), igual
    que el patrón ya probado en el índice histórico -- pedir estadísticas
    directamente sobre una salida llamada "dataMask" no es fiable."""
    return """//VERSION=3
function setup() {
  return {
    input: [{ bands: ["B04", "SCL", "dataMask"], units: "DN" }],
    output: [
      { id: "cobertura", bands: 1 },
      { id: "dataMask", bands: 1 }
    ]
  };
}
function evaluatePixel(samples) {
  let despejado = 1;
  if (samples.SCL == 3 || samples.SCL == 8 || samples.SCL == 9 || samples.SCL == 10) {
    despejado = 0;
  }
  return {
    cobertura: [despejado],
    dataMask: [samples.dataMask]
  };
}
"""


def _evalscript_firma():
    """Evalscript con las 12 bandas de reflectancia (DN) + máscara de nubes."""
    bandas_js = ", ".join(f'"{b["id"]}"' for b in BANDAS_S2)
    salida_js = ", ".join(f"samples.{b['id']}" for b in BANDAS_S2)
    return f"""//VERSION=3
function setup() {{
  return {{
    input: [{{ bands: [{bandas_js}, "SCL", "dataMask"], units: "DN" }}],
    output: [
      {{ id: "reflectancia", bands: {len(BANDAS_S2)}, sampleType: "FLOAT32" }},
      {{ id: "dataMask", bands: 1 }}
    ]
  }};
}}
function evaluatePixel(samples) {{
  let valido = samples.dataMask;
  if (samples.SCL == 3 || samples.SCL == 8 || samples.SCL == 9 || samples.SCL == 10) {{
    valido = 0;
  }}
  return {{
    reflectancia: [{salida_js}],
    dataMask: [valido]
  }};
}}
"""


# =====================================================================
# PETICIÓN GENÉRICA A LA STATISTICAL API
# =====================================================================

def _consultar_statistics(token, lat, lon, evalscript, fecha_inicio, fecha_fin, intervalo, clave_calculo):
    poligono, crs_uri = punto_a_poligono(lat, lon)
    cuerpo = {
        "input": {
            "bounds": {
                "geometry": poligono,
                "properties": {"crs": crs_uri}
            },
            "data": [{
                "type": "sentinel-2-l2a",
                "dataFilter": {"maxCloudCoverage": 100}
            }]
        },
        "aggregation": {
            "timeRange": {"from": fecha_inicio, "to": fecha_fin},
            "aggregationInterval": {"of": intervalo},
            "evalscript": evalscript,
            "resx": 10,
            "resy": 10
        },
        "calculations": {clave_calculo: {"statistics": {"default": {}}}}
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

    return json.loads(raw)


def _valor_numerico(bruto):
    """Coerciona a float y descarta NaN/inf/strings degenerados (ver el
    mismo problema resuelto en indices_historicos._parsear_respuesta_statistics)."""
    try:
        valor = float(bruto)
    except (TypeError, ValueError):
        return None
    if valor != valor or valor in (float("inf"), float("-inf")):
        return None
    return valor


# =====================================================================
# 1) BUSCAR LA MEJOR FECHA DISPONIBLE
# =====================================================================

def buscar_mejor_fecha(token, lat, lon, fecha_aproximada, ventana_dias=FIRMA_VENTANA_DIAS_BUSQUEDA):
    """Devuelve (fecha_elegida: datetime, fraccion_valida: float) del día,
    dentro de ± ventana_dias, con más cobertura despejada en ese punto.
    Devuelve (None, None) si no hay ninguna adquisición en la ventana."""
    desde = (fecha_aproximada - timedelta(days=ventana_dias)).strftime("%Y-%m-%dT00:00:00Z")
    hasta = (fecha_aproximada + timedelta(days=ventana_dias)).strftime("%Y-%m-%dT23:59:59Z")

    payload = _consultar_statistics(token, lat, lon, _evalscript_busqueda(), desde, hasta, "P1D", "cobertura")

    candidatos = []
    for item in payload.get("data", []):
        fecha_str = item.get("interval", {}).get("from")
        salida = item.get("outputs", {}).get("cobertura", {}).get("bands", {}).get("B0", {})
        stats = salida.get("stats", {})
        n_muestras = stats.get("sampleCount", 0)
        if n_muestras == 0:
            continue  # ningún píxel de esa fecha cae en nuestro punto (no hubo paso)
        fraccion_valida = _valor_numerico(stats.get("mean"))
        if fraccion_valida is None or not fecha_str:
            continue
        try:
            fecha = datetime.fromisoformat(fecha_str.replace("Z", "+00:00"))
        except ValueError:
            continue
        candidatos.append((fecha, fraccion_valida))

    if not candidatos:
        return None, None

    # Mejor = más cobertura despejada; empate -> más cercano a la fecha pedida
    candidatos.sort(key=lambda c: (-c[1], abs((c[0] - fecha_aproximada).days)))
    return candidatos[0]


# =====================================================================
# 2) CONSULTAR LA FIRMA ESPECTRAL COMPLETA PARA ESA FECHA
# =====================================================================

def consultar_firma_espectral(token, lat, lon, fecha):
    """Devuelve un dict {id_banda: reflectancia (0-1)} para el día exacto
    dado, o lanza RuntimeError/devuelve {} si no hay datos válidos."""
    # Pedimos un margen de un día a cada lado en vez de exactamente
    # 00:00-23:59:59 del día buscado: con un único día, un desajuste de
    # borde en el "bucket" diario de la API puede dejar la petición sin
    # ningún intervalo devuelto. Con margen, buscamos el intervalo exacto
    # que coincide con la fecha dentro de la respuesta.
    desde = (fecha - timedelta(days=1)).strftime("%Y-%m-%dT00:00:00Z")
    hasta = (fecha + timedelta(days=2)).strftime("%Y-%m-%dT00:00:00Z")

    payload = _consultar_statistics(token, lat, lon, _evalscript_firma(), desde, hasta, "P1D", "reflectancia")
    datos = payload.get("data", [])
    if not datos:
        return {}

    intervalo_elegido = None
    for item in datos:
        fecha_str = item.get("interval", {}).get("from", "")
        if fecha_str[:10] == fecha.strftime("%Y-%m-%d"):
            intervalo_elegido = item
            break
    if intervalo_elegido is None:
        return {}

    salida = intervalo_elegido.get("outputs", {}).get("reflectancia", {}).get("bands", {})
    resultado = {}
    for i, banda in enumerate(BANDAS_S2):
        stats = salida.get(f"B{i}", {}).get("stats", {})
        valor_dn = _valor_numerico(stats.get("mean"))
        if valor_dn is None:
            continue
        resultado[banda["id"]] = valor_dn / 10000.0  # DN -> reflectancia (0-1)
    return resultado


# =====================================================================
# GRÁFICA
# =====================================================================

def _similitud_sam(medido, referencia, bandas_ids):
    """Similitud por ángulo espectral (Spectral Angle Mapper), expresada
    como % (100% = misma forma exacta, independiente del brillo absoluto).
    Es la métrica estándar en teledetección para comparar firmas espectrales."""
    vec_a = [medido[b] for b in bandas_ids if b in medido and b in referencia]
    vec_b = [referencia[b] for b in bandas_ids if b in medido and b in referencia]
    if not vec_a:
        return 0.0
    producto = sum(a * b for a, b in zip(vec_a, vec_b))
    norma_a = sum(a * a for a in vec_a) ** 0.5
    norma_b = sum(b * b for b in vec_b) ** 0.5
    if norma_a == 0 or norma_b == 0:
        return 0.0
    coseno = max(-1.0, min(1.0, producto / (norma_a * norma_b)))
    return coseno * 100


class FirmaEspectralDialog(QDialog):
    def __init__(self, lat, lon, fecha_pedida, fecha_real, fraccion_valida,
                reflectancias, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Firma espectral - {lat:.5f}, {lon:.5f}")
        self.resize(1040, 740)
        self.setStyleSheet("background-color: white;")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 10)

        if not reflectancias:
            lbl_vacio = QLabel(
                "No se han obtenido valores válidos para la fecha encontrada "
                "(cobertura de nubes total en ese punto ese día).")
            lbl_vacio.setWordWrap(True)
            layout.addWidget(lbl_vacio)
            return

        self.reflectancias = reflectancias
        self.referencias_activas = []  # nombres de REFERENCIAS_FIRMA a superponer

        # --- Aviso de qué fecha real se ha usado ---
        dias_offset = abs((fecha_real.date() - fecha_pedida.date()).days)
        texto_fecha = f"Fecha usada: <b>{fecha_real.strftime('%d/%m/%Y')}</b>"
        if dias_offset > 0:
            texto_fecha += (f" (pedida: {fecha_pedida.strftime('%d/%m/%Y')}, "
                           f"{dias_offset} día{'s' if dias_offset != 1 else ''} de diferencia)")
        texto_fecha += f" · cobertura despejada en el punto: {fraccion_valida * 100:.0f}%"
        aviso = QLabel(texto_fecha)
        aviso.setTextFormat(Qt.TextFormat.RichText)
        aviso.setWordWrap(True)
        aviso.setStyleSheet("color: #444; font-size: 11px; padding-bottom: 4px;")
        layout.addWidget(aviso)
        if fraccion_valida < 0.5:
            alerta = QLabel(
                "⚠ La cobertura despejada en este punto es baja — puede haber "
                "contaminación residual de nubes o sombra en los valores.")
            alerta.setWordWrap(True)
            alerta.setStyleSheet("color: #b45309; font-size: 10.5px;")
            layout.addWidget(alerta)

        # --- Referencia más parecida (siempre calculada, ángulo espectral) ---
        bandas_ids = [b["id"] for b in BANDAS_S2]
        similitudes = [(nombre, _similitud_sam(reflectancias, info["valores"], bandas_ids))
                      for nombre, info in REFERENCIAS_FIRMA.items()]
        similitudes.sort(key=lambda par: -par[1])
        nombre_mejor, valor_mejor = similitudes[0]
        lbl_similitud = QLabel(
            f"Referencia más parecida: <b>{nombre_mejor}</b> "
            f"({valor_mejor:.0f}% de similitud, ángulo espectral)")
        lbl_similitud.setTextFormat(Qt.TextFormat.RichText)
        lbl_similitud.setWordWrap(True)
        lbl_similitud.setStyleSheet("color: #2e7d32; font-size: 11px; font-weight: bold; padding-bottom: 2px;")
        layout.addWidget(lbl_similitud)

        # --- Botón para superponer referencias a la vista ---
        fila_ref = QHBoxLayout()
        self.btn_referencias = QPushButton("+ Comparar con referencia")
        self.btn_referencias.setStyleSheet(
            "QPushButton { padding: 3px 12px; border-radius: 4px; border: 1px solid #ccc; }")
        self.btn_referencias.clicked.connect(self._menu_referencias)
        fila_ref.addWidget(self.btn_referencias)
        fila_ref.addStretch()
        layout.addLayout(fila_ref)

        # --- Figura ---
        self.fig = Figure(figsize=(10.4, 5.8), dpi=100)
        self.fig.patch.set_facecolor("white")
        self.canvas = FigureCanvas(self.fig)
        self.ax = self.fig.add_subplot(111)

        self.toolbar = NavigationToolbar(self.canvas, self)
        acciones_permitidas = {"Home", "Pan", "Zoom", "Back", "Forward"}
        for accion in self.toolbar.actions():
            if accion.text() not in acciones_permitidas and not accion.isSeparator():
                self.toolbar.removeAction(accion)
        self.toolbar.setStyleSheet("QToolBar { border: none; spacing: 2px; }")
        layout.addWidget(self.toolbar)
        layout.addWidget(self.canvas)

        self.lbl_hover = QLabel(" ")
        self.lbl_hover.setStyleSheet(
            "color: #222; font-size: 11px; font-weight: bold; padding-top: 2px;")
        layout.addWidget(self.lbl_hover)
        self.canvas.mpl_connect("motion_notify_event", self._al_mover_raton)
        self.canvas.mpl_connect("axes_leave_event", self._al_salir_raton)

        self._dibujar()

        # --- Disclaimer ---
        anio_actual = datetime.now().year
        disclaimer = QLabel(
            f"Fuente: Copernicus Sentinel-2 L2A (ESA), procesado vía Copernicus Data Space "
            f"Ecosystem. Acceso libre y gratuito según la Legal Notice on the use of Copernicus "
            f"Sentinel Data — atribución requerida al redistribuir: "
            f"<i>«Copernicus Sentinel data {anio_actual}»</i>. Datos entregados sin garantía "
            f"expresa ni implícita de exactitud.")
        disclaimer.setWordWrap(True)
        disclaimer.setTextFormat(Qt.TextFormat.RichText)
        disclaimer.setStyleSheet("color: #999; font-size: 9.5px; padding-top: 6px;")
        layout.addWidget(disclaimer)

        fila_botones = QHBoxLayout()
        fila_botones.addStretch()
        btn_cerrar = QPushButton("Cerrar")
        btn_cerrar.setStyleSheet("QPushButton { padding: 5px 18px; border-radius: 4px; }")
        btn_cerrar.clicked.connect(self.accept)
        fila_botones.addWidget(btn_cerrar)
        layout.addLayout(fila_botones)

    def _menu_referencias(self):
        menu = QMenu(self)
        for nombre, info in REFERENCIAS_FIRMA.items():
            accion = menu.addAction(nombre)
            accion.setCheckable(True)
            accion.setChecked(nombre in self.referencias_activas)
            accion.setToolTip(info["fuente"])
            accion.toggled.connect(partial(self._alternar_referencia, nombre))
        menu.exec(self.btn_referencias.mapToGlobal(self.btn_referencias.rect().bottomLeft()))

    def _alternar_referencia(self, nombre, activada):
        if activada and nombre not in self.referencias_activas:
            self.referencias_activas.append(nombre)
        elif not activada and nombre in self.referencias_activas:
            self.referencias_activas.remove(nombre)
        self._dibujar()

    def _dibujar(self):
        self.ax.clear()
        reflectancias = self.reflectancias
        bandas_presentes = [b for b in BANDAS_S2 if b["id"] in reflectancias]
        # Eje X a escala real de longitud de onda (nm), con el hueco vacío
        # 945-1610nm comprimido (ninguna banda cae ahí, así que no merece la
        # pena dedicarle la mitad del ancho del gráfico). Todo lo demás
        # conserva la proporción real entre bandas.
        posiciones = [_nm_a_x(b["nm"]) for b in bandas_presentes]
        valores = [reflectancias[b["id"]] for b in bandas_presentes]
        etiquetas = [f"{b['id']} · {b['nm']}nm" for b in bandas_presentes]
        colores_banda = [b.get("color", "#37474f") for b in bandas_presentes]

        self.ax.set_facecolor("#fbfbfb")

        # Franjas de fondo por región, a partir de sus límites reales en nm
        # (comprimidos con la misma transformación que los puntos).
        franjas = []  # (nombre, color, x_desde, x_hasta)
        for region in REGIONES_ESPECTRO:
            x_desde, x_hasta = _nm_a_x(region["desde"]), _nm_a_x(region["hasta"])
            franjas.append((region["nombre"], region["color"], x_desde, x_hasta))
        nm_min = min(b["nm"] for b in bandas_presentes) - 20
        nm_max = max(b["nm"] for b in bandas_presentes) + 20
        for nombre, color, x_desde, x_hasta in franjas:
            if x_hasta >= _nm_a_x(nm_min) and x_desde <= _nm_a_x(nm_max):
                self.ax.axvspan(x_desde, x_hasta, color=color, alpha=0.5, zorder=0)

        # Curva: interpolación PCHIP entre los 12 valores reales (no altera
        # ningún dato, solo dibuja una transición curva en vez de quebrada;
        # a diferencia de una media móvil, no mezcla el valor de una banda
        # con el de la vecina). Si no hay scipy disponible, línea recta normal.
        if _TIENE_SCIPY and len(posiciones) >= 3:
            interpolador = PchipInterpolator(posiciones, valores)
            x_fino = [posiciones[0] + i * (posiciones[-1] - posiciones[0]) / 300 for i in range(301)]
            y_fino = interpolador(x_fino)
            self.ax.plot(x_fino, y_fino, linewidth=1.8, color="#37474f", zorder=2)
        else:
            self.ax.plot(posiciones, valores, linewidth=1.8, color="#37474f", zorder=2)

        # Puntos: un color por banda (real en visible, convenio de falso
        # color en el resto) para leer de un vistazo qué banda es cada cosa.
        for x, y, color in zip(posiciones, valores, colores_banda):
            self.ax.plot(x, y, marker="o", markersize=8, color=color,
                        markeredgecolor="white", markeredgewidth=1, zorder=3)

        # Curvas de referencia superpuestas (si se han activado)
        handles_ref, etiquetas_ref = [], []
        for nombre_ref in self.referencias_activas:
            info = REFERENCIAS_FIRMA.get(nombre_ref)
            if not info:
                continue
            valores_ref = [info["valores"][b["id"]] for b in bandas_presentes if b["id"] in info["valores"]]
            posiciones_ref = [_nm_a_x(b["nm"]) for b in bandas_presentes if b["id"] in info["valores"]]
            if len(posiciones_ref) >= 3 and _TIENE_SCIPY:
                interp_ref = PchipInterpolator(posiciones_ref, valores_ref)
                xf = [posiciones_ref[0] + i * (posiciones_ref[-1] - posiciones_ref[0]) / 300 for i in range(301)]
                yf = interp_ref(xf)
                linea, = self.ax.plot(xf, yf, linestyle="--", linewidth=1.4,
                                     color=info["color"], alpha=0.85, zorder=1)
            else:
                linea, = self.ax.plot(posiciones_ref, valores_ref, linestyle="--", linewidth=1.4,
                                     color=info["color"], alpha=0.85, zorder=1)
            handles_ref.append(linea)
            etiquetas_ref.append(nombre_ref)

        self._posiciones = posiciones
        self._valores = valores
        self._bandas = bandas_presentes

        self.hover_marker, = self.ax.plot([], [], "o", markersize=13, markerfacecolor="none",
                                          markeredgecolor="#222", markeredgewidth=1.6,
                                          zorder=6, visible=False)

        # Marca de "hueco comprimido" en el eje, convenio habitual de eje partido
        x_rotura = _nm_a_x(GAP_DESDE_NM) + (_nm_a_x(GAP_HASTA_NM) - _nm_a_x(GAP_DESDE_NM)) / 2
        for dx in (-6, 6):
            self.ax.plot([x_rotura + dx - 4, x_rotura + dx + 4], [-0.045, -0.015],
                        transform=self.ax.get_xaxis_transform(), clip_on=False,
                        color="#888", linewidth=1.2, zorder=5)

        self.ax.set_xlabel("Banda / longitud de onda", fontsize=10, color="#444", labelpad=10)
        self.ax.set_xticks(posiciones)
        self.ax.set_xticklabels(etiquetas, fontsize=8.5, rotation=35, ha="right")
        margen = (posiciones[-1] - posiciones[0]) * 0.03
        self.ax.set_xlim(posiciones[0] - margen, posiciones[-1] + margen)
        self.ax.set_ylabel("Reflectancia (%)", fontsize=10, color="#444")
        self.ax.yaxis.set_major_formatter(PercentFormatter(xmax=1.0))
        self.ax.set_title("Firma espectral — Sentinel-2 L2A", fontsize=14,
                          fontweight="bold", color="#222", pad=14)
        # 0-100% por defecto (comparable entre gráficas), pero sin cortar
        # casos reales que superan el 100% (nieve puede dar 120-140%, por
        # ejemplo por sobrecorrección atmosférica sobre superficies muy brillantes).
        valores_para_techo = list(valores)
        for nombre_ref in self.referencias_activas:
            info = REFERENCIAS_FIRMA.get(nombre_ref)
            if info:
                valores_para_techo.extend(info["valores"].values())
        techo = max(1.0, max(valores_para_techo) * 1.08) if valores_para_techo else 1.0
        self.ax.set_ylim(0, techo)

        # Leyenda de regiones + referencias activas, combinadas en una sola.
        # Fondo blanco sólido: sin él, los cuadraditos de color (ya de por sí
        # pastel) se mezclan con las propias franjas de fondo que hay detrás.
        nombres_vistos = []
        handles, etiquetas_leyenda = [], []
        for nombre, color, x_desde, x_hasta in franjas:
            if nombre not in nombres_vistos and x_hasta >= _nm_a_x(nm_min) and x_desde <= _nm_a_x(nm_max):
                nombres_vistos.append(nombre)
                handles.append(self.ax.axvspan(0, 0, color=color, alpha=0.9))
                etiquetas_leyenda.append(nombre)
        handles += handles_ref
        etiquetas_leyenda += etiquetas_ref
        leyenda = self.ax.legend(handles, etiquetas_leyenda,
                                 loc="upper right", fontsize=8, ncol=2,
                                 frameon=True, facecolor="white", edgecolor="#ccc",
                                 framealpha=0.95)
        leyenda.set_zorder(10)

        self.ax.grid(True, axis="y", linestyle="--", linewidth=0.6, alpha=0.35, color="#999")
        self.ax.grid(False, axis="x")
        for lado in ("top", "right"):
            self.ax.spines[lado].set_visible(False)
        for lado in ("left", "bottom"):
            self.ax.spines[lado].set_color("#bbb")
        self.ax.tick_params(axis="y", labelsize=9.5, colors="#555")

        self.fig.tight_layout()
        self.canvas.draw()

    def _al_mover_raton(self, event):
        if event.inaxes != self.ax or not self._posiciones or event.xdata is None:
            self._al_salir_raton()
            return
        diffs = [abs(x - event.xdata) for x in self._posiciones]
        i = diffs.index(min(diffs))
        banda = self._bandas[i]

        self.hover_marker.set_data([self._posiciones[i]], [self._valores[i]])
        self.hover_marker.set_visible(True)
        self.canvas.draw_idle()

        self.lbl_hover.setText(
            f"{banda['id']} ({banda['region']})  ·  {banda['nm']} nm  ·  "
            f"reflectancia: {self._valores[i] * 100:.1f}%")

    def _al_salir_raton(self, event=None):
        if getattr(self, "hover_marker", None) is not None:
            self.hover_marker.set_visible(False)
            self.canvas.draw_idle()
        self.lbl_hover.setText(" ")
