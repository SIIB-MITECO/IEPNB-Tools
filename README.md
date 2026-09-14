# IEPNB - Tools (v2.1.0): Manual Integral de Usuario 🌍

**IEPNB - Tools** es la herramienta técnica de la Dirección General de Biodiversidad, Bosques y Desertificación para la consulta de los conjuntos de datos relativos al Inventario Español del Patrimonio Natural y la Biodiversidad (IEPNB), mediante servicios interoperables con el Sistema Integrado de Información de la Biodiversidad (SIIB), y para el análisis de series temporales de teledetección (Copernicus/Sentinel-2) sobre cualquier punto del territorio.

[![QGIS Minimum Version](https://img.shields.io/badge/QGIS-3.22%2B-green?style=flat-square&logo=qgis)](https://qgis.org/)
[![MITECO Oficial](https://img.shields.io/badge/Oficial-MITECO-blue?style=flat-square)](https://www.miteco.gob.es/)

## 📌 Índice de Contenidos

- [📺 Vídeo de Demostración](#-vídeo-de-demostración)
- [✨ Novedades y Arquitectura](#-novedades-y-arquitectura)
- [🛠️ Interfaz Principal y Barra de Herramientas](#️-interfaz-principal-barra-de-herramientas-inferior)
- [📋 Módulo 1: Pestaña "Identificar"](#-módulo-1-pestaña-identificar)
- [🔍 Módulo 2: Pestaña "Buscador"](#-módulo-2-pestaña-buscador)
- [🐾 Módulo 3: Pestaña "Especies" (EIDOS)](#-módulo-3-pestaña-especies-eidos)
- [🌐 Módulo 4: Pestaña "Servicios Web"](#-módulo-4-pestaña-servicios-web)
- [📸 Módulo 5: Fototeca CENEAM](#-módulo-5-fototeca-ceneam)
- [📈 Módulo 6: Índice Histórico (Copernicus)](#-módulo-6-índice-histórico-copernicus)
- [🔄 Historial de Versiones (Changelog)](#-historial-de-versiones-changelog)
- [🏛️ Soporte y Enlaces Oficiales](#️-soporte-y-enlaces-oficiales)

---

### 📺 Vídeo de demostración

Haz clic en la imagen de abajo para ver el funcionamiento del plugin en YouTube:

[![Ver el vídeo del plugin](https://img.youtube.com/vi/7XWND6h2__E/hqdefault.jpg)](https://www.youtube.com/watch?v=7XWND6h2__E&vq=hd1080)

> **Nota:** En este vídeo se explica la instalación básica y el flujo de trabajo principal. El módulo de Índice Histórico (Copernicus), incorporado en la v2.0/2.1, no aparece todavía en el vídeo.

---

### ✨ Novedades y Arquitectura

- **Compatibilidad Estructural:** Código refactorizado para garantizar compatibilidad con versiones de QGIS desde la 3.22 hasta QGIS 4.x (PyQt6).
- **Rendimiento Asíncrono (Anti-Congelación):** Sistema de carga en segundo plano y optimización de la gestión de memoria en peticiones de red mediante `QEventLoop`, tanto para los servicios WMS/WFS del IEPNB como para las consultas a la Statistical API de Copernicus.
- **Experiencia de Usuario (UX):** `QProgressBar` para la exportación de informes PDF, barras de desplazamiento horizontal en las tablas, solución de renderizado High-DPI para logos institucionales, y gráficas interactivas (zoom, inspección de valores) en el nuevo módulo de índices.
- **Autenticación segura:** Las credenciales de Copernicus Data Space Ecosystem se guardan cifradas en el Authentication Manager nativo de QGIS, nunca en texto plano.
- **Catálogo de servicios:** más de 30 categorías temáticas y cerca de 370 capas WMS/WFS indexadas, buscables desde la pestaña "Servicios Web".

---

## 🛠️ Interfaz Principal: Barra de Herramientas Inferior

La barra inferior centraliza accesos directos que cargan, con un solo clic, un subconjunto ya agrupado del catálogo de la IDE de MITECO (el catálogo completo, con todas las capas sueltas, se explora desde la pestaña [Servicios Web](#-módulo-4-pestaña-servicios-web)).

| Botón | Grupos que carga (subcategorías reales) |
| --- | --- |
| **Banco de Datos de la Naturaleza (BDN)** | Espacios Protegidos y Propiedad (ENP, RN2000, IBAs, RAMPE, MUP, Vías Pecuarias) · Convenios Internacionales (MAB, OSPAR, RAMSAR, ZEPIM, Geoparque) · Mapa Forestal Español (Foto Fija MFE) · Ecosistemas, Hábitats y Paisaje · Fauna, Flora y Recursos Genéticos · Erosión e Incendios Forestales (INES) · EIKOS (alertas anuales, mensuales y cambios de vegetación) |
| **SNCZI** | Cartografía de Zonas Inundables — Áreas con Riesgo Potencial Significativo de Inundación (ARPSI) |
| **Sistema de Información de Redes (SIR - DGA)** | Hidrología Cuantitativa (SIMPA, SAIH, ERHIN) · Reservas Hidrológicas y Zonas Protegidas · Saneamiento, Vertidos y Nitratos · DPH, Hidromorfología y Restauración · Seguimiento de Aguas Superficiales y Subterráneas · Masas de Agua y Estado (PHC 2022-2027) · Planificación, Ámbitos e Hidrografía |
| **Costas (DGC)** | Estrategias Marinas · POEM (Planes de Ordenación del Espacio Marítimo) · Dominio Público Marítimo-Terrestre y Gestión |
| **CEA** | Ruido Ambiental (UME y MER) · Emisiones Industriales, Residuos y Sensibilidad a Renovables · Calidad del Aire (general y por contaminante) · Cambio Climático y LULUCF |

> El botón **"Reto Demográfico"** que figuraba en versiones antiguas del manual ya no existe en el código actual — se eliminó del catálogo y no debe aparecer en la documentación.

#### Herramientas de Contexto Transversales

- **Cartografía Base:** Carga instantánea de la ortofoto de máxima actualidad del PNOA (teselas XYZ) y los límites administrativos oficiales en el fondo del proyecto.
- **Google Street View:** Transforma el cursor para abrir dinámicamente la vista a pie de calle en el navegador al hacer clic sobre cualquier coordenada del mapa.
- **Índice Histórico (Copernicus):** Icono con el logo de Copernicus; despliega un menú de índices espectrales por categorías y abre una gráfica temporal para el punto en el que se haga clic. Ver [Módulo 6](#-módulo-6-índice-histórico-copernicus).

---

## 📋 Módulo 1: Pestaña "Identificar"

El núcleo de interacción espacial, cruce de información territorial avanzada y generación de reportes corporativos automáticos cruzando bases de datos como ENP, RN2000 y MUP.

### 1. Herramientas de Selección Espacial

- **Selección por Punto:** Captura e identificación espacial mediante un único clic.
- **Selección por Área:** Habilita el dibujo manual de polígonos de estudio personalizados.
- **Importar Geometrías:** Permite cargar recintos y polígonos externos desde formatos vectoriales, asegurando una transferencia segura de geometrías WKT entre interfaces.
- **Buscador de Término Municipal (TTMM):** Botón independiente dentro de la propia pestaña que abre un diálogo de búsqueda por nombre de municipio contra el servicio WFS oficial (autocompletado desde 3 letras, con normalización de tildes). Al seleccionar un resultado, su geometría (con unión automática de posibles enclaves/islas) se usa directamente como área de estudio para el análisis — sin necesidad de salir a la pestaña "Buscador" ni dibujar nada a mano.

### 2. Motor de Análisis Espacial

El sistema analiza de forma simultánea capas críticas de protección (Espacios Naturales Protegidos, Red Natura 2000, Montes de Utilidad Pública, etc.). Además, incorpora soporte directo para el análisis de masas de agua a través de OGC API Features.

### 3. Emisión de Resultados y Reportes

- **Exportación CSV:** Vuelca de forma estructurada todos los solapes territoriales identificados.
- **Informe Oficial PDF:** Genera un documento técnico formal con mapa captura, cálculo exacto de superficies/distancias forzando el sistema de referencia oficial de España (RD 1071/2007) y listados taxonómicos.

---

## 🔍 Módulo 2: Pestaña "Buscador"

Herramienta territorial optimizada por capas y por término municipal — complementaria al buscador de TTMM que vive dentro de "Identificar": aquí el foco es explorar y visualizar, no lanzar directamente un análisis de intersección.

- **Búsqueda Ágil:** Permite localizar de forma rápida espacios protegidos, montes catalogados o realizar una búsqueda integrada de Términos Municipales (TTMM) como área de estudio.
- **Soporte de Enclaves Territoriales:** El sistema cuenta con soporte avanzado para municipios con islas o enclaves, aplicando una unificación automática de geometrías (*unary union*) para tratar el territorio como un único multipolígono continuo.
- **Tabla Responsiva:** Resultados estructurados con redimensionamiento automático.

---

## 🐾 Módulo 3: Pestaña "Especies" (EIDOS)

Integración e interoperabilidad directa con los servicios web de la API del catálogo EIDOS para la consulta de especies y su distribución.

- **Búsqueda Taxonómica:** Localización exacta por nombre científico, común o Taxón ID.
- **Visualización de Distribución:** Descarga las geometrías de distribución del taxón y las incorpora como capas vectoriales estilizadas dinámicamente.

---

## 🌐 Módulo 4: Pestaña "Servicios Web"

Catálogo completo, buscable, de los servicios interoperables WMS/WFS de MITECO — organizado en un árbol filtrable con más de **30 categorías temáticas** y cerca de **370 capas** individuales, agrupadas por dirección/organismo responsable:

| Prefijo | Ámbito | Ejemplos de categorías |
| --- | --- | --- |
| **[IEPNB]** | Biodiversidad, bosques y espacios protegidos | Espacios Protegidos y Propiedad, Convenios Internacionales, Mapa Forestal Español, Ecosistemas y Hábitats, Fauna y Flora, Erosión e Incendios (INES), EIKOS |
| **[DGA]** | Agua (Dirección General del Agua) | Planificación e Hidrografía, Masas de Agua (PHC 2022-2027), Seguimiento de Aguas Superficiales/Subterráneas, DPH e Hidromorfología, Saneamiento y Vertidos, Reservas Hidrológicas, Hidrología Cuantitativa, SNCZI |
| **[DGC]** | Costas | Dominio Público Marítimo-Terrestre, POEM, Estrategias Marinas |
| **[DGCEA]** | Calidad y Evaluación Ambiental | Cambio Climático y LULUCF, Calidad del Aire (general y por contaminante), Emisiones Industriales y Residuos, Ruido Ambiental |
| **[IGN]** | Cartografía de referencia | PNOA Histórico (serie completa 2006-2024), Redes de Transporte (carretera, ferrocarril, aéreo, marítimo) |
| **[COPERNICUS]** | Observación de la Tierra europea | Corine Land Cover & Backbone, High Resolution Layers (Bosques, Suelo Desnudo, Humedales, Zonas Urbanas/Costeras/Riparias) |

- **Búsqueda por texto libre** sobre todo el árbol de capas.
- **Doble clic o "Añadir al Mapa"** para incorporar cualquier capa individual al proyecto, con estilo y leyenda ya configurados.

---

## 📸 Módulo 5: Fototeca CENEAM

Consulta integrada en la base de recursos del Centro Nacional de Educación Ambiental.

- **Búsqueda Semántica y Tarjetas de Visualización:** Presentación en formato "Cards" con metadatos.
- **Descarga Nativa:** Botones integrados para abrir la resolución original o guardar el archivo directamente en el disco duro local saneando automáticamente los nombres de los ficheros.

---

## 📈 Módulo 6: Índice Histórico (Copernicus)

Herramienta de teledetección integrada directamente en el plugin: permite consultar la evolución temporal de un índice espectral en cualquier punto del territorio español, sin salir de QGIS ni depender de otro software. Los datos proceden de **Sentinel-2 L2A**, procesados en la nube a través de la **Statistical API de Copernicus Data Space Ecosystem (CDSE)**.

### 1. Uso básico

1. Pulsa el icono de Copernicus en la barra inferior.
2. Elige un índice del menú, organizado por categorías temáticas.
3. Haz clic en el punto del mapa que te interese.
4. Se abre una ventana con la serie temporal completa (desde 2017 hasta hoy, muestreada cada 5 días).

### 2. Índices disponibles, por categoría

| Categoría | Índices | Para qué sirven |
| --- | --- | --- |
| **Vegetación** | NDVI, EVI, SAVI, GNDVI, CIRE | Vigor y densidad de la vegetación, con variantes que corrigen suelo desnudo (SAVI), saturación en biomasa alta (EVI) o detectan estrés de clorofila más temprano (GNDVI, CIRE). |
| **Agua y nieve** | NDWI, NDMI, NDSI | Agua superficial (NDWI), contenido de humedad de la vegetación/estrés hídrico (NDMI) y cobertura de nieve (NDSI). |
| **Incendios y suelo desnudo** | NBR, BAI, BSI | Severidad de área quemada (NBR, BAI) y suelo desnudo expuesto, útil para seguimiento de regeneración post-incendio (BSI). |

Cada índice, dentro de la propia gráfica, incluye una ficha con su fórmula, rango típico de valores y cómo interpretarlos.

### 3. Comparar dos índices

Desde el botón **"+ Añadir índice"** dentro de la gráfica se puede superponer un segundo índice sobre el mismo punto (p. ej. NDVI vs NDMI, o NBR vs BAI), cada uno con su propio eje Y y color, para contrastar dos fenómenos a la vez sin volver a hacer clic en el mapa.

### 4. Interacción con la gráfica

- **Filtro de periodo:** botones rápidos de 1/3/5 años o el histórico completo.
- **Zoom:** barra de herramientas con lupa de zoom por rectángulo, desplazamiento (pan) y botón "Home" para volver a la vista completa.
- **Inspección de valores:** al pasar el ratón sobre la curva se resalta el punto más cercano y se muestra su fecha (dd/mm/aaaa) y valor exacto.
- **Suavizado:** las observaciones brutas se muestran atenuadas de fondo, con una media móvil superpuesta para facilitar la lectura de la tendencia.

### 5. Autenticación y cuota

El módulo requiere una cuenta gratuita en [dataspace.copernicus.eu](https://dataspace.copernicus.eu) y un **OAuth Client** (Client ID/Secret) generado desde el Dashboard de Sentinel Hub — no el usuario/contraseña personal de la cuenta. Las credenciales se piden una sola vez, mediante un diálogo con instrucciones y enlace directo, y quedan guardadas cifradas en el Authentication Manager de QGIS. El nivel gratuito de CDSE incluye 40.000 unidades de procesamiento al mes, muy por encima de lo que consume el uso normal de esta herramienta.

### 6. Origen de los datos y licencia

Los datos proceden del programa **Copernicus** (ESA / Unión Europea), de acceso libre y gratuito según la *Legal Notice on the use of Copernicus Sentinel Data*, que exige únicamente atribución (`Copernicus Sentinel data [año]`) al redistribuir. Este aviso se muestra también en cada gráfica generada por el plugin.

---

## 🔄 Historial de Versiones (Changelog)

- **Versión 2.1.0:**
  - Nueva funcionalidad: **Índice Histórico**. Botón en la barra de herramientas (icono Copernicus) que, al pulsarlo, permite elegir un índice espectral (NDVI, NDWI, NBR, EVI, NDMI, GNDVI, SAVI, BAI, NDSI, BSI, CIRE) y hacer clic en un punto del mapa para consultar su serie temporal completa desde 2017.
  - Los datos se obtienen de Sentinel-2 L2A a través de la Statistical API de Copernicus Data Space Ecosystem (CDSE), con enmascarado de nubes/sombras por banda SCL y muestreo cada 5 días.
  - Autenticación mediante OAuth Client (Client ID/Secret de Sentinel Hub, no el usuario/contraseña personal), guardada cifrada en el Authentication Manager de QGIS tras la primera consulta.
  - Gráfica con curva suavizada (media móvil) sobre las observaciones brutas, relleno de área, colores propios por índice, filtro rápido de periodo (1/3/5 años/Todo), zoom interactivo, inspección de valores al pasar el ratón, comparación de dos índices en la misma gráfica y aviso de fuente/licencia de los datos.
- **Versión 2.0:**
  - Compatibilidad con QGIS 4.x (PyQt6), manteniendo el soporte de QGIS 3.22+.
  - Corregidos fallos silenciosos en Territory, TTMM, ficha de especies y Fototeca CENEAM causados por el acceso a enums de `QNetworkReply` no compatible con PyQt6.
  - Solucionado el buscador de Términos Municipales (TTMM), que no localizaba resultados por un desajuste entre el identificador interno y el definido en la configuración de servicios.
  - Corregida la generación de informes PDF en QGIS 4 (método de impresión de `QTextDocument` no disponible en PyQt6).
  - Corregida la deformación de los logotipos institucionales (panel lateral e informe PDF) en QGIS4 y pantallas de alta densidad (HiDPI).
  - Reparación completa de la migración de servicios WMS de MAPA a MITECO.
  - Actualizado e integrado el catálogo completo de la IDE de MITECO con un total de 240 capas/servicios en la configuración (ampliado desde entonces).
  - Corregida la consulta a la API de aguas superficiales.
- **Versión 1.1.6:**
  - Optimización de la cartografía base sustituyendo el servicio WMTS del PNOA por conexión directa a teselas XYZ para un renderizado más fluido.
  - Integración del catálogo completo de servicios WMS de MITECO Costas (POEM, Zonas de Uso Prioritario, Zonas de Alto Potencial, Zonificación Eólica y DPMT).
  - Solucionado el recuento duplicado en los cruces espaciales con Provincias y Municipios (TTMM) mediante la agrupación estricta por atributos y unificación de geometrías multipartes.
  - Actualizado al catálogo PNOA2024 dentro de PNOA histórico.
- **Versión 1.1.5:**
  - Solucionado el problema del bounding box al cargar la cartografía base.
  - Nueva funcionalidad: identificación de resultados filtrados por provincias y términos municipales (TTMM) en búsqueda por punto y área.
  - Mejora en la generación de informes PDF mediante la incorporación de datos de límites administrativos.
  - Solucionada la carga de leyendas en las capas de peligrosidad por inundación fluvial y marina.
- **Versión 1.1.4:** Actualización de la descripción general del plugin en los metadatos.
- **Versión 1.1.3:**
  - Integración de nuevos servicios de datos (masas de agua OGC API Features) en los módulos de identificación espacial, buscador territorial e informes automáticos.
  - Reparación y actualización de las leyendas de múltiples servicios WMS del MITECO.
  - Reparación del zoom a nivel España al incorporar las capas base.
- **Versión 1.1.2:**
  - Nuevas capas añadidas en la sección de Calidad y Evaluación Ambiental.
  - Integración de histórico LULUCF en los servicios web.
  - Solucionado error en el cabecero de versión del plugin.
- **Versión 1.1.1:**
  - Nueva funcionalidad: búsqueda integrada de Términos Municipales (TTMM) como área de estudio.
  - Implementación de diálogo de búsqueda WFS independiente para la selección rápida de municipios.
  - Optimización de la gestión de memoria en peticiones de red (`QEventLoop`).
  - Soporte para municipios con enclaves o islas mediante unificación automática de geometrías (*unary union*).
  - Mejora en la transferencia segura de geometrías (WKT) entre interfaces gráficas.
- **Versión 1.1:**
  - Rediseño de interfaz (UI) para reducir el ancho mínimo del panel.
  - Barras de desplazamiento horizontal en tablas de resultados.
  - Reorganización de botoneras y mejora de usabilidad con botones reactivos.
  - Integración de `QProgressBar` para exportación de informes PDF.
  - Solución de renderizado High-DPI para logos institucionales.
- **Versión 1.0.x:** Corrección de títulos, limpieza de código (PEP8) y optimización de importaciones.

---

## 🏛️ Soporte y Enlaces Oficiales

Desarrollado para la **Dirección General de Biodiversidad, Bosques y Desertificación (MITECO)**.

- **Web Oficial:** <https://iepnb.gob.es/>
- **Repositorio de Código:** [GitHub - IEPNB-Tools](https://github.com/SIIB-MITECO/IEPNB-Tools)
- **Reporte de Incidencias (Issues):** [GitHub Tracker](https://github.com/SIIB-MITECO/IEPNB-Tools/issues)
- **Soporte Directo:** <buzon-bdatos@miteco.es>
