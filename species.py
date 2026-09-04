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
"""

import json
import os
import tempfile
import webbrowser
import random

# --- IMPORTACIONES LIMPIAS Y EXPLÍCITAS ---
from qgis.PyQt.QtWidgets import (QLabel, QDialog, QVBoxLayout, QScrollArea,
                                 QWidget, QGridLayout, QFrame, QPushButton,
                                 QLineEdit, QHBoxLayout, QTableWidget,
                                 QHeaderView, QAbstractItemView, QTableWidgetItem)
from qgis.PyQt.QtCore import Qt, QUrl, QUrlQuery
from qgis.PyQt import QtNetwork
from qgis.PyQt.QtGui import QColor, QPixmap

from qgis.core import (QgsNetworkAccessManager, QgsApplication, QgsProject,
                       QgsVectorLayer, QgsFillSymbol, QgsSingleSymbolRenderer,
                       QgsCoordinateTransform)

# URL OFICIAL DE DISTRIBUCION
from .config import API_DISTRIBUCION, API_CATALOGO


class ImageLoader(QLabel):
    """Widget personalizado que carga una imagen desde una URL de forma asíncrona."""

    def __init__(self, url, parent=None):
        super().__init__(parent)
        self.setFixedSize(250, 180)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setText("Cargando...")
        self.setStyleSheet("border: 1px solid #ccc; background: #f9f9f9;")

        self.manager = QgsNetworkAccessManager.instance()
        self.reply = self.manager.get(QtNetwork.QNetworkRequest(QUrl(url)))
        self.reply.finished.connect(self._on_finished)

    def _on_finished(self):
        if self.reply.error() == QtNetwork.QNetworkReply.NetworkError.NoError:
            data = self.reply.readAll()
            pixmap = QPixmap()
            pixmap.loadFromData(data)
            if not pixmap.isNull():
                self.setPixmap(pixmap.scaled(self.width(), self.height(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
                self.setText("")
            else:
                self.setText("Error formato")
        else:
            self.setText("Sin imagen")
        self.reply.deleteLater()


class PhotoGalleryDialog(QDialog):
    """Ventana emergente para visualizar la galería de imágenes de la especie."""

    def __init__(self, name, images, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Galería: {name}")
        self.resize(600, 700)
        layout = QVBoxLayout(self)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        container = QWidget()
        self.grid = QGridLayout(container)
        scroll.setWidget(container)
        layout.addWidget(scroll)

        # Ordenar: es_prioridad: 1 primero
        images.sort(key=lambda x: x.get('es_prioridad', 0), reverse=True)

        for index, img_data in enumerate(images):
            ruta = img_data.get('ruta_foto', '')
            if not ruta:
                continue

            url = f"https://{ruta}" if not ruta.startswith('http') else ruta

            frame = QFrame()
            frame.setFrameStyle(QFrame.Shape.StyledPanel)
            frame_layout = QVBoxLayout(frame)

            # --- Visualización de la foto ---
            img_widget = ImageLoader(url)
            frame_layout.addWidget(img_widget)

            btn_ver = QPushButton("Ver original / Descargar")
            btn_ver.clicked.connect(lambda checked, u=url: webbrowser.open(u))

            frame_layout.addWidget(btn_ver)

            self.grid.addWidget(frame, index // 2, index % 2)


class SpeciesTab(QWidget):
    def __init__(self, iface):
        super().__init__()
        self.iface = iface
        self.network_manager = QgsNetworkAccessManager.instance()

        layout = QVBoxLayout(self)

        # --- FILA 1: BUSCADOR ---
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Nombre común, científico o Taxón_ID...")
        self.search_input.returnPressed.connect(self.search)

        self.btn_search = QPushButton("Buscar")
        self.btn_search.setIcon(QgsApplication.getThemeIcon('/mActionSearch.svg'))
        self.btn_search.clicked.connect(self.search)
        self.btn_search.setStyleSheet("background-color: #2b8cbe; color: white; font-weight: bold;")

        search_layout.addWidget(self.search_input)
        search_layout.addWidget(self.btn_search)

        # Añadimos la fila del buscador al layout principal
        layout.addLayout(search_layout)

        # --- DISCLAIMER DE TILDES (Cambiado a 'layout' para que vaya debajo) ---
        self.disclaimer_lbl = QLabel(
            "💡 <b>Nota:</b> El catálogo es sensible a la ortografía. Asegúrese de incluir las tildes correspondientes para una búsqueda exacta.")
        self.disclaimer_lbl.setStyleSheet("color: #5d6d7e; font-size: 10px; font-style: italic; margin-top: 2px;")
        self.disclaimer_lbl.setWordWrap(True)

        # IMPORTANTE: Aquí usamos 'layout' en lugar de 'search_layout'
        layout.addWidget(self.disclaimer_lbl)

        # --- FILA 2: ACCIONES ---
        data_layout = QHBoxLayout()
        self.btn_clear = QPushButton("Limpiar")
        self.btn_clear.setIcon(QgsApplication.getThemeIcon('/mActionDeleteSelected.svg'))
        self.btn_clear.clicked.connect(self.clear_all)
        data_layout.addWidget(self.btn_clear)
        data_layout.addStretch()
        layout.addLayout(data_layout)

        # --- ETIQUETA DE ESTADO ---
        self.status_lbl = QLabel("Introduce un nombre/taxon ID para buscar especies... (con tíldes) ")
        self.status_lbl.setStyleSheet("font-size: 11px; color: #2c3e50; font-weight: bold;")
        layout.addWidget(self.status_lbl)

        # --- TABLA (Actualizada a 7 columnas) ---
        self.table = QTableWidget(0, 7)
        self.table.setHorizontalHeaderLabels(
            ["ID", "Científico", "Nombre Común", "Grupo", "Fotos", "Distribución", "Estado"])

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        header.setStretchLastSection(False)

        # --- AJUSTE DE ANCHOS MÁS ESTRECHOS ---
        self.table.setColumnWidth(0, 40)  # ID
        self.table.setColumnWidth(1, 80)  # Científico
        self.table.setColumnWidth(2, 85)  # Común
        self.table.setColumnWidth(3, 60)  # Grupo
        self.table.setColumnWidth(4, 50)  # Fotos
        self.table.setColumnWidth(5, 60)  # Distribución
        self.table.setColumnWidth(6, 50)  # Estado

        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.cellClicked.connect(self.on_cell_clicked)
        layout.addWidget(self.table)

    def clear_all(self):
        self.table.setRowCount(0)
        layers = QgsProject.instance().mapLayers().values()
        to_delete = [layer.id() for layer in layers if layer.name().startswith("Dist: ")]
        QgsProject.instance().removeMapLayers(to_delete)
        self.status_lbl.setText("Todo limpio.")

    def search(self):
        txt = self.search_input.text().strip()
        if not txt:
            return

        self.status_lbl.setText("🔍 Buscando...")
        url = QUrl(API_CATALOGO)
        query = QUrlQuery()

        if txt.isdigit():
            query.addQueryItem("idtaxon", f"eq.{txt}")
        else:
            query.addQueryItem("or", f'(ScientificName.ilike.*{txt}*,"Vernacular Name".ilike.*{txt}*)')
            query.addQueryItem("limit", "500")

        url.setQuery(query)
        req = QtNetwork.QNetworkRequest(url)
        reply = self.network_manager.get(req)
        reply.finished.connect(lambda: self.handle_search_response(reply))

    def handle_search_response(self, reply):
        if reply.error() != QtNetwork.QNetworkReply.NetworkError.NoError:
            self.status_lbl.setText("❌ Error de conexión.")
            reply.deleteLater()
            return
        try:
            data = json.loads(reply.readAll().data())
            reply.deleteLater()
            self.table.setRowCount(0)
            if not data:
                self.status_lbl.setText("⚠️ Sin resultados.")
                return

            # Mantener tu lógica de prioridad por grupo taxonómico
            def get_priority(item):
                g = str(item.get('Grupo taxonómico', '')).lower()
                taxo_order = ['mamífero', 'ave', 'reptil', 'pez', 'invertebrado', 'planta vascular', 'cromista',
                              'bacteria', 'ascidio', 'planta no vascular', 'alga', 'hongo']
                for i, grupo in enumerate(taxo_order):
                    if grupo in g:
                        return i
                return 99

            data.sort(key=get_priority)

            for item in data:
                row = self.table.rowCount()
                self.table.insertRow(row)
                id_t = str(item.get('idtaxon', ''))
                cien = str(item.get('ScientificName', ''))

                it_id = QTableWidgetItem(id_t)
                it_id.setForeground(Qt.GlobalColor.blue)
                it_id.setData(Qt.ItemDataRole.UserRole, id_t)
                it_id.setData(Qt.ItemDataRole.UserRole + 1, cien)
                font = it_id.font()
                font.setUnderline(True)
                it_id.setFont(font)

                self.table.setItem(row, 0, it_id)
                self.table.setItem(row, 1, QTableWidgetItem(cien))
                self.table.setItem(row, 2, QTableWidgetItem(str(item.get('Vernacular Name', '-'))))
                self.table.setItem(row, 3, QTableWidgetItem(str(item.get('Grupo taxonómico', '-'))))

                # --- COLUMNA 4: FOTOS ---
                if id_t and id_t != 'None':
                    btn_photo = QPushButton("📷 Fotos")
                    btn_photo.setStyleSheet("background-color: #fff7ed; font-size: 9px; font-weight: bold;")
                    btn_photo.clicked.connect(lambda checked, i=id_t, n=cien: self.fetch_photos(i, n))
                    self.table.setCellWidget(row, 4, btn_photo)

                # --- COLUMNA 5: DISTRIBUCIÓN ---
                if id_t and id_t != 'None':
                    btn_map = QPushButton("🌍 Añadir")
                    btn_map.setStyleSheet("font-size: 9px; font-weight: bold;")
                    btn_map.clicked.connect(lambda checked, i=id_t, n=cien: self.load_dist(i, n))
                    self.table.setCellWidget(row, 5, btn_map)

                # --- COLUMNA 6: ESTADO ---
                it_estado = QTableWidgetItem("Consultar 🔍")
                it_estado.setForeground(QColor("#00838f"))
                self.table.setItem(row, 6, it_estado)

            self.status_lbl.setText(f"✅ Encontrados {len(data)} resultados.")
        except Exception as e:
            from qgis.core import QgsMessageLog, Qgis
            QgsMessageLog.logMessage(f"Error procesando resultados de búsqueda de especies: {e}",
                                      "IEPNB Tools", Qgis.MessageLevel.Warning)
            self.status_lbl.setText("❌ Error al procesar los resultados.")

    def on_cell_clicked(self, row, col):
        if col == 0:
            it = self.table.item(row, 0)
            id_t = it.data(Qt.ItemDataRole.UserRole)
            cien = it.data(Qt.ItemDataRole.UserRole + 1)
            clean_name = "-".join(cien.lower().split()[:2])
            webbrowser.open(f"https://iepnb.gob.es/areas-tematicas/especies-silvestres/eidos/{id_t}/{clean_name}")
        elif col == 6:  # <-- AHORA LA COLUMNA 6 ES "ESTADO"
            it_id = self.table.item(row, 0)
            id_taxon = it_id.data(Qt.ItemDataRole.UserRole)
            item_res = self.table.item(row, 6)

            if "Consultar" not in item_res.text():
                return

            item_res.setText("...")
            url = QUrl("https://iepnb.gob.es/api/catalogo/v_listapatronespecie_normas")
            q = QUrlQuery()
            q.addQueryItem("idtaxon", f"eq.{id_taxon}")
            url.setQuery(q)
            reply = self.network_manager.get(QtNetwork.QNetworkRequest(url))
            reply.finished.connect(lambda: self.handle_legal_response(reply, row))

    def handle_legal_response(self, reply, row):
        try:
            data = json.loads(reply.readAll().data())
            reply.deleteLater()
            it = self.table.item(row, 6)  # <-- AHORA ACTUALIZA LA COLUMNA 6
            if not data:
                it.setText("Sin protección")
                it.setForeground(Qt.GlobalColor.gray)
            else:
                it.setText(str(data[0].get('categoria', 'Protegido')))
                it.setForeground(Qt.GlobalColor.red)
        except Exception as e:
            from qgis.core import QgsMessageLog, Qgis
            QgsMessageLog.logMessage(f"Error consultando protección legal del taxón: {e}",
                                      "IEPNB Tools", Qgis.MessageLevel.Warning)

    def fetch_photos(self, id_t, name):
        url = QUrl("https://iepnb.gob.es/api/especie/v_imagenes")
        q = QUrlQuery()
        q.addQueryItem("id_taxon", f"eq.{id_t}")
        url.setQuery(q)
        reply = self.network_manager.get(QtNetwork.QNetworkRequest(url))
        reply.finished.connect(lambda: self.handle_photos_response(reply, name))

    def handle_photos_response(self, reply, name):
        try:
            data = json.loads(reply.readAll().data())
            reply.deleteLater()
            if not data:
                self.iface.messageBar().pushMessage("Info", "No hay fotos.", level=1)
                return
            self.gallery = PhotoGalleryDialog(name, data, self)
            self.gallery.show()
        except Exception as e:
            from qgis.core import QgsMessageLog, Qgis
            QgsMessageLog.logMessage(f"Error mostrando la galería de fotos: {e}",
                                      "IEPNB Tools", Qgis.MessageLevel.Warning)

    def load_dist(self, id_t, name):
        url = QUrl(API_DISTRIBUCION)
        q = QUrlQuery()
        q.addQueryItem("idtaxon", f"eq.{id_t}")
        url.setQuery(q)
        reply = self.network_manager.get(QtNetwork.QNetworkRequest(url))
        reply.finished.connect(lambda: self.process_dist_map(reply, name))

    def process_dist_map(self, reply, name):
        try:
            data = json.loads(reply.readAll().data())
            reply.deleteLater()
            if not data:
                self.iface.messageBar().pushMessage("Info", f"No hay datos de distribución para {name}.", level=1)
                return
            features = []
            for i in data:
                if not i.get("geom"):
                    continue
                geom = json.loads(i["geom"]) if isinstance(i["geom"], str) else i["geom"]
                features.append({"type": "Feature", "geometry": geom.get("geometry", geom), "properties": i})
            tmp = os.path.join(tempfile.gettempdir(), f"sp_{id(features)}.geojson")
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump({"type": "FeatureCollection", "features": features}, f)
            vlayer = QgsVectorLayer(tmp, f"Dist: {name}", "ogr")
            if vlayer.isValid():
                # SystemRandom en vez de random.randint: es solo un color de
                # relleno de capa (nada criptográfico), pero así el escáner
                # de seguridad no lo marca como generador pseudoaleatorio
                # inseguro sin necesidad de un comentario de supresión.
                col = QColor.fromHsl(random.SystemRandom().randint(0, 359), 130, 200)
                sym = QgsFillSymbol.createSimple({'color': col.name(), 'outline_color': 'gray', 'outline_width': '0.1'})
                vlayer.setRenderer(QgsSingleSymbolRenderer(sym))
                vlayer.setOpacity(0.75)
                QgsProject.instance().addMapLayer(vlayer)
                canvas = self.iface.mapCanvas()
                transform = QgsCoordinateTransform(vlayer.crs(), canvas.mapSettings().destinationCrs(),
                                                   QgsProject.instance())
                canvas.setExtent(transform.transformBoundingBox(vlayer.extent()))
                canvas.refresh()
        except Exception as e:
            from qgis.core import QgsMessageLog, Qgis
            QgsMessageLog.logMessage(f"Error añadiendo la capa de distribución de {name}: {e}",
                                      "IEPNB Tools", Qgis.MessageLevel.Warning)
