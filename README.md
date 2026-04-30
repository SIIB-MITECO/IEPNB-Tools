# IEPNB - Tools (v1.1): Manual Integral de Usuario 🌍[cite: 9]

**IEPNB - Tools** es el complemento oficial para **QGIS** diseñado para la gestión, visualización y análisis de la información geográfica del **Inventario Español del Patrimonio Natural y la Biodiversidad (IEPNB)**[cite: 9]. Este plugin integra en una única interfaz todas las capacidades de consulta de la infraestructura de datos del Ministerio para la Transición Ecológica y el Reto Demográfico (MITECO)[cite: 9].

### ✨ Novedades de la Versión 1.1[cite: 9]
* **Interfaz Optimizada:** Rediseño completo del panel para ocupar el mínimo espacio horizontal, incorporando barras de desplazamiento dinámicas[cite: 9]. Solución de renderizado High-DPI implementada para evitar la distorsión de logos institucionales en pantallas de alta resolución o anchos reducidos[cite: 9].
* **Experiencia de Usuario (UX):** Nuevas barras de progreso gráficas nativas (QProgressBar), cursores de espera y nuevos avisos dinámicos en la barra de mensajes (QgsMessageBar) para la gestión de cargas masivas de servicios WMS[cite: 9]. Reorganización de botoneras estratégicas y botones de acción reactivos con estados visuales claros (activado/desactivado)[cite: 9].
* **Informes Avanzados:** Integración de una barra de progreso para la exportación de informes PDF[cite: 9]. Bloqueo de seguridad añadido en el selector de importación para rechazar archivos CSV no soportados[cite: 9].

---

## 🛠️ Interfaz Principal: Barra de Herramientas Inferior

En la base del panel dispones de una botonera de acceso rápido dividida en dos grandes bloques funcionales:

### 1. Servicios Institucionales WMS
Botones diseñados para automatizar la conexión y descarga de cartografía temática oficial. El plugin organiza las capas en tu panel bajo el grupo "Servicios MITECO"[cite: 4]:
* **BDN:** Carga Espacios Naturales Protegidos, Red Natura 2000, MUPs y sistemas de alertas de vegetación (EIKOS)[cite: 4, 6].
* **SNCZI-IPE:** Despliega los mapas de peligrosidad y riesgo del Sistema Nacional de Cartografía de Zonas Inundables[cite: 4, 6].
* **Agua (DGA):** Incorpora la red hidrográfica, demarcaciones y embalses de la Dirección General del Agua[cite: 4, 6].
* **Costas (DGC):** Superpone el Dominio Público Marítimo-Terrestre y sus servidumbres[cite: 4, 6].
* **CEA:** Carga la red de estaciones de Calidad y Evaluación Ambiental[cite: 4, 6].
* **Registro de Aguas:** Acceso directo a concesiones e inscripciones de la DGA[cite: 4].
> 💡 *Nota:* Al cargar estos servicios (especialmente el BDN), el sistema mostrará avisos en la barra de mensajes de QGIS y el cursor se pondrá en modo de espera[cite: 4, 9].

### 2. Herramientas de Contexto
* **Cartografía Base:** Carga instantánea de la ortofoto de máxima actualidad del PNOA y los límites administrativos oficiales[cite: 4]. Se colocan automáticamente al fondo del mapa para no interferir con el análisis[cite: 4].
* **Google Street View:** Transforma tu cursor[cite: 4]. Al hacer clic en el mapa de QGIS, el navegador web abrirá automáticamente la vista a pie de calle en esa coordenada exacta[cite: 4].

---

## 📋 Módulo 1: Pestaña "Identificar"

El núcleo de interacción espacial y generación de reportes automáticos[cite: 5, 9].

### 1. Herramientas de Selección Espacial
* **Selección por Punto:** Identificación mediante clic[cite: 5].
* **Selección por Área:** Dibujo manual de polígonos de estudio personalizados[cite: 5].
* **Importar:** Permite cargar recintos desde archivos vectoriales (SHP, GeoJSON, KML, etc.)[cite: 5]. Incorpora un bloqueo de seguridad que impide la importación de archivos CSV[cite: 5, 9].

### 2. Herramientas de Análisis (Botones Inteligentes)
La interfaz reacciona al usuario: los botones de análisis permanecen en gris (desactivados) y se reinician automáticamente, iluminándose solo cuando la información está lista[cite: 5, 9].
* **Intersección:** Calcula el área (ha) o longitud (m) de solape entre el polígono de estudio y las capas del inventario[cite: 5].
* **Exportación CSV:** Vuelca los resultados de la intersección a una tabla de datos estructurada[cite: 5].
* **Informe PDF:** Genera un documento corporativo detallado con un mapa captura, los cruces territoriales y la lista de especies intersectadas, mostrando el progreso mediante una barra de carga integrada[cite: 5, 9].

---

## 🔍 Módulo 2: Pestaña "Buscador"

Herramienta de localización territorial optimizada por capas[cite: 1, 9].
* **Búsqueda Ágil:** Localiza términos municipales, provincias, montes o espacios protegidos mediante texto[cite: 1].
* **Tabla Responsiva:** Resultados presentados en una tabla compacta con desplazamiento horizontal automático[cite: 1, 9].
* **Zoom Automático:** Encuadre instantáneo del mapa sobre la extensión del elemento localizado al añadirlo a la vista[cite: 1].

---

## 🐾 Módulo 3: Pestaña "Especies" (EIDOS)

Integración directa con el catálogo EIDOS para consulta de especies y distribución[cite: 2, 9].
* **Búsqueda Sensible:** Localización exacta por nombre científico, común o Taxón ID[cite: 2].
* **Visor de Datos:** Tabla compacta de resultados con desplazamiento horizontal que permite consultar el grupo taxonómico y el estado de protección[cite: 2, 9].
* **Distribución y Fichas:** Carga automática de los datos de distribución espacial y acceso a galerías de fotos[cite: 2].

---

## 🌐 Módulo 4: Pestaña "Servicios Web"

Acceso directo a servicios interoperables WMS/WFS[cite: 3, 9].
* **PNOA Histórico (1956-2023):** Acceso a toda la serie anual de ortofotos y vuelos históricos como el Americano Serie B, SIGPAC u OLISTAT[cite: 6].
* **Corine Land Cover:** Series históricas desde 1990 hasta la nueva generación CLC+[cite: 6].
* **Programa Copernicus:** Servicios HRL (High Resolution Layers) de Bosques, Suelo Desnudo, Humedales y cartografía de detalle local (Urban Atlas, Zonas Costeras y Riberas)[cite: 6].

---

## 📸 Módulo 5: Fototeca CENEAM

Consulta integrada a la fototeca del Centro Nacional de Educación Ambiental[cite: 7, 9].
* **Búsqueda Integrada:** Localiza fotografías introduciendo términos de búsqueda de texto libre[cite: 7].
* **Visualización y Descarga:** Tarjetas de resultados con información del título, autor y ubicación, ofreciendo botones para ver la imagen original o descargarla directamente[cite: 7].

---

## 🏛️ Créditos y Autoría

Desarrollado para el **Ministerio para la Transición Ecológica y el Reto Demográfico (MITECO)**[cite: 9].
* **Autor:** IEPNB - MITECO[cite: 9].
* **Soporte:** buzon-bdatos@miteco.es[cite: 9].
