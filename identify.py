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
import uuid
import csv
import unicodedata
import datetime

# --- IMPORTACIONES LIMPIAS Y EXPLÍCITAS ---
from qgis.PyQt.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout,
                                 QPushButton, QLabel, QTableWidget,
                                 QHeaderView, QFileDialog, QMessageBox,
                                 QTableWidgetItem, QApplication, QProgressBar,
                                 QDialog, QLineEdit)
from qgis.PyQt.QtCore import Qt, QUrl, QUrlQuery, QVariant, QEventLoop, pyqtSignal
from qgis.PyQt import QtNetwork
from qgis.PyQt.QtGui import QColor, QTextDocument, QPixmap

from qgis.core import (QgsWkbTypes, QgsPointXY, QgsGeometry,
                       QgsNetworkAccessManager, QgsApplication,
                       QgsProject, QgsVectorLayer, QgsFeature,
                       QgsFillSymbol, QgsCoordinateTransform,
                       QgsCoordinateReferenceSystem, QgsDistanceArea,
                       QgsJsonUtils, QgsLineSymbol,
                       QgsSingleSymbolRenderer, QgsField)
from qgis.gui import QgsMapTool, QgsMapToolEmitPoint, QgsRubberBand

from .config import CONFIG_IDENTIFY as CONFIG_SERVICIOS, CONFIG_TERRITORY


class ManualPolygonTool(QgsMapTool):
    polygon_finished = pyqtSignal(object)

    def __init__(self, iface):
        super().__init__(iface.mapCanvas())
        self.points = []
        self.rubber = QgsRubberBand(iface.mapCanvas(), QgsWkbTypes.GeometryType.PolygonGeometry)
        self.rubber.setColor(QColor(239, 68, 68, 180))
        self.rubber.setWidth(2)

    def canvasPressEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton:
            p = self.toMapCoordinates(e.pos())
            self.points.append(QgsPointXY(p))
            if len(self.points) == 1:
                self.rubber.addPoint(p, True)
            self.rubber.addPoint(p, True)
            self.rubber.show()
        elif e.button() == Qt.MouseButton.RightButton and len(self.points) > 2:
            self.polygon_finished.emit(QgsGeometry.fromPolygonXY([self.points]))
            self.deactivate()

    def canvasMoveEvent(self, e):
        if len(self.points) > 0:
            self.rubber.movePoint(self.toMapCoordinates(e.pos()))

    def deactivate(self):
        self.points = []
        self.rubber.reset(QgsWkbTypes.GeometryType.PolygonGeometry)
        super().deactivate()


class DialogoBusquedaTTMM(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Buscar Término Municipal (TTMM)")
        self.resize(500, 400)
        self.network_manager = QgsNetworkAccessManager.instance()
        self.srv_ttmm = next((s for s in CONFIG_TERRITORY if s["id"] == "Municipio"), None)

        # NUEVO: Aquí guardaremos la geometría seleccionada en lugar de usar señales
        self.geom_seleccionada = None

        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        h_layout = QHBoxLayout()
        self.input_nom = QLineEdit()
        self.input_nom.setPlaceholderText("Ej: Almonte, Valencia, Mérida...")
        self.input_nom.returnPressed.connect(self.buscar)
        self.btn_buscar = QPushButton("Buscar")
        self.btn_buscar.setIcon(QgsApplication.getThemeIcon('/mActionSearch.svg'))
        self.btn_buscar.clicked.connect(self.buscar)
        h_layout.addWidget(QLabel("Municipio:"))
        h_layout.addWidget(self.input_nom)
        h_layout.addWidget(self.btn_buscar)
        layout.addLayout(h_layout)

        self.lbl_estado = QLabel("Escribe al menos 3 letras para buscar.")
        self.lbl_estado.setStyleSheet("color: #2c3e50; font-style: italic;")
        layout.addWidget(self.lbl_estado)

        self.tabla = QTableWidget(0, 3)
        self.tabla.setHorizontalHeaderLabels(["Municipio", "Provincia", "Acción"])
        self.tabla.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.tabla)

    def normalize(self, t):
        if not t:
            return ""
        return ''.join(c for c in unicodedata.normalize('NFD', str(t)) if unicodedata.category(c) != 'Mn').lower()

    def buscar(self):
        if not self.srv_ttmm:
            self.lbl_estado.setText("Error: No se encontró la configuración de TTMM.")
            return

        nom = self.input_nom.text().strip()
        if len(nom) < 3:
            self.lbl_estado.setText("⚠️ Escribe al menos 3 letras.")
            return

        self.tabla.setRowCount(0)
        self.lbl_estado.setText("Buscando en servidor...")

        # Bloqueamos el cursor global para que el usuario espere
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)

        w_nom = nom
        for v in 'aáeéiíoóuúüAÁEÉIÍOÓUÚÜ':
            w_nom = w_nom.replace(v, '_')

        cql = f"{self.srv_ttmm['col_nom']} ILIKE '%{w_nom}%'"

        url = QUrl(self.srv_ttmm["url"])
        q = QUrlQuery()
        q.addQueryItem("service", "WFS")
        q.addQueryItem("version", "1.0.0")
        q.addQueryItem("request", "GetFeature")
        q.addQueryItem("typeName", self.srv_ttmm["layer"])
        q.addQueryItem("outputFormat", "application/json")
        q.addQueryItem("srsName", "EPSG:4326")
        q.addQueryItem("cql_filter", cql)
        url.setQuery(q)

        # --- INICIO PETICIÓN SÍNCRONA SEgura ---
        loop = QEventLoop()
        reply = self.network_manager.get(QtNetwork.QNetworkRequest(url))
        reply.finished.connect(loop.quit)
        loop.exec()  # QGIS se pausa aquí hasta recibir la respuesta completa
        # --- FIN PETICIÓN SÍNCRONA ---

        QApplication.restoreOverrideCursor()

        if reply.error() != QtNetwork.QNetworkReply.NetworkError.NoError:
            self.lbl_estado.setText("Error de red al consultar el WFS.")
            reply.deleteLater()
            return

        try:
            raw_data = reply.readAll().data()
            if not raw_data:
                self.lbl_estado.setText("El servidor no ha devuelto datos.")
                reply.deleteLater()
                return

            data = json.loads(raw_data)
            features = data.get("features", [])

            nom_clean = self.normalize(nom)
            resultados = {}

            for f in features:
                props = f["properties"]
                val_nom = props.get(self.srv_ttmm["col_nom"], "S/N")
                val_prov = props.get("nut3_nom", "-")

                if nom_clean in self.normalize(val_nom):
                    clave = (val_nom, val_prov)
                    if clave not in resultados:
                        resultados[clave] = []
                    resultados[clave].append(f)

            if not resultados:
                self.lbl_estado.setText("No se encontraron resultados exactos.")
            else:
                self.lbl_estado.setText(f"Encontrados {len(resultados)} resultados.")
                for (n, p), feats in resultados.items():
                    self.agregar_fila(n, p, feats)

        except Exception as e:
            self.lbl_estado.setText(f"Error procesando datos: {str(e)}")
        finally:
            reply.deleteLater()

    def agregar_fila(self, nom, prov, features):
        row = self.tabla.rowCount()
        self.tabla.insertRow(row)
        self.tabla.setItem(row, 0, QTableWidgetItem(nom))
        self.tabla.setItem(row, 1, QTableWidgetItem(prov))

        btn = QPushButton("Usar Área")
        btn.setStyleSheet("font-weight: bold; color: #2e7d32;")

        # NUEVO: Arreglo del bug del lambda pasando f=features
        btn.clicked.connect(lambda checked=False, f=features: self.seleccionar_municipio(f))

        self.tabla.setCellWidget(row, 2, btn)

    def seleccionar_municipio(self, features):
        geoms = []
        for f in features:
            geom_dict = f.get("geometry")
            if geom_dict:
                g = QgsJsonUtils.geometryFromGeoJson(json.dumps(geom_dict))
                if g and not g.isNull():
                    geoms.append(g)

        if geoms:
            # En lugar de emitir señal, guardamos la geometría unida en la variable
            self.geom_seleccionada = QgsGeometry.unaryUnion(geoms)
            self.accept()  # Cierra el diálogo


class IdentifyTab(QWidget):
    def abrir_buscador_ttmm(self):
        # Desactivamos herramientas manuales si estaban pulsadas
        self.btn_point.setChecked(False)
        self.btn_poly.setChecked(False)
        self.iface.mapCanvas().unsetMapTool(self.point_tool)
        self.iface.mapCanvas().unsetMapTool(self.poly_tool)

        # Instanciamos y abrimos el diálogo de forma segura
        dialogo = DialogoBusquedaTTMM(self)

        # NUEVO: Esperamos a que el diálogo se cierre (Aceptar)
        if dialogo.exec():
            # Comprobamos si el usuario llegó a seleccionar un municipio
            if dialogo.geom_seleccionada:
                # Extraemos la geometría a formato texto (WKT) de forma segura
                wkt_geom = dialogo.geom_seleccionada.asWkt()
                self.procesar_geometria_ttmm(wkt_geom)

    def procesar_geometria_ttmm(self, wkt_geom):
        # Reconstruimos la geometría desde el texto seguro
        geom_4326 = QgsGeometry.fromWkt(wkt_geom)

        canvas_crs = self.iface.mapCanvas().mapSettings().destinationCrs()
        wgs84_crs = QgsCoordinateReferenceSystem("EPSG:4326")

        if canvas_crs != wgs84_crs:
            xform = QgsCoordinateTransform(wgs84_crs, canvas_crs, QgsProject.instance())
            geom_transformada = QgsGeometry(geom_4326)
            geom_transformada.transform(xform)
        else:
            geom_transformada = geom_4326

        self.status_lbl.setText("Término Municipal establecido como zona de estudio.")
        self.process_geometry(geom_transformada)

    def __init__(self, iface):
        super().__init__()
        self.iface = iface
        self.network_manager = QgsNetworkAccessManager.instance()
        self.plugin_dir = os.path.dirname(__file__)
        self.group_name = "Consultas IEPNB"
        self.study_area_geom = None
        self.study_layer_id = None
        self.result_layers = []
        self.generated_intersection_layers = []
        self.auto_intersect = False
        self.last_epsg_used = "EPSG:25830"
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        tools_layout = QHBoxLayout()
        self.btn_point = QPushButton("Punto")
        self.btn_point.setIcon(QgsApplication.getThemeIcon('/mActionIdentify.svg'))
        self.btn_point.setCheckable(True)
        self.btn_point.clicked.connect(self.activate_point_tool)
        self.btn_poly = QPushButton("Área")
        self.btn_poly.setIcon(QgsApplication.getThemeIcon('/mActionCapturePolygon.svg'))
        self.btn_poly.setCheckable(True)
        self.btn_poly.clicked.connect(self.activate_poly_tool)
        self.btn_ttmm = QPushButton("TTMM")
        self.btn_ttmm.setIcon(QgsApplication.getThemeIcon('/mActionSelectPolygon.svg'))
        self.btn_ttmm.clicked.connect(self.abrir_buscador_ttmm)
        self.btn_import = QPushButton("Importar")
        self.btn_import.setIcon(QgsApplication.getThemeIcon('/mActionAddOgrLayer.svg'))
        self.btn_import.clicked.connect(self.import_shape)
        self.btn_clear_sel = QPushButton("Limpiar")
        self.btn_clear_sel.setIcon(QgsApplication.getThemeIcon('/mActionDeselectAll.svg'))
        self.btn_clear_sel.clicked.connect(self.clear_selection)
        tools_layout.addWidget(self.btn_point)
        tools_layout.addWidget(self.btn_poly)
        tools_layout.addWidget(self.btn_ttmm)
        tools_layout.addWidget(self.btn_import)
        tools_layout.addWidget(self.btn_clear_sel)
        layout.addLayout(tools_layout)

        data_layout = QHBoxLayout()
        self.btn_add_all = QPushButton("Añadir Todas")
        self.btn_add_all.setIcon(QgsApplication.getThemeIcon('/mActionAddAllToOverview.svg'))
        self.btn_add_all.setStyleSheet("font-weight: bold; color: #2e7d32;")
        self.btn_add_all.clicked.connect(self.add_all_results)
        self.btn_intersect = QPushButton("Intersección")
        self.btn_intersect.setIcon(QgsApplication.getThemeIcon('/mAlgorithmIntersect.svg'))
        self.btn_intersect.setStyleSheet("""
                    QPushButton:enabled { font-weight: bold; color: #d84315; }
                    QPushButton:disabled { font-weight: bold; color: #9e9e9e; }
                """)
        self.btn_intersect.setEnabled(False)  # Arranca desactivado
        self.btn_intersect.clicked.connect(self.run_intersection_analysis)

        self.btn_csv = QPushButton("CSV")
        self.btn_csv.setMaximumWidth(40)
        self.btn_csv.setStyleSheet("""
                    QPushButton:enabled { font-weight: bold; color: #2e7d32; }
                    QPushButton:disabled { font-weight: bold; color: #9e9e9e; }
                """)
        self.btn_csv.setEnabled(False)  # Arranca desactivado
        self.btn_csv.clicked.connect(self.export_csv)

        self.btn_report = QPushButton("Informe PDF")
        self.btn_report.setIcon(QgsApplication.getThemeIcon('/mActionFilePrint.svg'))
        self.btn_report.setStyleSheet("""
                    QPushButton:enabled { font-weight: bold; color: #1565c0; }
                    QPushButton:disabled { font-weight: bold; color: #9e9e9e; }
                """)
        self.btn_report.setEnabled(False)  # Arranca desactivado
        self.btn_report.clicked.connect(self.generate_report)
        self.btn_clear_map = QPushButton("Borrar")
        self.btn_clear_map.setIcon(QgsApplication.getThemeIcon('/mActionDeleteSelected.svg'))
        self.btn_clear_map.clicked.connect(self.clear_layers)

        data_layout.addWidget(self.btn_add_all)
        data_layout.addWidget(self.btn_intersect)
        data_layout.addWidget(self.btn_csv)
        data_layout.addWidget(self.btn_report)
        data_layout.addWidget(self.btn_clear_map)
        layout.addLayout(data_layout)

        self.status_lbl = QLabel("Selecciona herramienta o importa un polígono.")
        self.status_lbl.setStyleSheet("font-size: 11px; color: #2c3e50; font-weight: bold;")
        self.status_lbl.setWordWrap(True)
        layout.addWidget(self.status_lbl)

        self.progress_bar = QProgressBar()
        self.progress_bar.setStyleSheet("""
                QProgressBar { border: 1px solid #bbb; border-radius: 4px; text-align: center; height: 12px; }
                QProgressBar::chunk { background-color: #2e7d32; width: 10px; }
            """)
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(["Capa", "Cantidad", "Acción"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.table)

        self.point_tool = QgsMapToolEmitPoint(self.iface.mapCanvas())
        self.point_tool.canvasClicked.connect(self.handle_point_click)
        self.poly_tool = ManualPolygonTool(self.iface)
        self.poly_tool.polygon_finished.connect(self.process_geometry)

    def activate_point_tool(self):
        self.btn_poly.setChecked(False)
        if self.btn_point.isChecked():
            self.iface.mapCanvas().setMapTool(self.point_tool)
            self.status_lbl.setText("📍 Haz clic en el mapa para identificar el punto...")
        else:
            self.iface.mapCanvas().unsetMapTool(self.point_tool)
            self.status_lbl.setText("Herramienta desactivada.")

    def activate_poly_tool(self):
        self.btn_point.setChecked(False)
        if self.btn_poly.isChecked():
            self.iface.mapCanvas().setMapTool(self.poly_tool)
            self.status_lbl.setText("📐 Dibuja un área (Botón derecho para finalizar)...")
        else:
            self.iface.mapCanvas().unsetMapTool(self.poly_tool)
            self.status_lbl.setText("Herramienta desactivada.")

    def update_study_layer(self, geometry):
        if self.study_layer_id:
            QgsProject.instance().removeMapLayer(self.study_layer_id)
            self.study_layer_id = None

        crs_auth = self.iface.mapCanvas().mapSettings().destinationCrs().authid()
        vl = QgsVectorLayer(f"Polygon?crs={crs_auth}", "Zona de estudio", "memory")
        pr = vl.dataProvider()

        f = QgsFeature()
        f.setGeometry(geometry)
        pr.addFeatures([f])
        vl.updateExtents()

        sym = QgsFillSymbol.createSimple(
            {'color': '239,68,68,80', 'outline_color': '239,68,68', 'outline_width': '0.5'})
        vl.renderer().setSymbol(sym)

        root = QgsProject.instance().layerTreeRoot()
        group = root.findGroup(self.group_name) or root.insertGroup(0, self.group_name)
        QgsProject.instance().addMapLayer(vl, False)
        group.insertLayer(0, vl)
        self.study_layer_id = vl.id()

    def clear_selection(self):
        if self.study_layer_id:
            QgsProject.instance().removeMapLayer(self.study_layer_id)
            self.study_layer_id = None
        self.study_area_geom = None
        self.btn_intersect.setEnabled(False)
        self.btn_report.setEnabled(False)
        self.btn_csv.setEnabled(False)
        self.status_lbl.setText("Selección limpiada.")

    def clear_layers(self):
        self.clear_selection()
        self.result_layers = []
        self.generated_intersection_layers = []
        root = QgsProject.instance().layerTreeRoot()
        for gname in [self.group_name, "Intersecciones"]:
            group = root.findGroup(gname)
            if group:
                for ln in group.children():
                    QgsProject.instance().removeMapLayer(ln.layerId())
                root.removeChildNode(group)
        self.table.setRowCount(0)
        self.status_lbl.setText("Mapa limpiado.")

    def import_shape(self):
        self.auto_intersect = False
        path, _ = QFileDialog.getOpenFileName(self, "Seleccionar Capa", "",
                                              "Formatos Vectoriales (*.shp *.geojson *.gpkg *.kml *.kmz *.dxf);;Todos los archivos (*.*)")
        if not path:
            return

        vlayer_import = QgsVectorLayer(path, "temp_import", "ogr")
        if not vlayer_import.isValid():
            return

        geoms = [f.geometry() for f in vlayer_import.getFeatures() if f.hasGeometry()]
        if not geoms:
            return
        combined_geom = QgsGeometry.unaryUnion(geoms)

        canvas_crs = self.iface.mapCanvas().mapSettings().destinationCrs()
        if vlayer_import.crs() != canvas_crs:
            combined_geom.transform(QgsCoordinateTransform(vlayer_import.crs(), canvas_crs, QgsProject.instance()))

        self.study_area_geom = combined_geom
        self.process_geometry(combined_geom)
        self.status_lbl.setText(f"Importado: {os.path.basename(path)}")

    def handle_point_click(self, point):
        canvas_crs = self.iface.mapCanvas().mapSettings().destinationCrs()
        wgs84_crs = QgsCoordinateReferenceSystem("EPSG:4326")

        p_geom_wgs84 = QgsGeometry.fromPointXY(point)
        p_geom_wgs84.transform(QgsCoordinateTransform(canvas_crs, wgs84_crs, QgsProject.instance()))

        epsg_metric = "EPSG:4083" if p_geom_wgs84.asPoint().x() < -12 else "EPSG:25830"
        metric_crs = QgsCoordinateReferenceSystem(epsg_metric)

        p_geom = QgsGeometry.fromPointXY(point)
        xform_to_metric = QgsCoordinateTransform(canvas_crs, metric_crs, QgsProject.instance())
        p_geom.transform(xform_to_metric)
        buffer_geom = p_geom.buffer(10, 8)

        xform_to_canvas = QgsCoordinateTransform(metric_crs, canvas_crs, QgsProject.instance())
        buffer_canvas = QgsGeometry(buffer_geom)
        buffer_canvas.transform(xform_to_canvas)

        self.update_study_layer(buffer_canvas)
        self.study_area_geom = buffer_canvas

        xform_to_4326 = QgsCoordinateTransform(metric_crs, wgs84_crs, QgsProject.instance())
        buffer_4326 = QgsGeometry(buffer_geom)
        buffer_4326.transform(xform_to_4326)
        self.mask_4326 = buffer_4326
        box = buffer_4326.boundingBox()

        self.auto_intersect = False
        self.launch_sequence(f"{box.xMinimum():.10f},{box.yMinimum():.10f},{box.xMaximum():.10f},{box.yMaximum():.10f}")

    def process_geometry(self, geometry):
        self.auto_intersect = False

        dArea = QgsDistanceArea()
        dArea.setSourceCrs(self.iface.mapCanvas().mapSettings().destinationCrs(),
                           QgsProject.instance().transformContext())
        dArea.setEllipsoid('WGS84')
        area_m2 = dArea.measureArea(geometry)
        area_km2 = area_m2 / 1500000.0

        if area_km2 > 15000:
            QMessageBox.warning(self, "Área demasiado grande",
                                f"El polígono seleccionado tiene un área de {area_km2:,.2f} km².\n\n"
                                "El límite máximo permitido es de 15.000 km² para evitar sobrecargar las consultas al servidor.")
            self.status_lbl.setText("Error: Área de estudio supera el límite.")
            return

        self.area_estudio_ha = area_m2 / 10000.0

        self.update_study_layer(geometry)
        self.study_area_geom = geometry

        canvas = self.iface.mapCanvas()
        xform = QgsCoordinateTransform(canvas.mapSettings().destinationCrs(), QgsCoordinateReferenceSystem("EPSG:4326"),
                                       QgsProject.instance())
        geom_4326 = QgsGeometry(geometry)
        geom_4326.transform(xform)
        self.mask_4326 = geom_4326
        box = geom_4326.boundingBox()
        self.launch_sequence(f"{box.xMinimum():.10f},{box.yMinimum():.10f},{box.xMaximum():.10f},{box.yMaximum():.10f}")

    def launch_sequence(self, bbox):
        self.table.setRowCount(0)
        self.result_layers = []
        self.current_bbox = bbox

        # ✅ IDEA: Apagamos los botones (se pondrán grises) al arrancar una nueva consulta
        self.btn_intersect.setEnabled(False)
        self.btn_csv.setEnabled(False)
        self.btn_report.setEnabled(False)

        self.iface.mainWindow().setCursor(Qt.CursorShape.WaitCursor)
        self.status_lbl.setText("Consultando servicios...")
        self.query_next_service(0)

    def query_next_service(self, index):
        if index >= len(CONFIG_SERVICIOS):
            self.iface.mainWindow().setCursor(Qt.CursorShape.ArrowCursor)
            capas_queried = ", ".join([srv['id'] for srv in CONFIG_SERVICIOS])
            msg = f"Consulta finalizada. Encontrados: {self.table.rowCount()}<br>"
            msg += f"<span style='font-size: 9px; font-weight: normal; color: #555;'>Capas consultadas: {capas_queried}</span>"
            self.status_lbl.setText(msg)

            if self.auto_intersect and self.table.rowCount() > 0:
                self.add_all_results()
                self.run_intersection_analysis()

            if self.study_area_geom:
                rect = self.study_area_geom.boundingBox()
                if rect.width() < 100 or rect.height() < 100:
                    rect.scale(20.0)
                else:
                    rect.scale(1.5)
                self.iface.mapCanvas().setExtent(rect)
                self.iface.mapCanvas().refresh()
            return

        srv = CONFIG_SERVICIOS[index]
        QApplication.processEvents()

        url = QUrl()
        query = QUrlQuery()

        # --- BIFURCACIÓN SEGÚN EL TIPO DE SERVICIO ---
        if srv.get("type") == "OAPIF":
            # Formato moderno OGC API Features (MAPAMA)
            url = QUrl(f"{srv['url']}/items")
            query.addQueryItem("f", "json")
            query.addQueryItem("bbox", f"{self.current_bbox}")
        else:
            # Formato WFS Tradicional (Tus Geoserver)
            url = QUrl(srv["url"])
            query.addQueryItem("service", "WFS")
            query.addQueryItem("version", "1.0.0")
            query.addQueryItem("request", "GetFeature")
            query.addQueryItem("typeName", srv["layer"])
            query.addQueryItem("outputFormat", "application/json")
            query.addQueryItem("bbox", f"{self.current_bbox},EPSG:4326")
            query.addQueryItem("srsName", "EPSG:4326")

        url.setQuery(query)

        reply = self.network_manager.get(QtNetwork.QNetworkRequest(url))
        reply.finished.connect(lambda: self.process_wfs_response(reply, index))

    def process_wfs_response(self, reply, index):
        srv = CONFIG_SERVICIOS[index]
        raw = reply.readAll().data()
        reply.deleteLater()

        if raw:
            try:
                data = json.loads(raw)
                features = data.get("features", [])

                if features:
                    grupos_locales = {}

                    for f in features:
                        geom_dict = f.get("geometry")
                        if not geom_dict:
                            continue

                        geom_json_str = json.dumps(geom_dict)
                        feat_geom = QgsJsonUtils.geometryFromGeoJson(geom_json_str)

                        # Intersección espacial con la máscara
                        if feat_geom and not feat_geom.isNull() and hasattr(self, 'mask_4326') and feat_geom.intersects(
                                self.mask_4326):
                            props = f.get("properties", {})

                            # --- 1. EXTRACCIÓN ROBUSTA DE NOMBRES (Inspirado en territory.py) ---
                            info_val = None
                            if srv.get("id") == "Municipio":
                                info_val = props.get("nut3_nom") or props.get("municipio")
                            elif srv.get("id") in ["Provincia", "CCAA"]:
                                info_val = props.get("nut2_nom") or props.get("provincia")

                            # Si no es TTMM/Provincia, usamos su col_inf o un campo nombre por defecto
                            if not info_val:
                                info_val = props.get(srv.get("col_inf")) or props.get("nombre") or props.get("name")

                            info_val = str(info_val).strip(" ,") if info_val else "Elemento sin nombre"

                            # Agrupamos en el diccionario
                            if info_val not in grupos_locales:
                                grupos_locales[info_val] = []
                            grupos_locales[info_val].append(f)

                    if grupos_locales:
                        filtered_features = []
                        collected_infos = []

                        # --- 2. UNIFICACIÓN DE MICROPOLÍGONOS ---
                        for info_val, lista_micropoligonos in grupos_locales.items():
                            if len(lista_micropoligonos) == 1:
                                filtered_features.append(lista_micropoligonos[0])
                            else:
                                # Hay varios fragmentos: extraemos sus geometrías y las unimos
                                geoms_a_unir = []
                                for feat in lista_micropoligonos:
                                    g = QgsJsonUtils.geometryFromGeoJson(json.dumps(feat["geometry"]))
                                    if g and not g.isNull():
                                        geoms_a_unir.append(g)

                                if geoms_a_unir:
                                    # Fusión total de las partes disjuntas
                                    geom_fusionada = QgsGeometry.unaryUnion(geoms_a_unir)

                                    # Clonamos el diccionario base y le sobreescribimos la geometría unida
                                    feature_unificada = lista_micropoligonos[0].copy()
                                    feature_unificada["geometry"] = json.loads(geom_fusionada.asJson())

                                    filtered_features.append(feature_unificada)

                            # Añadimos al sumario de texto
                            if info_val != "Elemento sin nombre":
                                collected_infos.append(info_val)

                        combined_info = ", ".join(list(set(collected_infos))) if collected_infos else "Varios"

                        # Ahora filtered_features tiene longitud exacta = número de municipios/provincias reales
                        self.add_group_row(srv["id"], filtered_features, combined_info, srv["color"])
            except Exception as e:
                from qgis.core import QgsMessageLog, Qgis
                QgsMessageLog.logMessage(f"Error procesando WFS: {e}", "IEPNB Tools", Qgis.MessageLevel.Warning)

        self.query_next_service(index + 1)

    def add_group_row(self, cap, feature_list, combined_info, color):
        row = self.table.rowCount()
        self.table.insertRow(row)
        count = len(feature_list)
        count_str = f"{count} elementos"

        item_cap = QTableWidgetItem(str(cap))
        item_cap.setData(Qt.ItemDataRole.UserRole, {
            "feature_list": feature_list,
            "cap": cap,
            "count_str": count_str,
            "info": combined_info,
            "color": color
        })

        self.table.setItem(row, 0, item_cap)
        self.table.setItem(row, 1, QTableWidgetItem(count_str))

        btn = QPushButton("Añadir Grupo")
        btn.clicked.connect(lambda: self.load_group_to_map(feature_list, cap, count_str, combined_info, color))
        self.table.setCellWidget(row, 2, btn)

    def add_all_results(self):
        for r in range(self.table.rowCount()):
            data = self.table.item(r, 0).data(Qt.ItemDataRole.UserRole)
            self.load_group_to_map(data["feature_list"], data["cap"], data["count_str"], data["info"], data["color"])

        # IDEA: Si la tabla tenía resultados y se han añadido, habilitamos el botón explícitamente
        if self.table.rowCount() > 0:
            self.btn_intersect.setEnabled(True)

    def load_group_to_map(self, feature_list, cap, name_suffix, info, color):
        if not feature_list:
            return
        tmp_path = os.path.join(tempfile.gettempdir(), f"res_grp_{uuid.uuid4().hex[:8]}.geojson")
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump({"type": "FeatureCollection", "features": feature_list}, f)

        vlayer = QgsVectorLayer(tmp_path, f"{cap} ({name_suffix})", "ogr")
        if vlayer.isValid():
            vlayer.setCrs(QgsCoordinateReferenceSystem("EPSG:4326"))
            vlayer.setCustomProperty("service_id", cap)
            vlayer.setCustomProperty("original_info", info)

            if vlayer.geometryType() == QgsWkbTypes.GeometryType.LineGeometry:
                sym = QgsLineSymbol.createSimple({'line_color': color.name(), 'line_width': '0.7'})
            else:
                sym = QgsFillSymbol.createSimple(
                    {'color': color.name(), 'outline_color': 'black', 'outline_width': '0.3'})

            vlayer.setRenderer(QgsSingleSymbolRenderer(sym))
            vlayer.setOpacity(0.4)
            root = QgsProject.instance().layerTreeRoot()
            group = root.findGroup(self.group_name) or root.insertGroup(0, self.group_name)
            QgsProject.instance().addMapLayer(vlayer, False)
            group.addLayer(vlayer)
            self.result_layers.append(vlayer)
            if self.study_area_geom:
                self.btn_intersect.setEnabled(True)

    def run_intersection_analysis(self):
        self.iface.mainWindow().setCursor(Qt.CursorShape.WaitCursor)
        if not self.auto_intersect:
            self.status_lbl.setText("Calculando intersecciones...")

        root = QgsProject.instance().layerTreeRoot()
        group_consultas = root.findGroup(self.group_name)
        if group_consultas:
            for child in group_consultas.children():
                if child.layerId() != self.study_layer_id:
                    child.setItemVisibilityChecked(False)
                else:
                    child.setItemVisibilityChecked(True)

        self.generated_intersection_layers = []
        target_crs = QgsCoordinateReferenceSystem("EPSG:4326")
        mask_geom = QgsGeometry(self.study_area_geom)

        if self.iface.mapCanvas().mapSettings().destinationCrs() != target_crs:
            mask_geom.transform(
                QgsCoordinateTransform(self.iface.mapCanvas().mapSettings().destinationCrs(), target_crs,
                                       QgsProject.instance()))

        centroid = mask_geom.centroid().asPoint()
        self.last_epsg_used = "EPSG:4083" if centroid.x() < -12 else "EPSG:25830"
        crs_metric = QgsCoordinateReferenceSystem(self.last_epsg_used)

        xform_area = QgsCoordinateTransform(target_crs, crs_metric, QgsProject.instance())
        group_out = QgsProject.instance().layerTreeRoot().findGroup(
            "Intersecciones") or QgsProject.instance().layerTreeRoot().insertGroup(0, "Intersecciones")

        for vlayer in self.result_layers:
            # --- BLOQUE DE SEGURIDAD CONTRA CAPAS BORRADAS ---
            try:
                # Esto fuerza a Python a comprobar si el objeto C++ sigue existiendo
                if vlayer is None or not vlayer.isValid():
                    continue

                # Intentamos acceder a los campos para verificar que realmente está viva
                fields = vlayer.fields()

            except RuntimeError:
                # Si llegamos aquí, es que la capa fue borrada (objeto eliminado)
                # Saltamos a la siguiente y continuamos
                continue
            # --------------------------------------------------

            # A partir de aquí, el código continúa con total seguridad
            feats_out = []

            # IMPORTANTE: Ahora que sabemos que vlayer es segura, usamos 'fields'
            # que obtuvimos arriba dentro del try
            fields.append(QgsField("calc_valor", QVariant.Double))
            fields.append(QgsField("calc_unidad", QVariant.String))
            fields.append(QgsField("info_origen", QVariant.String))

            orig_type = vlayer.geometryType()

            # --- LÓGICA DE AGRUPACIÓN ---
            nom_idx = -1
            for c in ["nombre", "monte", "site_name", "nb_via", "id"]:
                idx = fields.indexOf(c)
                if idx != -1:
                    nom_idx = idx
                    break

            grouped_intersections = {}

            # 2. Intersectar y agrupar en el diccionario temporal
            for feat in vlayer.getFeatures():
                if feat.geometry().intersects(mask_geom):
                    intersection = feat.geometry().intersection(mask_geom)
                    if not intersection.isEmpty():
                        # Usar el nombre como clave (o el ID si no hay nombre)
                        clave = str(feat.attribute(nom_idx)) if nom_idx != -1 else str(feat.id())

                        if clave in grouped_intersections:
                            # Si ya existe esta vía o monte, unimos las geometrías (Dissolve)
                            grouped_intersections[clave]['geom'] = grouped_intersections[clave]['geom'].combine(
                                intersection)
                        else:
                            # Si no existe, guardamos la primera geometría y la entidad original
                            grouped_intersections[clave] = {
                                'geom': QgsGeometry(intersection),
                                'feat': feat
                            }

            # 3. Procesar los elementos ya agrupados para calcular su área/longitud total
            for clave, data in grouped_intersections.items():
                feat_orig = data['feat']
                geom_final = data['geom']

                new_feat = QgsFeature(fields)

                # Copiamos todos los atributos originales del primer fragmento encontrado
                for i in range(vlayer.fields().count()):
                    new_feat.setAttribute(i, feat_orig.attribute(i))

                # Le asignamos la geometría combinada
                new_feat.setGeometry(geom_final)

                # Calculamos el área o longitud sobre la geometría total combinada
                geom_calc = QgsGeometry(geom_final)
                geom_calc.transform(xform_area)
                val = round(
                    geom_calc.area() / 10000.0 if orig_type == QgsWkbTypes.GeometryType.PolygonGeometry else geom_calc.length(),
                    2)
                unit = "ha" if orig_type == QgsWkbTypes.GeometryType.PolygonGeometry else "m"

                new_feat.setAttribute("calc_valor", val)
                new_feat.setAttribute("calc_unidad", unit)
                new_feat.setAttribute("info_origen", vlayer.customProperty("original_info"))
                feats_out.append(new_feat)
            # --- FIN LÓGICA DE AGRUPACIÓN ---

            if feats_out:
                uri_type = "MultiPolygon" if orig_type == QgsWkbTypes.GeometryType.PolygonGeometry else "MultiLineString"
                # --- NUEVO: Limpiamos el nombre original y ponemos el conteo real ---
                # Cortamos por el paréntesis para quitar el " (179)" original
                clean_name = vlayer.name().split('(')[0].strip()
                # Creamos el nuevo nombre con el número de elementos agrupados y la palabra "elementos"
                new_layer_name = f"Corte: {clean_name} ({len(feats_out)} elementos)"

                vl_out = QgsVectorLayer(f"{uri_type}?crs=EPSG:4326", new_layer_name, "memory")
                vl_out.setCustomProperty("service_id", vlayer.customProperty("service_id"))
                pr = vl_out.dataProvider()
                pr.addAttributes(fields)
                vl_out.updateFields()
                pr.addFeatures(feats_out)
                if orig_type == QgsWkbTypes.GeometryType.LineGeometry:
                    sym = QgsLineSymbol.createSimple({'line_color': '#FF0000', 'line_width': '0.2'})
                else:
                    props = vlayer.renderer().symbol().symbolLayer(0).properties()
                    props.update({'outline_width': '0.2', 'outline_color': '#FF0000', 'style': 'dense5'})
                    sym = QgsFillSymbol.createSimple(props)
                vl_out.setRenderer(QgsSingleSymbolRenderer(sym))
                QgsProject.instance().addMapLayer(vl_out, False)
                layer_node = group_out.addLayer(vl_out)

                if vl_out.customProperty("service_id") == "Riqueza Esp.":
                    layer_node.setItemVisibilityChecked(False)

                self.generated_intersection_layers.append(vl_out)

        self.btn_report.setEnabled(True)
        self.btn_csv.setEnabled(True)
        self.iface.mainWindow().setCursor(Qt.CursorShape.ArrowCursor)
        if not self.auto_intersect:
            self.status_lbl.setText(f"Completado. Sistema: {self.last_epsg_used}")

    def fetch_api_sync(self, url_str):
        loop = QEventLoop()
        reply = self.network_manager.get(QtNetwork.QNetworkRequest(QUrl(url_str)))
        reply.finished.connect(loop.quit)
        loop.exec()
        data = reply.readAll().data()
        reply.deleteLater()
        try:
            return json.loads(data)
        except Exception:
            return []

    def export_csv(self):
        desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
        default_save = os.path.join(desktop_path, "Resultados_IEPNB.csv")

        path_csv, _ = QFileDialog.getSaveFileName(self, "Guardar CSV", default_save, "CSV (*.csv)")
        if not path_csv:
            return
        self.iface.mainWindow().setCursor(Qt.CursorShape.WaitCursor)
        try:
            with open(path_csv, mode='w', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f, delimiter=';')
                writer.writerow(["Capa", "Elemento", "Valor", "Unidad", "Info Origen"])
                for layer_item in self.generated_intersection_layers:
                    capa_name = layer_item.name().replace('Corte: ', '')
                    for feat in layer_item.getFeatures():
                        nom = "S/N"
                        for c in ["nombre", "monte", "site_name", "nb_via", "id"]:
                            idx = layer_item.fields().indexOf(c)
                            if idx != -1 and feat.attribute(idx):
                                nom = str(feat.attribute(idx))
                                break
                        val = round(feat.attribute('calc_valor'), 2)
                        unit = feat.attribute('calc_unidad')
                        info = str(feat.attribute('info_origen'))
                        writer.writerow([capa_name, nom, val, unit, info])
            self.status_lbl.setText("CSV exportado con éxito.")
        except Exception as e:
            self.status_lbl.setText(f"Error al exportar CSV: {e}")
        self.iface.mainWindow().setCursor(Qt.CursorShape.ArrowCursor)

    def generate_report(self):
        import base64
        import os
        import tempfile
        from qgis.PyQt.QtWidgets import QFileDialog, QApplication
        from qgis.PyQt.QtCore import Qt, QUrl, QEventLoop
        from qgis.PyQt import QtNetwork
        from qgis.PyQt.QtPrintSupport import QPrinter

        desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
        default_save = os.path.join(desktop_path, "Resultados_IEPNB.pdf")

        path_pdf, _ = QFileDialog.getSaveFileName(self, "Guardar PDF", default_save, "PDF (*.pdf)")
        if not path_pdf:
            return
        self.iface.mainWindow().setCursor(Qt.CursorShape.WaitCursor)
        self.status_lbl.setText("Iniciando generación de informe...")

        img_path = os.path.join(tempfile.gettempdir(), "map_snap.png")
        self.iface.mapCanvas().saveAsImage(img_path)

        map_file_url = QUrl.fromLocalFile(img_path).toString()
        logo1 = os.path.join(self.plugin_dir, "logo-iepnb.png")
        logo2 = os.path.join(self.plugin_dir, "minis.png")
        logo1_url = QUrl.fromLocalFile(logo1).toString()
        logo2_url = QUrl.fromLocalFile(logo2).toString()

        # El motor de texto enriquecido de Qt no calcula el ancho a partir
        # del alto de forma automática como haría un navegador: si en el
        # <img> solo se indica 'height' (sin 'width'), la imagen puede
        # salir deformada. Calculamos ambos a partir del tamaño real del
        # PNG para mantener la proporción.
        def _wh_for_height(ruta, alto_deseado):
            pm = QPixmap(ruta)
            if pm.isNull() or pm.height() == 0:
                return alto_deseado, alto_deseado
            ancho = round(pm.width() * (alto_deseado / pm.height()))
            return ancho, alto_deseado

        logo1_w, logo1_h = _wh_for_height(logo1, 45)
        logo2_w, logo2_h = _wh_for_height(logo2, 45)

        FIELD_MAP = {
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
            "Masas Agua Sub.": {"fig": "cod_masa", "nom": "nom_masa"},
            "Masas Agua Sup. (Líneas)": {"fig": "cod_masa", "nom": "nombre_masa"},
            "Masas Agua Sup. (Polígonos)": {"fig": "cod_masa", "nom": "nombre_masa"},
        }

        esp_ids = set()
        for layer_item in self.generated_intersection_layers:
            if layer_item.customProperty("service_id") == "Riqueza Esp.":
                for feat in layer_item.getFeatures():
                    for x in str(feat.attribute("info_origen")).split(","):
                        if x.strip() and x != "-":
                            esp_ids.add(x.strip())

        tax_prior = ['mamífero', 'ave', 'reptil', 'pez', 'anfibio', 'invertebrado', 'planta vascular',
                     'planta no vascular', 'hongo', 'alga', 'cromista', 'bacteria']

        def prio(g):
            g_low = str(g).lower()
            for i, ord_g in enumerate(tax_prior):
                if ord_g in g_low:
                    return i
            return 99

        import time
        start_time = time.time()

        info_sp = []
        total_esp = len(esp_ids)

        if total_esp > 0:
            self.progress_bar.setMaximum(total_esp)
            self.progress_bar.setValue(0)
            self.progress_bar.setVisible(True)

        for index, id_t in enumerate(esp_ids):
            eta_text = ""
            if index > 0:
                elapsed = time.time() - start_time
                avg_time = elapsed / index
                remaining_seconds = int(avg_time * (total_esp - index))
                mins, secs = divmod(remaining_seconds, 60)
                eta_text = f" | Tiempo restante: {mins:02d}:{secs:02d}"

            self.status_lbl.setText(f"Procesando especies {index + 1}/{total_esp}{eta_text}")
            self.progress_bar.setValue(index + 1)
            QApplication.processEvents()

            cat = self.fetch_api_sync(f"https://iepnb.gob.es/api/catalogo/v_listapatronespecie?idtaxon=eq.{id_t}")
            it = cat[0] if cat else {}
            grp = it.get('Grupo taxonómico', 'Otros')

            img_local_path = ""
            res_img = self.fetch_api_sync(f"https://iepnb.gob.es/api/especie/v_imagenes?id_taxon=eq.{id_t}")

            if isinstance(res_img, list) and len(res_img) > 0:
                foto_seleccionada = next((img for img in res_img if img.get('es_prioridad') == 1), res_img[0])
                ruta_foto = foto_seleccionada.get('ruta_foto')

                if ruta_foto:
                    ruta_foto = str(ruta_foto).strip()
                    if ruta_foto.startswith("http"):
                        url_img_final = ruta_foto
                    elif ruta_foto.startswith("www."):
                        url_img_final = "https://" + ruta_foto
                    elif ruta_foto.startswith("/"):
                        url_img_final = "https://www.miteco.gob.es" + ruta_foto
                    else:
                        url_img_final = "https://www.miteco.gob.es/" + ruta_foto.lstrip('/')

                    try:
                        img_reply = self.network_manager.get(QtNetwork.QNetworkRequest(QUrl(url_img_final)))
                        loop = QEventLoop()
                        img_reply.finished.connect(loop.quit)
                        loop.exec()

                        if img_reply.error() == QtNetwork.QNetworkReply.NetworkError.NoError:
                            data_bytes = img_reply.readAll().data()
                            if len(data_bytes) > 100:
                                b64 = base64.b64encode(data_bytes).decode('ascii')
                                img_local_path = f"data:image/jpeg;base64,{b64}"
                    except Exception as e:
                        from qgis.core import QgsMessageLog, Qgis
                        QgsMessageLog.logMessage(
                            f"No se pudo descargar la foto de la especie {id_t} para el informe: {e}",
                            "IEPNB Tools", Qgis.MessageLevel.Warning)

            info_sp.append({
                "id": id_t, "cien": it.get('ScientificName', 'N/A'),
                "vulg": it.get('Vernacular Name', '-'), "grupo": grp,
                "prio": prio(grp), "img": img_local_path
            })

        self.status_lbl.setText("Escribiendo documento PDF...")
        QApplication.processEvents()
        info_sp.sort(key=lambda x: (x["prio"], x["cien"]))
        area_txt = f"{self.area_estudio_ha:,.2f} ha" if hasattr(self, 'area_estudio_ha') else "No calculada"

        municipios = set()
        provincias = set()

        for layer_item in self.generated_intersection_layers:
            sid = layer_item.customProperty("service_id")

            if sid == "Provincia":
                for feat in layer_item.getFeatures():
                    idx = layer_item.fields().indexOf("nut3_nom")
                    if idx != -1 and feat.attribute(idx):
                        provincias.add(str(feat.attribute(idx)))

            elif sid == "Municipio":
                for feat in layer_item.getFeatures():
                    idx = layer_item.fields().indexOf("nombre")
                    if idx != -1 and feat.attribute(idx):
                        municipios.add(str(feat.attribute(idx)))

        bloque_ubicacion_html = ""

        if municipios or provincias:
            lineas_html = []
            if provincias:
                txt_prov = ", ".join(sorted(provincias))
                lineas_html.append(f'<b style="color: #2e7d32;">Provincias afectadas:</b> {txt_prov}')

            if municipios:
                txt_muni = ", ".join(sorted(municipios))
                lineas_html.append(f'<b style="color: #2e7d32;">Términos municipales afectados:</b> {txt_muni}')

            contenido_dinamico = "<br>".join(lineas_html)

            bloque_ubicacion_html = f"""
                    <div style="background-color: #f8f9fa; border-left: 4px solid #2e7d32; padding: 8px; margin-bottom: 13px;">
                        <p style="margin: 0; font-family: sans-serif; font-size: 10px; color: #2c3e50;">
                            {contenido_dinamico}
                        </p>
                    </div>
                    """

        # ---------------------------------------------------------------------
        # Cálculo del nombre del EPSG
        epsg_str = str(self.last_epsg_used).replace("EPSG:", "").strip()

        if epsg_str == "25830":
            crs_name = " - ETRS89 - UTM 30 N"
        elif epsg_str == "4083":
            crs_name = " - REGCAN UTM 28N"
        else:
            crs_name = ""

        # Generación del HTML unificado
        html = f"""<html><head><style>
                    body {{ font-family: sans-serif; font-size: 10px; color: #333; }}
                    h1 {{ color: #2c3e50; border-bottom: 2px solid #2c3e50; margin-bottom: 10px; }}
                    h3 {{ color: #2980b9; margin-top: 15px; border-left: 4px solid #2980b9; padding-left: 8px; }}

                    table {{
                        width: 100%;
                        border-collapse: separate;
                        border-spacing: 0;
                        margin-top: 5px;
                    }}
                    th, td {{
                        border: 1px solid #bdc3c7;
                        padding: 8px;
                        text-align: left;
                        vertical-align: top;
                    }}
                    th {{ background-color: #ecf0f1; font-weight: bold; vertical-align: middle; }}

                    /* 'page-break-inside: avoid' en tr/td NO surte efecto al
                       imprimir con QTextDocument (Qt lo ignora para tablas);
                       el control de saltos de página real se hace a mano en
                       Python con page-break-before por tandas de filas. */

                    a {{ color: #2980b9; text-decoration: none; font-weight: bold; }}
                    img {{ display: block; margin: 0 auto; }}

                    .footer-logos {{ width: 100%; margin-top: 20px; border-top: 1px solid #eee; padding-top: 10px; }}
                    .crs-info {{ color: #7f8c8d; font-style: italic; margin-top: 2px; font-size: 9px; }}
                    .disclaimer {{
                        background-color: #f4f7f9;
                        border: 1px solid #d1d9e1;
                        padding: 10px;
                        margin-top: 30px;
                        font-size: 8.5px;
                        color: #555;
                        line-height: 1.4;
                        text-align: justify;
                    }}
                </style></head><body>

            <h1>Informe de resultados - IEPNB Tools</h1>
            <p><b>Fecha de generación:</b> {datetime.datetime.now().strftime('%d/%m/%Y %H:%M')}</p>
            <p class='crs-info'>Los cálculos de superficies y distancias se han realizado utilizando el sistema de referencia proyectado: <b>{self.last_epsg_used}{crs_name}</b></p>

            <center><img src="{map_file_url}" width="480"></center>

            <p style='font-size: 12px; text-align: center; margin-top: 12px; margin-bottom: 15px; color: #2c3e50;'>
                <b>Superficie total de estudio:</b> {area_txt}
            </p>

            {bloque_ubicacion_html}

            <h3>1. Intersecciones detectadas con las capas seleccionadas</h3>
            <table border="1" cellspacing="0" cellpadding="5" width="98%" style="margin-left: 1%;">
                <tr>
                    <th width="20%" style='text-align:center;'>Capa</th>
                    <th width="24%" style='text-align:center;'>Figura</th>
                    <th width="24%" style='text-align:center;'>Nombre</th>
                    <th width="16%" style='text-align:center;'>Resultados INT</th>
                    <th width="18%" style='text-align:center;'>% Ocupación</th>
                </tr>"""

        for layer_item in self.generated_intersection_layers:
            sid = layer_item.customProperty("service_id")

            if sid in ["Riqueza Esp.", "Provincia", "Municipio"]:
                continue

            for feat in layer_item.getFeatures():
                fig_val = ""
                nom_val = "S/N"

                if sid in FIELD_MAP:
                    conf = FIELD_MAP[sid]
                    if conf["fig"]:
                        f_idx = layer_item.fields().indexOf(conf["fig"])
                        if f_idx != -1 and feat.attribute(f_idx):
                            fig_val = str(feat.attribute(f_idx))
                    if conf["nom"]:
                        n_idx = layer_item.fields().indexOf(conf["nom"])
                        if n_idx != -1 and feat.attribute(n_idx):
                            nom_val = str(feat.attribute(n_idx))
                else:
                    for c in ["nombre", "monte", "site_name", "nb_via", "id"]:
                        idx = layer_item.fields().indexOf(c)
                        if idx != -1 and feat.attribute(idx):
                            nom_val = str(feat.attribute(idx))
                            break

                val = feat.attribute('calc_valor')
                unit = feat.attribute('calc_unidad')
                porcentaje_html = "-"
                if unit == 'ha' and hasattr(self, 'area_estudio_ha') and self.area_estudio_ha > 0:
                    pct = min((val / self.area_estudio_ha) * 100, 100.0)
                    porcentaje_html = f"<span style='color: #d35400;'><b>{pct:.2f} %</b></span>"

                html += f"<tr><td>{layer_item.name().replace('Corte: ', '')}</td><td>{fig_val}</td><td>{nom_val}</td><td style='text-align:center;'><b>{val:.2f} {unit}</b></td><td style='text-align:center;'>{porcentaje_html}</td></tr>"

        if info_sp:
            # IMPORTANTE: Qt (QTextDocument) NO soporta 'page-break-inside:
            # avoid' para filas de tabla al imprimir - es una limitación del
            # motor, no un descuido de CSS. Si una fila no cabe entera en lo
            # que queda de página, Qt corta cada celda por separado en vez
            # de mover la fila completa a la página siguiente (de ahí el
            # descuadre). La única forma fiable es forzar manualmente un
            # salto de página cada N filas, para que cada tabla-tanda
            # arranque siempre en la parte superior de una página en
            # blanco y ninguna fila llegue nunca "al límite".
            ROWS_PER_PAGE = 8  # filas de especies (con foto de 90px) por página; ajustable si hiciera falta

            def cabecera_tabla_especies():
                return """<table border="1" cellspacing="0" cellpadding="5" width="98%" style="margin-left: 1%;">
                        <tr>
                            <th width="22%" style='text-align:center;'>Imagen</th>
                            <th width="12%" style='text-align:center;'>Taxón ID</th>
                            <th width="25%" style='text-align:center;'>Nombre Común</th>
                            <th width="25%" style='text-align:center;'>Nombre Científico</th>
                            <th width="16%" style='text-align:center;'>Grupo</th>
                        </tr>"""

            html += ('</table><div style="page-break-before: always;"></div>'
                     '<h3>2. Riqueza de Especies (Clasificación Taxonómica)</h3>'
                     + cabecera_tabla_especies())

            for i, s in enumerate(info_sp):
                if i > 0 and i % ROWS_PER_PAGE == 0:
                    html += '</table><div style="page-break-before: always;"></div>' + cabecera_tabla_especies()

                link = f"https://iepnb.gob.es/areas-tematicas/especies-silvestres/eidos/{s['id']}"
                # Ancho Y alto fijos: si solo se fija el ancho, cada foto usa
                # su alto natural (muy variable) y la fila se descuadra al
                # paginar el PDF, desplazando los datos a la fila siguiente.
                img_tag = (f'<img src="{s["img"]}" width="110" height="90">'
                           if s["img"] else "<i>Sin foto</i>")

                html += f"""<tr>
                            <td style='text-align:center; vertical-align:middle;'>{img_tag}</td>
                            <td style='text-align:center; vertical-align:middle;'><a href='{link}'>{s['id']}</a></td>
                            <td style='vertical-align:middle;'>{s['vulg']}</td>
                            <td style='vertical-align:middle;'><b>{s['cien']}</b></td>
                            <td style='vertical-align:middle;'><i>{s['grupo']}</i></td>
                        </tr>"""

        html += f"""</table>
            <div class='disclaimer'>
                <b>Nota legal e informativa:</b> Este informe se ha generado mediante herramientas SIG (QGIS) a partir de datos procedentes de servicios web.
                Las fotografías de especies mostradas proceden de la Fototeca del CENEAM y están sujetas a derechos de autor y condiciones de uso específicas.
                El presente documento tiene carácter puramente informativo y no sustituye, en ningún caso, a las certificaciones oficiales emitidas por los organismos competentes.
                La ausencia de registros de especies en el área de estudio no implica necesariamente su ausencia en el territorio, sino la inexistencia de datos georreferenciados
                almacenados en las bases de datos de distribución consultadas a la fecha de generación. Los cálculos de superficie y distancia se han realizado bajo el
                sistema de referencia oficial de España (RD 1071/2007) indicado en la cabecera de este documento.
            </div>

            <div class='footer-logos'>
                <table style='border:none; width:100%;'>
                    <tr style='border:none;'>
                        <td style='border:none; text-align:left; width:50%;'><img src='{logo1_url}' width='{logo1_w}' height='{logo1_h}'></td>
                        <td style='border:none; text-align:right; width:50%;'><img src='{logo2_url}' width='{logo2_w}' height='{logo2_h}'></td>
                    </tr>
                </table>
            </div></body></html>"""

        printer = QPrinter()
        printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
        printer.setOutputFileName(path_pdf)
        doc = QTextDocument()
        doc.setHtml(html)
        # PyQt5 expone el método como 'print_' (alias histórico, 'print' era
        # palabra reservada en Python 2); PyQt6 solo expone 'print'.
        metodo_print = getattr(doc, "print_", None) or getattr(doc, "print")
        metodo_print(printer)
        self.status_lbl.setText("Informe exportado con éxito.")
        self.progress_bar.setVisible(False)
        self.iface.mainWindow().setCursor(Qt.CursorShape.ArrowCursor)
