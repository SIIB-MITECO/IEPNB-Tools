import os
from functools import partial

# --- COMPATIBILIDAD QGIS 3 Y 4 ---
from qgis.PyQt.QtCore import Qt, QUrl, QSize
from qgis.PyQt.QtGui import QIcon, QPixmap, QDesktopServices
from qgis.PyQt.QtWidgets import (QAction, QDockWidget, QTabWidget, QWidget,
                                 QVBoxLayout, QHBoxLayout, QLabel, QPushButton)
# ---------------------------------

from qgis.gui import QgsMapTool
from qgis.core import (QgsProject, QgsCoordinateReferenceSystem,
                       QgsCoordinateTransform, QgsRasterLayer)

from .identify import IdentifyTab
from .territory import TerritoryTab
from .species import SpeciesTab
from .services_iepnb import ServicesIEPNBTab
from .ceneam import CeneamTab
from .config import CATALOGO_WMS


class GoogleStreetViewTool(QgsMapTool):
    def __init__(self, canvas):
        super().__init__(canvas)
        self.canvas = canvas
        self.setCursor(Qt.CrossCursor)

    def canvasReleaseEvent(self, event):
        point = self.toMapCoordinates(event.pos())
        crs_src = self.canvas.mapSettings().destinationCrs()
        crs_dest = QgsCoordinateReferenceSystem("EPSG:4326")
        transform = QgsCoordinateTransform(crs_src, crs_dest, QgsProject.instance())
        point_wgs = transform.transform(point)
        url = f"https://www.google.com/maps/@?api=1&map_action=pano&viewpoint={point_wgs.y()},{point_wgs.x()}"
        QDesktopServices.openUrl(QUrl(url))


class IepnbTools:
    def __init__(self, iface):
        self.iface = iface
        self.dockwidget = None
        self.plugin_dir = os.path.dirname(__file__)
        self.gsv_tool = None

    def initGui(self):
        icon_path = os.path.join(self.plugin_dir, 'icon.png')
        self.action = QAction(QIcon(icon_path), "IEPNB - Tools v1.1.0", self.iface.mainWindow())
        self.action.triggered.connect(self.run)
        self.iface.addToolBarIcon(self.action)
        self.iface.addPluginToMenu("&IEPNB - Tools v1.1.0", self.action)

    def unload(self):
        if self.action:
            self.iface.removeToolBarIcon(self.action)
            self.iface.removePluginMenu("&IEPNB - Tools v1.1.0", self.action)
        if self.dockwidget:
            self.iface.removeDockWidget(self.dockwidget)

    def reset_map_cursor(self):
        """Devuelve el cursor al estado de navegación estándar de QGIS"""
        self.iface.actionPan().trigger()

    def run(self):
        if not self.dockwidget:
            self.dockwidget = QDockWidget("IEPNB - Tools v1.1.0", self.iface.mainWindow())
            self.dockwidget.setObjectName("IEPNBToolsDockWidget")

            self.gsv_tool = GoogleStreetViewTool(self.iface.mapCanvas())

            main_container = QWidget()
            main_layout = QVBoxLayout(main_container)
            main_layout.setContentsMargins(0, 0, 0, 0)
            main_layout.setSpacing(0)

            # --- HEADER ---
            header_widget = QWidget()
            header_widget.setStyleSheet("background-color: #f8f9fa; border-bottom: 1px solid #ddd;")
            header_layout = QHBoxLayout(header_widget)
            header_layout.setContentsMargins(10, 5, 10, 5)

            icon_header_lbl = QLabel()
            path_icon = os.path.join(self.plugin_dir, 'icon.png')
            if os.path.exists(path_icon):
                icon_header_lbl.setPixmap(QPixmap(path_icon).scaledToHeight(24, Qt.SmoothTransformation))
            header_layout.addWidget(icon_header_lbl)

            title_lbl = QLabel("IEPNB - Tools v1.1.0")
            title_lbl.setStyleSheet("font-weight: bold; font-size: 10px; color: #333; margin-left: 5px;")
            header_layout.addWidget(title_lbl)
            header_layout.addStretch()
            main_layout.addWidget(header_widget)

            # --- TABS ---
            self.tabs = QTabWidget()
            self.tabs.addTab(IdentifyTab(self.iface), "Identificar")
            self.tabs.addTab(TerritoryTab(self.iface), "Buscador")
            self.tabs.addTab(SpeciesTab(self.iface), "Especies")
            self.tabs.addTab(ServicesIEPNBTab(self.iface), "Servicios Web")
            self.tabs.addTab(CeneamTab(self.iface), "Fototeca CENEAM")

            # Conectamos el cambio de pestaña al reset del cursor
            self.tabs.currentChanged.connect(self.reset_map_cursor)

            main_layout.addWidget(self.tabs)

            # --- FOOTER ---
            footer_widget = QWidget()
            footer_layout = QVBoxLayout(footer_widget)
            footer_layout.setContentsMargins(5, 10, 5, 10)
            footer_layout.setSpacing(15)

            buttons_row = QHBoxLayout()
            buttons_row.setSpacing(2)  # Espaciado un poco más estrecho para que quepa todo bien
            buttons_row.setAlignment(Qt.AlignCenter)

            btn_style = """
                QPushButton { border: 1px solid #0078d4; border-radius: 4px; background-color: white; padding: 0px; }
                QPushButton:hover { background-color: #f0f7ff; border-width: 2px; }
            """

            # Lista actualizada con CEA.png
            configs = [
                ("BDN.png", "Banco de Datos de la Naturaleza",
                 ["Espacios Protegidos - IEPNB", "Convenios Internacionales - IEPNB", "MFE (Foto Fija)",
                  "EIKOS - Alertas Anuales (IEPNB)", "EIKOS - Alertas Mensuales (IEPNB)"],
                 "Espacios Naturales Protegidos (ENP)"),
                ("SNCZI.png", "SN Cartografía de Zonas Inundables", "MITECO - SNCZI - Inundabilidad", "Áreas con riesgo potencial significativo de inundación (ARPSI)"),
                ("SIR.png", "Sistema de Información de Redes - DGA", "MITECO - Agua (DGA)", "Ríos (Pfafstetter)"),
                ("COSTAS.png", "Costas", "MITECO - Costas (DGC)", "Dominio Público Marítimo-Terrestre"),
                ("CEA.png", "Calidad y Evaluación Ambiental", "MITECO - Calidad y Evaluación Ambiental", "Red de Estaciones de Calidad del Aire"),
                ("RD.png", "Reto Demográfico", "MITECO - Agua (DGA)", "Registro de Aguas"),
                ("mb.png", "Cartografía Base", "MAPA_BASE", None),
                ("gsv.png", "Street View", "GSV", None)
            ]

            for icon_name, tip, keys, priority_layer in configs:
                btn = QPushButton()

                # Tamaño de botón estándar (44px para que no sea gigante)
                btn.setFixedSize(44, 44)

                # Lógica de tamaño de PNG aumentado (excepto gsv)
                if icon_name != "gsv.png":
                    icon_display_size = QSize(38, 38)  # PNG Grande
                else:
                    icon_display_size = QSize(30, 30)  # PNG Discreto para Street View

                btn.setStyleSheet(btn_style)
                btn.setToolTip(tip)

                path = os.path.join(self.plugin_dir, icon_name)
                if not os.path.exists(path):
                    path = os.path.join(self.plugin_dir, "icons", icon_name)

                if os.path.exists(path):
                    btn.setIcon(QIcon(path))
                    btn.setIconSize(icon_display_size)
                else:
                    btn.setText(icon_name[:2])

                if keys == "MAPA_BASE":
                    btn.clicked.connect(self.load_reference_layers)
                elif keys == "GSV":
                    btn.clicked.connect(self.activate_gsv)
                else:
                    sub_group = "Banco de Datos de la Naturaleza (BDN) - IEPNB" if icon_name == "BDN.png" else None
                    btn.clicked.connect(
                        partial(self.load_multiple_categories, keys, priority_layer, "Servicios MITECO", sub_group))

                buttons_row.addWidget(btn)

            footer_layout.addLayout(buttons_row)

            # LOGOS
            logos_row = QHBoxLayout()
            logos_row.setAlignment(Qt.AlignCenter)
            logos_row.setSpacing(20)

            for logo_file in ['logo-iepnb.png', 'minis.png']:
                path = os.path.join(self.plugin_dir, logo_file)
                if os.path.exists(path):
                    lbl = QLabel()
                    pixmap = QPixmap(path)

                    if not pixmap.isNull() and pixmap.height() > 0:
                        alto_deseado = 30
                        ratio = alto_deseado / pixmap.height()
                        ancho_proporcional = int(pixmap.width() * ratio)

                        lbl.setFixedSize(ancho_proporcional, alto_deseado)
                        lbl.setPixmap(pixmap)
                        lbl.setScaledContents(True)

                    logos_row.addWidget(lbl)

            footer_layout.addLayout(logos_row)
            main_layout.addWidget(footer_widget)

            self.dockwidget.setWidget(main_container)
            self.iface.addDockWidget(Qt.RightDockWidgetArea, self.dockwidget)

        self.dockwidget.show()
        # Forzamos el cursor al abrir el plugin
        self.reset_map_cursor()

    # --- Los demás métodos se mantienen iguales ---
    def load_reference_layers(self):
        # Definimos los nombres en variables para no fallar
        nombre_pnoa = "Ortoimágenes de España (Sentinel2 y ortofotos del PNOA MA)"
        nombre_ua = "Unidades Administrativas (IGN)"

        uri_pnoa = "contextualWMSLegend=0&crs=EPSG:3857&dpiMode=7&featureCount=10&format=image/jpeg&layers=OI.OrthoimageCoverage&styles=default&tileMatrixSet=GoogleMapsCompatible&url=http://www.ign.es/wmts/pnoa-ma"
        uri_ua = "contextualWMSLegend=0&crs=EPSG:3857&format=image/png&layers=AU.AdministrativeUnit&styles=&url=https://www.ign.es/wms-inspire/unidades-administrativas"

        # Creamos los objetos de capa con los nombres de las variables
        layer_pnoa = QgsRasterLayer(uri_pnoa, nombre_pnoa, "wms")
        layer_ua = QgsRasterLayer(uri_ua, nombre_ua, "wms")

        project = QgsProject.instance()
        root = project.layerTreeRoot()
        group = root.findGroup("Cartografía Base") or root.addGroup("Cartografía Base")

        # Ahora la comprobación sí encontrará el nombre correcto
        if layer_pnoa.isValid() and not project.mapLayersByName(nombre_pnoa):
            project.addMapLayer(layer_pnoa, False)
            group.addLayer(layer_pnoa)

        if layer_ua.isValid() and not project.mapLayersByName(nombre_ua):
            project.addMapLayer(layer_ua, False)
            group.insertLayer(0, layer_ua)
            self.iface.mapCanvas().setExtent(layer_ua.extent())
            self.iface.mapCanvas().refresh()

    def activate_gsv(self):
        if self.gsv_tool:
            self.iface.mapCanvas().setMapTool(self.gsv_tool)

    def load_multiple_categories(self, categories, visible_layer_name=None, main_group_name="Servicios MITECO",
                                 sub_group_name=None):
        if isinstance(categories, str):
            categories = [categories]
        root = QgsProject.instance().layerTreeRoot()
        parent_group = root.findGroup(main_group_name) or root.insertGroup(0, main_group_name)
        target_group = parent_group
        if sub_group_name:
            target_group = parent_group.findGroup(sub_group_name) or parent_group.insertGroup(0, sub_group_name)
        accion_borrar = bool(target_group.findGroup(categories[0]))
        for cat in categories:
            self.load_wms_category_into_group(cat, target_group, visible_layer_name, force_remove=accion_borrar)
        if accion_borrar:
            if sub_group_name and not target_group.children():
                parent_group.removeChildNode(target_group)
            if not parent_group.children():
                root.removeChildNode(parent_group)
        else:
            target_group.setExpanded(False)
            parent_group.setExpanded(True)

    def load_wms_category_into_group(self, category_name, parent_group_obj, visible_layer_name=None,
                                     force_remove=False):
        if category_name not in CATALOGO_WMS:
            return
        group = parent_group_obj.findGroup(category_name)
        if group and force_remove:
            parent_group_obj.removeChildNode(group)
            self._recursive_cleanup(CATALOGO_WMS[category_name])
            return
        if not group:
            group = parent_group_obj.insertGroup(0, category_name)
            group.setExpanded(False)
            self._recursive_layer_loader(CATALOGO_WMS[category_name], group, visible_layer_name)

    def _recursive_layer_loader(self, data_dict, parent_group, visible_layer_name):
        project = QgsProject.instance()
        for name, content in data_dict.items():
            if isinstance(content, dict) and "url" in content:
                url, layers = content["url"], content["layers"]
                srv_type = content.get("type", "wms")
                uri = f"layers={layers}&styles=&url={url}" if srv_type == "wmts" else f"contextualWMSLegend=0&crs=EPSG:3857&format=image/png&layers={layers}&styles=&url={url}"
                lyr = QgsRasterLayer(uri, name, "wms")
                if lyr.isValid():
                    if any(x in name for x in ["SNCZI", "Riesgo", "Peligrosidad", "Inundación"]):
                        lyr.setOpacity(0.7)
                    project.addMapLayer(lyr, False)
                    node = parent_group.addLayer(lyr)
                    node.setExpanded(False)
                    node.setItemVisibilityChecked(name == visible_layer_name)
            elif isinstance(content, dict):
                sub = parent_group.addGroup(name)
                sub.setExpanded(False)
                self._recursive_layer_loader(content, sub, visible_layer_name)

    def _recursive_cleanup(self, data_dict):
        project = QgsProject.instance()
        for name, content in data_dict.items():
            if isinstance(content, dict) and "url" in content:
                for lyr in project.mapLayersByName(name):
                    project.removeMapLayer(lyr.id())
            elif isinstance(content, dict):
                self._recursive_cleanup(content)
