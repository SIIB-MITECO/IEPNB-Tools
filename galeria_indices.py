# -*- coding: utf-8 -*-
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

Galerías de selección visual para el botón Copernicus del IEPNB_Tools.

Sustituyen al antiguo QMenu anidado (menú > submenú > submenú), que
funcionaba pero era poco visual: todo texto, sin color, había que ir
desplegando niveles para llegar a la opción deseada.

Cada opción se muestra como una "tarjeta" (TarjetaIndice, un QToolButton
estilizado): franja de color arriba, fondo con un tinte suave del color
de su categoría, icono propio (hoja/gota/llama para vegetación, agua y
nieve, incendios) y el tooltip con la fórmula/descripción que antes
llevaba cada QAction. Las tarjetas de cada categoría van agrupadas
dentro de un panel con fondo tintado y en una rejilla de columnas fijas,
para que se vean como un bloque y no como tarjetas sueltas.

Se han dividido en tres diálogos encadenados, imitando los mismos pasos
que tenía el menú (acción -> punto/área -> estilo), para que en el
futuro cada uno pueda convertirse directamente en una página de un
QWizard sin tener que rehacer la lógica de selección.

    GaleriaAccionesDialog   -> Firma espectral / Ver imagen / índice directo
    GaleriaPuntoAreaDialog  -> Punto (2x2 km) / Dibujar área
    GaleriaEstiloDialog     -> Color real / Falso color / índice

Todas exponen el resultado en `self.resultado` tras un exec() aceptado.
"""

from functools import partial

from qgis.PyQt.QtCore import Qt, QSize, QRectF, QPointF
from qgis.PyQt.QtGui import QIcon, QPixmap, QPainter, QColor, QPen, QPainterPath
from qgis.PyQt.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QGridLayout,
                                 QLabel, QToolButton, QDialogButtonBox, QFrame,
                                 QGraphicsDropShadowEffect)

from .config import CATEGORIAS_INDICES, INDICE_FORMULAS, VER_IMAGEN_MAX_AREA_KM2
from .imagen_satelite import ESTILOS_RGB


# Mismos colores que ya se usan en config.py para las bandas/regiones del
# espectro, para que la paleta sea coherente en todo el plugin.
COLOR_CATEGORIA = {
    "Vegetación": "#43a047",
    "Agua y nieve": "#1e88e5",
    "Incendios y suelo desnudo": "#e53935",
}
COLOR_ACCION = "#6d4c9f"       # Firma espectral / Ver imagen (acciones, no índices)
COLOR_ESTILO_RGB = "#546e7a"   # Color real / Falso color infrarrojo

_NUM_COLUMNAS = 5  # rejilla fija: la categoría más ancha (Vegetación) tiene 5


# --------------------------------------------------------------------------
# Utilidades de color
# --------------------------------------------------------------------------

def _rgba(color_hex, alpha):
    """'#43a047' + alpha (0-255) -> 'rgba(67, 160, 71, alpha)'."""
    c = QColor(color_hex)
    return f"rgba({c.red()}, {c.green()}, {c.blue()}, {alpha})"


def _ajustar_texto(texto, umbral=11):
    """Textos largos (p.ej. 'Falso color infrarrojo') se recortarían con
    puntos suspensivos en una tarjeta estrecha; en vez de eso, partimos
    por el espacio más cercano al centro para que quepan en dos líneas."""
    if len(texto) <= umbral or " " not in texto:
        return texto
    espacios = [i for i, c in enumerate(texto) if c == " "]
    centro = len(texto) / 2
    corte = min(espacios, key=lambda i: abs(i - centro))
    return texto[:corte] + "\n" + texto[corte + 1:]


# --------------------------------------------------------------------------
# Iconos dibujados a mano (sin depender de ficheros externos): un
# pictograma sencillo por categoría/acción, coloreado con el color que
# le corresponda.
# --------------------------------------------------------------------------

def _icono_hoja(color_hex, size=30):
    """Vegetación: una hoja con nervadura central."""
    pm = QPixmap(size, size)
    pm.fill(Qt.GlobalColor.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    p.translate(size / 2, size / 2)
    p.rotate(-45)
    w, h = size * 0.62, size * 0.9
    path = QPainterPath()
    path.moveTo(0, -h / 2)
    path.quadTo(-w / 2, 0, 0, h / 2)
    path.quadTo(w / 2, 0, 0, -h / 2)
    p.setBrush(QColor(color_hex))
    p.setPen(Qt.PenStyle.NoPen)
    p.drawPath(path)
    pen = QPen(QColor(255, 255, 255, 190))
    pen.setWidthF(1.3)
    p.setPen(pen)
    p.drawLine(QPointF(0, -h / 2 * 0.85), QPointF(0, h / 2 * 0.85))
    p.end()
    return QIcon(pm)


def _icono_agua(color_hex, size=30):
    """Agua y nieve: una gota."""
    pm = QPixmap(size, size)
    pm.fill(Qt.GlobalColor.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    w = size
    path = QPainterPath()
    path.moveTo(w * 0.5, w * 0.08)
    path.cubicTo(w * 0.90, w * 0.55, w * 0.80, w * 0.92, w * 0.5, w * 0.92)
    path.cubicTo(w * 0.20, w * 0.92, w * 0.10, w * 0.55, w * 0.5, w * 0.08)
    p.setBrush(QColor(color_hex))
    p.setPen(Qt.PenStyle.NoPen)
    p.drawPath(path)
    p.setBrush(QColor(255, 255, 255, 150))
    p.drawEllipse(QRectF(w * 0.36, w * 0.5, w * 0.14, w * 0.14))
    p.end()
    return QIcon(pm)


def _icono_llama(color_hex, size=30):
    """Incendios y suelo desnudo: una llama con núcleo más claro."""
    pm = QPixmap(size, size)
    pm.fill(Qt.GlobalColor.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    w = size
    path = QPainterPath()
    path.moveTo(w * 0.5, w * 0.05)
    path.cubicTo(w * 0.80, w * 0.35, w * 0.62, w * 0.42, w * 0.72, w * 0.60)
    path.cubicTo(w * 0.80, w * 0.80, w * 0.62, w * 0.95, w * 0.5, w * 0.95)
    path.cubicTo(w * 0.38, w * 0.95, w * 0.20, w * 0.80, w * 0.28, w * 0.60)
    path.cubicTo(w * 0.34, w * 0.68, w * 0.40, w * 0.62, w * 0.38, w * 0.50)
    path.cubicTo(w * 0.42, w * 0.55, w * 0.46, w * 0.52, w * 0.44, w * 0.42)
    path.cubicTo(w * 0.55, w * 0.30, w * 0.42, w * 0.20, w * 0.5, w * 0.05)
    p.setBrush(QColor(color_hex))
    p.setPen(Qt.PenStyle.NoPen)
    p.drawPath(path)
    p.setBrush(QColor(255, 235, 180, 220))
    nucleo = QPainterPath()
    nucleo.moveTo(w * 0.5, w * 0.45)
    nucleo.cubicTo(w * 0.62, w * 0.60, w * 0.58, w * 0.75, w * 0.5, w * 0.82)
    nucleo.cubicTo(w * 0.42, w * 0.75, w * 0.40, w * 0.60, w * 0.5, w * 0.45)
    p.drawPath(nucleo)
    p.end()
    return QIcon(pm)


def _icono_grafica(color_hex, size=30):
    """Firma espectral: mini gráfica de línea con ejes."""
    pm = QPixmap(size, size)
    pm.fill(Qt.GlobalColor.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    w = size
    pen_ejes = QPen(QColor(120, 120, 120))
    pen_ejes.setWidthF(1.4)
    p.setPen(pen_ejes)
    p.drawLine(QPointF(w * 0.15, w * 0.15), QPointF(w * 0.15, w * 0.85))
    p.drawLine(QPointF(w * 0.15, w * 0.85), QPointF(w * 0.90, w * 0.85))
    pen_linea = QPen(QColor(color_hex))
    pen_linea.setWidthF(2.2)
    pen_linea.setCapStyle(Qt.PenCapStyle.RoundCap)
    pen_linea.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
    p.setPen(pen_linea)
    puntos = [QPointF(w * 0.22, w * 0.65), QPointF(w * 0.40, w * 0.72),
              QPointF(w * 0.55, w * 0.40), QPointF(w * 0.70, w * 0.55),
              QPointF(w * 0.85, w * 0.25)]
    for i in range(len(puntos) - 1):
        p.drawLine(puntos[i], puntos[i + 1])
    p.setBrush(QColor(color_hex))
    p.setPen(Qt.PenStyle.NoPen)
    for pt in puntos:
        p.drawEllipse(pt, w * 0.035, w * 0.035)
    p.end()
    return QIcon(pm)


def _icono_foto(color_hex, size=30):
    """Ver imagen: marco + sol + montaña, icono clásico de "imagen"."""
    pm = QPixmap(size, size)
    pm.fill(Qt.GlobalColor.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    w = size
    pen = QPen(QColor(color_hex))
    pen.setWidthF(1.8)
    p.setPen(pen)
    p.setBrush(Qt.BrushStyle.NoBrush)
    marco = QRectF(w * 0.08, w * 0.14, w * 0.84, w * 0.72)
    p.drawRoundedRect(marco, w * 0.06, w * 0.06)
    p.setBrush(QColor(color_hex))
    p.setPen(Qt.PenStyle.NoPen)
    p.drawEllipse(QRectF(w * 0.20, w * 0.26, w * 0.14, w * 0.14))
    montana = QPainterPath()
    montana.moveTo(w * 0.14, w * 0.80)
    montana.lineTo(w * 0.40, w * 0.45)
    montana.lineTo(w * 0.56, w * 0.62)
    montana.lineTo(w * 0.68, w * 0.48)
    montana.lineTo(w * 0.86, w * 0.80)
    montana.closeSubpath()
    p.drawPath(montana)
    p.end()
    return QIcon(pm)


ICONO_CATEGORIA = {
    "Vegetación": _icono_hoja,
    "Agua y nieve": _icono_agua,
    "Incendios y suelo desnudo": _icono_llama,
}


# --------------------------------------------------------------------------
# Widgets base
# --------------------------------------------------------------------------

class TarjetaIndice(QToolButton):
    """Botón-tarjeta: icono propio, franja de color arriba, fondo con un
    tinte suave del mismo color, texto en negrita y sombra suave. Es la
    pieza básica de todas las galerías de este módulo."""

    def __init__(self, texto, color_hex, tooltip="", icono=None,
                 ancho=92, alto=80, icono_size=28, parent=None):
        super().__init__(parent)
        self.setText(texto)
        if icono is not None:
            self.setIcon(icono)
            self.setIconSize(QSize(icono_size, icono_size))
            self.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
        else:
            self.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextOnly)
        self.setFixedSize(ancho, alto)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        if tooltip:
            self.setToolTip(tooltip)

        tinte = _rgba(color_hex, 28)
        tinte_hover = _rgba(color_hex, 65)

        self.setStyleSheet(f"""
            QToolButton {{
                border: 1px solid #e2e2e2;
                border-top: 4px solid {color_hex};
                border-radius: 8px;
                background-color: {tinte};
                font-size: 11px;
                font-weight: 600;
                color: #333333;
                padding-top: 4px;
            }}
            QToolButton:hover {{
                border: 2px solid {color_hex};
                border-top: 4px solid {color_hex};
                background-color: {tinte_hover};
            }}
            QToolButton:pressed {{
                background-color: {tinte_hover};
                border: 2px solid {color_hex};
                border-top: 4px solid {color_hex};
            }}
        """)

        sombra = QGraphicsDropShadowEffect(self)
        sombra.setBlurRadius(14)
        sombra.setXOffset(0)
        sombra.setYOffset(2)
        sombra.setColor(QColor(0, 0, 0, 55))
        self.setGraphicsEffect(sombra)


def _panel_categoria(categoria, indices, color_hex, on_click, con_tooltip=True):
    """Devuelve un QFrame con cabecera (icono + nombre de categoría) y una
    rejilla de _NUM_COLUMNAS columnas fijas con una tarjeta por índice,
    todo dentro de un panel con fondo tintado -- para que cada categoría
    se vea como un bloque agrupado y no como tarjetas sueltas."""
    panel = QFrame()
    panel.setStyleSheet(f"""
        QFrame {{
            background-color: {_rgba(color_hex, 16)};
            border: 1px solid {_rgba(color_hex, 55)};
            border-radius: 10px;
        }}
    """)
    layout_panel = QVBoxLayout(panel)
    layout_panel.setContentsMargins(10, 8, 10, 10)
    layout_panel.setSpacing(6)

    icono_fn = ICONO_CATEGORIA.get(categoria)
    cabecera = QHBoxLayout()
    cabecera.setSpacing(6)
    if icono_fn:
        etiqueta_icono = QLabel()
        etiqueta_icono.setPixmap(icono_fn(color_hex, 18).pixmap(QSize(18, 18)))
        cabecera.addWidget(etiqueta_icono)
    etiqueta_texto = QLabel(categoria)
    etiqueta_texto.setStyleSheet(f"color: {color_hex}; font-weight: bold; font-size: 11px;")
    cabecera.addWidget(etiqueta_texto)
    cabecera.addStretch()
    layout_panel.addLayout(cabecera)

    rejilla = QGridLayout()
    rejilla.setSpacing(8)
    for columna in range(_NUM_COLUMNAS + 1):
        rejilla.setColumnStretch(columna, 1 if columna == _NUM_COLUMNAS else 0)

    icono_indice = icono_fn(color_hex) if icono_fn else None
    for posicion, indice in enumerate(indices):
        tooltip = ""
        if con_tooltip:
            meta = INDICE_FORMULAS.get(indice, {})
            if meta:
                tooltip = (f"{meta.get('descripcion', '')}\n"
                           f"Fórmula: {meta.get('formula_legible', '')}\n"
                           f"Rango: {meta.get('rango', '')}")
        tarjeta = TarjetaIndice(indice, color_hex, tooltip, icono=icono_indice)
        tarjeta.clicked.connect(partial(on_click, indice))
        rejilla.addWidget(tarjeta, posicion // _NUM_COLUMNAS, posicion % _NUM_COLUMNAS)
    layout_panel.addLayout(rejilla)

    return panel


def _paneles_por_categoria(layout, on_click, con_tooltip=True):
    """Añade a `layout` un panel por cada categoría de CATEGORIAS_INDICES."""
    for categoria, indices in CATEGORIAS_INDICES.items():
        color = COLOR_CATEGORIA.get(categoria, "#616161")
        layout.addWidget(_panel_categoria(categoria, indices, color, on_click, con_tooltip))


def _linea_separadora():
    linea = QFrame()
    linea.setFrameShape(QFrame.Shape.HLine)
    linea.setFrameShadow(QFrame.Shadow.Sunken)
    return linea


# --------------------------------------------------------------------------
# Diálogos
# --------------------------------------------------------------------------

class GaleriaAccionesDialog(QDialog):
    """Primera pantalla al pinchar el botón Copernicus: elegir entre
    Firma espectral, Ver imagen, o directamente un índice histórico."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Copernicus — Sentinel-2")
        self.resultado = None  # ("firma", None) | ("ver_imagen", None) | ("indice", nombre)

        layout = QVBoxLayout(self)
        layout.setSpacing(8)

        layout.addWidget(QLabel("<b>¿Qué quieres consultar?</b>"))

        fila_acciones = QHBoxLayout()
        fila_acciones.setSpacing(10)

        tarjeta_firma = TarjetaIndice(
            "Firma\nespectral", COLOR_ACCION,
            "Reflectancia de todas las bandas para una fecha aproximada — "
            "busca la adquisición real más despejada de nubes cerca de esa fecha.",
            icono=_icono_grafica(COLOR_ACCION, 32), ancho=112, alto=88, icono_size=32)
        tarjeta_firma.clicked.connect(lambda: self._elegir(("firma", None)))
        fila_acciones.addWidget(tarjeta_firma)

        tarjeta_imagen = TarjetaIndice(
            "Ver\nimagen", COLOR_ACCION,
            "Descarga y carga una imagen Sentinel-2 (color real, falso color "
            "o un índice) de un punto o de un área dibujada.",
            icono=_icono_foto(COLOR_ACCION, 32), ancho=112, alto=88, icono_size=32)
        tarjeta_imagen.clicked.connect(lambda: self._elegir(("ver_imagen", None)))
        fila_acciones.addWidget(tarjeta_imagen)
        fila_acciones.addStretch()
        layout.addLayout(fila_acciones)

        layout.addWidget(_linea_separadora())
        layout.addWidget(QLabel("<b>Índice histórico</b> — elige un índice:"))

        _paneles_por_categoria(layout, lambda indice: self._elegir(("indice", indice)))

        botones = QDialogButtonBox(QDialogButtonBox.StandardButton.Cancel)
        botones.rejected.connect(self.reject)
        layout.addWidget(botones)

    def _elegir(self, resultado):
        self.resultado = resultado
        self.accept()


class GaleriaPuntoAreaDialog(QDialog):
    """Segunda pantalla de "Ver imagen": punto o área dibujada."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Ver imagen — ubicación")
        self.resultado = None  # "punto" | "area"

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("<b>¿Punto o área?</b>"))

        fila = QHBoxLayout()
        fila.setSpacing(10)

        t_punto = TarjetaIndice(
            "Punto\n(2×2 km)", COLOR_ACCION,
            "Clic en el mapa: descarga un recorte de 2×2 km centrado en ese punto.",
            icono=_icono_foto(COLOR_ACCION, 30), ancho=104, alto=84)
        t_punto.clicked.connect(lambda: self._elegir("punto"))
        fila.addWidget(t_punto)

        t_area = TarjetaIndice(
            "Dibujar\nárea", COLOR_ACCION,
            f"Dibuja un polígono (máx. {VER_IMAGEN_MAX_AREA_KM2} km²) y descarga esa zona.",
            icono=_icono_foto(COLOR_ACCION, 30), ancho=104, alto=84)
        t_area.clicked.connect(lambda: self._elegir("area"))
        fila.addWidget(t_area)
        fila.addStretch()
        layout.addLayout(fila)

        botones = QDialogButtonBox(QDialogButtonBox.StandardButton.Cancel)
        botones.rejected.connect(self.reject)
        layout.addWidget(botones)

    def _elegir(self, resultado):
        self.resultado = resultado
        self.accept()


class GaleriaEstiloDialog(QDialog):
    """Tercera pantalla de "Ver imagen": estilo RGB o índice a visualizar."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Ver imagen — estilo")
        self.resultado = None  # nombre del estilo elegido (RGB o índice)

        layout = QVBoxLayout(self)
        layout.setSpacing(8)
        layout.addWidget(QLabel("<b>Estilo de la imagen</b>"))

        fila_rgb = QHBoxLayout()
        fila_rgb.setSpacing(10)
        for estilo in ESTILOS_RGB:
            tarjeta = TarjetaIndice(_ajustar_texto(estilo), COLOR_ESTILO_RGB,
                                    icono=_icono_foto(COLOR_ESTILO_RGB, 26))
            tarjeta.clicked.connect(partial(self._elegir, estilo))
            fila_rgb.addWidget(tarjeta)
        fila_rgb.addStretch()
        layout.addLayout(fila_rgb)

        layout.addWidget(_linea_separadora())

        _paneles_por_categoria(layout, self._elegir, con_tooltip=True)

        botones = QDialogButtonBox(QDialogButtonBox.StandardButton.Cancel)
        botones.rejected.connect(self.reject)
        layout.addWidget(botones)

    def _elegir(self, estilo):
        self.resultado = estilo
        self.accept()
