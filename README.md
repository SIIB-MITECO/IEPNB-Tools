# IEPNB - Tools (v1.1): Manual Integral de Usuario 🌍

**IEPNB - Tools** es el complemento oficial para **QGIS** diseñado para la gestión, visualización y análisis de la información geográfica del **Inventario Español del Patrimonio Natural y la Biodiversidad (IEPNB)**. Este plugin integra en una única interfaz todas las capacidades de consulta de la infraestructura de datos del Ministerio para la Transición Ecológica y el Reto Demográfico (MITECO).

![QGIS 3 & 4 Compatible](https://img.shields.io/badge/QGIS-3.x%20%7C%204.x%20Ready-green?style=flat-square&logo=qgis)

## 📌 Índice de Contenidos
* [📺 Vídeo de Demostración](#-vídeo-de-demostración)
* [✨ Novedades y Arquitectura de la Versión 1.1](#-novedades-y-arquitectura-de-la-versión-11)
* [🛠️ Interfaz Principal y Accesos IDEE](#️-interfaz-principal-barra-de-herramientas-inferior)
* [📋 Módulo 1: Pestaña "Identificar"](#-módulo-1-pestaña-identificar)
* [🔍 Módulo 2: Pestaña "Buscador"](#-módulo-2-pestaña-buscador)
* [🐾 Módulo 3: Pestaña "Especies" (EIDOS)](#-módulo-3-pestaña-especies-eidos)
* [🌐 Módulo 4: Pestaña "Servicios Web"](#-módulo-4-pestaña-servicios-web)
* [📸 Módulo 5: Fototeca CENEAM](#-módulo-5-fototeca-ceneam)

---

### 📺 Vídeo de demostración
Haz clic en la imagen de abajo para ver el funcionamiento del plugin en YouTube:

[![Ver el vídeo del plugin](https://img.youtube.com/vi/7XWND6h2__E/hqdefault.jpg)](https://www.youtube.com/watch?v=7XWND6h2__E&vq=hd1080)

> **Nota:** En este vídeo se explica la instalación básica y el flujo de trabajo principal.

---

### ✨ Novedades y Arquitectura de la Versión 1.1
* **Compatibilidad Estructural:** Código refactorizado para garantizar compatibilidad total con el actual ecosistema QGIS 3.x y preparado ('Future-Proof') para el salto a QGIS 4.x.
* **Interfaz Optimizada:** Rediseño completo del panel para ocupar el mínimo espacio horizontal mediante barras dinámicas. Implementación High-DPI para evitar la distorsión de logos institucionales en pantallas de alta resolución.
* **Rendimiento Asíncrono (Anti-Congelación):** Nuevo sistema de carga de imágenes en segundo plano (`ImageLoader`) para los catálogos fotográficos, garantizando que la interfaz de QGIS nunca se congele durante las consultas web.
* **Experiencia de Usuario (UX):** Nuevas barras de progreso gráficas nativas (`QProgressBar`), cursores de espera y nuevos avisos dinámicos en la barra de mensajes (`QgsMessageBar`) para la gestión de cargas masivas de servicios WMS.

---

## 🛠️ Interfaz Principal: Barra de Herramientas Inferior

La barra inferior automatiza la conexión y descarga de cartografía temática oficial. Al pulsarlos, el plugin organiza automáticamente las capas en tu panel bajo el grupo corporativo "Servicios MITECO":

| Botón / Servicio | Información Geográfica Integrada |
| :--- | :--- |
| **Banco de Datos de la Naturaleza** | Espacios Protegidos, Red Natura 2000, Áreas Protegidas por Instrumentos Internacionales. |
| **SNCZI** | Mapas de peligrosidad y riesgo de zonas inundables. |
| **Sistema de Información de Redes** | Red hidrográfica, embalses y demarcaciones lógicas. |
| **Costas** | Dominio Público Marítimo-Terrestre y servidumbres asociadas. |
| **CEA** | Calidad y Evaluación Ambiental. |
| **Reto Demográfico** | Acceso directo al Registro de Aguas. |

#### Herramientas de Contexto Transversales
* **Cartografía Base:** Carga instantánea de la ortofoto de máxima actualidad del PNOA y los límites administrativos oficiales en el fondo del mapa.
* **Google Street View:** Transforma el cursor para abrir dinámicamente la vista a pie de calle en el navegador al hacer clic sobre cualquier coordenada del lienzo.

---

## 📋 Módulo 1: Pestaña "Identificar"

El núcleo de interacción espacial y generación de reportes territoriales automatizados.

### 1. Herramientas de Selección Espacial
* **Selección por Punto:** Identificación mediante clic exacto.
* **Selección por Área:** Dibujo manual de polígonos de estudio personalizados en el lienzo interactivo.
* **Importar Geometrías:** Permite cargar recintos desde archivos vectoriales (SHP, GeoJSON, KML, etc.). 

> [!CAUTION]
> **Seguridad Estricta de Datos:** El selector de importación cuenta con un bloqueo de seguridad nativo que rechaza la entrada de archivos CSV no soportados para evitar rupturas de topología o fallos de geometría en la intersección.

### 2. Motor de Análisis Espacial
El sistema de intersección no es genérico; cruza automáticamente la geometría de estudio contra las siguientes bases de datos estructurales del IEPNB:
* *Espacios Naturales Protegidos (ENP)*
* *Red Natura 2000*
* *Montes de Utilidad Pública (MUP)*
* *Vías Pecuarias*
* *Áreas Marinas Protegidas (RAMPE)*
* *Reservas de la Biosfera e IBAs*

> [!TIP]
> **Reactividad Inteligente:** Los botones de análisis permanecen desactivados (en gris) y se iluminan dinámicamente solo cuando la geometría de análisis y los servicios requeridos están listos.

### 3. Emisión de Resultados
* **Exportación CSV:** Vuelca los resultados de la intersección a una tabla de datos estructurada.
* **Informe Oficial PDF:** Genera un documento corporativo detallado que incluye mapa captura, cruces territoriales y listado de riqueza de especies. *Nota técnica:* Los cálculos de superficie y distancia del reporte fuerzan estrictamente el sistema de referencia oficial de España (RD 1071/2007).

---

## 🔍 Módulo 2: Pestaña "Buscador"

Herramienta de localización territorial optimizada.
* **Búsqueda Ágil:** Localiza términos municipales (TTMM), provincias, montes o espacios protegidos introduciendo texto libre (mínimo 3 caracteres).
* **Tabla Responsiva:** Resultados presentados en tabla compacta con ajuste proporcional automático.
* **Zoom Dinámico:** Encuadre instantáneo del mapa sobre la extensión (Bounding Box) del elemento territorial al añadirlo a la vista.

---

## 🐾 Módulo 3: Pestaña "Especies" (EIDOS)

Integración directa con el catálogo EIDOS para consulta taxonómica.
* **Búsqueda Sensible:** Localización exacta por nombre científico, nombre común o Taxón ID.
* **Visor de Datos:** Tabla compacta con desplazamiento horizontal para consultar grupo taxonómico y estado de protección legal.
* **Distribución y Galerías:** Carga automática de la envolvente de distribución espacial en el mapa y visualización de galerías fotográficas en tiempo real.

---

## 🌐 Módulo 4: Pestaña "Servicios Web"

Acceso directo a servicios interoperables WMS/WFS/WMTS.
* **PNOA Histórico (1956-2023):** Acceso a toda la serie anual de ortofotos y vuelos históricos (Americano Serie B, SIGPAC, OLISTAT).
* **Corine Land Cover:** Series históricas desde 1990 hasta la nueva generación CLC+.
* **Programa Copernicus (HRL):** Servicios satelitales de alta resolución de Bosques, Suelo Desnudo, Humedales y cartografía de detalle local (Urban Atlas, Zonas Costeras y Riberas).

---

## 📸 Módulo 5: Fototeca CENEAM

Consulta integrada a la base de recursos del Centro Nacional de Educación Ambiental.
* **Búsqueda Semántica:** Localiza fotografías introduciendo términos de búsqueda de texto libre.
* **Tarjetas de Visualización:** Presentación en formato "Cards" con metadatos del título, autor y ubicación.
* **Descarga Nativa:** Botones integrados para abrir la resolución original en navegador o guardar el archivo directamente en el disco duro local a través de la API de QGIS.

---

## 🏛️ Créditos y Autoría

Desarrollado para el **Ministerio para la Transición Ecológica y el Reto Demográfico (MITECO)**.
* **Autor:** IEPNB - MITECO.
* **Soporte y Reporte de Bugs:** buzon-bdatos@miteco.es.
