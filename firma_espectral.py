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

from qgis.PyQt.QtCore import Qt, QUrl, QByteArray, QEventLoop, QDate, QObject, pyqtSignal
from qgis.PyQt.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                                 QPushButton, QDateEdit, QDialogButtonBox, QMenu,
                                 QFrame, QComboBox, QWidget)
from qgis.PyQt.QtGui import QPainter, QColor, QPen
from qgis.PyQt import QtNetwork
from qgis.gui import QgsMapTool
from qgis.core import (QgsProject, QgsCoordinateReferenceSystem,
                       QgsCoordinateTransform, QgsNetworkAccessManager,
                       QgsMessageLog, Qgis)

from .config import (CDSE_STATS_URL, BANDAS_S2, REGIONES_ESPECTRO, FIRMA_VENTANA_DIAS_BUSQUEDA,
                     GAP_DESDE_NM, GAP_HASTA_NM, GAP_COMPRESION, REFERENCIAS_FIRMA)
from .exportar import crear_boton_exportar, exportar_figura, exportar_csv
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

_MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio",
          "agosto", "septiembre", "octubre", "noviembre", "diciembre"]
_COLOR_FECHA = "#6d4c9f"   # mismo morado de las tarjetas de acción de la galería
_FECHA_MINIMA = QDate(2017, 1, 1)

# (texto del botón, mes, día) -> fecha central de cada estación; la búsqueda
# de ±N días alrededor de ella cae dentro de la propia estación.
_ESTACIONES = [("🌱 Primavera", 5, 5), ("☀️ Verano", 8, 5),
               ("🍂 Otoño", 11, 5), ("❄️ Invierno", 2, 5)]


class LineaTemporalDisponibilidad(QWidget):
    """Franja con una barra por cada imagen de Sentinel-2 disponible sobre el
    punto: color y altura según la parte despejada de nubes (verde = despejada,
    ámbar = parcial, gris = nublada).

    Por defecto enseña una ventana de ~6 meses centrada en la fecha elegida
    (barras anchas y separadas, fáciles de pinchar); con "Ver año" enseña el
    año completo. Al pasar el ratón se resalta la imagen que se elegiría (la
    más cercana al cursor) y se emite su información; al pinchar se emite la
    fecha de esa imagen."""

    fecha_elegida = pyqtSignal(QDate)
    ventana_cambiada = pyqtSignal()
    info_cambiada = pyqtSignal(str)

    _VERDE, _AMBAR, _GRIS = QColor("#43a047"), QColor("#f9a825"), QColor("#90a4ae")
    _MORADO = QColor(_COLOR_FECHA)
    _ALTO_BARRAS = 50
    _MARGEN = 8
    _DIAS_VENTANA = 183
    _ALCANCE_IMAN = 60          # píxeles: dentro de este radio se elige la imagen más cercana
    TEXTO_AYUDA = "Pasa el ratón por las barras y pincha para elegir esa imagen"

    def __init__(self, hoy, parent=None):
        super().__init__(parent)
        self.setFixedHeight(96)
        self.setMouseTracking(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._hoy = hoy
        self._por_anio = {}          # año -> [(QDate, fraccion)]
        self._modo_anio = False
        self._ini = self._fin = None
        self._fecha = None
        self._mensaje = ""
        self._hover = None           # (QDate, fraccion) de la imagen resaltada

    # --- ventana visible
    def rango(self):
        return self._ini, self._fin

    def anios_visibles(self):
        return sorted({self._ini.year(), self._fin.year()}) if self._ini else []

    def modo_anio(self):
        return self._modo_anio

    def alternar_modo(self):
        self._modo_anio = not self._modo_anio
        self._centrar(self._fecha or self._hoy)

    def _centrar(self, qdate):
        """Coloca la ventana alrededor de qdate respetando 2017 - hoy."""
        if self._modo_anio:
            self._ini, self._fin = QDate(qdate.year(), 1, 1), QDate(qdate.year(), 12, 31)
        else:
            mitad = self._DIAS_VENTANA // 2
            ini, fin = qdate.addDays(-mitad), qdate.addDays(self._DIAS_VENTANA - mitad)
            if fin > self._hoy:
                fin, ini = self._hoy, self._hoy.addDays(-self._DIAS_VENTANA)
            if ini < _FECHA_MINIMA:
                ini, fin = _FECHA_MINIMA, _FECHA_MINIMA.addDays(self._DIAS_VENTANA)
            self._ini, self._fin = ini, fin
        self._hover = None
        self.update()
        self.ventana_cambiada.emit()

    def desplazar(self, dias):
        """Mueve la ventana (no el día elegido). Solo en la vista de ~6 meses."""
        if self._modo_anio or self._ini is None:
            return
        ini = self._ini.addDays(dias)
        if ini < _FECHA_MINIMA:
            ini = _FECHA_MINIMA
        if ini.addDays(self._DIAS_VENTANA) > self._hoy:
            ini = self._hoy.addDays(-self._DIAS_VENTANA)
        self._ini, self._fin = ini, ini.addDays(self._DIAS_VENTANA)
        self._hover = None
        self.update()
        self.ventana_cambiada.emit()

    def puede_retroceder(self):
        return not self._modo_anio and self._ini is not None and self._ini > _FECHA_MINIMA

    def puede_avanzar(self):
        return not self._modo_anio and self._fin is not None and self._fin < self._hoy

    # --- datos y estado
    def set_imagenes(self, anio, imagenes):
        self._por_anio[anio] = sorted(imagenes, key=lambda par: par[0])
        self.update()

    def set_mensaje(self, mensaje):
        self._mensaje = mensaje
        self.update()

    def marcar_fecha(self, qdate):
        self._fecha = qdate
        fuera = (self._ini is None or not (self._ini <= qdate <= self._fin)
                 or (self._modo_anio and qdate.year() != self._ini.year()))
        if fuera:
            self._centrar(qdate)
        else:
            self.update()

    def imagenes_visibles(self):
        if self._ini is None:
            return []
        return [(q, f) for lista in self._por_anio.values() for q, f in lista
                if self._ini <= q <= self._fin]

    # --- geometría
    def _x_de(self, qdate):
        dias = self._ini.daysTo(self._fin) or 1
        ancho = self.width() - 2 * self._MARGEN
        return self._MARGEN + ancho * self._ini.daysTo(qdate) / dias

    def _fecha_de(self, x):
        dias = self._ini.daysTo(self._fin)
        ancho = max(1, self.width() - 2 * self._MARGEN)
        frac = min(max((x - self._MARGEN) / ancho, 0.0), 1.0)
        return self._ini.addDays(int(round(frac * dias)))

    def _imagen_cercana(self, x):
        """La imagen visible más próxima a x, si cae dentro del alcance del imán."""
        mejor, dist = None, self._ALCANCE_IMAN + 1
        for qdate, fraccion in self.imagenes_visibles():
            d = abs(self._x_de(qdate) - x)
            if d < dist:
                mejor, dist = (qdate, fraccion), d
        return mejor

    @classmethod
    def _color(cls, fraccion):
        return cls._VERDE if fraccion >= 0.8 else (cls._AMBAR if fraccion >= 0.5 else cls._GRIS)

    # --- dibujo
    def paintEvent(self, _evento):
        if self._ini is None:
            return
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setPen(QPen(QColor("#e0e0e0")))
        p.setBrush(QColor("#fafafa"))
        p.drawRoundedRect(0, 0, self.width() - 1, self.height() - 1, 6, 6)

        base = self._MARGEN + self._ALTO_BARRAS
        fuente = p.font()
        fuente.setPointSizeF(7.5)
        p.setFont(fuente)

        # Línea base y meses
        p.setPen(QPen(QColor("#ccc")))
        p.drawLine(self._MARGEN, base + 1, self.width() - self._MARGEN, base + 1)
        mes = QDate(self._ini.year(), self._ini.month(), 1)
        primero = True
        while mes <= self._fin:
            if mes >= self._ini:
                x = int(self._x_de(mes))
                p.setPen(QPen(QColor("#999")))
                p.drawLine(x, base + 2, x, base + 6)
                nombre = _MESES[mes.month() - 1][:3].capitalize()
                if mes.month() == 1 or primero:
                    nombre += f" {mes.year()}"
                p.drawText(x + 2, base + 18, nombre)
                primero = False
            mes = mes.addMonths(1)

        if self._mensaje:
            p.setPen(QPen(QColor("#777")))
            p.drawText(self._MARGEN, self._MARGEN, self.width() - 2 * self._MARGEN,
                       self._ALTO_BARRAS, int(Qt.AlignmentFlag.AlignCenter), self._mensaje)

        ancho_barra = 3 if self._modo_anio else 6
        p.setPen(Qt.PenStyle.NoPen)

        # Columna resaltada de la imagen que se elegiría
        if self._hover is not None:
            x = int(self._x_de(self._hover[0]))
            p.setBrush(QColor(109, 76, 159, 45))
            p.drawRoundedRect(x - 8, self._MARGEN - 3, 16, self._ALTO_BARRAS + 6, 4, 4)

        for qdate, fraccion in self.imagenes_visibles():
            alto = 10 + (self._ALTO_BARRAS - 10) * max(0.0, min(1.0, fraccion))
            x = int(self._x_de(qdate))
            resaltada = self._hover is not None and self._hover[0] == qdate
            ancho = ancho_barra + 3 if resaltada else ancho_barra
            p.setBrush(self._color(fraccion))
            p.drawRect(x - ancho // 2, int(base - alto), ancho, int(alto))

        # Fecha marcada
        if self._fecha is not None and self._ini <= self._fecha <= self._fin:
            x = int(self._x_de(self._fecha))
            p.setPen(QPen(self._MORADO, 2))
            p.drawLine(x, self._MARGEN - 3, x, base + 1)

    # --- ratón
    @staticmethod
    def _x_evento(evento):
        return (evento.position() if hasattr(evento, "position") else evento.pos()).x()

    def mouseMoveEvent(self, evento):
        if self._ini is None:
            return
        cerca = self._imagen_cercana(self._x_evento(evento))
        if cerca != self._hover:
            self._hover = cerca
            self.update()
            if cerca:
                qdate, fraccion = cerca
                self.info_cambiada.emit(
                    f"📅 {qdate.toString('dd/MM/yyyy')} · {fraccion * 100:.0f} % despejado")
            else:
                self.info_cambiada.emit(self.TEXTO_AYUDA)

    def leaveEvent(self, _evento):
        if self._hover is not None:
            self._hover = None
            self.update()
        self.info_cambiada.emit(self.TEXTO_AYUDA)

    def mousePressEvent(self, evento):
        if evento.button() != Qt.MouseButton.LeftButton or self._ini is None:
            return
        x = self._x_evento(evento)
        cerca = self._imagen_cercana(x)
        self.fecha_elegida.emit(cerca[0] if cerca else self._fecha_de(x))


class DialogoFechaAproximada(QDialog):
    """Selector de fecha para Firma espectral y Ver imagen: atajos rápidos
    (hoy, hace 1 mes...), selección por estación y año, y el calendario clásico
    para ajustar el día exacto. Una frase se actualiza sola y dice qué rango de
    fechas se va a explorar."""

    def __init__(self, parent=None, token=None, lat=None, lon=None):
        super().__init__(parent)
        self.setWindowTitle("Elegir fecha")
        self.setMinimumWidth(760)
        self._hoy = QDate.currentDate()
        # Datos para la línea temporal de imágenes disponibles (opcionales)
        self._token, self._lat, self._lon = token, lat, lon
        self._cache_anios = {}       # año -> [(QDate, fraccion)]
        self._cargando = set()       # años con una petición en curso
        self._fallidos = set()       # años cuya última petición falló
        self._cerrado = False

        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        # --- Cabecera: la fecha elegida, en grande
        cabecera = QFrame()
        cabecera.setStyleSheet(
            "QFrame { background-color: rgba(109, 76, 159, 22); "
            "border: 1px solid rgba(109, 76, 159, 90); border-radius: 10px; }")
        lay_cab = QVBoxLayout(cabecera)
        lay_cab.setContentsMargins(14, 10, 14, 10)
        lay_cab.setSpacing(2)
        etiqueta_pregunta = QLabel("📅  ¿Qué fecha te interesa?")
        etiqueta_pregunta.setStyleSheet(
            f"color: {_COLOR_FECHA}; font-size: 11px; font-weight: bold; border: none; "
            f"background: transparent;")
        self.lbl_fecha = QLabel()
        self.lbl_fecha.setStyleSheet(
            "font-size: 20px; font-weight: bold; color: #333; border: none; background: transparent;")
        self.lbl_rango = QLabel()
        self.lbl_rango.setWordWrap(True)
        self.lbl_rango.setStyleSheet(
            "font-size: 11px; color: #555; border: none; background: transparent;")
        lay_cab.addWidget(etiqueta_pregunta)
        lay_cab.addWidget(self.lbl_fecha)
        lay_cab.addWidget(self.lbl_rango)
        layout.addWidget(cabecera)

        # --- Atajos rápidos
        layout.addWidget(self._titulo_seccion("Atajos"))
        fila_atajos = QHBoxLayout()
        fila_atajos.setSpacing(6)
        for texto, meses in (("Hoy", 0), ("Hace 1 mes", 1), ("Hace 6 meses", 6), ("Hace 1 año", 12)):
            boton = self._boton_fecha(texto)
            boton.clicked.connect(lambda _c=False, m=meses: self._poner_fecha(self._hoy.addMonths(-m)))
            fila_atajos.addWidget(boton)
        layout.addLayout(fila_atajos)

        # --- Por estación del año
        layout.addWidget(self._titulo_seccion("Por estación del año"))
        fila_estacion = QHBoxLayout()
        fila_estacion.setSpacing(6)
        self.combo_anio = QComboBox()
        for anio in range(self._hoy.year(), _FECHA_MINIMA.year() - 1, -1):
            self.combo_anio.addItem(str(anio), anio)
        self.combo_anio.setMinimumWidth(70)
        fila_estacion.addWidget(self.combo_anio)
        self.botones_estacion = []
        for texto, mes, dia in _ESTACIONES:
            boton = self._boton_fecha(texto)
            boton.clicked.connect(lambda _c=False, m=mes, d=dia: self._poner_estacion(m, d))
            self.botones_estacion.append((boton, mes, dia))
            fila_estacion.addWidget(boton)
        layout.addLayout(fila_estacion)
        self.combo_anio.currentIndexChanged.connect(self._actualizar_estaciones)
        self.combo_anio.currentIndexChanged.connect(self._al_cambiar_anio)

        # --- Línea temporal: imágenes disponibles en el punto y su nubosidad
        self.linea = None
        if token and lat is not None and lon is not None:
            layout.addWidget(self._titulo_seccion("Imágenes disponibles en este punto"))
            self.linea = LineaTemporalDisponibilidad(self._hoy)
            self.linea.fecha_elegida.connect(self._poner_fecha)
            self.linea.ventana_cambiada.connect(self._al_cambiar_ventana)
            layout.addWidget(self.linea)

            fila_nav = QHBoxLayout()
            fila_nav.setSpacing(6)
            self.btn_ant = self._boton_fecha("◀")
            self.btn_sig = self._boton_fecha("▶")
            for boton in (self.btn_ant, self.btn_sig):
                boton.setFixedWidth(40)
            self.btn_ant.setToolTip("Meses anteriores")
            self.btn_sig.setToolTip("Meses siguientes")
            self.btn_ant.clicked.connect(lambda _c=False: self.linea.desplazar(-90))
            self.btn_sig.clicked.connect(lambda _c=False: self.linea.desplazar(90))
            self.lbl_rango_linea = QLabel()
            self.lbl_rango_linea.setStyleSheet("color: #555; font-size: 11px;")
            self.btn_modo = self._boton_fecha("Ver año completo")
            self.btn_modo.clicked.connect(lambda _c=False: self.linea.alternar_modo())
            fila_nav.addWidget(self.btn_ant)
            fila_nav.addWidget(self.btn_sig)
            fila_nav.addWidget(self.lbl_rango_linea)
            fila_nav.addStretch()
            fila_nav.addWidget(self.btn_modo)
            layout.addLayout(fila_nav)

            self.lbl_info = QLabel(LineaTemporalDisponibilidad.TEXTO_AYUDA)
            self.lbl_info.setStyleSheet("color: #444; font-size: 11px; font-weight: 600;")
            self.lbl_info.setMinimumHeight(16)
            self.linea.info_cambiada.connect(self.lbl_info.setText)
            layout.addWidget(self.lbl_info)
            leyenda = QLabel(
                '<span style="color:#43a047">■</span> despejada &nbsp; '
                '<span style="color:#f9a825">■</span> parcial &nbsp; '
                '<span style="color:#90a4ae">■</span> nublada')
            leyenda.setStyleSheet("color: #777; font-size: 10px;")
            layout.addWidget(leyenda)

        # --- Ajuste fino con el calendario
        layout.addWidget(self._titulo_seccion("Día exacto"))
        self.fecha_edit = QDateEdit()
        self.fecha_edit.setCalendarPopup(True)
        self.fecha_edit.setDisplayFormat("dd/MM/yyyy")
        self.fecha_edit.setMaximumDate(self._hoy)
        self.fecha_edit.setMinimumDate(_FECHA_MINIMA)
        self.fecha_edit.setMinimumHeight(28)
        layout.addWidget(self.fecha_edit)

        botones = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        botones.button(QDialogButtonBox.StandardButton.Ok).setText("Buscar imagen")
        botones.button(QDialogButtonBox.StandardButton.Cancel).setText("Cancelar")
        botones.accepted.connect(self.accept)
        botones.rejected.connect(self.reject)
        layout.addWidget(botones)

        self.fecha_edit.dateChanged.connect(self._refrescar_texto)
        self.fecha_edit.setDate(self._hoy)
        self._refrescar_texto()
        self._actualizar_estaciones()
        self._sincronizar_linea()

    # --- piezas de interfaz
    @staticmethod
    def _titulo_seccion(texto):
        etiqueta = QLabel(texto.upper())
        etiqueta.setStyleSheet("color: #777; font-size: 10px; font-weight: bold; letter-spacing: 1px;")
        return etiqueta

    @staticmethod
    def _boton_fecha(texto):
        boton = QPushButton(texto)
        boton.setCursor(Qt.CursorShape.PointingHandCursor)
        boton.setMinimumHeight(30)
        boton.setStyleSheet(f"""
            QPushButton {{
                border: 1px solid #d5d5d5; border-radius: 6px;
                background-color: rgba(109, 76, 159, 14); color: #333; padding: 2px 8px;
            }}
            QPushButton:hover {{
                border: 1px solid {_COLOR_FECHA}; background-color: rgba(109, 76, 159, 55);
            }}
            QPushButton:disabled {{ color: #aaa; background-color: #f3f3f3; }}
        """)
        return boton

    # --- lógica
    def _poner_fecha(self, qdate):
        """Fija la fecha respetando los límites (2017 - hoy)."""
        self.fecha_edit.setDate(min(max(qdate, _FECHA_MINIMA), self._hoy))

    def _poner_estacion(self, mes, dia):
        anio = self.combo_anio.currentData()
        self._poner_fecha(QDate(anio, mes, dia))

    def _actualizar_estaciones(self):
        """Desactiva las estaciones que caen en el futuro (año en curso)."""
        anio = self.combo_anio.currentData()
        for boton, mes, dia in self.botones_estacion:
            fecha = QDate(anio, mes, dia)
            boton.setEnabled(_FECHA_MINIMA <= fecha <= self._hoy)

    def _refrescar_texto(self, *_):
        qd = self.fecha_edit.date()
        self.lbl_fecha.setText(f"{qd.day()} de {_MESES[qd.month() - 1]} de {qd.year()}")
        desde = max(qd.addDays(-FIRMA_VENTANA_DIAS_BUSQUEDA), _FECHA_MINIMA)
        hasta = min(qd.addDays(FIRMA_VENTANA_DIAS_BUSQUEDA), self._hoy)
        self.lbl_rango.setText(
            f"Se buscará la imagen de Sentinel-2 más despejada entre el "
            f"{desde.toString('dd/MM/yyyy')} y el {hasta.toString('dd/MM/yyyy')}. "
            f"Puede que no sea exactamente del día elegido.")
        anio = qd.year()
        indice = self.combo_anio.findData(anio)
        if indice >= 0 and indice != self.combo_anio.currentIndex():
            self.combo_anio.blockSignals(True)
            self.combo_anio.setCurrentIndex(indice)
            self.combo_anio.blockSignals(False)
            self._actualizar_estaciones()
        self._sincronizar_linea()

    # --- línea temporal (carga en segundo plano)
    def _al_cambiar_anio(self, *_):
        """Cambiar el año del selector lleva la fecha al mismo día de ese año
        (o al último día disponible) y recarga la línea temporal."""
        anio = self.combo_anio.currentData()
        if anio is None or anio == self.fecha_edit.date().year():
            return
        actual = self.fecha_edit.date()
        dia = min(actual.day(), QDate(anio, actual.month(), 1).daysInMonth())
        self._poner_fecha(QDate(anio, actual.month(), dia))

    def _sincronizar_linea(self):
        if self.linea is None:
            return
        self.linea.marcar_fecha(self.fecha_edit.date())
        self._al_cambiar_ventana()

    def _al_cambiar_ventana(self):
        """La ventana de la línea temporal ha cambiado: actualiza los controles
        y pide los años que haga falta y aún no estén cargados."""
        ini, fin = self.linea.rango()
        if ini is None:
            return
        if self.linea.modo_anio():
            self.lbl_rango_linea.setText(f"Año {ini.year()}")
            self.btn_modo.setText("Ver 6 meses")
        else:
            self.lbl_rango_linea.setText(
                f"{_MESES[ini.month() - 1][:3]} {ini.year()} – {_MESES[fin.month() - 1][:3]} {fin.year()}")
            self.btn_modo.setText("Ver año completo")
        self.btn_ant.setEnabled(self.linea.puede_retroceder())
        self.btn_sig.setEnabled(self.linea.puede_avanzar())
        for anio in self.linea.anios_visibles():
            if anio not in self._cache_anios and anio not in self._cargando:
                self._cargar_anio(anio)
        self._actualizar_estado_linea()

    def _cargar_anio(self, anio):
        self._fallidos.discard(anio)
        self._cargando.add(anio)
        fin = min(QDate(anio, 12, 31), self._hoy)
        desde = f"{anio}-01-01T00:00:00Z"
        hasta = f"{fin.toString('yyyy-MM-dd')}T23:59:59Z"
        try:
            solicitar_disponibilidad(
                self._token, self._lat, self._lon, desde, hasta,
                lambda lista, error, a=anio: self._al_llegar(a, lista, error),
                parent=self)
        except Exception as exc:
            self._cargando.discard(anio)
            self._fallidos.add(anio)
            QgsMessageLog.logMessage(f"Línea temporal: {exc}", "IEPNB Tools", Qgis.MessageLevel.Warning)

    def _al_llegar(self, anio, lista, error):
        if self._cerrado:
            return   # el diálogo ya se cerró: se descarta la respuesta
        self._cargando.discard(anio)
        if lista is None:
            QgsMessageLog.logMessage(f"Línea temporal {anio}: {error}", "IEPNB Tools", Qgis.MessageLevel.Warning)
            self._fallidos.add(anio)
        else:
            imagenes = [(QDate(f.year, f.month, f.day), fr) for f, fr in lista]
            self._cache_anios[anio] = imagenes
            self.linea.set_imagenes(anio, imagenes)
        self._actualizar_estado_linea()

    def _actualizar_estado_linea(self):
        """Mensaje sobre la franja: cargando, error o sin imágenes."""
        visibles = self.linea.anios_visibles()
        cargando = [a for a in visibles if a in self._cargando]
        fallidos = [a for a in visibles if a in self._fallidos]
        if cargando:
            mensaje = "Cargando las imágenes de " + " y ".join(str(a) for a in cargando) + "…"
        elif fallidos:
            mensaje = "No se han podido cargar las imágenes (puedes elegir fecha igualmente)"
        elif not self.linea.imagenes_visibles():
            mensaje = "Sin imágenes de Sentinel-2 sobre este punto en este periodo"
        else:
            mensaje = ""
        self.linea.set_mensaje(mensaje)

    def done(self, resultado):
        # Las peticiones en curso no se abortan (ver _al_llegar): su respuesta
        # se descarta al llegar porque el diálogo está cerrado.
        self._cerrado = True
        super().done(resultado)

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

def _cuerpo_statistics(lat, lon, evalscript, fecha_inicio, fecha_fin, intervalo, clave_calculo):
    poligono, crs_uri = punto_a_poligono(lat, lon)
    return {
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


def _nueva_peticion_statistics(token):
    request = QtNetwork.QNetworkRequest(QUrl(CDSE_STATS_URL))
    request.setHeader(QtNetwork.QNetworkRequest.KnownHeaders.ContentTypeHeader, "application/json")
    request.setRawHeader(b"Authorization", f"Bearer {token}".encode("utf-8"))
    return request


def _consultar_statistics(token, lat, lon, evalscript, fecha_inicio, fecha_fin, intervalo, clave_calculo):
    cuerpo = _cuerpo_statistics(lat, lon, evalscript, fecha_inicio, fecha_fin, intervalo, clave_calculo)

    network_manager = QgsNetworkAccessManager.instance()
    request = _nueva_peticion_statistics(token)

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

def _extraer_candidatos(payload):
    """[(fecha, fraccion_despejada), ...] de la respuesta de _evalscript_busqueda,
    sin los días en los que no hay paso del satélite sobre el punto."""
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
    return candidatos


class SolicitudDisponibilidad(QObject):
    """Petición NO bloqueante de los días con imagen sobre un punto. Cuando
    llega la respuesta llama a al_terminar(lista, error): lista = [(fecha,
    fraccion_despejada)] y error = None, o lista = None y error = texto.
    Es un QObject con un método como slot (y no un cierre conectado a la
    señal) porque es el patrón que PyQt gestiona con seguridad cuando la
    respuesta se libera dentro de su propia señal."""

    def __init__(self, token, lat, lon, desde, hasta, al_terminar, parent=None):
        super().__init__(parent)
        self._al_terminar = al_terminar
        cuerpo = _cuerpo_statistics(lat, lon, _evalscript_busqueda(), desde, hasta, "P1D", "cobertura")
        self._reply = QgsNetworkAccessManager.instance().post(
            _nueva_peticion_statistics(token), QByteArray(json.dumps(cuerpo).encode("utf-8")))
        self._reply.finished.connect(self._fin)

    def _fin(self):
        reply, self._reply = self._reply, None
        if reply is None:
            return
        error = reply.error()
        raw = bytes(reply.readAll())
        reply.deleteLater()
        al_terminar, self._al_terminar = self._al_terminar, None
        self.deleteLater()
        if al_terminar is None:
            return
        if error == QtNetwork.QNetworkReply.NetworkError.OperationCanceledError:
            return
        if error != QtNetwork.QNetworkReply.NetworkError.NoError:
            al_terminar(None, raw.decode("utf-8", "ignore") or str(error))
            return
        try:
            lista = _extraer_candidatos(json.loads(raw))
        except Exception as exc:
            al_terminar(None, str(exc))
            return
        al_terminar(lista, None)


def solicitar_disponibilidad(token, lat, lon, desde, hasta, al_terminar, parent=None):
    """Lanza una SolicitudDisponibilidad y la devuelve."""
    return SolicitudDisponibilidad(token, lat, lon, desde, hasta, al_terminar, parent)


def buscar_mejor_fecha(token, lat, lon, fecha_aproximada, ventana_dias=FIRMA_VENTANA_DIAS_BUSQUEDA):
    """Devuelve (fecha_elegida: datetime, fraccion_valida: float) del día,
    dentro de ± ventana_dias, con más cobertura despejada en ese punto.
    Devuelve (None, None) si no hay ninguna adquisición en la ventana."""
    desde = (fecha_aproximada - timedelta(days=ventana_dias)).strftime("%Y-%m-%dT00:00:00Z")
    hasta = (fecha_aproximada + timedelta(days=ventana_dias)).strftime("%Y-%m-%dT23:59:59Z")

    payload = _consultar_statistics(token, lat, lon, _evalscript_busqueda(), desde, hasta, "P1D", "cobertura")

    candidatos = _extraer_candidatos(payload)

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
        self.lat, self.lon, self.fecha_real = lat, lon, fecha_real
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
        fila_botones.addWidget(crear_boton_exportar(
            self, self._exportar_imagen, self._exportar_csv))
        btn_cerrar = QPushButton("Cerrar")
        btn_cerrar.setStyleSheet("QPushButton { padding: 5px 18px; border-radius: 4px; }")
        btn_cerrar.clicked.connect(self.accept)
        fila_botones.addWidget(btn_cerrar)
        layout.addLayout(fila_botones)

    def _nombre_base_exportacion(self):
        return (f"firma_espectral_{self.lat:.5f}_{self.lon:.5f}_"
                f"{self.fecha_real.strftime('%Y-%m-%d')}")

    def _exportar_imagen(self):
        exportar_figura(self, self.fig, self._nombre_base_exportacion(),
                        artistas_ocultos=[self.hover_marker])

    def _exportar_csv(self):
        """Una fila por banda con su reflectancia (0-1); si hay referencias
        superpuestas en la gráfica, una columna más por cada una."""
        nombres_ref = list(self.referencias_activas)
        cabecera = ["banda", "longitud_onda_nm", "region", "reflectancia"]
        cabecera += [f"ref_{n}" for n in nombres_ref]
        filas = []
        for banda in BANDAS_S2:
            if banda["id"] not in self.reflectancias:
                continue
            fila = [banda["id"], banda["nm"], banda["region"],
                    float(self.reflectancias[banda["id"]])]
            for nombre in nombres_ref:
                valor = REFERENCIAS_FIRMA[nombre]["valores"].get(banda["id"])
                fila.append(float(valor) if valor is not None else None)
            filas.append(fila)
        exportar_csv(self, self._nombre_base_exportacion(), cabecera, filas,
                     detalle=f"Imagen Sentinel-2 del {self.fecha_real.strftime('%d/%m/%Y')}.")

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
