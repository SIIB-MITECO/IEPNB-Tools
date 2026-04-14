# IEPNB - Tools (v1.0): Manual Integral de Usuario 🌍

**IEPNB - Tools** es el complemento oficial para **QGIS** diseñado para la gestión, visualización y análisis de la información geográfica del **Inventario Español del Patrimonio Natural y la Biodiversidad (IEPNB)**. Este plugin integra en una única interfaz todas las capacidades de consulta de la infraestructura de datos del Ministerio para la Transición Ecológica y el Reto Demográfico (MITECO).

---

## 🛠️ Interfaz Principal: Herramientas de Pie de Página

Ubicadas en la parte inferior de la interfaz, estas herramientas proporcionan el contexto geográfico básico necesario para cualquier análisis:

### 1. Cartografía Base (PNOA y Límites)
Permite la carga instantánea de las capas de referencia fundamentales:
* **PNOA Actual:** Carga de la ortofoto de máxima actualidad del Plan Nacional de Ortofotografía Aérea.
* **Límites Administrativos:** Capas oficiales de delimitación de términos municipales, provincias y comunidades autónomas, optimizadas para una visualización clara sobre ortofotos o mapas vectoriales.

### 2. Herramienta Google Street View
Funcionalidad de apoyo visual que permite sincronizar la vista de QGIS con la realidad a pie de calle. Al activar esta herramienta y hacer clic en cualquier punto del mapa, se abre automáticamente una pestaña en el navegador con la vista de Street View en esa ubicación exacta, facilitando la verificación visual de infraestructuras o tipos de vegetación.

---

## 📋 Módulo 1: Pestaña "Identificar"

Este módulo constituye el núcleo de interacción con los datos vectoriales y servicios del inventario.

### 1. Herramientas de Selección
Permite interrogar a las capas cargadas mediante diferentes metodologías:
* **Selección por Clic:** Identificación puntual de entidades.
* **Selección por Área (Rectángulo/Polígono):** Permite obtener información masiva de múltiples geometrías de forma simultánea.
* **Gestión de Capas Activas:** El sistema identifica automáticamente qué capas del IEPNB están visibles y prioriza la devolución de sus atributos.

### 2. Herramientas de Acción y Análisis
Una vez seleccionada la información, el módulo permite:
* **Consulta de Atributos:** Visualización de fichas técnicas completas con datos de protección, nombres científicos y metadatos de actualización.
* **Análisis Espacial:** Herramientas para el cálculo de superficies y exportación de tablas de datos a formatos compatibles (Excel/CSV).

---

## 🔍 Módulo 2: Pestaña "Buscador"

Herramienta de localización avanzada diseñada para navegar entre los miles de registros de las bases de datos ambientales:
* **Búsqueda Semántica:** Localización de montes, centros CENEAM y espacios protegidos mediante texto.
* **Filtros Geográficos:** Capacidad de restringir las búsquedas a ámbitos territoriales específicos (Provincias o CCAA).
* **Zoom Automático:** Al localizar un elemento, el plugin ajusta automáticamente el lienzo del mapa a la extensión de la geometría encontrada.

---

## 🐾 Módulo 3: Pestaña "Especies" (EIDOS)

Integración directa con el sistema **EIDOS**, el banco de datos de biodiversidad más importante de España.

### 1. Capacidades de Búsqueda Multivariable
Permite localizar información biológica cruzando diversos criterios:
* **Taxonomía:** Búsqueda por nombre científico, nombre común o familia.
* **Categorías de Protección:** Filtrado según el Catálogo Español de Especies Amenazadas (CEEA) o el Listado de Especies Silvestres en Régimen de Protección Especial (LESRPE).
* **Ámbito Territorial:** Diferenciación clara entre Inventarios Terrestres y Marinos.

### 2. Acceso a Información y Cartografía
* **Fichas EIDOS:** Enlace directo a la documentación técnica de cada especie.
* **Cuadrículas de Distribución:** Carga automática de la presencia de especies en cuadrículas 10x10 o 1x1, según la resolución disponible en el inventario oficial.

---

## 🌐 Módulo 4: Pestaña "Servicios Web"

Este módulo gestiona el catálogo masivo de servicios WMS y WFS, organizados por temáticas y series históricas.

### 1. Interfaz y Botones de Acción
Permite una gestión ágil de las capas: conexión, carga, eliminación y ordenación de servicios web oficiales.

### 2. Catálogo de Capas y Servicios Disponibles
* **PNOA Histórico (2004-2023):** Acceso a toda la serie anual de ortofotos y vuelos históricos fundamentales (Interministerial 1973-1986, Nacional 1981-1986, OLISTAT, SIGPAC y el Vuelo Americano Serie B de 1956-1957).
* **Corine Land Cover (CLC):** Capas de ocupación del suelo de los años 1990, 2000, 2006, 2012 y 2018, junto con la nueva generación **CLC+** (2018-2023).
* **Programa Copernicus (HRL y Local):**
    * **Bosques:** Evolución de la Densidad Arbórea (TCD) y Tipo de Hoja (DLT).
    * **Agrícola y Pastizales:** Capas de Suelo Desnudo y Pastizales.
    * **Agua y Humedales:** Estado de humedad del suelo y masas de agua.
    * **Zonas Locales:** Cartografía de detalle para Zonas Costeras, Riberas, Espacios Natura 2000 y Arbolado Urbano (Urban Atlas).

---

## 📸 Módulo 5: Fototeca CENEAM

Pasarela directa a la **Fototeca del Centro Nacional de Educación Ambiental**.
* **Consulta Fotográfica:** Permite buscar y visualizar fotografías sobre naturaleza, medio ambiente e historia rural vinculadas a localizaciones geográficas.
* **Documentación Visual:** Herramienta clave para técnicos que necesiten documentar la evolución del paisaje o identificar elementos singulares sobre el terreno mediante registros fotográficos históricos y actuales.

---

## 🏛️ Créditos y Autoría

Desarrollado para el **Ministerio para la Transición Ecológica y el Reto Demográfico (MITECO)**.
* **Promotor:** Dirección General de Biodiversidad, Bosques y Desertificación.
* **Departamento:** Inventario Español del Patrimonio Natural y la Biodiversidad.
