# IEPNB - Tools (v1.1): Manual Integral de Usuario 🌍

**IEPNB - Tools** es el complemento oficial para **QGIS** diseñado para la gestión, visualización y análisis de la información geográfica del **Inventario Español del Patrimonio Natural y la Biodiversidad (IEPNB)**. Este plugin integra en una única interfaz todas las capacidades de consulta de la infraestructura de datos del Ministerio para la Transición Ecológica y el Reto Demográfico (MITECO).

### ✨ Novedades de la Versión 1.1
* **Interfaz Optimizada:** Rediseño completo del panel para ocupar el mínimo espacio horizontal, incorporando barras de desplazamiento dinámicas. Solución de renderizado High-DPI implementada para evitar la distorsión de logos institucionales en pantallas de alta resolución o anchos reducidos.
* **Experiencia de Usuario (UX):** Nuevas barras de progreso gráficas nativas (QProgressBar), cursores de espera y nuevos avisos dinámicos en la barra de mensajes (QgsMessageBar) para la gestión de cargas masivas de servicios WMS. Reorganización de botoneras estratégicas y botones de acción reactivos con estados visuales claros (activado/desactivado).
* **Informes Avanzados:** Integración de una barra de progreso para la exportación de informes PDF. Bloqueo de seguridad añadido en el selector de importación para rechazar archivos CSV no soportados.

---

## 🛠️ Interfaz Principal: Barra de Herramientas Inferior

En la barra inferior encontramos estos 6 botones que representan un amplio espectro de la información geográfica ubicada en la IDEE del MITECO. Estos botones automatizan la conexión y descarga de cartografía temática oficial. Al pulsarlos, el plugin organiza las capas en tu panel bajo el grupo "Servicios MITECO":

* **Banco de Datos de la Naturaleza:** Espacios protegidos, Red Natura 2000...
* **SNCZI:** Mapas de peligrosidad y riesgo de zonas inundables.
* **Sistema de Información de Redes (Agua):** Red hidrográfica, embalses y demarcaciones.
* **Costas:** Dominio Público Marítimo-Terrestre y servidumbres.
* **CEA:** Calidad y Evaluación Ambiental.
* **Reto Demográfico:** Acceso al Registro de Aguas.

### Herramientas de Contexto
* **Cartografía Base:** Carga instantánea de la ortofoto de máxima actualidad del PNOA y los límites administrativos oficiales. Se colocan automáticamente al fondo del mapa para no interferir con el análisis.
* **Google Street View:** Transforma tu cursor. Al hacer clic en el mapa de QGIS, el navegador web abrirá automáticamente la vista a pie de calle en esa coordenada exacta.

---

## 📋 Módulo 1: Pestaña "Identificar"

El núcleo de interacción espacial y generación de reportes automáticos.

### 1. Herramientas de Selección Espacial
* **Selección por Punto:** Identificación mediante clic.
* **Selección por Área:** Dibujo manual de polígonos de estudio personalizados.
* **Importar:** Permite cargar recintos desde archivos vectoriales (SHP, GeoJSON, KML, etc.). Incorpora un bloqueo de seguridad que impide la importación de archivos CSV.

### 2. Herramientas de Análisis (Botones Inteligentes)
La interfaz reacciona al usuario: los botones de análisis permanecen en gris (desactivados) y se reinician automáticamente, iluminándose solo cuando la información está lista.
* **Intersección:** Calcula el área (ha) o longitud (m) de solape entre el polígono de estudio y las capas del inventario.
* **Exportación CSV:** Vuelca los resultados de la intersección a una tabla de datos estructurada.
* **Informe PDF:** Genera un documento corporativo detallado con un mapa captura, los cruces territoriales y la lista de especies intersectadas, mostrando el progreso mediante una barra de carga integrada.

---

## 🔍 Módulo 2: Pestaña "Buscador"

Herramienta de localización territorial optimizada por capas.
* **Búsqueda Ágil:** Localiza términos municipales, provincias, montes o espacios protegidos mediante texto.
* **Tabla Responsiva:** Resultados presentados en una tabla compacta con desplazamiento horizontal automático.
* **Zoom Automático:** Encuadre instantáneo del mapa sobre la extensión del elemento localizado al añadirlo a la vista.

---

## 🐾 Módulo 3: Pestaña "Especies" (EIDOS)

Integración directa con el catálogo EIDOS para consulta de especies y distribución.
* **Búsqueda Sensible:** Localización exacta por nombre científico, común o Taxón ID.
* **Visor de Datos:** Tabla compacta de resultados con desplazamiento horizontal que permite consultar el grupo taxonómico y el estado de protección.
* **Distribución y Fichas:** Carga automática de los datos de distribución espacial y acceso a galerías de fotos.

---

## 🌐 Módulo 4: Pestaña "Servicios Web"

Acceso directo a servicios interoperables WMS/WFS.
* **PNOA Histórico (1956-2023):** Acceso a toda la serie anual de ortofotos y vuelos históricos como el Americano Serie B, SIGPAC u OLISTAT.
* **Corine Land Cover:** Series históricas desde 1990 hasta la nueva generación CLC+.
* **Programa Copernicus:** Servicios HRL (High Resolution Layers) de Bosques, Suelo Desnudo, Humedales y cartografía de detalle local (Urban Atlas, Zonas Costeras y Riberas).

---

## 📸 Módulo 5: Fototeca CENEAM

Consulta integrada a la fototeca del Centro Nacional de Educación Ambiental.
* **Búsqueda Integrada:** Localiza fotografías introduciendo términos de búsqueda de texto libre.
* **Visualización y Descarga:** Tarjetas de resultados con información del título, autor y ubicación, ofreciendo botones para ver la imagen original o descargarla directamente.

---

## 🏛️ Créditos y Autoría

Desarrollado para el **Ministerio para la Transición Ecológica y el Reto Demográfico (MITECO)**.
* **Autor:** IEPNB - MITECO.
* **Soporte:** buzon-bdatos@miteco.es.
