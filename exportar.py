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

Exportación de las gráficas de Copernicus (Índice Histórico y Firma
Espectral): imagen (PNG, JPG, SVG o PDF) y datos en CSV. Lo comparten los
dos diálogos para que el botón y el comportamiento sean idénticos.
"""

import csv
import os
from datetime import datetime

from qgis.PyQt.QtWidgets import QFileDialog, QMenu, QMessageBox, QPushButton

_FILTROS_IMAGEN = {
    "PNG (*.png)": ".png",
    "JPG (*.jpg)": ".jpg",
    "SVG (*.svg)": ".svg",
    "PDF (*.pdf)": ".pdf",
}
_EXTENSIONES_IMAGEN = {".png", ".jpg", ".jpeg", ".svg", ".pdf"}

_FILTRO_CSV_ES = "CSV para Excel (separador ';' y coma decimal) (*.csv)"
_FILTRO_CSV_STD = "CSV estándar (separador ',' y punto decimal) (*.csv)"


def _carpeta_inicial():
    escritorio = os.path.join(os.path.expanduser("~"), "Desktop")
    return escritorio if os.path.isdir(escritorio) else os.path.expanduser("~")


def _nombre_seguro(nombre):
    """Quita caracteres que dan problemas en nombres de archivo."""
    return "".join(c if c.isalnum() or c in "-_." else "_" for c in nombre)


def crear_boton_exportar(parent, al_exportar_imagen, al_exportar_csv):
    """Botón 'Exportar' con un menú: gráfica como imagen / datos como CSV."""
    boton = QPushButton("Exportar")
    boton.setStyleSheet("QPushButton { padding: 5px 18px; border-radius: 4px; }")
    boton.setToolTip("Guarda la gráfica como imagen o los datos que muestra como CSV")
    menu = QMenu(boton)
    menu.addAction("Gráfica como imagen…").triggered.connect(al_exportar_imagen)
    menu.addAction("Datos como CSV…").triggered.connect(al_exportar_csv)
    boton.setMenu(menu)
    return boton


def exportar_figura(parent, fig, nombre_base, artistas_ocultos=()):
    """Pide una ruta y guarda la figura de matplotlib tal y como se ve
    (periodo y zoom actuales). Añade la atribución de Copernicus, que la
    Legal Notice exige al redistribuir. Devuelve la ruta o None."""
    filtros = ";;".join(_FILTROS_IMAGEN)
    ruta, filtro = QFileDialog.getSaveFileName(
        parent, "Exportar gráfica como imagen",
        os.path.join(_carpeta_inicial(), _nombre_seguro(nombre_base) + ".png"), filtros)
    if not ruta:
        return None

    if os.path.splitext(ruta)[1].lower() not in _EXTENSIONES_IMAGEN:
        ruta += _FILTROS_IMAGEN.get(filtro, ".png")

    # El marcador del ratón no debe salir en la imagen
    estados = [(a, a.get_visible()) for a in artistas_ocultos if a is not None]
    for artista, _ in estados:
        artista.set_visible(False)
    atribucion = fig.text(
        0.995, 0.004, f"Copernicus Sentinel data {datetime.now().year} · IEPNB Tools",
        ha="right", va="bottom", fontsize=7, color="#888")
    try:
        fig.savefig(ruta, dpi=200, facecolor="white", bbox_inches="tight", pad_inches=0.2)
    except Exception as exc:
        QMessageBox.warning(parent, "Exportar gráfica", f"No se pudo guardar la imagen:\n{exc}")
        return None
    finally:
        atribucion.remove()
        for artista, visible in estados:
            artista.set_visible(visible)
        fig.canvas.draw_idle()

    QMessageBox.information(parent, "Exportar gráfica", f"Gráfica guardada en:\n{ruta}")
    return ruta


def _formatear(valor, decimal_coma):
    if valor is None:
        return ""
    texto = f"{valor:.5f}"
    return texto.replace(".", ",") if decimal_coma else texto


def exportar_csv(parent, nombre_base, cabecera, filas, detalle=""):
    """Pide una ruta y escribe un CSV. 'filas' es una lista de listas donde
    los float se formatean con 5 decimales (y None queda vacío). El filtro
    elegido en el diálogo decide el formato: Excel en español (';' y coma
    decimal, como el resto de exportaciones del plugin) o estándar."""
    ruta, filtro = QFileDialog.getSaveFileName(
        parent, "Exportar datos como CSV",
        os.path.join(_carpeta_inicial(), _nombre_seguro(nombre_base) + ".csv"),
        f"{_FILTRO_CSV_ES};;{_FILTRO_CSV_STD}")
    if not ruta:
        return None
    if not ruta.lower().endswith(".csv"):
        ruta += ".csv"

    estandar = filtro == _FILTRO_CSV_STD
    separador = "," if estandar else ";"
    try:
        with open(ruta, "w", newline="", encoding="utf-8-sig") as f:
            escritor = csv.writer(f, delimiter=separador)
            escritor.writerow(cabecera)
            for fila in filas:
                escritor.writerow([
                    _formatear(v, not estandar) if isinstance(v, float) or v is None else v
                    for v in fila])
    except OSError as exc:
        QMessageBox.warning(
            parent, "Exportar datos",
            f"No se pudo guardar el CSV (¿está abierto en otro programa?):\n{exc}")
        return None

    QMessageBox.information(
        parent, "Exportar datos",
        f"{len(filas)} filas guardadas en:\n{ruta}" + (f"\n\n{detalle}" if detalle else ""))
    return ruta
