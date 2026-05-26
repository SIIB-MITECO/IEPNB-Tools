# IEPNB - Tools (v1.1.4): Manual Integral de Usuario 🌍

[cite_start]**IEPNB - Tools** Herramienta técnica de la Dirección General de Biodiversidad, Bosques y Desertificación para la consulta de los conjuntos de datos relativos al Inventario Español del Patrimonio Natural y la Biodiversidad (IEPNB) mediante servicios interoperables con el Sistema Integrado de Información de la Biodiversidad (SIIB).


![QGIS Minimum Version](https://img.shields.io/badge/QGIS-3.22%2B-green?style=flat-square&logo=qgis)
![MITECO Oficial](https://img.shields.io/badge/Oficial-MITECO-blue?style=flat-square)

## 📌 Índice de Contenidos
* [📺 Vídeo de Demostración](#-vídeo-de-demostración)
* [✨ Novedades y Arquitectura](#-novedades-y-arquitectura)
* [🛠️ Interfaz Principal y Barra de Herramientas](#️-interfaz-principal-barra-de-herramientas-inferior)
* [📋 Módulo 1: Pestaña "Identificar"](#-módulo-1-pestaña-identificar)
* [🔍 Módulo 2: Pestaña "Buscador"](#-módulo-2-pestaña-buscador)
* [🐾 Módulo 3: Pestaña "Especies" (EIDOS)](#-módulo-3-pestaña-especies-eidos)
* [🌐 Módulo 4: Pestaña "Servicios Web"](#-módulo-4-pestaña-servicios-web)
* [📸 Módulo 5: Fototeca CENEAM](#-módulo-5-fototeca-ceneam)
* [🔄 Historial de Versiones (Changelog)](#-historial-de-versiones-changelog)
* [🏛️ Soporte y Enlaces Oficiales](#-soporte-y-enlaces-oficiales)

---

### 📺 Vídeo de demostración
Haz clic en la imagen de abajo para ver el funcionamiento del plugin en YouTube:

[![Ver el vídeo del plugin](https://img.youtube.com/vi/7XWND6h2__E/hqdefault.jpg)](https://www.youtube.com/watch?v=7XWND6h2__E&vq=hd1080)

> **Nota:** En este vídeo se explica la instalación básica y el flujo de trabajo principal.

---

### ✨ Novedades y Arquitectura
* [cite_start]**Compatibilidad Estructural:** Código refactorizado para garantizar compatibilidad con versiones de QGIS desde la 3.22 hasta la 3.99.
* [cite_start]**Rendimiento Asíncrono (Anti-Congelación):** Incorporación de un sistema de carga en segundo plano y optimización de la gestión de memoria en peticiones de red mediante `QEventLoop`[cite: 28].
* [cite_start]**Experiencia de Usuario (UX):** Integración de `QProgressBar` para la exportación de informes PDF [cite: 33][cite_start], barras de desplazamiento horizontal en las tablas y solución de renderizado High-DPI para evitar la distorsión de logos institucionales[cite: 32, 33].

---

## 🛠️ Interfaz Principal: Barra de Herramientas Inferior

La barra inferior del plugin centraliza los accesos directos automatizados para la conexión y descarga de la cartografía temática de la IDEE del MITECO. 

| Botón de Acción | Información Geográfica Integrada |
| :--- | :--- |
| **Banco de Datos de la Naturaleza** | Carga automatizada de Espacios Protegidos, Red Natura 2000 y áreas de biodiversidad. |
| **SNCZI** | Mapas de peligrosidad y riesgo de zonas inundables. |
| **Sistema de Información de Redes** | Conexión directa con la red hidrográfica oficial y embalses. |
| **Costas** | Despliegue de las delimitaciones del Dominio Público Marítimo-Terrestre. |
| **CEA** | Capas oficiales de Calidad y Evaluación Ambiental. |
| **Reto Demográfico** | Acceso inmediato al Registro de Aguas. |

#### Herramientas de Contexto Transversales
* [cite_start]**Cartografía Base:** Carga instantánea de la ortofoto de máxima actualidad del PNOA y los límites administrativos oficiales en el fondo del proyecto[cite: 6].
* [cite_start]**Google Street View:** Transforma el cursor para abrir dinámicamente la vista a pie de calle en el navegador al hacer clic sobre cualquier coordenada del mapa[cite: 6].

---

## 📋 Módulo 1: Pestaña "Identificar"

[cite_start]El núcleo de interacción espacial, cruce de información territorial avanzada y generación de reportes corporativos automáticos cruzando bases de datos como ENP, RN2000 y MUP[cite: 2].

### 1. Herramientas de Selección Espacial
* **Selección por Punto:** Captura e identificación espacial mediante un único clic.
* **Selección por Área:** Habilita el dibujo manual de polígonos de estudio personalizados.
* [cite_start]**Importar Geometrías:** Permite cargar recintos y polígonos externos desde formatos vectoriales, asegurando una transferencia segura de geometrías WKT entre interfaces[cite: 30].

### 2. Motor de Análisis Espacial
El sistema analiza de forma simultánea capas críticas de protección (Espacios Naturales Protegidos, Red Natura 2000, Montes de Utilidad Pública, etc.). [cite_start]Además, incorpora soporte directo para el análisis de masas de agua a través de OGC API Features.

### 3. Emisión de Resultados y Reportes
* **Exportación CSV:** Vuelca de forma estructurada todos los solapes territoriales identificados.
* **Informe Oficial PDF:** Genera un documento técnico formal con mapa captura, cálculo exacto de superficies/distancias forzando el sistema de referencia oficial de España (RD 1071/2007) y listados taxonómicos.

---

## 🔍 Módulo 2: Pestaña "Buscador"

[cite_start]Herramienta territorial optimizada por capas y por término municipal[cite: 3].
* [cite_start]**Búsqueda Ágil:** Permite localizar de forma rápida espacios protegidos, montes catalogados o realizar una búsqueda integrada de Términos Municipales (TTMM) como área de estudio[cite: 26].
* [cite_start]**Soporte de Enclaves Territoriales:** El sistema cuenta con soporte avanzado para municipios con islas o enclaves, aplicando una unificación automática de geometrías (*unary union*) para tratar el territorio como un único multipolígono continuo.
* **Tabla Responsiva:** Resultados estructurados con redimensionamiento automático.

---

## 🐾 Módulo 3: Pestaña "Especies" (EIDOS)

[cite_start]Integración e interoperabilidad directa con los servicios web de la API del catálogo EIDOS para la consulta de especies y su distribución[cite: 4].
* **Búsqueda Taxonómica:** Localización exacta por nombre científico, común o Taxón ID.
* **Visualización de Distribución:** Descarga las geometrías de distribución del taxón y las incorpora como capas vectoriales estilizadas dinámicamente.

---

## 🌐 Módulo 4: Pestaña "Servicios Web"

[cite_start]Acceso centralizado a servicios interoperables WMS de entidades como el MFE, Copernicus, PNOA, EIKOS, BDN, DGA, LULUCF y la IDEE del MITECO[cite: 5].

El catálogo integrado contiene:
* **Series Históricas:** PNOA Histórico (1956-2023) y Corine Land Cover.
* **Programa Copernicus (HRL):** Mapas de Alta Resolución de Bosques, Suelo Desnudo y Humedales.
* **Cartografía de Detalle:** Urban Atlas, Zonas Costeras y Zonas Riparias.
* [cite_start]**Inventarios LULUCF:** Integración del histórico de datos del sector de Uso de la Tierra, Cambio de Uso de la Tierra y Silvicultura.

---

## 📸 Módulo 5: Fototeca CENEAM

[cite_start]Consulta integrada en la base de recursos del Centro Nacional de Educación Ambiental[cite: 6].
* **Búsqueda Semántica y Tarjetas de Visualización:** Presentación en formato "Cards" con metadatos.
* **Descarga Nativa:** Botones integrados para abrir la resolución original o guardar el archivo directamente en el disco duro local saneando automáticamente los nombres de los ficheros.

---

## 🔄 Historial de Versiones (Changelog)

* [cite_start]**Versión 1.1.3:** Integración de nuevos servicios de datos para masas de agua (OGC API Features) en identificación, buscador e informes. [cite_start]Reparación y actualización de leyendas de múltiples servicios WMS.
* [cite_start]**Versión 1.1.2:** Añadidas capas en la sección de Calidad y Evaluación Ambiental e integración del histórico LULUCF en servicios web[cite: 24, 25]. [cite_start]Corrección en la cabecera de versión del plugin.
* [cite_start]**Versión 1.1.1:** Implementación de búsqueda independiente por Términos Municipales (TTMM)[cite: 26, 27]. [cite_start]Optimización de memoria (`QEventLoop`), mejora en la transferencia WKT y soporte de unión automática (*unary union*) para enclaves e islas municipales[cite: 28, 29, 30].
* [cite_start]**Versión 1.1.0:** Rediseño de UI para reducir el ancho mínimo del panel[cite: 31]. [cite_start]Nuevas barras de desplazamiento horizontal [cite: 32][cite_start], botoneras reactivas, adición de `QProgressBar` para PDF y renderizado High-DPI de logos[cite: 32, 33].
* [cite_start]**Versión 1.0.x:** Corrección de títulos, optimización de importaciones y limpieza de código según estándar PEP8.

---

## 🏛️ Soporte y Enlaces Oficiales

[cite_start]Desarrollado para la **Dirección General de Biodiversidad, Bosques y Desertificación (MITECO)**.
* [cite_start]**Web Oficial:** [https://iepnb.gob.es/](https://iepnb.gob.es/) 
* [cite_start]**Repositorio de Código:** [GitHub - IEPNB-Tools](https://github.com/SIIB-MITECO/IEPNB-Tools) 
* [cite_start]**Reporte de Incidencias (Issues):** [GitHub Tracker](https://github.com/SIIB-MITECO/IEPNB-Tools/issues) 
* [cite_start]**Soporte Directo:** buzon-bdatos@miteco.es
