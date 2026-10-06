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

from qgis.PyQt.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                                 QLineEdit, QTreeWidget, QTreeWidgetItem,
                                 QPushButton, QMenu)
from qgis.PyQt.QtCore import Qt

from qgis.core import (QgsApplication, QgsProject, QgsRasterLayer,
                       QgsMessageLog, Qgis, QgsSettings)

from .config import CATALOGO_WMS as CATALOGO_SERVICIOS


CLAVE_FAVORITOS = "IEPNB_Tools/servicios_favoritos"
ROL_RUTA = Qt.ItemDataRole.UserRole + 1  # ruta única de la capa dentro del catálogo
TXT_FAVORITOS = "⭐ Favoritos"


class ServicesIEPNBTab(QWidget):
    def __init__(self, iface):
        super().__init__()
        self.iface = iface
        self.group_name_wms = "Servicios Web"
        self._items_catalogo = {}    # ruta -> item de la capa en el árbol principal
        self._favoritos = self._leer_favoritos()
        self.fav_root = None

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
        self.tree.currentItemChanged.connect(self._actualizar_boton_favorito)
        self.tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self._menu_contextual)
        layout.addWidget(self.tree)

        btn_layout = QHBoxLayout()
        self.btn_add = QPushButton("Añadir al Mapa")
        self.btn_add.setStyleSheet("background-color: #2b8cbe; color: white; font-weight: bold;")
        self.btn_add.clicked.connect(self.add_selected_service)

        self.btn_del = QPushButton("Eliminar")
        self.btn_del.clicked.connect(self.delete_selected_service)

        self.btn_fav = QPushButton("☆ Favorito")
        self.btn_fav.setEnabled(False)
        self.btn_fav.clicked.connect(lambda: self.alternar_favorito())

        btn_layout.addWidget(self.btn_add)
        btn_layout.addWidget(self.btn_del)
        btn_layout.addWidget(self.btn_fav)
        layout.addLayout(btn_layout)

        self.status_lbl = QLabel("Selecciona un servicio.")
        layout.addWidget(self.status_lbl)

        self.populate_tree()

    def populate_tree(self):
        self.tree.clear()
        self._items_catalogo = {}

        # Grupo de favoritos siempre arriba del todo
        self.fav_root = QTreeWidgetItem(self.tree.invisibleRootItem())
        self.fav_root.setText(0, TXT_FAVORITOS)
        fuente = self.fav_root.font(0)
        fuente.setBold(True)
        self.fav_root.setFont(0, fuente)
        self.fav_root.setFlags(self.fav_root.flags() & ~Qt.ItemFlag.ItemIsSelectable)

        # Llamamos a la función recursiva empezando desde la raíz
        self._add_items_recursively(self.tree.invisibleRootItem(), CATALOGO_SERVICIOS)
        self._refrescar_favoritos()

    def _add_items_recursively(self, parent_item, data_dict, ruta_padre=""):
        for key, value in data_dict.items():
            item = QTreeWidgetItem(parent_item)
            item.setText(0, key)
            ruta = f"{ruta_padre} › {key}" if ruta_padre else key

            # Si el valor tiene una "url", es una CAPA FINAL
            if isinstance(value, dict) and "url" in value:
                datos = value
                # Detectamos el icono según sea WMS o WMTS
                icon_type = '/mIconWms.svg' if datos.get("type", "wms") == "wms" else '/mIconWmts.svg'
                item.setIcon(0, QgsApplication.getThemeIcon(icon_type))
                item.setData(0, Qt.ItemDataRole.UserRole, datos)
                item.setData(0, ROL_RUTA, ruta)
                self._items_catalogo[ruta] = item

            # Si el valor es otro diccionario, es un SUBGRUPO
            elif isinstance(value, dict):
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsSelectable)  # No se puede añadir al mapa directamente
                self._add_items_recursively(item, value, ruta)  # Bajamos un nivel más

    def filter_tree(self, text):
        search_text = text.lower().strip()
        root = self.tree.invisibleRootItem()

        if not search_text:
            for i in range(root.childCount()):
                parent = root.child(i)
                parent.setHidden(False)
                parent.setExpanded(parent is self.fav_root)  # favoritos siempre a la vista
                for j in range(parent.childCount()):
                    parent.child(j).setHidden(False)
            return

        # Mientras se busca se oculta el grupo de favoritos para no duplicar resultados
        self.fav_root.setHidden(True)

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
            if root.child(i) is not self.fav_root:
                check_item(root.child(i))

    # ------------------------------------------------------------------
    # Favoritos (se guardan en la configuración de QGIS del usuario)
    # ------------------------------------------------------------------

    def _leer_favoritos(self):
        valor = QgsSettings().value(CLAVE_FAVORITOS, [])
        if isinstance(valor, str):
            valor = [valor] if valor else []
        return [v for v in (valor or []) if isinstance(v, str)]

    def _guardar_favoritos(self):
        QgsSettings().setValue(CLAVE_FAVORITOS, list(self._favoritos))

    def _refrescar_favoritos(self):
        """Reconstruye el grupo ⭐ Favoritos y marca en negrita, dentro del
        catálogo, las capas favoritas. Los favoritos que ya no existan en el
        catálogo (por una actualización del plugin) simplemente no se muestran."""
        self.fav_root.takeChildren()

        for ruta, item in self._items_catalogo.items():
            fuente = item.font(0)
            fuente.setBold(ruta in self._favoritos)
            item.setFont(0, fuente)

        vigentes = [r for r in self._favoritos if r in self._items_catalogo]
        for ruta in vigentes:
            original = self._items_catalogo[ruta]
            copia = QTreeWidgetItem(self.fav_root)
            copia.setText(0, original.text(0))
            copia.setIcon(0, original.icon(0))
            copia.setData(0, Qt.ItemDataRole.UserRole, original.data(0, Qt.ItemDataRole.UserRole))
            copia.setData(0, ROL_RUTA, ruta)
            copia.setToolTip(0, ruta)  # de qué grupo del catálogo viene

        if not vigentes:
            vacio = QTreeWidgetItem(self.fav_root)
            vacio.setText(0, "Aún no hay favoritos: selecciona una capa y pulsa ☆ Favorito")
            vacio.setFlags(vacio.flags() & ~Qt.ItemFlag.ItemIsSelectable)
            fuente = vacio.font(0)
            fuente.setItalic(True)
            vacio.setFont(0, fuente)

        self.fav_root.setExpanded(True)

    def _actualizar_boton_favorito(self, actual=None, _anterior=None):
        ruta = actual.data(0, ROL_RUTA) if actual else None
        self.btn_fav.setEnabled(bool(ruta))
        if ruta and ruta in self._favoritos:
            self.btn_fav.setText("★ Favorito")
            self.btn_fav.setToolTip("Quitar de favoritos")
        else:
            self.btn_fav.setText("☆ Favorito")
            self.btn_fav.setToolTip("Añadir a favoritos")

    def alternar_favorito(self, ruta=None):
        if not ruta:
            item = self.tree.currentItem()
            ruta = item.data(0, ROL_RUTA) if item else None
        if not ruta or ruta not in self._items_catalogo:
            return

        nombre = self._items_catalogo[ruta].text(0)
        if ruta in self._favoritos:
            self._favoritos.remove(ruta)
            self.status_lbl.setText(f"☆ Quitado de favoritos: {nombre}")
        else:
            self._favoritos.append(ruta)
            self.status_lbl.setText(f"⭐ Añadido a favoritos: {nombre}")
        self._guardar_favoritos()
        self._refrescar_favoritos()
        self._actualizar_boton_favorito(self.tree.currentItem())

    def _menu_contextual(self, posicion):
        item = self.tree.itemAt(posicion)
        ruta = item.data(0, ROL_RUTA) if item else None
        if not ruta:
            return
        self.tree.setCurrentItem(item)

        menu = QMenu(self)
        menu.addAction("Añadir al mapa").triggered.connect(lambda: self.add_selected_service())
        texto_fav = "★ Quitar de favoritos" if ruta in self._favoritos else "☆ Añadir a favoritos"
        menu.addAction(texto_fav).triggered.connect(lambda: self.alternar_favorito(ruta))
        menu.exec(self.tree.viewport().mapToGlobal(posicion))

    def add_selected_service(self):
        item = self.tree.currentItem()
        if not item or not item.data(0, Qt.ItemDataRole.UserRole):
            return

        data = item.data(0, Qt.ItemDataRole.UserRole)

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

        # --- 1. ASIGNACIÓN DE CRS INTELIGENTE ---
        if "geoville" in base_url or "eea.europa" in base_url:
            crs_code = "EPSG:3857"
        elif "mapama.gob.es" in base_url or "idee.es" in base_url:
            crs_code = "EPSG:25830"
        else:
            crs_code = "EPSG:4326"

        # --- 2. EL AJUSTE DEL ESTILO (La clave del éxito) ---
        # Si el config.py dice "default", lo convertimos a cadena vacía
        # para que la URI final quede como '&styles&', igual que el QGIS nativo.
        if style_name == "default":
            style_name = ""

        # --- 3. CONSTRUCCIÓN DE LA URI EXACTA ---
        if srv_type == "wmts":
            uri = f"layers={layer_name}&styles={style_name}&url={base_url}"
        else:
            # Replicamos fielmente la cadena que funcionó en la consola
            uri = f"contextualWMSLegend=0&crs={crs_code}&dpiMode=7&featureCount=10&format=image/png&layers={layer_name}&styles={style_name}&tilePixelRatio=0&url={base_url}"

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
            QgsMessageLog.logMessage(f"Fallo al cargar: {uri}", "IEPNB Tools", Qgis.MessageLevel.Warning)

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
