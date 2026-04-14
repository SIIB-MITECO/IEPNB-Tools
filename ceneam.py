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

import webbrowser
import re

# --- CAMBIO PARA COMPATIBILIDAD QGIS 3 Y 4 ---
from qgis.PyQt.QtWidgets import *
from qgis.PyQt.QtCore import QUrl, Qt
from qgis.PyQt.QtGui import QPixmap
from qgis.PyQt.QtNetwork import QNetworkRequest
# ---------------------------------------------

from qgis.core import QgsNetworkAccessManager
from .species import ImageLoader

class CeneamTab(QWidget):
    def __init__(self, iface):
        super().__init__()
        self.iface = iface
        self.base_url = "https://www.miteco.gob.es"
        self.search_url_base = "https://www.miteco.gob.es/es/ceneam/centro-de-documentacion-ceneam/fototeca/fototeca-ceneam.html?view=imagenes&fulltext="

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)

        header = QLabel("Fototeca CENEAM (MITECO)")
        header.setStyleSheet("font-weight: bold; font-size: 13px; color: #1b5e20; margin-bottom: 5px;")
        layout.addWidget(header)

        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Ej: degaña, lince, doñana...")
        self.search_input.returnPressed.connect(self.run_search)

        btn_search = QPushButton("🔍 Buscar")
        btn_search.clicked.connect(self.run_search)

        search_layout.addWidget(self.search_input)
        search_layout.addWidget(btn_search)
        layout.addLayout(search_layout)

        self.counter_label = QLabel("")
        self.counter_label.setStyleSheet("color: #666; font-size: 11px; margin: 5px 0px;")
        layout.addWidget(self.counter_label)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet("QScrollArea { border: none; background-color: #f5f5f5; }")

        self.container = QWidget()
        self.results_layout = QVBoxLayout(self.container)
        self.results_layout.setAlignment(Qt.AlignTop)
        self.scroll.setWidget(self.container)
        layout.addWidget(self.scroll)

        disclaimer = QLabel(
            "© Imágenes propiedad del CENEAM - Ministerio para la Transición Ecológica y el Reto Demográfico. "
            "Su uso está sujeto a las condiciones de la Fototeca CENEAM."
        )
        disclaimer.setWordWrap(True)
        disclaimer.setStyleSheet("""
            font-style: italic; 
            font-size: 10px; 
            color: #7f8c8d; 
            padding: 8px; 
            background-color: #fdfdfd; 
            border-top: 1px solid #ddd;
        """)
        layout.addWidget(disclaimer)

    def run_search(self):
        query_raw = self.search_input.text().strip()
        if not query_raw:
            return

        trans_tab = str.maketrans("áéíóúüÁÉÍÓÚÜ", "aeiouuAEIOUU")
        query_clean = query_raw.translate(trans_tab).lower()

        if hasattr(self, 'reply') and self.reply and self.reply.isRunning():
            self.reply.abort()

        self.clear_results()
        self.counter_label.setText(f"🔍 Buscando '{query_clean}'...")

        url = self.search_url_base + query_clean
        request = QNetworkRequest(QUrl(url))
        request.setHeader(QNetworkRequest.UserAgentHeader, "Mozilla/5.0")

        self.nam = QgsNetworkAccessManager.instance()
        self.reply = self.nam.get(request)
        self.reply.finished.connect(self.process_html_results)

    def clear_results(self):
        while self.results_layout.count():
            item = self.results_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def process_html_results(self):
        self.clear_results()

        if self.reply.error() != 0:
            self.counter_label.setText("❌ Error en la conexión.")
            return

        html = self.reply.readAll().data().decode('utf-8', errors='ignore').replace('\n', ' ').replace('\r', ' ')
        bloques = re.split(r'<div[^>]*class=["\'][^"\']*cmp-image[^"\']*["\'][^>]*>', html)
        bloques = bloques[1:]

        urls_procesadas = set()
        count = 0

        for b in bloques:
            img_m = re.search(r'src=["\'](/content/dam/fototeca/imagenes/.*?\.(?:jpg|jpeg|png))["\']', b, re.I)
            if not img_m:
                continue

            full_img_url = self.base_url + img_m.group(1)

            if full_img_url in urls_procesadas:
                continue

            urls_procesadas.add(full_img_url)
            count += 1

            def get_val(label):
                p = rf'{label}</span>.*?t2["\']>([\s\S]*?)</span>'
                m = re.search(p, b, re.I)
                return m.group(1).strip() if m else ""

            titulo = get_val("Título")
            if not titulo:
                alt_m = re.search(r'alt=["\'](.*?)["\']', b, re.I)
                titulo = alt_m.group(1).strip() if alt_m else "Fotografía CENEAM"

            autor = get_val("Autor")
            prov = get_val("Provincia")
            sci = get_val("Nombre científico")

            self.add_card(titulo, autor, prov, sci, full_img_url)

        if count > 0:
            self.counter_label.setText(f"✅ Se han encontrado {count} imágenes.")
        else:
            self.counter_label.setText("❌ No se han encontrado resultados.")
            self.results_layout.addWidget(QLabel("Prueba con otros términos."))

        self.results_layout.addStretch()

    def add_card(self, title, author, prov, sci, img_url):
        original_url = img_url.split('.thumb')[0]
        card = QFrame()
        card.setStyleSheet(
            "QFrame { background-color: white; border: 1px solid #d0d0d0; border-radius: 4px; margin-bottom: 8px; }")

        v = QVBoxLayout(card)
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(0)

        img = ImageLoader(img_url)
        img.setAlignment(Qt.AlignCenter)
        v.addWidget(img, 0, Qt.AlignCenter)

        text_container = QWidget()
        text_v = QVBoxLayout(text_container)
        text_v.setContentsMargins(10, 5, 10, 8)

        t = QLabel(title.upper())
        t.setWordWrap(True)
        t.setStyleSheet("font-weight: bold; color: #1b5e20; font-size: 11px; border: none;")
        text_v.addWidget(t)

        info = f"📷 {author}"
        if prov:
            info += f"  |  📍 {prov}"
        i = QLabel(info)
        i.setStyleSheet("color: #666; font-size: 9px; border: none;")
        text_v.addWidget(i)

        btn_layout = QHBoxLayout()
        btn_style = "QPushButton { font-size: 10px; padding: 5px; background: #ffffff; border: 1px solid #ccc; border-radius: 12px; } QPushButton:hover { background: #f2f2f2; }"

        btn_view = QPushButton("👁️ Ver Original")
        btn_view.setStyleSheet(btn_style)
        btn_view.clicked.connect(lambda: webbrowser.open(original_url))

        btn_save = QPushButton("💾 Descargar")
        btn_save.setStyleSheet(btn_style.replace("#ffffff", "#f0f4f7"))
        btn_save.clicked.connect(lambda: self.download_image(original_url, title))

        btn_layout.addWidget(btn_view)
        btn_layout.addWidget(btn_save)
        text_v.addLayout(btn_layout)

        v.addWidget(text_container)
        self.results_layout.addWidget(card)

    def download_image(self, url, title):
        filename = "".join([c for c in title if c.isalnum() or c in (' ', '_')]).rstrip()
        filename = (filename[:50] + ".jpg") if filename else "foto_ceneam.jpg"
        path, _ = QFileDialog.getSaveFileName(self, "Guardar Imagen", filename, "Images (*.jpg *.jpeg *.png)")
        if path:
            reply = self.nam.get(QNetworkRequest(QUrl(url)))
            reply.finished.connect(lambda: self.save_file(reply, path))

    def save_file(self, reply, path):
        if reply.error() == 0:
            with open(path, 'wb') as f:
                f.write(reply.readAll().data())
            self.iface.messageBar().pushMessage("Éxito", f"Imagen guardada", level=0)