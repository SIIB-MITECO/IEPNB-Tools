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

import os

# --- CAMBIO PARA COMPATIBILIDAD QGIS 3 Y 4 ---
from qgis.PyQt.QtCore import Qt, QSettings, QUrl, QSize
from qgis.PyQt.QtGui import QIcon, QPixmap, QDesktopServices
from qgis.PyQt.QtWidgets import (QAction, QDockWidget, QTabWidget, QWidget,
                                 QVBoxLayout, QHBoxLayout, QLabel, QPushButton)
# ---------------------------------------------

from qgis.gui import QgsMapTool
from qgis.core import (QgsProject, QgsCoordinateReferenceSystem,
                       QgsCoordinateTransform, QgsRasterLayer)

from .identify import IdentifyTab
from .territory import TerritoryTab
from .species import SpeciesTab
from .services_iepnb import ServicesIEPNBTab
from .ceneam import CeneamTab


# =============================================================================
# CLASE: HERRAMIENTA GOOGLE STREET VIEW
# =============================================================================
class GoogleStreetViewTool(QgsMapTool):
    def __init__(self, canvas):
        super().__init__(canvas)
        self.canvas = canvas
        self.setCursor(Qt.CrossCursor)

    def canvasReleaseEvent(self, event):
        """Se ejecuta al soltar el clic en el mapa."""
        point = self.toMapCoordinates(event.pos())

        crs_src = self.canvas.mapSettings().destinationCrs()
        crs_dest = QgsCoordinateReferenceSystem("EPSG:4326")
        transform = QgsCoordinateTransform(crs_src, crs_dest, QgsProject.instance())
        point_wgs = transform.transform(point)

        lat = point_wgs.y()
        lon = point_wgs.x()
        url = f"http://maps.google.com/maps?q=&layer=c&cbll={lat},{lon}"
        QDesktopServices.openUrl(QUrl(url))


# =============================================================================
# CLASE PRINCIPAL: IEPNB TOOLS
# =============================================================================
class IepnbTools:
    def __init__(self, iface):
        self.iface = iface
        self.dockwidget = None
        self.action = None
        self.plugin_dir = os.path.dirname(__file__)
        self.gsv_tool = None

    def initGui(self):
        icon_path = os.path.join(self.plugin_dir, 'icon.png')
        self.action = QAction(QIcon(icon_path), "IEPNB - Tools v1.0", self.iface.mainWindow())
        self.action.triggered.connect(self.run)

        self.iface.addToolBarIcon(self.action)
        self.iface.addPluginToMenu("&IEPNB - Tools v1.0", self.action)

        self.iface.initializationCompleted.connect(self.restore_ui)

    def unload(self):
        if self.action:
            self.iface.removeToolBarIcon(self.action)
            self.iface.removePluginMenu("&IEPNB - Tools", self.action)
        if self.dockwidget:
            self.store_visibility(self.dockwidget.isVisible())
            self.iface.removeDockWidget(self.dockwidget)
        if self.gsv_tool and self.iface.mapCanvas().mapTool() == self.gsv_tool:
            self.iface.mapCanvas().unsetMapTool(self.gsv_tool)

    def restore_ui(self):
        settings = QSettings()
        was_visible = settings.value("IEPNBTools/visible", False, type=bool)
        if was_visible:
            self.run()

    def store_visibility(self, visible):
        settings = QSettings()
        settings.setValue("IEPNBTools/visible", visible)

    # --- FUNCIONALIDAD: STREET VIEW ---
    def activate_gsv(self):
        if not self.gsv_tool:
            self.gsv_tool = GoogleStreetViewTool(self.iface.mapCanvas())
        self.iface.mapCanvas().setMapTool(self.gsv_tool)
        self.iface.messageBar().pushInfo("IEPNB Tools v1.0", "Haz clic en el mapa para abrir Google Street View")

    # --- FUNCIONALIDAD: CARGAR PNOA Y LIMITES EN GRUPO ---
    def load_reference_layers(self):
        """Carga capas base en un grupo llamado 'Cartografía Base'."""

        # 1. Definición de URIs
        uri_pnoa = (
            "contextualWMSLegend=0&crs=EPSG:3857&dpiMode=7&featureCount=10"
            "&format=image/jpeg&layers=OI.OrthoimageCoverage&styles=default"
            "&tileMatrixSet=GoogleMapsCompatible&url=http://www.ign.es/wmts/pnoa-ma"
        )

        uri_ua = (
            "contextualWMSLegend=0&crs=EPSG:3857&format=image/png"
            "&layers=AU.AdministrativeUnit&styles="
            "&url=https://www.ign.es/wms-inspire/unidades-administrativas"
        )

        # 2. Creación de capas (sin añadir aún)
        layer_pnoa = QgsRasterLayer(uri_pnoa, "Imágenes de satélite Sentinel y ortofotos PNOA    ", "wms")
        layer_ua = QgsRasterLayer(uri_ua, "Unidades Administrativas (IGN)", "wms")

        project = QgsProject.instance()
        root = project.layerTreeRoot()

        # 3. Gestionar el Grupo
        group_name = "Cartografía Base"
        group = root.findGroup(group_name)

        if not group:
            # Si no existe, lo creamos al final
            group = root.addGroup(group_name)
            # Opcional: Mover el grupo al final de la leyenda para que esté abajo
            # root.addChildNode(group.clone())
            # root.removeChildNode(group)
            # (QGIS añade grupos arriba por defecto, si prefieres abajo descomenta lo anterior)

        # 4. Añadir capas al grupo

        # A. Añadir PNOA al grupo
        if layer_pnoa.isValid():
            # Comprobamos si ya existe en el proyecto (por nombre) para no duplicar
            if not project.mapLayersByName("PNOA (Imagen Aérea)"):
                project.addMapLayer(layer_pnoa, False)  # False = Solo registro, no leyenda
                group.addLayer(layer_pnoa)  # Añadir visualmente al grupo

                # Mover PNOA al fondo del grupo (posición final)
                # En grupos pequeños, simplemente añadiéndolo primero suele bastar si insertamos el siguiente encima
        else:
            self.iface.messageBar().pushWarning("IEPNB Tools", "Error al cargar PNOA")

        # B. Añadir UA al grupo (encima del PNOA)
        if layer_ua.isValid():
            if not project.mapLayersByName("Unidades Administrativas (IGN)"):
                project.addMapLayer(layer_ua, False)
                # Insertamos en la posición 0 del grupo (arriba del todo dentro del grupo)
                group.insertLayer(0, layer_ua)
                self.iface.messageBar().pushSuccess("IEPNB Tools", "Capas cargadas en 'Cartografía Base'")
        else:
            self.iface.messageBar().pushWarning("IEPNB Tools", "Error al cargar UA")

            # Expandir el grupo para que el usuario vea que ha pasado algo
            group.setExpanded(True)

            # --- NUEVO CÓDIGO: FORZAR ZOOM A LA EXTENSIÓN DE LA CAPA BASE ---
            if layer_pnoa.isValid() or layer_ua.isValid():
                # Cogemos la extensión del PNOA (o de las Unidades Administrativas si PNOA fallase)
                layer_for_extent = layer_pnoa if layer_pnoa.isValid() else layer_ua

                # Aplicamos esa extensión al lienzo del mapa
                canvas = self.iface.mapCanvas()
                canvas.setExtent(layer_for_extent.extent())
                canvas.refresh()
            # ----------------------------------------------------------------

    def run(self):
        if not self.dockwidget:
            self.dockwidget = QDockWidget("IEPNB - Tools v1.0", self.iface.mainWindow())
            self.dockwidget.setObjectName("IEPNBToolsDockWidget")
            self.dockwidget.visibilityChanged.connect(self.store_visibility)

            main_container = QWidget()
            main_layout = QVBoxLayout()
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
                pix_icon = QPixmap(path_icon).scaledToHeight(24, Qt.SmoothTransformation)
                icon_header_lbl.setPixmap(pix_icon)
            header_layout.addWidget(icon_header_lbl)

            title_lbl = QLabel("IEPNB - Tools v1.0 ")
            title_lbl.setStyleSheet("font-weight: bold; font-size: 10px; color: #333; margin-left: 5px;")
            header_layout.addWidget(title_lbl)
            header_layout.addStretch()
            main_layout.addWidget(header_widget)

            # --- PESTAÑAS ---ºº
            self.tabs = QTabWidget()
            self.tabs.addTab(IdentifyTab(self.iface), "Identificar")
            self.tabs.addTab(TerritoryTab(self.iface), "Buscador")
            self.tabs.addTab(SpeciesTab(self.iface), "Especies")
            self.tabs.addTab(ServicesIEPNBTab(self.iface), "Servicios Web")
            self.tab_ceneam = CeneamTab(self.iface)
            self.tabs.addTab(self.tab_ceneam, "Fototeca CENEAM")
            main_layout.addWidget(self.tabs)

            # --- FOOTER ---
            footer_widget = QWidget()
            footer_widget.setStyleSheet("background-color: white;")
            footer_layout = QHBoxLayout(footer_widget)
            footer_layout.setContentsMargins(15, 8, 15, 8)
            footer_layout.setSpacing(12)

            LOGO_HEIGHT = 36

            # 1. Logo IEPNB
            path_logo1 = os.path.join(self.plugin_dir, 'logo-iepnb.png')
            if os.path.exists(path_logo1):
                lbl1 = QLabel()
                lbl1.setPixmap(QPixmap(path_logo1).scaledToHeight(LOGO_HEIGHT, Qt.SmoothTransformation))
                footer_layout.addWidget(lbl1)
            else:
                footer_layout.addWidget(QLabel("IEPNB"))

            footer_layout.addStretch()

            # --- ESTILO DE BOTONES ---
            btn_style = """
                QPushButton {
                    border: 2px solid #0078d4;
                    border-radius: 6px;
                    background-color: #ffffff;
                    min-width: 40px;
                    min-height: 40px;
                    padding: 0px; /* Quitamos padding para que el icono crezca */
                }
                QPushButton:hover {
                    background-color: #eaf6fd;
                    border-color: #005a9e;
                }
                QPushButton:pressed {
                    background-color: #cfe4fa;
                    border-color: #004578;
                }
            """

            # --- Botón GSV ---
            path_gsv = os.path.join(self.plugin_dir, 'gsv.png')
            btn_gsv = QPushButton()
            btn_gsv.setStyleSheet(btn_style)
            if os.path.exists(path_gsv):
                btn_gsv.setIcon(QIcon(path_gsv))
                btn_gsv.setIconSize(QSize(32, 32))
            else:
                btn_gsv.setText("GSV")
                btn_gsv.setStyleSheet(btn_style + "font-size: 10px;")

            btn_gsv.setToolTip("Activar Google Street View")
            btn_gsv.setCursor(Qt.PointingHandCursor)
            btn_gsv.clicked.connect(self.activate_gsv)
            footer_layout.addWidget(btn_gsv)

            # --- Botón Mapas Base (LOGO GRANDE) ---
            path_base = os.path.join(self.plugin_dir, 'mb.png')
            btn_base = QPushButton()
            btn_base.setStyleSheet(btn_style)

            if os.path.exists(path_base):
                btn_base.setIcon(QIcon(path_base))
                # CAMBIO: Aumentado a 38x38 para llenar el botón de 40x40
                btn_base.setIconSize(QSize(38, 38))
            else:
                btn_base.setText("MAP")
                btn_base.setStyleSheet(btn_style + "font-weight: bold; color: #0078d4; font-size: 10px;")

            btn_base.setToolTip("Cargar Cartografía Base (PNOA + Límites)")
            btn_base.setCursor(Qt.PointingHandCursor)
            btn_base.clicked.connect(self.load_reference_layers)
            footer_layout.addWidget(btn_base)

            footer_layout.addStretch()

            # 2. Logo Ministerio
            path_logo2 = os.path.join(self.plugin_dir, 'minis.png')
            if not os.path.exists(path_logo2):
                path_logo2 = os.path.join(self.plugin_dir, 'minis.jpg')

            if os.path.exists(path_logo2):
                lbl2 = QLabel()
                lbl2.setPixmap(QPixmap(path_logo2).scaledToHeight(LOGO_HEIGHT, Qt.SmoothTransformation))
                footer_layout.addWidget(lbl2)
            else:
                footer_layout.addWidget(QLabel("MITECO"))

            main_layout.addWidget(footer_widget)
            main_container.setLayout(main_layout)
            self.dockwidget.setWidget(main_container)

            self.iface.addDockWidget(Qt.RightDockWidgetArea, self.dockwidget)

        self.dockwidget.show()
        self.store_visibility(True)
