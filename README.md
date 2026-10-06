# IEPNB - Tools (v2.1.3) 🌍

**IEPNB - Tools** es el complemento de QGIS de la Dirección General de Biodiversidad, Bosques y Desertificación (MITECO) para consultar los datos del Inventario Español del Patrimonio Natural y la Biodiversidad (IEPNB) mediante servicios interoperables con el Sistema Integrado de Información de la Biodiversidad (SIIB), y para analizar el territorio con imágenes **Copernicus / Sentinel-2** (series temporales, firmas espectrales e imágenes) sin salir de QGIS.

[![QGIS](https://img.shields.io/badge/QGIS-3.22%2B%20%7C%204.x-green?style=flat-square&logo=qgis)](https://qgis.org/)
[![Versión](https://img.shields.io/badge/versi%C3%B3n-2.1.3-informational?style=flat-square)](#-historial-de-versiones-changelog)
[![MITECO Oficial](https://img.shields.io/badge/Oficial-MITECO-blue?style=flat-square)](https://www.miteco.gob.es/)

## 📌 Índice de contenidos

- [📺 Vídeo de demostración](#-vídeo-de-demostración)
- [⚙️ Instalación y requisitos](#️-instalación-y-requisitos)
- [✨ Novedades y arquitectura](#-novedades-y-arquitectura)
- [🛠️ Interfaz principal y barra inferior](#️-interfaz-principal-y-barra-inferior)
- [📋 Módulo 1: Identificar](#-módulo-1-identificar)
- [🔍 Módulo 2: Buscador](#-módulo-2-buscador)
- [🐾 Módulo 3: Especies (EIDOS)](#-módulo-3-especies-eidos)
- [🌐 Módulo 4: Servicios Web](#-módulo-4-servicios-web)
- [📸 Módulo 5: Fototeca CENEAM](#-módulo-5-fototeca-ceneam)
- [🛰️ Módulo 6: Copernicus / Sentinel-2](#️-módulo-6-copernicus--sentinel-2)
- [🔄 Historial de versiones (Changelog)](#-historial-de-versiones-changelog)
- [🏛️ Soporte y enlaces oficiales](#️-soporte-y-enlaces-oficiales)

---

## 📺 Vídeo de demostración

Haz clic en la imagen para ver el funcionamiento del plugin en YouTube:

[![Ver el vídeo del plugin](https://img.youtube.com/vi/7XWND6h2__E/hqdefault.jpg)](https://www.youtube.com/watch?v=7XWND6h2__E&vq=hd1080)

> **Nota:** el vídeo explica la instalación básica y el flujo de trabajo principal. El módulo de Copernicus / Sentinel-2 (incorporado a partir de la v2.1) todavía no aparece en él.

---

## ⚙️ Instalación y requisitos

**Desde QGIS:** menú `Complementos > Administrar e instalar complementos…`, busca **IEPNB - Tools** e instálalo.

**Instalación manual (ZIP):** `Complementos > Administrar e instalar complementos… > Instalar a partir de ZIP`, selecciona `IEPNB_Tools.zip` y pulsa *Instalar complemento*.

| Requisito | Detalle |
| --- | --- |
| **QGIS** | 3.22 o superior, incluida la serie 4.x (PyQt6). |
| **Conexión a Internet** | Todos los módulos consultan servicios remotos (IEPNB, MITECO, EIDOS, CENEAM, Copernicus). |
| **Cuenta de Copernicus (gratuita)** | Solo para el [Módulo 6](#️-módulo-6-copernicus--sentinel-2). El resto del plugin funciona sin ella. |

---

## ✨ Novedades y arquitectura

**Lo último (v2.1.x):**

- 🛰️ **Copernicus / Sentinel-2** con tres herramientas: *Índice Histórico*, *Firma Espectral* y *Ver Imagen*, accesibles desde una **galería visual de tarjetas** por categorías.
- 📤 **Exportar gráficas** (imagen PNG/JPG/SVG/PDF y CSV) desde el Índice Histórico y la Firma Espectral.
- ⭐ **Favoritos** en *Servicios Web*: tus capas habituales siempre arriba del árbol.

**Arquitectura:**

- **Compatibilidad estructural:** código preparado para QGIS 3.22 – 4.x (PyQt5/PyQt6).
- **Peticiones en segundo plano:** carga asíncrona y gestión de memoria con `QEventLoop`, tanto en los servicios WMS/WFS como en las consultas a Copernicus, para que QGIS no se quede congelado.
- **Experiencia de usuario:** barra de progreso en la exportación de informes PDF, tablas con desplazamiento horizontal, logotipos nítidos en pantallas High-DPI y gráficas interactivas con zoom e inspección de valores.
- **Autenticación segura:** las credenciales de Copernicus se guardan cifradas en el *Authentication Manager* de QGIS, nunca en texto plano.
- **Catálogo de servicios:** **33 categorías** temáticas y **351 capas** WMS/WMTS indexadas y buscables desde la pestaña *Servicios Web*.

---

## 🛠️ Interfaz principal y barra inferior

La barra inferior reúne accesos directos que cargan con un clic un conjunto ya agrupado de capas de la IDE de MITECO (el catálogo completo se explora desde [Servicios Web](#-módulo-4-servicios-web)). Las capas se organizan en el grupo **«Servicios MITECO»** del panel de capas.

| Botón | Qué carga |
| --- | --- |
| **Banco de Datos de la Naturaleza (BDN)** | Espacios Protegidos y Propiedad (ENP, RN2000, IBAs, RAMPE, MUP, Vías Pecuarias) · Convenios Internacionales (MAB, OSPAR, RAMSAR, ZEPIM, Geoparque) · Mapa Forestal Español (Foto Fija MFE) · Ecosistemas, Hábitats y Paisaje · Fauna, Flora y Recursos Genéticos · Erosión e Incendios Forestales (INES) · EIKOS (alertas anuales, mensuales y cambios de vegetación) |
| **SNCZI** | Cartografía de Zonas Inundables: áreas con riesgo potencial significativo de inundación (ARPSI) |
| **Sistema de Información de Redes (SIR – DGA)** | Hidrología Cuantitativa (SIMPA, SAIH, ERHIN) · Reservas Hidrológicas y Zonas Protegidas · Saneamiento, Vertidos y Nitratos · DPH, Hidromorfología y Restauración · Seguimiento de Aguas Superficiales y Subterráneas · Masas de Agua y Estado (PHC 2022-2027) · Planificación, Ámbitos e Hidrografía |
| **Costas (DGC)** | Estrategias Marinas · POEM (Planes de Ordenación del Espacio Marítimo) · Dominio Público Marítimo-Terrestre y Gestión |
| **CEA** | Ruido Ambiental (UME y MER) · Emisiones Industriales, Residuos y Sensibilidad a Renovables · Calidad del Aire (general y por contaminante) · Cambio Climático y LULUCF |

**Herramientas de contexto transversales**

| Botón | Función |
| --- | --- |
| **Cartografía Base** | Carga la ortofoto de máxima actualidad del PNOA (teselas XYZ) y los límites administrativos oficiales, siempre al fondo del proyecto. |
| **Google Street View** | Convierte el cursor en una herramienta: al hacer clic en el mapa abre Street View en el navegador, en esas coordenadas. |
| **Copernicus** | Abre la galería de [Copernicus / Sentinel-2](#️-módulo-6-copernicus--sentinel-2): Firma Espectral, Ver Imagen e Índice Histórico. |

---

## 📋 Módulo 1: Identificar

Núcleo del análisis espacial: define una zona de estudio y el plugin consulta qué figuras de protección y qué especies hay en ella, con cálculo de superficies e informe.

### 1. Herramientas de selección

| Botón | Qué hace |
| --- | --- |
| **Punto** | Identificación con un clic. Aplica un pequeño buffer alrededor del punto para capturar también elementos colindantes. |
| **Área** | Dibujo manual de un polígono (clic izquierdo para añadir vértices, clic derecho para terminar). |
| **TTMM** | Busca un **término municipal** por nombre (autocompletado desde 3 letras, sin distinguir tildes) y lo usa directamente como zona de estudio. Si el municipio tiene enclaves o islas, se unifican en una sola geometría. |
| **Importar** | Carga un polígono desde un archivo externo (KMZ, KML, Shapefile, GeoJSON, GPKG). |
| **Limpiar** | Borra la zona de estudio dibujada pero conserva la tabla de resultados. |

### 2. Qué se analiza

ENP, Red Natura 2000 (ZEC y ZEPA), Montes de Utilidad Pública, Vías Pecuarias, IBAs, Áreas Marinas Protegidas (RAMPE), malla de riqueza de especies y Convenios Internacionales (MAB, RAMSAR, OSPAR, ZEPIM, Geoparques). Incluye también el análisis de masas de agua mediante OGC API Features y el cruce con provincias y términos municipales.

### 3. Acciones y resultados

| Botón | Qué hace |
| --- | --- |
| **Añadir Todas** / **Añadir Grupo** | Lleva al panel de capas de QGIS los resultados de la tabla (todos, o solo un grupo). |
| **Intersección** | Intersecta los resultados con tu zona y calcula las **hectáreas / metros** exactos de afección, proyectando a los sistemas oficiales de España (ETRS89 UTM huso 30 para Península y Baleares; REGCAN95 huso 28 para Canarias). Se activa tras añadir capas. |
| **CSV** | Exporta todos los solapes identificados. |
| **Informe PDF** | Genera un documento técnico con mapa de la zona, tabla de superficies/distancias y listado de especies (con enlace a su ficha EIDOS). Se activa tras calcular la intersección. |
| **Borrar** | Limpieza total: elimina las capas temporales, vacía la tabla y el grupo «Consultas IEPNB». |

---

## 🔍 Módulo 2: Buscador

Motor de búsqueda para **localizar y cargar solo lo que necesitas** en vez de añadir capas enteras de toda España. Complementa al botón TTMM de *Identificar*: aquí el objetivo es explorar y visualizar, no lanzar un análisis.

- **Dos vías de consulta**, combinables: por *nombre* y por *tipo / información* (por ejemplo, «Parque Natural»).
- **Capas consultadas:** límites administrativos (CCAA, provincias, términos municipales), ENP, RN2000, MUP, Vías Pecuarias, IBAs, RAMPE, riqueza de especies y Convenios Internacionales.
- **Municipios con enclaves o islas:** se unifican automáticamente en un único multipolígono.
- **Resultados:** tabla con redimensionado automático, botón *Añadir* por fila, *Añadir todas* y exportación a CSV.

---

## 🐾 Módulo 3: Especies (EIDOS)

Acceso directo a la API del Inventario Español de Especies Silvestres (EIDOS).

- **Búsqueda** por Taxón ID, nombre científico o nombre común. Respeta la ortografía oficial del catálogo, tildes incluidas.
- **Ficha oficial:** el Taxón ID es un enlace a la ficha del taxón en el portal del IEPNB.
- **Estado de protección** de cada especie, consultable desde la tabla.
- **Fotos:** galería con las imágenes vinculadas al taxón en EIDOS.
- **Distribución:** si el servidor dispone de ella, el botón *Añadir* descarga la cuadrícula de distribución y la carga en QGIS con simbología propia.

---

## 🌐 Módulo 4: Servicios Web

Catálogo buscable de servicios WMS/WMTS: **33 categorías y 351 capas**, sin configurar conexiones ni sistemas de coordenadas.

| Prefijo | Ámbito | Contenido |
| --- | --- | --- |
| **[IEPNB]** | Biodiversidad, bosques y espacios protegidos | Espacios Protegidos y Propiedad · Convenios Internacionales · Mapa Forestal Español · Ecosistemas, Hábitats y Paisaje · Fauna, Flora y Recursos Genéticos · Erosión e Incendios Forestales (INES) · EIKOS (alertas anuales y mensuales, cambios anuales de vegetación) |
| **[DGA]** | Agua | Planificación e Hidrografía · Masas de Agua y Estado (PHC 2022-2027) · Seguimiento de Aguas Superficiales y Subterráneas · DPH e Hidromorfología · Saneamiento, Vertidos y Nitratos · Reservas Hidrológicas · Hidrología Cuantitativa · SNCZI |
| **[DGC]** | Costas y mar | Dominio Público Marítimo-Terrestre · POEM · Estrategias Marinas |
| **[DGCEA]** | Calidad y Evaluación Ambiental | Cambio Climático y LULUCF · Calidad del Aire (general y por contaminante) · Emisiones Industriales y Residuos · Ruido Ambiental |
| **[IGN]** | Cartografía de referencia | PNOA Histórico (ortofotos anuales 2004-2024 y vuelos históricos: Americano Serie B 1956-57, Interministerial 1973-86, Nacional 1981-86, OLISTAT 1997-98, SIGPAC 1997-2003) · Redes de Transporte (carretera, ferrocarril, aéreo, marítimo) |
| **[COPERNICUS]** | Observación de la Tierra | Corine Land Cover y Backbone (CLC+) · High Resolution Layers y capas locales |

**Cómo se usa**

- **Filtro de texto** sobre todo el árbol: escribe parte del nombre y el árbol se filtra al instante.
- **Doble clic** o botón **Añadir al Mapa** para cargar una capa; **Eliminar** la retira del proyecto. Las capas se agrupan en el grupo «Servicios Web».
- ⭐ **Favoritos** *(nuevo en v2.1.3)*: selecciona una capa y pulsa **☆ Favorito** (o clic derecho → *Añadir a favoritos*). Aparece en el grupo **⭐ Favoritos**, siempre arriba del árbol, y en negrita dentro del catálogo. Se guardan en la configuración de QGIS, así que **persisten entre sesiones**. Al buscar, el grupo se oculta para no duplicar resultados.

---

## 📸 Módulo 5: Fototeca CENEAM

Consulta de la Fototeca del CENEAM (Centro Nacional de Educación Ambiental) desde QGIS.

- Búsqueda libre por cualquier dato del catálogo.
- Resultados en **tarjetas** con imagen, título, autor y provincia.
- **Ver original** abre la imagen en máxima resolución; **Descargar** la guarda en tu disco con un nombre de archivo saneado.

> ⚖️ Las imágenes son propiedad del CENEAM (MITECO) y su uso está sujeto a las condiciones de la Fototeca.

---

## 🛰️ Módulo 6: Copernicus / Sentinel-2

Teledetección integrada en el plugin: consulta **Sentinel-2 L2A** (reflectancia de superficie) para cualquier punto de España, procesada en la nube por **Copernicus Data Space Ecosystem (CDSE)** mediante la *Statistical API* y la *Process API*.

### 1. La galería de Copernicus

Al pulsar el botón de Copernicus se abre una **galería de tarjetas** con color e icono por categoría. Pasa el ratón sobre una tarjeta para ver su fórmula, rango e interpretación.

| Tarjeta | Qué hace |
| --- | --- |
| **Firma espectral** | Reflectancia de las 12 bandas en un punto y una fecha ([ver apartado 3](#3-firma-espectral)). |
| **Ver imagen** | Descarga una imagen Sentinel-2 y la carga como capa ráster ([ver apartado 4](#4-ver-imagen)). |
| **Un índice** (NDVI, NBR…) | Abre la serie temporal de ese índice en un punto ([ver apartado 2](#2-índice-histórico)). |

**Los 11 índices espectrales**

| Categoría | Índices | Para qué sirven |
| --- | --- | --- |
| 🌿 **Vegetación** | NDVI, EVI, SAVI, GNDVI, CIRE | Vigor y densidad de la vegetación. EVI corrige la saturación en biomasa alta, SAVI el efecto del suelo, y GNDVI y CIRE detectan antes el estrés de clorofila. |
| 💧 **Agua y nieve** | NDWI, NDMI, NDSI | Agua superficial (NDWI), humedad de la vegetación y estrés hídrico (NDMI) y cobertura de nieve (NDSI). |
| 🔥 **Incendios y suelo desnudo** | NBR, BAI, BSI | Severidad de área quemada (NBR, BAI) y suelo desnudo expuesto, útil para seguir la regeneración tras un incendio (BSI). |

### 2. Índice Histórico

Haz clic en un índice de la galería y después en el mapa: se abre la **serie temporal completa desde 2017**, con una observación cada 5 días (se descartan nubes y sombras con la banda SCL, y escenas con más de un 80 % de nubosidad).

- **Periodo:** botones de 1, 3 y 5 años o todo el histórico, sin repetir la consulta.
- **Comparar dos índices:** **+ Añadir índice** superpone un segundo índice (p. ej. NDVI frente a NDMI, o NBR frente a BAI), cada uno con su eje Y y su color.
- **Lectura:** observaciones brutas atenuadas de fondo y media móvil encima; al pasar el ratón se muestran la fecha y el valor exacto del punto más cercano.
- **Zoom:** lupa por rectángulo, desplazamiento (*pan*) y *Home* para volver a la vista completa.
- **Ficha del índice** bajo la gráfica: fórmula, rango típico y cómo interpretarlo.

### 3. Firma Espectral

Para un punto y una **fecha aproximada**, el plugin busca la adquisición más despejada de nubes en una ventana de **±15 días** y dibuja la reflectancia de las 12 bandas frente a la longitud de onda.

- **Fecha usada:** se indica cuál es, la diferencia con la pedida y la cobertura despejada en el punto (con aviso si es baja).
- **Referencia más parecida:** compara tu firma con 7 firmas de referencia (*vegetación sana, vegetación seca (NPV), suelo desnudo, urbano/construido, quemado/carbón, agua y nieve*) usando el **ángulo espectral (SAM)**.
- **+ Comparar con referencia:** superpone una o varias de esas firmas en la gráfica.

### 4. Ver Imagen

Descarga una imagen real de Sentinel-2 y la carga en tu proyecto como **capa ráster georreferenciada**.

1. Elige **Ver imagen** en la galería.
2. **Ubicación:** *Punto* (recorte fijo de 2 × 2 km centrado en tu clic) o *Dibujar área* (polígono a mano, **hasta 1000 km²**; la imagen se recorta a la forma exacta del polígono, no a su rectángulo envolvente).
3. **Estilo:** *Color real*, *Falso color infrarrojo* o cualquiera de los 11 índices.
4. Elige la fecha: se usa la más despejada de nubes dentro de ±15 días.

Los índices se descargan como **valor real de una sola banda** (no como color ya aplicado), con un estilo de QGIS que los muestra coloreados pero te permite consultar el valor exacto de cada píxel o reclasificarlo.

> ⚠️ **Resolución en áreas grandes.** La imagen se pide con un máximo de **1024 píxeles por lado**. Sentinel-2 ofrece 10 m/píxel, así que esa resolución se conserva mientras el lado mayor del área no supere ~10,2 km (unos 105 km² en un cuadrado). Por encima, cada píxel cubre más terreno (p. ej. ~30 m en un área cuadrada de 1000 km²). Si necesitas 10 m, divide el área en trozos más pequeños.

### 5. Exportar gráficas *(nuevo en v2.1.3)*

El botón **Exportar** del Índice Histórico y de la Firma Espectral ofrece:

- **Gráfica como imagen:** PNG, JPG, SVG o PDF, tal y como la ves (periodo y zoom actuales), con la atribución de Copernicus incluida.
- **Datos como CSV:**
  - *Índice Histórico:* el periodo mostrado, con el valor de cada observación y la curva suavizada (y el segundo índice, si estás comparando).
  - *Firma Espectral:* una fila por banda, con su reflectancia y, si las has superpuesto, las referencias.
  - Elige el formato al guardar: **CSV para Excel en español** (separador `;` y coma decimal) o **CSV estándar** (separador `,` y punto decimal).

### 6. Autenticación y cuota

Necesitas una cuenta gratuita en [dataspace.copernicus.eu](https://dataspace.copernicus.eu) y un **OAuth Client** (Client ID y Client Secret) creado en el *Dashboard* de Sentinel Hub: **no** es el usuario y contraseña de tu cuenta. El plugin te lo pide una sola vez, con instrucciones paso a paso, y lo guarda cifrado en el *Authentication Manager* de QGIS.

Una cuenta gratuita (*Copernicus General*) dispone de **10.000 unidades de procesamiento y 10.000 peticiones al mes**, que se renuevan el día 1. Las series históricas y las firmas suelen consumir poco; **Ver Imagen consume más cuanto mayor es el área**. Puedes consultar tu saldo en el Dashboard de CDSE.

### 7. Origen de los datos y licencia

Los datos proceden del programa **Copernicus** (ESA / Unión Europea), de acceso libre y gratuito según la *Legal Notice on the use of Copernicus Sentinel Data*, que exige atribución al redistribuir: *«Copernicus Sentinel data [año]»*. El plugin muestra este aviso en las gráficas y lo incluye en las imágenes exportadas. Los datos se ofrecen sin garantía expresa ni implícita de exactitud.

---

## 🔄 Historial de versiones (Changelog)

- **Versión 2.1.3:**
  - **Exportar gráficas:** botón *Exportar* en el Índice Histórico y la Firma Espectral para guardar la gráfica como imagen (PNG, JPG, SVG, PDF) o los datos como CSV (formato Excel en español o estándar).
  - **Servicios Web:** nuevos favoritos (botón ☆ Favorito y menú contextual), con grupo «⭐ Favoritos» fijo arriba del árbol y persistencia entre sesiones.
  - El título del panel y del menú del plugin lee ahora la versión de `metadata.txt`.
- **Versión 2.1.2:** el límite de área de *Ver Imagen* sube a 1000 km².
- **Versión 2.1.1:**
  - Selección de Copernicus rediseñada: galería de tarjetas visuales por categorías en lugar de un menú desplegable anidado.
  - Nueva funcionalidad **Ver Imagen** (color real, falso color infrarrojo o cualquiera de los índices, por punto o por área dibujada).
  - Nueva funcionalidad **Firma Espectral**, con comparación frente a 7 firmas de referencia.
  - Índices espectrales ampliados a 11 (se añaden NDSI, BSI y CIRE), organizados por categorías.
- **Versión 2.1.0:**
  - Nueva funcionalidad **Índice Histórico** (NDVI, NDWI, NBR, EVI, NDMI, GNDVI, SAVI y BAI) con la serie temporal desde 2017 vía Statistical API de CDSE, enmascarado de nubes y sombras por banda SCL y muestreo cada 5 días.
  - Autenticación mediante OAuth Client, guardada cifrada en el *Authentication Manager* de QGIS.
  - Gráfica con media móvil, filtro de periodo, zoom, inspección de valores, comparación de dos índices y aviso de fuente y licencia.
- **Versión 2.0:**
  - Compatibilidad con QGIS 4.x (PyQt6), manteniendo QGIS 3.22+.
  - Corregidos fallos silenciosos en Buscador, TTMM, ficha de especies y Fototeca CENEAM por el acceso a enums de `QNetworkReply` incompatibles con PyQt6.
  - Solucionado el buscador de términos municipales (TTMM).
  - Corregida la generación de informes PDF en QGIS 4 y la deformación de logotipos en pantallas HiDPI.
  - Migración completa de los servicios WMS de MAPA a MITECO y catálogo ampliado de la IDE de MITECO.
  - Corregida la consulta a la API de aguas superficiales.
- **Versión 1.1.6:** cartografía base con teselas XYZ del PNOA; catálogo completo de Costas (POEM, DPMT…); corregido el recuento duplicado en cruces con provincias y municipios; catálogo PNOA2024.
- **Versión 1.1.5:** corregido el *bounding box* de la cartografía base; identificación por provincias y términos municipales en búsquedas por punto y área; límites administrativos en los informes PDF; leyendas de peligrosidad por inundación.
- **Versión 1.1.4:** actualización de la descripción general en los metadatos.
- **Versión 1.1.3:** masas de agua (OGC API Features) en identificación, buscador e informes; leyendas de servicios WMS reparadas; zoom a nivel España al cargar las capas base.
- **Versión 1.1.2:** nuevas capas de Calidad y Evaluación Ambiental; histórico LULUCF; corregido el título de versión del plugin.
- **Versión 1.1.1:** búsqueda de términos municipales (TTMM) como zona de estudio, con diálogo WFS y soporte para enclaves e islas; mejor gestión de memoria en peticiones de red.
- **Versión 1.1:** rediseño de la interfaz (panel más estrecho), barras de desplazamiento horizontal, botoneras reorganizadas, barra de progreso en la exportación de PDF y logotipos High-DPI.
- **Versión 1.0.x:** corrección de títulos, limpieza de código (PEP8) y optimización de importaciones.

---

## 🏛️ Soporte y enlaces oficiales

Desarrollado para la **Dirección General de Biodiversidad, Bosques y Desertificación (MITECO)**.

- **Web oficial:** <https://iepnb.gob.es/>
- **Repositorio de código:** [GitHub – IEPNB-Tools](https://github.com/SIIB-MITECO/IEPNB-Tools)
- **Reporte de incidencias:** [GitHub Tracker](https://github.com/SIIB-MITECO/IEPNB-Tools/issues)
- **Soporte directo:** <buzon-bdatos@miteco.es>
