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
import csv
import tempfile
import unicodedata

# --- IMPORTACIONES LIMPIAS Y EXPLÍCITAS ---
from qgis.PyQt.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
                                 QGridLayout, QLabel, QComboBox, QLineEdit,
                                 QPushButton, QTableWidget, QHeaderView,
                                 QTableWidgetItem, QApplication, QFileDialog)
from qgis.PyQt.QtCore import Qt, QUrl, QUrlQuery
from qgis.PyQt import QtNetwork
from qgis.PyQt.QtGui import QBrush

from qgis.core import (QgsNetworkAccessManager, QgsApplication, QgsProject,
                       QgsVectorLayer, QgsWkbTypes, QgsFillSymbol, QgsLineSymbol,
                       QgsMarkerSymbol, QgsSingleSymbolRenderer, QgsCoordinateTransform)

from .config import CONFIG_TERRITORY as CONFIG_SERVICIOS


class TerritoryTab(QWidget):
    def __init__(self, iface):
        super().__init__()
        self.iface = iface
        self.group_name = "Consultas IEPNB"
        self.network_manager = QgsNetworkAccessManager.instance()
        self.current_services = []
        self.all_results = []

        # Mapeo de campos para Nombre y Figura/Info
        self.FIELD_MAP = {
            "ENP": {"fig": "figura", "nom": "nombre"},
            "RN2000": {"fig": "desc_figura", "nom": "nombre"},
            "IBAs": {"fig": None, "nom": "nombre"},
            "MUP": {"fig": "nombre_propiedad", "nom": "monte"},
            "VP": {"fig": "nb_tipo_vp", "nom": "nb_via"},
            "Áreas Marinas": {"fig": "tipo", "nom": "site_name"},
            "Reservas de la Biosfera": {"fig": None, "nom": "nombre"},
            "OSPAR": {"fig": None, "nom": "nombre"},
            "RAMSAR": {"fig": None, "nom": "nombre"},
            "ZEPIM": {"fig": None, "nom": "nombre"},
            "Geoparque": {"fig": None, "nom": "nombre"},
        }

        layout = QVBoxLayout(self)

        # --- PANEL DE BÚSQUEDA ---
        search_group = QGroupBox("Buscador Territorial")
        grid = QGridLayout()

        grid.addWidget(QLabel("Capa:"), 0, 0)
        self.combo_capas = QComboBox()
        self.combo_capas.addItem("Todas las capas")
        for srv in CONFIG_SERVICIOS:
            if srv["id"] == "Riqueza de especies":
                continue
            self.combo_capas.addItem(srv["id"])
        grid.addWidget(self.combo_capas, 0, 1)

        grid.addWidget(QLabel("Nombre:"), 1, 0)
        self.search_nom = QLineEdit()
        self.search_nom.setPlaceholderText("Ej: Doñana, Laguna, Almonte...")
        self.search_nom.returnPressed.connect(self.start_search)
        grid.addWidget(self.search_nom, 1, 1)

        grid.addWidget(QLabel("Tipo/Info:"), 2, 0)
        self.search_inf = QLineEdit()
        self.search_inf.setPlaceholderText("Ej: Parque Natural, ZEPA, Monumento...")
        self.search_inf.returnPressed.connect(self.start_search)
        grid.addWidget(self.search_inf, 2, 1)

        self.btn_search = QPushButton(" Ejecutar Búsqueda")
        self.btn_search.setIcon(QgsApplication.getThemeIcon('/mActionSearch.svg'))
        self.btn_search.clicked.connect(self.start_search)
        self.btn_search.setStyleSheet("background-color: #2b8cbe; color: white; font-weight: bold; padding: 5px;")
        grid.addWidget(self.btn_search, 3, 0, 1, 2)

        search_group.setLayout(grid)
        layout.addWidget(search_group)

        # --- ACCIONES RÁPIDAS ---
        actions_layout = QHBoxLayout()
        self.btn_add_all = QPushButton("Añadir todas")
        self.btn_add_all.setIcon(QgsApplication.getThemeIcon('/mActionAddAllToView.svg'))
        self.btn_add_all.clicked.connect(self.add_all_to_map)
        self.btn_add_all.setStyleSheet("font-weight: bold; color: #1e8449;")
        self.btn_add_all.setEnabled(False)

        self.btn_clear = QPushButton("Limpiar")
        self.btn_clear.setIcon(QgsApplication.getThemeIcon('/mActionDeleteSelected.svg'))
        self.btn_clear.clicked.connect(self.clear_all)

        self.btn_export = QPushButton("CSV")
        self.btn_export.setIcon(QgsApplication.getThemeIcon('/mActionFileSaveAs.svg'))
        self.btn_export.clicked.connect(self.export_table)

        actions_layout.addWidget(self.btn_add_all)
        actions_layout.addWidget(self.btn_clear)
        actions_layout.addWidget(self.btn_export)
        actions_layout.addStretch()
        layout.addLayout(actions_layout)

        self.status_lbl = QLabel("Indica un nombre o tipo para buscar.")
        self.status_lbl.setStyleSheet("color: #2c3e50; font-style: italic;")
        layout.addWidget(self.status_lbl)

        # --- TABLA ---
        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["Capa", "Nombre", "Información", "Acción"])
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.setAlternatingRowColors(True)
        layout.addWidget(self.table)

    def normalize(self, t):
        if not t:
            return ""
        return ''.join(c for c in unicodedata.normalize('NFD', str(t)) if unicodedata.category(c) != 'Mn').lower()

    def clear_all(self):
        self.table.setRowCount(0)
        self.all_results = []
        self.btn_add_all.setEnabled(False)
        root = QgsProject.instance().layerTreeRoot()
        group = root.findGroup(self.group_name)
        if group:
            for l_node in group.children():
                QgsProject.instance().removeMapLayer(l_node.layerId())
            root.removeChildNode(group)
        self.status_lbl.setText("Vista limpia.")

    def start_search(self):
        nom = self.search_nom.text().strip()
        inf = self.search_inf.text().strip()

        if len(nom) < 3 and len(inf) < 3:
            self.status_lbl.setText("⚠️ Escribe al menos 3 letras.")
            return

        seleccion = self.combo_capas.currentText()
        if seleccion == "Todas las capas":
            self.current_services = [s for s in CONFIG_SERVICIOS if s["id"] != "Riqueza de especies"]
        else:
            self.current_services = [s for s in CONFIG_SERVICIOS if s["id"] == seleccion]

        self.table.setRowCount(0)
        self.all_results = []
        self.btn_add_all.setEnabled(False)
        self.iface.mainWindow().setCursor(Qt.CursorShape.WaitCursor)
        self.query_next_service(0, nom, inf)

    def query_next_service(self, index, nom_orig, inf_orig):
        if index >= len(self.current_services):
            self.iface.mainWindow().setCursor(Qt.CursorShape.ArrowCursor)
            num = self.table.rowCount()
            self.status_lbl.setText(f"✅ Finalizado. {num} resultados.")
            if num > 0:
                self.btn_add_all.setEnabled(True)
            return

        srv = self.current_services[index]
        self.status_lbl.setText(f"🔎 Consultando {srv['id']}...")
        QApplication.processEvents()

        # --- Identificar columnas de búsqueda ---
        col_busqueda_inf = srv.get('col_inf')
        if srv["id"] == "Municipio":
            col_busqueda_inf = "nut3_nom"
        elif srv["id"] in ["Provincia", "CCAA"]:
            col_busqueda_inf = "nut2_nom"
        elif srv["id"] in self.FIELD_MAP and self.FIELD_MAP[srv["id"]]["fig"]:
            col_busqueda_inf = self.FIELD_MAP[srv["id"]]["fig"]

        col_busqueda_nom = srv.get("col_nom")
        if srv["id"] in self.FIELD_MAP:
            col_busqueda_nom = self.FIELD_MAP[srv["id"]]["nom"]

        # --- 1. CONSTRUCCIÓN DE LOS FILTROS DE TEXTO (COMÚN PARA TODOS) ---
        filtros = []
        if len(nom_orig) >= 3:
            w_nom = nom_orig
            for v in 'aáeéiíoóuúüAÁEÉIÍOÓUÚÜ':
                w_nom = w_nom.replace(v, '_')
            filtros.append(f"{col_busqueda_nom} ILIKE '%{w_nom}%'")

        if len(inf_orig) >= 3 and col_busqueda_inf:
            w_inf = inf_orig
            for v in 'aáeéiíoóuúüAÁEÉIÍOÓUÚÜ':
                w_inf = w_inf.replace(v, '_')
            filtros.append(f"{col_busqueda_inf} ILIKE '%{w_inf}%'")

        cql = " AND ".join(filtros)

        # --- 2. CONSTRUCCIÓN DE LA URL SEGÚN TIPO DE SERVICIO ---
        url = QUrl()
        q = QUrlQuery()

        if srv.get("type") == "OAPIF":
            # OGC API Features (MAPAMA)
            url = QUrl(f"{srv['url']}/items")
            q.addQueryItem("f", "json")

            if cql:
                # Enviamos el filtro al servidor para no descargar toda España
                q.addQueryItem("filter", cql)
                q.addQueryItem("filter-lang", "cql-text")
            else:
                # Límite de seguridad por si hacen una búsqueda vacía
                q.addQueryItem("limit", "50")

        else:
            # WFS Tradicional (Tus Geoservers)
            url = QUrl(srv["url"])
            q.addQueryItem("service", "WFS")
            q.addQueryItem("version", "1.0.0")
            q.addQueryItem("request", "GetFeature")

            layer_name = srv.get("layer")
            if layer_name:
                q.addQueryItem("typeName", layer_name)

            q.addQueryItem("outputFormat", "application/json")
            q.addQueryItem("srsName", "EPSG:4326")

            if cql:
                q.addQueryItem("cql_filter", cql)

        url.setQuery(q)

        reply = self.network_manager.get(QtNetwork.QNetworkRequest(url))
        reply.finished.connect(lambda: self.process_response(reply, index, nom_orig, inf_orig))

    def process_response(self, reply, index, nom_orig, inf_orig):
        try:
            if reply.error() == QtNetwork.QNetworkReply.NetworkError.NoError:
                srv = self.current_services[index]
                data = json.loads(reply.readAll().data())
                nom_clean = self.normalize(nom_orig)
                inf_clean = self.normalize(inf_orig)

                grupos = {}
                for f in data.get("features", []):
                    props = f["properties"]

                    # Obtener Nombre
                    f_nom_key = srv["col_nom"]
                    if srv["id"] in self.FIELD_MAP:
                        f_nom_key = self.FIELD_MAP[srv["id"]]["nom"]
                    val_nom = props.get(f_nom_key) or "S/N"

                    # Obtener Información
                    val_inf = "-"
                    if srv["id"] == "Municipio":
                        val_inf = props.get("nut3_nom") or "-"
                    elif srv["id"] in ["Provincia", "CCAA"]:
                        val_inf = props.get("nut2_nom") or "-"
                    elif srv["id"] in self.FIELD_MAP and self.FIELD_MAP[srv["id"]]["fig"]:
                        val_inf = props.get(self.FIELD_MAP[srv["id"]]["fig"]) or "-"
                    else:
                        val_inf = props.get(srv["col_inf"]) or "-"

                    # Refinado final local para asegurar tildes y normalización
                    if (nom_clean in self.normalize(val_nom)) and (inf_clean in self.normalize(val_inf)):
                        clave = (srv["id"], val_nom, val_inf)
                        if clave not in grupos:
                            grupos[clave] = []
                        grupos[clave].append(f)

                for (cap_id, v_nom, v_inf), features in grupos.items():
                    self.all_results.append({
                        'features': features, 'cap': cap_id,
                        'nom': v_nom, 'inf': v_inf, 'col': srv["color"]
                    })
                    self.add_row(cap_id, v_nom, v_inf, features, srv["color"])
        except Exception as e:
            from qgis.core import QgsMessageLog, Qgis
            QgsMessageLog.logMessage(f"Error procesando respuesta de búsqueda territorial (servicio índice {index}): {e}",
                                      "IEPNB Tools", Qgis.MessageLevel.Warning)
        finally:
            reply.deleteLater()
            self.query_next_service(index + 1, nom_orig, inf_orig)

    def add_row(self, cap, nom, info, lista_features, col):
        row = self.table.rowCount()
        self.table.insertRow(row)
        it_cap = QTableWidgetItem(str(cap))
        it_cap.setForeground(QBrush(col.darker(150)))
        self.table.setItem(row, 0, it_cap)
        self.table.setItem(row, 1, QTableWidgetItem(str(nom)))
        self.table.setItem(row, 2, QTableWidgetItem(str(info)))
        btn = QPushButton("Añadir")
        btn.clicked.connect(lambda: self.load_to_map(lista_features, cap, nom, col))
        self.table.setCellWidget(row, 3, btn)

    def load_to_map(self, lista_features, cap, name, col, do_zoom=True):
        try:
            tmp_path = os.path.join(tempfile.gettempdir(), f"terr_{id(lista_features)}.geojson")
            with open(tmp_path, "w", encoding="utf-8") as f:
                json.dump({"type": "FeatureCollection", "features": lista_features}, f)

            vlayer = QgsVectorLayer(tmp_path, f"{cap}: {name}", "ogr")
            if vlayer.isValid():
                geom_type = vlayer.geometryType()
                if geom_type == QgsWkbTypes.GeometryType.PolygonGeometry:
                    sym = QgsFillSymbol.createSimple(
                        {'color': col.name(), 'outline_color': 'black', 'outline_width': '0.1'})
                elif geom_type == QgsWkbTypes.GeometryType.LineGeometry:
                    sym = QgsLineSymbol.createSimple({'line_color': col.name(), 'line_width': '0.6'})
                else:
                    sym = QgsMarkerSymbol.createSimple({'color': col.name(), 'size': '2'})

                vlayer.setRenderer(QgsSingleSymbolRenderer(sym))
                vlayer.setOpacity(0.6)

                root = QgsProject.instance().layerTreeRoot()
                group = root.findGroup(self.group_name) or root.insertGroup(0, self.group_name)
                QgsProject.instance().addMapLayer(vlayer, False)
                group.addLayer(vlayer)

                if do_zoom:
                    canvas = self.iface.mapCanvas()
                    xform = QgsCoordinateTransform(vlayer.crs(), canvas.mapSettings().destinationCrs(),
                                                   QgsProject.instance())
                    rect = xform.transformBoundingBox(vlayer.extent())
                    rect.scale(1.2)
                    canvas.setExtent(rect)
                    canvas.refresh()
                return vlayer
        except Exception:
            return None

    def add_all_to_map(self):
        if not self.all_results:
            return

        self.iface.mainWindow().setCursor(Qt.CursorShape.WaitCursor)

        # 1. AGRUPAR RESULTADOS POR CAPA
        grupos_por_capa = {}
        for res in self.all_results:
            cap = res['cap']
            if cap not in grupos_por_capa:
                # Inicializamos el grupo para esta capa
                grupos_por_capa[cap] = {
                    'features': [],
                    'col': res['col']  # Mantenemos el color asignado a la capa
                }
            # Añadimos las geometrías a la lista agrupada
            grupos_por_capa[cap]['features'].extend(res['features'])

        total_rect = None
        canvas = self.iface.mapCanvas()
        dest_crs = canvas.mapSettings().destinationCrs()

        # 2. CARGAR CADA GRUPO COMO UNA ÚNICA CAPA EN QGIS
        for cap, data in grupos_por_capa.items():
            # Pasamos "Resultados Agrupados" como nombre genérico
            lyr = self.load_to_map(data['features'], cap, "Resultados Agrupados", data['col'], do_zoom=False)

            # Calcular la extensión total para hacer zoom al final
            if lyr:
                xform = QgsCoordinateTransform(lyr.crs(), dest_crs, QgsProject.instance())
                rect = xform.transformBoundingBox(lyr.extent())
                if total_rect is None:
                    total_rect = rect
                else:
                    total_rect.combineExtentWith(rect)

        # 3. HACER ZOOM A LA EXTENSIÓN DE TODAS LAS CAPAS AÑADIDAS
        if total_rect:
            total_rect.scale(1.1)
            canvas.setExtent(total_rect)
            canvas.refresh()

        self.iface.mainWindow().setCursor(Qt.CursorShape.ArrowCursor)

    def export_table(self):
        path, _ = QFileDialog.getSaveFileName(self, "Exportar", "IEPNB_Resultados.csv", "CSV (*.csv)")
        if path:
            with open(path, 'w', newline='', encoding='utf-8-sig') as s:
                writer = csv.writer(s, delimiter=';')
                writer.writerow(["Capa", "Nombre", "Info"])
                for r in range(self.table.rowCount()):
                    writer.writerow(
                        [self.table.item(r, 0).text(), self.table.item(r, 1).text(), self.table.item(r, 2).text()])
