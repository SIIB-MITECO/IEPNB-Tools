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

# --- IMPORTACIONES LIMPIAS Y EXPLÍCITAS ---
from qgis.PyQt.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                                 QLineEdit, QTreeWidget, QTreeWidgetItem,
                                 QPushButton)
from qgis.PyQt.QtCore import Qt
# ---------------------------------------------

from qgis.core import (QgsApplication, QgsProject, QgsRasterLayer,
                       QgsMessageLog, Qgis)

from .config import CATALOGO_WMS as CATALOGO_SERVICIOS


class ServicesIEPNBTab(QWidget):
    def __init__(self, iface):
        super().__init__()
        self.iface = iface
        self.group_name_wms = "Servicios Web"

        layout = QVBoxLayout(self)

        search_layout = QHBoxLayout()
        lbl_search = QLabel("🔍")
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Filtrar servicios...")
        self.search_bar.textChanged.connect(self.filter_tree)
        search_layout.addWidget(lbl_search)
        search_layout.addWidget(self.search_bar)
        layout.addLayout(search_layout)

        self.tree = QTreeWidget()
        self.tree.setHeaderHidden(True)
        self.tree.itemDoubleClicked.connect(self.add_selected_service)
        layout.addWidget(self.tree)

        btn_layout = QHBoxLayout()
        self.btn_add = QPushButton("Añadir al Mapa")
        self.btn_add.setStyleSheet("background-color: #2b8cbe; color: white; font-weight: bold;")
        self.btn_add.clicked.connect(self.add_selected_service)

        self.btn_del = QPushButton("Eliminar")
        self.btn_del.clicked.connect(self.delete_selected_service)

        btn_layout.addWidget(self.btn_add)
        btn_layout.addWidget(self.btn_del)
        layout.addLayout(btn_layout)

        self.status_lbl = QLabel("Selecciona un servicio.")
        layout.addWidget(self.status_lbl)

        self.populate_tree()

    def populate_tree(self):
        self.tree.clear()
        # Llamamos a la función recursiva empezando desde la raíz
        self._add_items_recursively(self.tree.invisibleRootItem(), CATALOGO_SERVICIOS)

    def _add_items_recursively(self, parent_item, data_dict):
        for key, value in data_dict.items():
            item = QTreeWidgetItem(parent_item)
            item.setText(0, key)

            # Si el valor tiene una "url", es una CAPA FINAL
            if isinstance(value, dict) and "url" in value:
                datos = value
                # Detectamos el icono según sea WMS o WMTS
                icon_type = '/mIconWms.svg' if datos.get("type", "wms") == "wms" else '/mIconWmts.svg'
                item.setIcon(0, QgsApplication.getThemeIcon(icon_type))
                item.setData(0, Qt.UserRole, datos)

            # Si el valor es otro diccionario, es un SUBGRUPO
            elif isinstance(value, dict):
                item.setFlags(item.flags() & ~Qt.ItemIsSelectable)  # No se puede añadir al mapa directamente
                self._add_items_recursively(item, value)  # Bajamos un nivel más

    def filter_tree(self, text):
        search_text = text.lower().strip()
        root = self.tree.invisibleRootItem()

        if not search_text:
            for i in range(root.childCount()):
                parent = root.child(i)
                parent.setHidden(False)
                parent.setExpanded(False)
                for j in range(parent.childCount()):
                    parent.child(j).setHidden(False)
            return

        def check_item(item):
            match = search_text in item.text(0).lower()
            has_matching_child = False

            for i in range(item.childCount()):
                if check_item(item.child(i)):
                    has_matching_child = True

            item.setHidden(not (match or has_matching_child))

            if has_matching_child:
                item.setExpanded(True)

            return match or has_matching_child

        for i in range(root.childCount()):
            check_item(root.child(i))

    def add_selected_service(self):
        item = self.tree.currentItem()
        if not item or not item.data(0, Qt.UserRole):
            return

        data = item.data(0, Qt.UserRole)

        # 1. Extraemos el estilo de config.py si existe (si no, queda vacío "")
        style_name = data.get("styles", "")

        # 2. Se lo pasamos como quinto parámetro a la función de carga
        self.load_service_layer(
            data["url"],
            data["layers"],
            item.text(0),
            data.get("type", "wms"),
            style_name  # <-- Aquí pasamos el estilo
        )

    def load_service_layer(self, url, layer_name, title, srv_type, style_name=""):
        base_url = url.split('?')[0]
        if "geoville" in base_url or "eea.europa" in base_url:
            crs_code = "EPSG:3857"
        else:
            crs_code = "EPSG:4326"

        if srv_type == "wmts":
            uri = f"layers={layer_name}&styles={style_name}&url={base_url}"
        else:
            # Añadimos explícitamente el style_name mapeado
            uri = f"contextualWMSLegend=0&crs={crs_code}&dpiMode=7&featureCount=10&format=image/png&layers={layer_name}&styles={style_name}&url={base_url}"

        rlayer = QgsRasterLayer(uri, title, "wms")

        if rlayer.isValid():
            rlayer.setOpacity(0.65)
            root = QgsProject.instance().layerTreeRoot()
            group = root.findGroup(self.group_name_wms) or root.insertGroup(0, self.group_name_wms)
            QgsProject.instance().addMapLayer(rlayer, False)
            group.addLayer(rlayer)
            node = group.findLayer(rlayer.id())
            if node:
                node.setExpanded(False)
            self.status_lbl.setText(f"✅ Cargado: {title}")
        else:
            self.status_lbl.setText(f"❌ Error al cargar {title}")
            QgsMessageLog.logMessage(f"Fallo al cargar: {uri}", "IEPNB Tools", Qgis.Warning)

    def delete_selected_service(self):
        item = self.tree.currentItem()
        if not item:
            return

        group = QgsProject.instance().layerTreeRoot().findGroup(self.group_name_wms)
        if group:
            for child in group.children():
                if child.name() == item.text(0):
                    QgsProject.instance().removeMapLayer(child.layerId())
                    self.status_lbl.setText(f"🗑️ Eliminado: {item.text(0)}")
