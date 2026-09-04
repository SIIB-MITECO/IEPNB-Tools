"""
/***************************************************************************
 * IEPNB Tools - Herramientas para el Inventario Español (MITECO)          *
 * *                                                                       *
 * Copyright (C) 2026 Rodrigo Saz-Orozco Maier (IEPNB - MITECO)            *
 * Email: rsazorozco@miteco.es                                             *
 * *                                                                       *
 * This program is free software; you can redistribute it and/or modify    *
 * it under the terms of the GNU General Public License as published by    *
 * the Free Software Foundation; either version 3 of the License, or       *
 * (at your option) any later version.                                     *
 ***************************************************************************/

--- ACTUALIZADO tras revisión del Directorio de Servicios MITECO ---
Cambios principales respecto a la versión anterior:
  - Agua y Costas migrados de wms.mapama.gob.es/sig/... a
    gis.miteco.gob.es/geoserver/agua|costas/<capa>/wms (nombres de capa
    GeoServer nativos, ya no INSPIRE genéricos tipo HY.PhysicalWaters...).
  - Añadidos nuevos servicios de Biodiversidad (Hábitat Art17/12, IEZH,
    Atlas de Paisajes, Regiones Biogeográficas, Erosión, Incendios
    Forestales por frecuencia, etc.) publicados en el directorio pero
    no incluidos hasta ahora.
  - GEOPARQUE (convenio_internacional) ya NO aparece listado en el
    directorio oficial actual: se mantiene en el config pero revisar
    si sigue vigente.
  - Montes de Utilidad Pública: el directorio muestra una capa
    "propiedad_montes_2025" que podría sustituir a "propiedad_montes"
    (sin año) usada en CONFIG_IDENTIFY/CONFIG_TERRITORY; no se ha
    confirmado con capabilities, así que NO se ha tocado ese WFS.
  - EIKOS (Alertas Anuales/Mensuales) no aparece en el directorio
    público: probablemente sea un servicio interno IEPNB; se deja
    igual por no encontrar confirmación de cambio ni de baja.
  - LULUCF, PNOA Histórico, Corine Land Cover y Copernicus HRL son
    servicios externos (no MITECO/IEPNB): no se han verificado en esta
    revisión y se mantienen igual.
"""

# --- CAMBIO PARA COMPATIBILIDAD QGIS 3 Y 4 ---
from qgis.PyQt.QtGui import QColor

# --- SERVIDORES BASE ---
BASE_GEOSERVER = "https://pro.iepnb.gob.es/geoserver"
BASE_API_EIDOS = "https://iepnb.gob.es/api"
BASE_GISMITECO = "https://gis.miteco.gob.es/geoserver"
BASE_IGN_TRANSPORTES = "https://servicios.idee.es/wms-inspire/transportes"

# --- CONFIGURACIÓN PARA IDENTIFICACIÓN (identify.py) ---
CONFIG_IDENTIFY = [
    {"id": "Provincia", "url": f"{BASE_GEOSERVER}/cartografia_base/wfs", "layer": "cartografia_base:provincias", "col_nom": "nut3_nom", "col_inf": "id", "color": QColor(0, 0, 255)},
    {"id": "Municipio", "url": f"{BASE_GEOSERVER}/cartografia_base/wfs", "layer": "cartografia_base:ttmm", "col_nom": "nombre", "col_inf": "municipio", "color": QColor(255, 0, 0)},
    {"id": "ENP", "url": f"{BASE_GEOSERVER}/ENP/wfs", "layer": "ENP:enp", "col_nom": "nombre", "col_inf": "figura", "color": QColor(165, 214, 167)},
    {"id": "RN2000", "url": f"{BASE_GEOSERVER}/RN2000/wfs", "layer": "RN2000:rn2000", "col_nom": "nombre", "col_inf": "desc_figura", "color": QColor(144, 202, 249)},
    {"id": "IBAs", "url": f"{BASE_GEOSERVER}/espacios_protegidos/wfs", "layer": "espacios_protegidos:ibas", "col_nom": "nombre", "col_inf": "ca", "color": QColor(255, 241, 118)},
    {"id": "Montes UP", "url": f"{BASE_GEOSERVER}/propiedad_montes/wfs", "layer": "propiedad_montes:propiedad_montes", "col_nom": "monte", "col_inf": "monte_ca", "color": QColor(141, 110, 99)},
    {"id": "V. Pecuarias", "url": f"{BASE_GEOSERVER}/vias_pecuarias/wfs", "layer": "vias_pecuarias:rgvp_2024", "col_nom": "nb_via", "col_inf": "nb_canada", "color": QColor(240, 98, 146)},
    {"id": "Á. Marinas", "url": f"{BASE_GEOSERVER}/areas_marinas_protegidas/wfs", "layer": "areas_marinas_protegidas:rampe", "col_nom": "site_name", "col_inf": "tipo", "color": QColor(77, 182, 172)},
    {"id": "Riqueza Esp.", "url": f"{BASE_GEOSERVER}/especies/wfs", "layer": "especies:riqueza_especies", "col_nom": "id", "col_inf": "lista_idstaxon_filtro", "color": QColor(156, 39, 176)},
    {"id": "Reservas de la Biosfera", "url": f"{BASE_GEOSERVER}/convenio_internacional/wfs", "layer": "convenio_internacional:MAB", "col_nom": "nombre", "col_inf": "nombre", "color": QColor(46, 125, 50)},
    {"id": "OSPAR", "url": f"{BASE_GEOSERVER}/convenio_internacional/wfs", "layer": "convenio_internacional:OSPAR", "col_nom": "nombre", "col_inf": "nombre", "color": QColor(21, 101, 192)},
    {"id": "RAMSAR", "url": f"{BASE_GEOSERVER}/convenio_internacional/wfs", "layer": "convenio_internacional:RAMSAR", "col_nom": "nombre", "col_inf": "nombre", "color": QColor(0, 150, 136)},
    {"id": "ZEPIM", "url": f"{BASE_GEOSERVER}/convenio_internacional/wfs", "layer": "convenio_internacional:ZEPIM", "col_nom": "nombre", "col_inf": "nombre", "color": QColor(173, 20, 87)},
    {"id": "Geoparque", "url": f"{BASE_GEOSERVER}/convenio_internacional/wfs", "layer": "convenio_internacional:GEOPARQUE", "col_nom": "nombre", "col_inf": "nombre", "color": QColor(230, 81, 0)},
    {
        "id": "Masas Agua Sub.",
        "url": f"{BASE_GISMITECO}/ogc/features/v1/collections/agua:masas_aguasub_2027",
        "type": "OAPIF",
        "layer": None,
        "col_nom": "nom_masa",
        "col_inf": "cod_masa",
        "color": QColor(33, 150, 243)
    },
    {
        "id": "Masas Agua Sup. (Líneas)",
        "url": f"{BASE_GISMITECO}/ogc/features/v1/collections/agua:masas_aguaspf_2027_l",
        "type": "OAPIF",
        "layer": None,
        "col_nom": "nom_masa",
        "col_inf": "cod_masa",
        "color": QColor(3, 169, 244)
    },
    {
        "id": "Masas Agua Sup. (Polígonos)",
        "url": f"{BASE_GISMITECO}/ogc/features/v1/collections/agua:masas_aguaspf_2027_a",
        "type": "OAPIF",
        "layer": None,
        "col_nom": "nom_masa",
        "col_inf": "cod_masa",
        "color": QColor(0, 188, 212)
    }
]

# Alias para compatibilidad con código existente
CONFIG_SERVICIOS = CONFIG_IDENTIFY

# --- CONFIGURACIÓN PARA TERRITORIO (territory.py) SIN DUPLICADOS ---
CONFIG_TERRITORY = [
    {"id": "CCAA", "url": f"{BASE_GEOSERVER}/cartografia_base/wfs", "layer": "cartografia_base:ccaa", "col_nom": "nut2_nom", "col_inf": "id", "color": QColor(0, 0, 255)}
] + CONFIG_IDENTIFY

# --- SERVICIOS WMS/WMTS (services_iepnb.py) ---
CATALOGO_WMS = {
    # =========================================================================
    # [IEPNB] INVENTARIO ESPAÑOL DEL PATRIMONIO NATURAL Y LA BIODIVERSIDAD
    # =========================================================================
    "[IEPNB] Espacios Protegidos y Propiedad": {
        "Espacios Naturales Protegidos (ENP)": {"url": f"{BASE_GEOSERVER}/ENP/wms", "layers": "enp"},
        "Red Natura 2000 (RN2000)": {"url": f"{BASE_GEOSERVER}/RN2000/wms", "layers": "rn2000"},
        "IBAs (Áreas Importantes para Aves)": {"url": f"{BASE_GEOSERVER}/espacios_protegidos/wms", "layers": "ibas"},
        "Áreas Marinas Protegidas (RAMPE)": {"url": f"{BASE_GEOSERVER}/areas_marinas_protegidas/wms", "layers": "rampe"},
        "Montes de Utilidad Pública (MUP)": {"url": f"{BASE_GEOSERVER}/propiedad_montes/wms", "layers": "propiedad_montes"},
        "Vías Pecuarias": {"url": f"{BASE_GEOSERVER}/vias_pecuarias/wms", "layers": "rgvp_2024"}
    },
    "[IEPNB] Convenios Internacionales": {
        "Reservas de la Biosfera (MAB)": {"url": f"{BASE_GEOSERVER}/convenio_internacional/wms", "layers": "MAB"},
        "OSPAR": {"url": f"{BASE_GEOSERVER}/convenio_internacional/wms", "layers": "OSPAR"},
        "RAMSAR": {"url": f"{BASE_GEOSERVER}/convenio_internacional/wms", "layers": "RAMSAR"},
        "ZEPIM": {"url": f"{BASE_GEOSERVER}/convenio_internacional/wms", "layers": "ZEPIM"},
        "Geoparque": {"url": f"{BASE_GEOSERVER}/convenio_internacional/wms", "layers": "GEOPARQUE"}
    },
    "[IEPNB] Mapa Forestal Español (Foto Fija MFE)": {
        "MFE - Tipo de Bosque": {"url": f"{BASE_GEOSERVER}/foto_fija_mfe/wms", "layers": "ff_tipo_bosque"},
        "MFE - Uso": {"url": f"{BASE_GEOSERVER}/foto_fija_mfe/wms", "layers": "ff_uso"}
    },
    "[IEPNB] Ecosistemas, Hábitats y Paisaje": {
        "Distribución de Hábitat Artículo 12 (2007-2012)": {"url": f"{BASE_GEOSERVER}/ecosistemas/wms", "layers": "habitats_art12_2007_2012"},
        "Distribución de Hábitat Artículo 17 (2013-2018)": {"url": f"{BASE_GEOSERVER}/ecosistemas/wms", "layers": "habitats_art17_2013_2018"},
        "Rangos de Hábitat Artículo 17 (2013-2018)": {"url": f"{BASE_GEOSERVER}/ecosistemas/wms", "layers": "rangos_habitat_art17_2013_2018"},
        "Humedales y Turberas (BCAM2)": {"url": f"{BASE_GEOSERVER}/ecosistemas/wms", "layers": "hum_turb_bcam2"},
        "Inventario Español de Zonas Húmedas (IEZH)": {"url": f"{BASE_GEOSERVER}/ecosistemas/wms", "layers": "iezh"},
        "Atlas de los Paisajes de España": {"url": f"{BASE_GEOSERVER}/ecosistemas/wms", "layers": "atlas_paisajes"},
        "Regiones Biogeográficas": {"url": f"{BASE_GEOSERVER}/cartografia_base/wms", "layers": "regbiogeograf_termar"}
    },
    "[IEPNB] Fauna, Flora y Recursos Genéticos": {
        "Distribución de Aves Artículo 12 (2013-2018)": {"url": f"{BASE_GEOSERVER}/especies/wms", "layers": "distribucion_aves_art12_2013_2018"},
        "Distribución de Especies Artículo 17 (2013-2018)": {"url": f"{BASE_GEOSERVER}/especies/wms", "layers": "distribucion_especies_art17_2013_2018"},
        "Rangos de Especies Artículo 17 (2013-2018)": {"url": f"{BASE_GEOSERVER}/especies/wms", "layers": "rangos_especies_art17_2013_2018"},
        "Región de Procedencia (Recursos Genéticos)": {"url": f"{BASE_GEOSERVER}/recursos_geneticos/wms", "layers": "region_procedencia"}
    },
    "[IEPNB] Erosión e Incendios Forestales (INES)": {
        "Erosión de Cauces": {"url": f"{BASE_GEOSERVER}/INES/wms", "layers": "erosion_cauces"},
        "Erosión Eólica": {"url": f"{BASE_GEOSERVER}/INES/wms", "layers": "ErosionEolica"},
        "Erosión Laminar": {"url": f"{BASE_GEOSERVER}/INES/wms", "layers": "ErosionLaminarNiveles"},
        "Erosión Potencial": {"url": f"{BASE_GEOSERVER}/INES/wms", "layers": "ErosionPotencialNiveles"},
        "Movimientos en Masa": {"url": f"{BASE_GEOSERVER}/INES/wms", "layers": "MovimientosMasa"},
        "Frecuencia de Incendios Forestales (1996-2005)": {"url": f"{BASE_GEOSERVER}/incendios_forestales/wms", "layers": "frec_incend_1996_2005"},
        "Frecuencia de Incendios Forestales (2006-2015)": {"url": f"{BASE_GEOSERVER}/incendios_forestales/wms", "layers": "frec_incend_2006_2015"}
    },
    "[IEPNB] EIKOS - Alertas Anuales": {
        "Alertas Anuales 2025": {"url": f"{BASE_GEOSERVER}/alertas_anuales_vegetacion/wms", "layers": "alertas_anuales_2025"},
        "Alertas Anuales 2024": {"url": f"{BASE_GEOSERVER}/alertas_anuales_vegetacion/wms", "layers": "alertas_anuales_2024"},
        "Alertas Anuales 2023": {"url": f"{BASE_GEOSERVER}/alertas_anuales_vegetacion/wms", "layers": "alertas_anuales_2023"},
        "Alertas Anuales 2022": {"url": f"{BASE_GEOSERVER}/alertas_anuales_vegetacion/wms", "layers": "alertas_anuales_2022"},
        "Alertas Anuales 2021": {"url": f"{BASE_GEOSERVER}/alertas_anuales_vegetacion/wms", "layers": "alertas_anuales_2021"},
        "Alertas Anuales 2020": {"url": f"{BASE_GEOSERVER}/alertas_anuales_vegetacion/wms", "layers": "alertas_anuales_2020"}
    },
    "[IEPNB] EIKOS - Alertas Mensuales": {
        "Alertas Mensuales - Enero": {"url": f"{BASE_GEOSERVER}/EIKOS_Alertas/wms", "layers": "Alertas_ENE"},
        "Alertas Mensuales - Febrero": {"url": f"{BASE_GEOSERVER}/EIKOS_Alertas/wms", "layers": "Alertas_FEB"},
        "Alertas Mensuales - Marzo": {"url": f"{BASE_GEOSERVER}/EIKOS_Alertas/wms", "layers": "Alertas_MAR"},
        "Alertas Mensuales - Abril": {"url": f"{BASE_GEOSERVER}/EIKOS_Alertas/wms", "layers": "Alertas_ABR"},
        "Alertas Mensuales - Mayo": {"url": f"{BASE_GEOSERVER}/EIKOS_Alertas/wms", "layers": "Alertas_MAY"},
        "Alertas Mensuales - Junio": {"url": f"{BASE_GEOSERVER}/EIKOS_Alertas/wms", "layers": "Alertas_JUN"},
        "Alertas Mensuales - Julio": {"url": f"{BASE_GEOSERVER}/EIKOS_Alertas/wms", "layers": "Alertas_JUL"},
        "Alertas Mensuales - Agosto": {"url": f"{BASE_GEOSERVER}/EIKOS_Alertas/wms", "layers": "Alertas_AGO"},
        "Alertas Mensuales - Septiembre": {"url": f"{BASE_GEOSERVER}/EIKOS_Alertas/wms", "layers": "Alertas_SEP"},
        "Alertas Mensuales - Octubre": {"url": f"{BASE_GEOSERVER}/EIKOS_Alertas/wms", "layers": "Alertas_OCT"},
        "Alertas Mensuales - Noviembre": {"url": f"{BASE_GEOSERVER}/EIKOS_Alertas/wms", "layers": "Alertas_NOV"},
        "Alertas Mensuales - Diciembre": {"url": f"{BASE_GEOSERVER}/EIKOS_Alertas/wms", "layers": "Alertas_DIC"}
    },
    "[IEPNB] EIKOS - Cambios Anuales de Vegetación": {
        "Pérdidas de Vegetación 2024": {"url": f"{BASE_GEOSERVER}/cambios_anuales_vegetacion/wms", "layers": "cambios_or_2024_perdidas"},
        "Ganancias de Vegetación 2024": {"url": f"{BASE_GEOSERVER}/cambios_anuales_vegetacion/wms", "layers": "cambios_or_2024_ganancias"},
        "Pérdidas de Vegetación 2023": {"url": f"{BASE_GEOSERVER}/cambios_anuales_vegetacion/wms", "layers": "cambios_or_2023_perdidas"},
        "Ganancias de Vegetación 2023": {"url": f"{BASE_GEOSERVER}/cambios_anuales_vegetacion/wms", "layers": "cambios_or_2023_ganancias"},
        "Pérdidas de Vegetación 2022": {"url": f"{BASE_GEOSERVER}/cambios_anuales_vegetacion/wms", "layers": "cambios_or_2022_perdidas"},
        "Ganancias de Vegetación 2022": {"url": f"{BASE_GEOSERVER}/cambios_anuales_vegetacion/wms", "layers": "cambios_or_2022_ganancias"},
        "Pérdidas de Vegetación 2021": {"url": f"{BASE_GEOSERVER}/cambios_anuales_vegetacion/wms", "layers": "cambios_or_2021_perdidas"},
        "Ganancias de Vegetación 2021": {"url": f"{BASE_GEOSERVER}/cambios_anuales_vegetacion/wms", "layers": "cambios_or_2021_ganancias"}
    },

    # =========================================================================
    # [DGA] DIRECCIÓN GENERAL DEL AGUA
    # =========================================================================
    "[DGA] Planificación, Ámbitos e Hidrografía": {
        "Demarcaciones Hidrográficas (PHC 2022-2027)": {"url": f"{BASE_GISMITECO}/agua/demarhidro_2027/wms", "layers": "demarhidro_2027"},
        "Demarcaciones Hidrográficas (PHC 2015-2021)": {"url": f"{BASE_GISMITECO}/agua/DemarHidro2021/wms", "layers": "DemarHidro2021"},
        "Demarcaciones hidrográficas (ámbito terrestre)": {"url": f"{BASE_GISMITECO}/agua/Demarcaciones_ET/wms", "layers": "Demarcaciones_ET"},
        "Demarcaciones hidrográficas (costeras)": {"url": f"{BASE_GISMITECO}/agua/DemarcacionesCosteras/wms", "layers": "DemarcacionesCosteras"},
        "Ámbitos de gestión de los organismos de cuenca": {"url": f"{BASE_GISMITECO}/agua/ambitos_oocc/wms", "layers": "ambitos_oocc"},
        "Cuencas de ríos principales (Pfafstetter modificado)": {"url": f"{BASE_GISMITECO}/agua/cuencas_rios_comp_pfaf/wms", "layers": "cuencas_rios_comp_pfaf"},
        "Subcuencas de tramos de río (Pfafstetter modificado)": {"url": f"{BASE_GISMITECO}/agua/cuencas/wms", "layers": "cuencas"},
        "Subcuencas de masas de agua superficiales de la DMA": {"url": f"{BASE_GISMITECO}/agua/subcuencas_mspf/wms", "layers": "subcuencas_mspf"},
        "Subcuencas de cauces de la red hidrográfica básica": {"url": f"{BASE_GISMITECO}/agua/subcuencas/wms", "layers": "subcuencas"},
        "Ríos (Pfafstetter)": {"url": f"{BASE_GISMITECO}/agua/rios_comp_pfaf/wms", "layers": "rios_comp_pfaf"},
        "Tramos de ríos (Pfafstetter modificado)": {"url": f"{BASE_GISMITECO}/agua/rios_pfaf_cx/wms", "layers": "rios_pfaf_cx"},
        "Ríos principales (cuenca > 500 km2)": {"url": f"{BASE_GISMITECO}/agua/rios_princ/wms", "layers": "rios_princ"},
        "Red hidrográfica básica (MDT 100x100)": {"url": f"{BASE_GISMITECO}/agua/rios_mdt100/wms", "layers": "rios_mdt100"},
        "Red de canales principales": {"url": f"{BASE_GISMITECO}/agua/canales/wms", "layers": "canales"},
        "Embalses": {"url": f"{BASE_GISMITECO}/agua/Embalses/wms", "layers": "Embalses", "styles": "Agua_Embalses_eGISPE"},
        "Presas": {"url": f"{BASE_GISMITECO}/agua/Presas/wms", "layers": "Presas", "styles": "agua_presas_egispe"},
        "Mapa de Direcciones de Drenaje (MDD 25x25)": {"url": f"{BASE_GISMITECO}/agua/MDD25/wms", "layers": "MDD25"},
        "Superficie de cuenca vertiente (25x25)": {"url": f"{BASE_GISMITECO}/agua/Sup25x25/wms", "layers": "Sup25x25"}
    },
    "[DGA] Masas de Agua y Estado (PHC 2022-2027)": {
        "Masas de agua subterránea PHC 2022-2027": {"url": f"{BASE_GISMITECO}/agua/masas_aguasub_2027/wms", "layers": "masas_aguasub_2027"},
        "Horizontes de masas de agua subterránea PHC 2022-2027": {"url": f"{BASE_GISMITECO}/agua/horizontes_masas_aguasub_2027/wms", "layers": "horizontes_masas_aguasub_2027"},
        "Masas de aguas superficiales (líneas) PHC 2022-2027": {"url": f"{BASE_GISMITECO}/agua/masas_aguaspf_2027_l/wms", "layers": "masas_aguaspf_2027_l"},
        "Masas de agua superficial (polígonos) PHC 2022-2027": {"url": f"{BASE_GISMITECO}/agua/masas_aguaspf_2027_a/wms", "layers": "masas_aguaspf_2027_a"},
        "Red hidrográfica PHC 2022-2027": {"url": f"{BASE_GISMITECO}/agua/redhidrografica_2027/wms", "layers": "redhidrografica_2027"},
        "Acuíferos compartidos": {"url": f"{BASE_GISMITECO}/agua/acuiferos_compartidos_aguasub/wms", "layers": "acuiferos_compartidos_aguasub"},
        "Masas de agua subterránea declaradas en riesgo (2027)": {"url": f"{BASE_GISMITECO}/agua/masas_aguasub_riesgo_2027/wms", "layers": "masas_aguasub_riesgo_2027"},
        "Sistemas de explotación PHC 2022-2027": {"url": f"{BASE_GISMITECO}/agua/sist_explotacion_2027/wms", "layers": "sist_explotacion_2027"},
        "Unidades de demanda urbana (polígonos) PHC 2022-2027": {"url": f"{BASE_GISMITECO}/agua/uudd_urbana_2027_a/wms", "layers": "uudd_urbana_2027_a"},
        "Unidades de demanda urbana (puntos) PHC 2022-2027": {"url": f"{BASE_GISMITECO}/agua/uudd_urbana_2027_p/wms", "layers": "uudd_urbana_2027_p"},
        "Estado/potencial ecológico superficial (líneas) 2022-2027": {"url": f"{BASE_GISMITECO}/agua/estado_masas_aguaspf_2027_l/wms", "layers": "estado_masas_aguaspf_2027_l"},
        "Estado/potencial ecológico superficial (polígonos) 2022-2027": {"url": f"{BASE_GISMITECO}/agua/estado_masas_aguaspf_2027_a/wms", "layers": "estado_masas_aguaspf_2027_a"},
        "Estado cuantitativo subterránea 2022-2027": {"url": f"{BASE_GISMITECO}/agua/estado_masas_aguasub_2027/wms", "layers": "estado_masas_aguasub_2027"},
        "Estado químico subterránea 2022-2027": {"url": f"{BASE_GISMITECO}/agua/estado_masas_aguasub_2027_qui/wms", "layers": "estado_masas_aguasub_2027_qui"},
        "Estado químico superficial (líneas) 2022-2027": {"url": f"{BASE_GISMITECO}/agua/estado_masas_aguaspf_2027_l_qui/wms", "layers": "estado_masas_aguaspf_2027_l_qui"},
        "Estado químico superficial (polígonos) 2022-2027": {"url": f"{BASE_GISMITECO}/agua/estado_masas_aguaspf_2027_a_qui/wms", "layers": "estado_masas_aguaspf_2027_a_qui"},
        "Masas subterráneas que no alcanzan buen estado cuantitativo (2027)": {"url": f"{BASE_GISMITECO}/agua/masas_aguasub_nbec_2027/wms", "layers": "masas_aguasub_nbec_2027"},
        "Masas superficiales (líneas) que no alcanzan buen estado (2027)": {"url": f"{BASE_GISMITECO}/agua/masas_aguaspf_nbec_2027_l/wms", "layers": "masas_aguaspf_nbec_2027_l"},
        "Estado global subterránea (2027)": {"url": f"{BASE_GISMITECO}/agua/estado_masas_aguasub_2027_global/wms", "layers": "estado_masas_aguasub_2027_global"},
        "Estado global superficial líneas (2027)": {"url": f"{BASE_GISMITECO}/agua/estado_masas_aguaspf_2027_l_global/wms", "layers": "estado_masas_aguaspf_2027_l_global"},
        "Estado global superficial polígonos (2027)": {"url": f"{BASE_GISMITECO}/agua/estado_masas_aguaspf_2027_a_global/wms", "layers": "estado_masas_aguaspf_2027_a_global"},
        "Redes de seguimiento aguas subterráneas PHC 2022-2027": {"url": f"{BASE_GISMITECO}/agua/redseg_masas_agua_2027_sub/wms", "layers": "redseg_masas_agua_2027_sub"}
    },
    "[DGA] Seguimiento y Control de Aguas Subterráneas": {
        "Red Piezométrica": {"url": f"{BASE_GISMITECO}/agua/RedPiezometrica/wms", "layers": "RedPiezometrica"},
        "Red Hidrométrica de Manantiales": {"url": f"{BASE_GISMITECO}/agua/manantiales/wms", "layers": "manantiales"},
        "Red de Control Químico de Vigilancia General": {"url": f"{BASE_GISMITECO}/agua/casub_quimico_vigilancia/wms", "layers": "casub_quimico_vigilancia"},
        "Red de Control Químico Operativo General": {"url": f"{BASE_GISMITECO}/agua/casub_quimico_operativo/wms", "layers": "casub_quimico_operativo"},
        "Red de Control de Plaguicidas Agrarios": {"url": f"{BASE_GISMITECO}/agua/casub_plaguicidas_agrarios/wms", "layers": "casub_plaguicidas_agrarios"},
        "Red de Control de Aguas de Abastecimiento": {"url": f"{BASE_GISMITECO}/agua/casub_aguas_abastecimiento/wms", "layers": "casub_aguas_abastecimiento"},
        "Red de Control de Aguas Afectadas por Nitratos": {"url": f"{BASE_GISMITECO}/agua/casub_aguas_afectadas_nitratos/wms", "layers": "casub_aguas_afectadas_nitratos"},
        "Catálogo de Sondeos": {"url": f"{BASE_GISMITECO}/agua/sondeos/wms", "layers": "sondeos"},
        "Contenido de nitratos en aguas subterráneas (2024)": {"url": f"{BASE_GISMITECO}/agua/iasub_nitratos_2024/wms", "layers": "iasub_nitratos_2024"},
        "Detección de plaguicidas en aguas subterráneas (2024)": {"url": f"{BASE_GISMITECO}/agua/iasub_plaguicidas_2024/wms", "layers": "iasub_plaguicidas_2024"},
        "Intrusión salina en aguas subterráneas (2024)": {"url": f"{BASE_GISMITECO}/agua/iasub_intrusion_salina_2024/wms", "layers": "iasub_intrusion_salina_2024"}
    },
    "[DGA] Seguimiento y Control de Aguas Superficiales": {
        "Control Emisiones al Atlántico (OSPAR)": {"url": f"{BASE_GISMITECO}/agua/CE_Atlantico/wms", "layers": "CE_Atlantico"},
        "Control Emisiones al Mediterráneo (Barcelona)": {"url": f"{BASE_GISMITECO}/agua/CE_Mediterraneo/wms", "layers": "CE_Mediterraneo"},
        "Control Ríos Transfronterizos Portugal (Albufeira)": {"url": f"{BASE_GISMITECO}/agua/CE_Portugal/wms", "layers": "CE_Portugal"},
        "Control Seguimiento Estado General": {"url": f"{BASE_GISMITECO}/agua/CC_Antropogenica/wms", "layers": "CC_Antropogenica"},
        "Red de Referencia (Cambios Naturales)": {"url": f"{BASE_GISMITECO}/agua/CC_Naturales/wms", "layers": "CC_Naturales"},
        "Red de seguimiento del cambio climático": {"url": f"{BASE_GISMITECO}/agua/casup_vrc_red_seg_cambio_climatico/wms", "layers": "casup_vrc_red_seg_cambio_climatico"},
        "Red de seguimiento del depósito atmosférico": {"url": f"{BASE_GISMITECO}/agua/casup_vrc_red_seg_deposito_atmos/wms", "layers": "casup_vrc_red_seg_deposito_atmos"},
        "Control Operativo General": {"url": f"{BASE_GISMITECO}/agua/CO_General/wms", "layers": "CO_General"},
        "Control Sustancias Peligrosas origen agrario": {"url": f"{BASE_GISMITECO}/agua/CS_Peligrosas/wms", "layers": "CS_Peligrosas"},
        "Control Plaguicidas origen puntual": {"url": f"{BASE_GISMITECO}/agua/C_Plaguicidas/wms", "layers": "C_Plaguicidas"},
        "Control ambiental de aguas de baño": {"url": f"{BASE_GISMITECO}/agua/casup_vrc_ambiental_aguas_bano/wms", "layers": "casup_vrc_ambiental_aguas_bano"},
        "Control de aguas destinadas a abastecimiento": {"url": f"{BASE_GISMITECO}/agua/C_Abastecimientos/wms", "layers": "C_Abastecimientos"},
        "Control aguas en zonas vulnerables a nitratos": {"url": f"{BASE_GISMITECO}/agua/casup_vrc_zonas_vulnerables/wms", "layers": "casup_vrc_zonas_vulnerables"},
        "Control aguas en zonas de protección de hábitats/especies": {"url": f"{BASE_GISMITECO}/agua/casup_vrc_habitat/wms", "layers": "casup_vrc_habitat"},
        "Control aguas en zonas sensibles por vertidos urbanos": {"url": f"{BASE_GISMITECO}/agua/casup_vrc_zonas_sensibles/wms", "layers": "casup_vrc_zonas_sensibles"},
        "Contenido de nitratos en aguas superficiales (2024)": {"url": f"{BASE_GISMITECO}/agua/iasup_nitratos_2024/wms", "layers": "iasup_nitratos_2024"},
        "Detección de plaguicidas en aguas superficiales (2024)": {"url": f"{BASE_GISMITECO}/agua/iasup_plaguicidas_2024/wms", "layers": "iasup_plaguicidas_2024"},
        "Grado trófico de aguas lénticas superficiales (2024)": {"url": f"{BASE_GISMITECO}/agua/iasup_grado_trofico_2024/wms", "layers": "iasup_grado_trofico_2024"},
        "Contenido de amonio en ríos (2024)": {"url": f"{BASE_GISMITECO}/agua/iasup_amonio_2024/wms", "layers": "iasup_amonio_2024"},
        "Contenido de fosfatos en ríos (2024)": {"url": f"{BASE_GISMITECO}/agua/iasup_fosfatos_2024/wms", "layers": "iasup_fosfatos_2024"},
        "Contenido de fósforo total en lagos (2024)": {"url": f"{BASE_GISMITECO}/agua/iasup_fosforo_total_2024/wms", "layers": "iasup_fosforo_total_2024"},
        "Fitobentos en ríos (2024)": {"url": f"{BASE_GISMITECO}/agua/iasup_fitobentos_2024/wms", "layers": "iasup_fitobentos_2024"},
        "Macroinvertebrados bentónicos en ríos (2024)": {"url": f"{BASE_GISMITECO}/agua/iasup_macroinvertebrados_2024/wms", "layers": "iasup_macroinvertebrados_2024"}
    },
    "[DGA] DPH, Hidromorfología y Restauración": {
        "Cauces con DPH deslindado": {"url": f"{BASE_GISMITECO}/agua/DPH_Deslindado/wms", "layers": "DPH_Deslindado"},
        "Cauces con DPH cartográfico": {"url": f"{BASE_GISMITECO}/agua/DPH_Estimado/wms", "layers": "DPH_Estimado"},
        "Zonas de Flujo Preferente": {"url": f"{BASE_GISMITECO}/agua/ZI_Laminas_ZFP/wms", "layers": "ZI_Laminas_ZFP"},
        "Caracterización de la vegetación de ribera": {"url": f"{BASE_GISMITECO}/agua/sectorizacion_riparia/wms", "layers": "sectorizacion_riparia"},
        "Proyectos ejecutados de restauración de ríos (ENRR)": {"url": f"{BASE_GISMITECO}/agua/zi_pryrestauracionrios/wms", "layers": "zi_pryrestauracionrios"},
        "Azudes y presas obsoletas demolidas (ENRR)": {"url": f"{BASE_GISMITECO}/agua/zi_presasdemolidas/wms", "layers": "zi_presasdemolidas"},
        "Escalas y estructuras para paso de peces (ENRR)": {"url": f"{BASE_GISMITECO}/agua/zi_constescalapeces/wms", "layers": "zi_constescalapeces"},
        "Inventario de obras longitudinales": {"url": f"{BASE_GISMITECO}/agua/zi_inventario_ol/wms", "layers": "zi_inventario_ol"},
        "Inventario de obstáculos transversales": {"url": f"{BASE_GISMITECO}/agua/hm_vinventario_ot/wms", "layers": "hm_vinventario_ot"},
        "Tipo morfológico actual": {"url": f"{BASE_GISMITECO}/agua/hm_vtipo_morfologico/wms", "layers": "hm_vtipo_morfologico"},
        "Tipo de valle": {"url": f"{BASE_GISMITECO}/agua/hm_vtipo_valle/wms", "layers": "hm_vtipo_valle"},
        "Tramos modificados por acciones directas en cauce": {"url": f"{BASE_GISMITECO}/agua/hm_vaccion_cauce/wms", "layers": "hm_vaccion_cauce"}
    },
    "[DGA] Saneamiento, Vertidos y Nitratos": {
        "Aprovechamientos Hidroeléctricos": {"url": f"{BASE_GISMITECO}/agua/AprovHidro/wms", "layers": "AprovHidro"},
        "Censo Nacional de Vertidos (CNV)": {"url": f"{BASE_GISMITECO}/agua/CNV/wms", "layers": "CNV"},
        "Aglomeraciones urbanas (Q2023, Dir 91/271/CEE)": {"url": f"{BASE_GISMITECO}/agua/aauu_q2023/wms", "layers": "aauu_q2023"},
        "Depuradoras de aguas residuales (Q2023)": {"url": f"{BASE_GISMITECO}/agua/edar_q2023/wms", "layers": "edar_q2023"},
        "Puntos de vertido de depuradoras urbanas (Q2023)": {"url": f"{BASE_GISMITECO}/agua/pvert_q2023/wms", "layers": "pvert_q2023"},
        "Zonas de captación de zonas sensibles (Q2023)": {"url": f"{BASE_GISMITECO}/agua/zonsen_captacion_q2023/wms", "layers": "zonsen_captacion_q2023"},
        "Zonas sensibles identificadas por líneas (Q2023)": {"url": f"{BASE_GISMITECO}/agua/zonas_sensibles_q2023_l/wms", "layers": "zonas_sensibles_q2023_l"},
        "Zonas sensibles identificadas por polígonos (Q2023)": {"url": f"{BASE_GISMITECO}/agua/zonas_sensibles_q2023_a/wms", "layers": "zonas_sensibles_q2023_a"},
        "Aguas afectadas por nitratos (RD 47/2022)": {"url": f"{BASE_GISMITECO}/agua/aguas_afectadas_2022/wms", "layers": "aguas_afectadas_2022"},
        "Zonas vulnerables a nitratos (2023)": {"url": f"{BASE_GISMITECO}/agua/zonas_vulnerables_q2023/wms", "layers": "zonas_vulnerables_q2023"},
        "Red de control de nitratos en aguas subterráneas (2023)": {"url": f"{BASE_GISMITECO}/agua/redcontrol_no3_aguasub_2023/wms", "layers": "redcontrol_no3_aguasub_2023"},
        "Red de control de nitratos en aguas superficiales (2023)": {"url": f"{BASE_GISMITECO}/agua/redcontrol_no3_aguasup_2023/wms", "layers": "redcontrol_no3_aguasup_2023"}
    },
    "[DGA] Reservas Hidrológicas y Zonas Protegidas": {
        "Censo de Zonas de Aguas de Baño (2024)": {"url": f"{BASE_GISMITECO}/agua/AguasBanio24/wms", "layers": "AguasBanio24"},
        "Reservas Naturales Fluviales declaradas": {"url": f"{BASE_GISMITECO}/agua/vrnf_declaradas/wms", "layers": "vrnf_declaradas"},
        "Cuencas hidrográficas de las Reservas Naturales Fluviales": {"url": f"{BASE_GISMITECO}/agua/cuencashidro_rnf_decl/wms", "layers": "cuencashidro_rnf_decl"},
        "Reservas Naturales Lacustres declaradas": {"url": f"{BASE_GISMITECO}/agua/rnl_decl/wms", "layers": "rnl_decl"},
        "Cuencas hidrográficas de las Reservas Naturales Lacustres": {"url": f"{BASE_GISMITECO}/agua/cuencas_rnl_decl/wms", "layers": "cuencas_rnl_decl"},
        "Reservas Naturales Subterráneas declaradas": {"url": f"{BASE_GISMITECO}/agua/rns_decl/wms", "layers": "rns_decl"},
        "Manantiales de las Reservas Naturales Subterráneas": {"url": f"{BASE_GISMITECO}/agua/rns_decl_manantial/wms", "layers": "rns_decl_manantial"},
        "Zonas protegidas aguas potables (líneas) PHC 2022-2027": {"url": f"{BASE_GISMITECO}/agua/zonprot_potables_2027_l/wms", "layers": "zonprot_potables_2027_l"},
        "Zonas protegidas aguas potables (polígonos) PHC 2022-2027": {"url": f"{BASE_GISMITECO}/agua/zonprot_potables_2027_a/wms", "layers": "zonprot_potables_2027_a"},
        "Zonas protegidas especies acuáticas: moluscos PHC 2022-2027": {"url": f"{BASE_GISMITECO}/agua/zonprot_moluscos_2027/wms", "layers": "zonprot_moluscos_2027"}
    },
    "[DGA] Hidrología Cuantitativa (SIMPA, SAIH, ERHIN)": {
        "Precipitación total anual (SIMPA 1980-2005)": {"url": f"{BASE_GISMITECO}/agua/rechid_precipitacion_1980_2005/wms", "layers": "rechid_precipitacion_1980_2005"},
        "Temperatura media anual (SIMPA 1980-2005)": {"url": f"{BASE_GISMITECO}/agua/rechid_temp_media_1980_2005/wms", "layers": "rechid_temp_media_1980_2005"},
        "Evapotranspiración potencial ETP (SIMPA 1980-2005)": {"url": f"{BASE_GISMITECO}/agua/rechid_etp_1980_2005/wms", "layers": "rechid_etp_1980_2005"},
        "Evapotranspiración real ETR (SIMPA 1980-2005)": {"url": f"{BASE_GISMITECO}/agua/rechid_etr_1980_2005/wms", "layers": "rechid_etr_1980_2005"},
        "Escorrentía subterránea (SIMPA 1980-2005)": {"url": f"{BASE_GISMITECO}/agua/rechid_esc_subt_1980_2005/wms", "layers": "rechid_esc_subt_1980_2005"},
        "Recarga de acuíferos (SIMPA 1980-2005)": {"url": f"{BASE_GISMITECO}/agua/rechid_recarga_1980_2005/wms", "layers": "rechid_recarga_1980_2005"},
        "Escorrentía total anual (SIMPA 1980-2005)": {"url": f"{BASE_GISMITECO}/agua/rechid_esc_total_1980_2005/wms", "layers": "rechid_esc_total_1980_2005"},
        "Aportación total anual (SIMPA 1980-2005)": {"url": f"{BASE_GISMITECO}/agua/rechid_aportacion_1980_2005/wms", "layers": "rechid_aportacion_1980_2005"},
        "Subcuencas nivales (ERHIN)": {"url": f"{BASE_GISMITECO}/agua/Subcuencas_Nivales/wms", "layers": "Subcuencas_Nivales"},
        "Red de pértigas (ERHIN)": {"url": f"{BASE_GISMITECO}/agua/Pertigas_Erhin/wms", "layers": "Pertigas_Erhin"},
        "Telenivómetros (ERHIN)": {"url": f"{BASE_GISMITECO}/agua/Telenivometros_Erhin/wms", "layers": "Telenivometros_Erhin"},
        "Glaciares del Pirineo (ERHIN)": {"url": f"{BASE_GISMITECO}/agua/Glaciares_Erhin/wms", "layers": "Glaciares_Erhin"},
        "Red Integrada de Estaciones de Aforo (SAIH-ROEA)": {"url": f"{BASE_GISMITECO}/agua/Estaciones_Aforos/wms", "layers": "Estaciones_Aforos"},
        "Embalses: nivel/volumen (SAIH)": {"url": f"{BASE_GISMITECO}/agua/embalses_et/wms", "layers": "embalses_et"},
        "Red Pluviométrica (SAIH)": {"url": f"{BASE_GISMITECO}/agua/pluviometros_et/wms", "layers": "pluviometros_et"},
        "Ríos: caudal/nivel (SAIH)": {"url": f"{BASE_GISMITECO}/agua/caudales_et/wms", "layers": "caudales_et"}
    },
    "[DGA] SNCZI - Cartografía de Zonas Inundables": {
        "Áreas con riesgo potencial significativo de inundación (ARPSI)": {
            "Áreas con riesgo potencial significativo de inundación (ARPSI)": {
                "url": f"{BASE_GISMITECO}/agua/Zi_arpsi/wms",
                "layers": "Zi_arpsi",
                "type": "wms"
            }
        },
        "Inundaciones Fluviales": {
            "Peligrosidad (Fluvial)": {
                "T=10 años": {"url": "https://servicios.idee.es/wms-inspire/riesgos-naturales/inundaciones", "layers": "NZ.Flood.FluvialT10", "type": "wms", "styles": "default"},
                "T=100 años": {"url": "https://servicios.idee.es/wms-inspire/riesgos-naturales/inundaciones", "layers": "NZ.Flood.FluvialT100", "type": "wms", "styles": "default"},
                "T=500 años": {"url": "https://servicios.idee.es/wms-inspire/riesgos-naturales/inundaciones", "layers": "NZ.Flood.FluvialT500", "type": "wms", "styles": "default"},
                "Modelo Digital del Terreno ARPSI": {"url": "https://servicios.idee.es/wms-inspire/riesgos-naturales/inundaciones", "layers": "EL.GridCoverage", "type": "wms", "styles": "default"}
            },
            "Riesgo (Fluvial)": {
                "T=10 años": {
                    "Población afectada": {"url": f"{BASE_GISMITECO}/agua/Zif_poblacion_afect_q10/wms", "layers": "Zif_poblacion_afect_q10", "type": "wms"},
                    "Riesgo Actividad Económica": {"url": f"{BASE_GISMITECO}/agua/ZIF_Riesgo_ECO_Q10/wms", "layers": "ZIF_Riesgo_ECO_Q10", "type": "wms"},
                    "Puntos Especial Importancia": {"url": f"{BASE_GISMITECO}/agua/ZIF_RiesgoInundacion_Q10/wms", "layers": "ZIF_RiesgoInundacion_Q10", "type": "wms"},
                    "Áreas Importancia Medioambiental": {"url": f"{BASE_GISMITECO}/agua/Zif_riesgo_medamb_q10/wms", "layers": "Zif_riesgo_medamb_q10", "type": "wms"}
                },
                "T=100 años": {
                    "Población afectada": {"url": f"{BASE_GISMITECO}/agua/Zif_riesgo_pob_q100/wms", "layers": "Zif_riesgo_pob_q100", "type": "wms"},
                    "Riesgo Actividad Económica": {"url": f"{BASE_GISMITECO}/agua/Zif_riesgo_eco_q100/wms", "layers": "Zif_riesgo_eco_q100", "type": "wms"},
                    "Puntos Especial Importancia": {"url": f"{BASE_GISMITECO}/agua/Zif_riesgoinundacion_q100/wms", "layers": "Zif_riesgoinundacion_q100", "type": "wms"},
                    "Áreas Importancia Medioambiental": {"url": f"{BASE_GISMITECO}/agua/Zif_riesgo_medamb_q100/wms", "layers": "Zif_riesgo_medamb_q100", "type": "wms"}
                },
                "T=500 años": {
                    "Población afectada": {"url": f"{BASE_GISMITECO}/agua/Zif_riesgo_pob_q500/wms", "layers": "Zif_riesgo_pob_q500", "type": "wms"},
                    "Riesgo Actividad Económica": {"url": f"{BASE_GISMITECO}/agua/Zif_riesgo_eco_q500/wms", "layers": "Zif_riesgo_eco_q500", "type": "wms"},
                    "Puntos Especial Importancia": {"url": f"{BASE_GISMITECO}/agua/Zif_riesgoinundacion_q500/wms", "layers": "Zif_riesgoinundacion_q500", "type": "wms"},
                    "Áreas Importancia Medioambiental": {"url": f"{BASE_GISMITECO}/agua/Zif_riesgo_medamb_q500/wms", "layers": "Zif_riesgo_medamb_q500", "type": "wms"}
                }
            }
        },
        "Inundaciones Marinas": {
            "Peligrosidad (Marino)": {
                "T=100 años": {"url": "https://servicios.idee.es/wms-inspire/riesgos-naturales/inundaciones", "layers": "NZ.Flood.MarinaT100", "type": "wms", "styles": "default"},
                "T=500 años": {"url": "https://servicios.idee.es/wms-inspire/riesgos-naturales/inundaciones", "layers": "NZ.Flood.MarinaT500", "type": "wms", "styles": "default"}
            },
            "Riesgo (Marino)": {
                "T=100 años": {
                    "Población afectada": {"url": f"{BASE_GISMITECO}/costas/zim_poblacion_afect_q100/wms", "layers": "zim_poblacion_afect_q100", "type": "wms"},
                    "Riesgo Actividad Económica": {"url": f"{BASE_GISMITECO}/costas/zim_activ_eco_afect_q100/wms", "layers": "zim_activ_eco_afect_q100", "type": "wms"},
                    "Puntos Especial Importancia": {"url": f"{BASE_GISMITECO}/costas/zim_ptos_esp_import_q100/wms", "layers": "zim_ptos_esp_import_q100", "type": "wms"},
                    "Áreas Importancia Medioambiental": {"url": f"{BASE_GISMITECO}/costas/zim_area_imp_medamb_q100/wms", "layers": "zim_area_imp_medamb_q100", "type": "wms"}
                },
                "T=500 años": {
                    "Población afectada": {"url": f"{BASE_GISMITECO}/costas/zim_poblacion_afect_q500/wms", "layers": "zim_poblacion_afect_q500", "type": "wms"},
                    "Riesgo Actividad Económica": {"url": f"{BASE_GISMITECO}/costas/zim_activ_eco_afect_q500/wms", "layers": "zim_activ_eco_afect_q500", "type": "wms"},
                    "Puntos Especial Importancia": {"url": f"{BASE_GISMITECO}/costas/zim_ptos_esp_import_q500/wms", "layers": "zim_ptos_esp_import_q500", "type": "wms"},
                    "Áreas Importancia Medioambiental": {"url": f"{BASE_GISMITECO}/costas/zim_area_imp_medamb_q500/wms", "layers": "zim_area_imp_medamb_q500", "type": "wms"}
                }
            }
        }
    },

    # =========================================================================
    # [DGC] DIRECCIÓN GENERAL DE LA COSTA Y EL MAR
    # =========================================================================
    "[DGC] Dominio Público Marítimo-Terrestre y Gestión": {
        "Dominio Público Marítimo-Terrestre": {
            "url": f"{BASE_GISMITECO}/costas/dominio_publico_maritimo_terrestre/wms",
            "layers": "dominio_publico_maritimo_terrestre",
            "styles": "linea_estilo_dpmt"
        },
        "Información adicional para la Servidumbre de Protección": {
            "url": f"{BASE_GISMITECO}/costas/Servidumbre_Proteccion/wms",
            "layers": "Servidumbre_Proteccion",
            "styles": "Servidumbre_Proteccion_estilo"
        },
        "DPMT Núcleos excluidos": {
            "url": f"{BASE_GISMITECO}/costas/nucleos_excluidos/wms",
            "layers": "nucleos_excluidos",
            "styles": "nucleos_excluidos_estilo_dpmt"
        },
        "Terrenos íntegramente incluidos en DPMT": {
            "url": f"{BASE_GISMITECO}/costas/dpmt_terrenos_incluidos/wms",
            "layers": "dpmt_terrenos_incluidos",
            "styles": "terrenos_integramente_incluidos"
        }
    },
    "[DGC] POEM - Planes de Ordenación del Espacio Marítimo": {
        "Ámbito espacial del POEM": {
            "url": f"{BASE_GISMITECO}/costas/poem_ambito/wms",
            "layers": "poem_ambito",
            "styles": "poem_ambito_estilo"
        },
        "Demarcaciones Marinas": {
            "url": f"{BASE_GISMITECO}/costas/demarcaciones_marinas/wms",
            "layers": "demarcaciones_marinas",
            "styles": "demarcaciones_marinas_estilo"
        },
        "ZUP - Defensa Nacional": {
            "url": f"{BASE_GISMITECO}/costas/poem_uso_prio_def_nac_zupdn/wms",
            "layers": "poem_uso_prio_def_nac_zupdn",
            "styles": "poem_uso_prio_def_nac_zupdn_estilo"
        },
        "ZUP - Extracción de áridos": {
            "url": f"{BASE_GISMITECO}/costas/poem_uso_prio_aridos_zupea/wms",
            "layers": "poem_uso_prio_aridos_zupea",
            "styles": "poem_uso_prio_aridos_zupea_estilo"
        },
        "ZUP - Investigación, desarrollo e innovación (I+D+i)": {
            "url": f"{BASE_GISMITECO}/costas/poem_uso_prio_inv_des_zupid/wms",
            "layers": "poem_uso_prio_inv_des_zupid",
            "styles": "poem_uso_prio_inv_des_zupid_estilo"
        },
        "ZUP - Protección de la biodiversidad": {
            "url": f"{BASE_GISMITECO}/costas/poem_uso_prio_biodiv_zupbd/wms",
            "layers": "poem_uso_prio_biodiv_zupbd",
            "styles": "poem_uso_prio_biodiv_zupbd_estilo"
        },
        "ZUP - Protección del patrimonio cultural": {
            "url": f"{BASE_GISMITECO}/costas/poem_uso_prio_pat_cul_zuppc/wms",
            "layers": "poem_uso_prio_pat_cul_zuppc",
            "styles": "poem_uso_prio_pat_cul_zuppc_estilo"
        },
        "ZUP - Seguridad de la navegación": {
            "url": f"{BASE_GISMITECO}/costas/poem_uso_prio_navega_zupsn/wms",
            "layers": "poem_uso_prio_navega_zupsn",
            "styles": "poem_uso_prio_navega_zupsn_estilo"
        },
        "ZAP - Desarrollo de energía eólica marina": {
            "url": f"{BASE_GISMITECO}/costas/poem_alto_pot_ene_eol_zaper/wms",
            "layers": "poem_alto_pot_ene_eol_zaper",
            "styles": "poem_alto_pot_ene_eol_zaper_estilo"
        },
        "ZAP - Actividad portuaria": {
            "url": f"{BASE_GISMITECO}/costas/poem_alto_pot_act_por_zapap/wms",
            "layers": "poem_alto_pot_act_por_zapap",
            "styles": "poem_alto_pot_act_por_zapap_estilo"
        },
        "ZAP - Acuicultura marina": {
            "url": f"{BASE_GISMITECO}/costas/poem_alto_pot_acuicu_zapac/wms",
            "layers": "poem_alto_pot_acuicu_zapac",
            "styles": "poem_alto_pot_acuicu_zapac_alto_estilo"
        },
        "ZAP - Conservación de la biodiversidad": {
            "url": f"{BASE_GISMITECO}/costas/poem_alto_pot_biodiv_zapbd/wms",
            "layers": "poem_alto_pot_biodiv_zapbd",
            "styles": "poem_alto_pot_biodiv_zapbd_estilo"
        },
        "ZAP - Extracción de áridos": {
            "url": f"{BASE_GISMITECO}/costas/poem_alto_pot_aridos_zapea/wms",
            "layers": "poem_alto_pot_aridos_zapea",
            "styles": "poem_alto_pot_aridos_zapea_estilo"
        },
        "ZAP - Investigación, desarrollo e innovación (I+D+i)": {
            "url": f"{BASE_GISMITECO}/costas/poem_alto_pot_inv_des_zapid/wms",
            "layers": "poem_alto_pot_inv_des_zapid",
            "styles": "poem_alto_pot_inv_des_zapid_estilo"
        },
        "Instalaciones eólicas (Biodiversidad)": {
            "url": f"{BASE_GISMITECO}/costas/poem_zon_ubi_inst_eol_biodiv/wms",
            "layers": "poem_zon_ubi_inst_eol_biodiv",
            "styles": "poem_zon_ubi_inst_eol_biodiv_estilo"
        }
    },
    "[DGC] Estrategias Marinas": {
        "Áreas marinas de evaluación de la eutrofización": {
            "url": f"{BASE_GISMITECO}/costas/areas_marinas/wms",
            "layers": "areas_marinas"
        },
        "Estaciones de seguimiento": {
            "url": f"{BASE_GISMITECO}/costas/estaciones_seguimiento/wms",
            "layers": "estaciones_seguimiento"
        },
        "Transectos de seguimiento": {
            "url": f"{BASE_GISMITECO}/costas/transectos_de_seguimiento/wms",
            "layers": "transectos_de_seguimiento"
        }
    },

    # =========================================================================
    # [CALIDAD Y EVALUACIÓN AMBIENTAL]
    # =========================================================================
    "[DGCEA] Cambio Climático y LULUCF": {
        "Instalaciones sujetas a comercio de derechos de emisión": {"url": f"{BASE_GISMITECO}/cambioclimatico/mc_inst_com_der_emision/wms", "layers": "mc_inst_com_der_emision"},
        "Mapa LULUCF 2021": {"url": f"{BASE_GISMITECO}/evaluacionambiental/ea_lulucf_2021/wms?", "layers": "ea_lulucf_2021", "styles": "ea_lulucf"},
        "Mapa LULUCF 2018": {"url": f"{BASE_GISMITECO}/evaluacionambiental/ea_lulucf_2018/wms?", "layers": "ea_lulucf_2018", "styles": "ea_lulucf"},
        "Mapa LULUCF 2015": {"url": f"{BASE_GISMITECO}/evaluacionambiental/ea_lulucf_2015/wms?", "layers": "ea_lulucf_2015", "styles": "ea_lulucf"},
        "Mapa LULUCF 2012": {"url": f"{BASE_GISMITECO}/evaluacionambiental/ea_lulucf_2012/wms?", "layers": "ea_lulucf_2012", "styles": "ea_lulucf"},
        "Mapa LULUCF 2009": {"url": f"{BASE_GISMITECO}/evaluacionambiental/ea_lulucf_2009/wms?", "layers": "ea_lulucf_2009", "styles": "ea_lulucf"},
        "Mapa LULUCF 2006": {"url": f"{BASE_GISMITECO}/evaluacionambiental/ea_lulucf_2006/wms?", "layers": "ea_lulucf_2006", "styles": "ea_lulucf"},
        "Mapa LULUCF 2000": {"url": f"{BASE_GISMITECO}/evaluacionambiental/ea_lulucf_2000/wms?", "layers": "ea_lulucf_2000", "styles": "ea_lulucf"},
        "Mapa LULUCF 1990": {"url": f"{BASE_GISMITECO}/evaluacionambiental/ea_lulucf_1990/wms?", "layers": "ea_lulucf_1990", "styles": "ea_lulucf"},
        "Mapa LULUCF 1970": {"url": f"{BASE_GISMITECO}/evaluacionambiental/ea_lulucf_1970/wms?", "layers": "ea_lulucf_1970", "styles": "ea_lulucf"}
    },
    "[DGCEA] Calidad del Aire": {
        "Estaciones de calidad del aire": {"url": f"{BASE_GISMITECO}/evaluacionambiental/ca_red_estaciones/wms", "layers": "ca_red_estaciones"},
        "Puntos de muestreo de calidad del aire": {"url": f"{BASE_GISMITECO}/evaluacionambiental/ca_red_ptos_muestreo/wms", "layers": "ca_red_ptos_muestreo"},
        "Áreas de Modelos de Calidad del Aire": {"url": f"{BASE_GISMITECO}/evaluacionambiental/ca_areas_modelo/wms", "layers": "ca_areas_modelo"},
        "Red de Seguimiento de la Contaminación Atmosférica en Ecosistemas": {"url": f"{BASE_GISMITECO}/evaluacionambiental/ca_red_seguimiento_cont_atm/wms", "layers": "ca_red_seguimiento_cont_atm"}
    },
    "[DGCEA] Calidad del Aire (Evaluación por Contaminante)": {
        "SO2 - Valor Límite Horario - Estaciones": {"url": f"{BASE_GISMITECO}/evaluacionambiental/vgs_ca_vestacion_estad_legislacion_so2/wms", "layers": "vgs_ca_vestacion_estad_legislacion_so2"},
        "SO2 - Valor Límite Horario - Evaluación": {"url": f"{BASE_GISMITECO}/evaluacionambiental/vgs_ca_vevaluacion_zonas_situacion_so2/wms", "layers": "vgs_ca_vevaluacion_zonas_situacion_so2"},
        "SO2 - Valor Límite Diario - Estaciones": {"url": f"{BASE_GISMITECO}/evaluacionambiental/vgs_ca_vestacion_estad_legislacion_so2D/wms", "layers": "vgs_ca_vestacion_estad_legislacion_so2D"},
        "SO2 - Valor Límite Diario - Evaluación": {"url": f"{BASE_GISMITECO}/evaluacionambiental/vgs_ca_vevaluacion_zonas_situacion_so2D/wms", "layers": "vgs_ca_vevaluacion_zonas_situacion_so2D"},
        "NO2 - Valor Límite Horario - Estaciones": {"url": f"{BASE_GISMITECO}/evaluacionambiental/vgs_ca_vestacion_estad_legislacion_no2/wms", "layers": "vgs_ca_vestacion_estad_legislacion_no2"},
        "NO2 - Valor Límite Horario - Evaluación": {"url": f"{BASE_GISMITECO}/evaluacionambiental/vgs_ca_vevaluacion_zonas_situacion_no2/wms", "layers": "vgs_ca_vevaluacion_zonas_situacion_no2"},
        "NO2 - Valor Límite Anual - Estaciones": {"url": f"{BASE_GISMITECO}/evaluacionambiental/vgs_ca_vestacion_estad_legislacion_no2A/wms", "layers": "vgs_ca_vestacion_estad_legislacion_no2A"},
        "NO2 - Valor Límite Anual - Evaluación": {"url": f"{BASE_GISMITECO}/evaluacionambiental/vgs_ca_vevaluacion_zonas_situacion_no2A/wms", "layers": "vgs_ca_vevaluacion_zonas_situacion_no2A"},
        "PM10 - Valor Límite Diario - Estaciones": {"url": f"{BASE_GISMITECO}/evaluacionambiental/vgs_ca_vestacion_estad_legislacion_PM10/wms", "layers": "vgs_ca_vestacion_estad_legislacion_PM10"},
        "PM10 - Valor Límite Diario - Evaluación": {"url": f"{BASE_GISMITECO}/evaluacionambiental/vgs_ca_vevaluacion_zonas_situacion_PM10/wms", "layers": "vgs_ca_vevaluacion_zonas_situacion_PM10"},
        "PM10 - Valor Límite Anual - Estaciones": {"url": f"{BASE_GISMITECO}/evaluacionambiental/vgs_ca_vestacion_estad_legislacion_PM10A/wms", "layers": "vgs_ca_vestacion_estad_legislacion_PM10A"},
        "PM10 - Valor Límite Anual - Evaluación": {"url": f"{BASE_GISMITECO}/evaluacionambiental/vgs_ca_vevaluacion_zonas_situacion_PM10A/wms", "layers": "vgs_ca_vevaluacion_zonas_situacion_PM10A"},
        "PM2.5 - Valor Límite Anual - Estaciones": {"url": f"{BASE_GISMITECO}/evaluacionambiental/vgs_ca_vestacion_estad_legislacion_PM25/wms", "layers": "vgs_ca_vestacion_estad_legislacion_PM25"},
        "PM2.5 - Valor Límite Anual - Evaluación": {"url": f"{BASE_GISMITECO}/evaluacionambiental/vgs_ca_vevaluacion_zonas_situacion_PM25/wms", "layers": "vgs_ca_vevaluacion_zonas_situacion_PM25"},
        "Pb - Valor Límite Anual - Estaciones": {"url": f"{BASE_GISMITECO}/evaluacionambiental/vgs_ca_vestacion_estad_legislacion_Pb/wms", "layers": "vgs_ca_vestacion_estad_legislacion_Pb"},
        "Pb - Valor Límite Anual - Evaluación": {"url": f"{BASE_GISMITECO}/evaluacionambiental/vgs_ca_vevaluacion_zonas_situacion_Pb/wms", "layers": "vgs_ca_vevaluacion_zonas_situacion_Pb"},
        "C6H6 - Valor Límite Anual - Estaciones": {"url": f"{BASE_GISMITECO}/evaluacionambiental/vgs_ca_vestacion_estad_legislacion_C6H6/wms", "layers": "vgs_ca_vestacion_estad_legislacion_C6H6"},
        "C6H6 - Valor Límite Anual - Evaluación": {"url": f"{BASE_GISMITECO}/evaluacionambiental/vgs_ca_vevaluacion_zonas_situacion_C6H6/wms", "layers": "vgs_ca_vevaluacion_zonas_situacion_C6H6"},
        "O3 - Valor Objetivo - Estaciones": {"url": f"{BASE_GISMITECO}/evaluacionambiental/vgs_ca_vestacion_estad_legislacion_O3/wms", "layers": "vgs_ca_vestacion_estad_legislacion_O3"},
        "O3 - Valor Objetivo - Evaluación": {"url": f"{BASE_GISMITECO}/evaluacionambiental/vgs_ca_vevaluacion_zonas_situacion_O3/wms", "layers": "vgs_ca_vevaluacion_zonas_situacion_O3"},
        "As - Valor Objetivo - Estaciones": {"url": f"{BASE_GISMITECO}/evaluacionambiental/vgs_ca_vestacion_estad_legislacion_AS/wms", "layers": "vgs_ca_vestacion_estad_legislacion_AS"},
        "As - Valor Objetivo - Evaluación": {"url": f"{BASE_GISMITECO}/evaluacionambiental/vgs_ca_vevaluacion_zonas_situacion_AS/wms", "layers": "vgs_ca_vevaluacion_zonas_situacion_AS"},
        "Cd - Valor Objetivo - Estaciones": {"url": f"{BASE_GISMITECO}/evaluacionambiental/vgs_ca_vestacion_estad_legislacion_CD/wms", "layers": "vgs_ca_vestacion_estad_legislacion_CD"},
        "Cd - Valor Objetivo - Evaluación": {"url": f"{BASE_GISMITECO}/evaluacionambiental/vgs_ca_vevaluacion_zonas_situacion_CD/wms", "layers": "vgs_ca_vevaluacion_zonas_situacion_CD"},
        "Ni - Valor Objetivo - Estaciones": {"url": f"{BASE_GISMITECO}/evaluacionambiental/vgs_ca_vestacion_estad_legislacion_NI/wms", "layers": "vgs_ca_vestacion_estad_legislacion_NI"},
        "Ni - Valor Objetivo - Evaluación": {"url": f"{BASE_GISMITECO}/evaluacionambiental/vgs_ca_vevaluacion_zonas_situacion_NI/wms", "layers": "vgs_ca_vevaluacion_zonas_situacion_NI"},
        "BaP - Valor Objetivo - Estaciones": {"url": f"{BASE_GISMITECO}/evaluacionambiental/vgs_ca_vestacion_estad_legislacion_BAP/wms", "layers": "vgs_ca_vestacion_estad_legislacion_BAP"},
        "BaP - Valor Objetivo - Evaluación": {"url": f"{BASE_GISMITECO}/evaluacionambiental/vgs_ca_vevaluacion_zonas_situacion_BAP/wms", "layers": "vgs_ca_vevaluacion_zonas_situacion_BAP"}
    },
    "[DGCEA] Emisiones Industriales, Residuos y Sensibilidad Renovables": {
        "Emisiones contaminantes de complejos industriales": {"url": f"{BASE_GISMITECO}/evaluacionambiental/ei_emisiones_contaminantes/wms", "layers": "ei_emisiones_contaminantes"},
        "Transferencia de residuos fuera del complejo industrial": {"url": f"{BASE_GISMITECO}/evaluacionambiental/ei_transferencia_residuos/wms", "layers": "ei_transferencia_residuos"},
        "Emplazamientos y complejos industriales": {"url": f"{BASE_GISMITECO}/evaluacionambiental/ei_emplazamientos_complejos/wms", "layers": "ei_emplazamientos_complejos"},
        "Grandes Plantas de Combustión (LCP/GIC)": {"url": f"{BASE_GISMITECO}/evaluacionambiental/ei_gp_combustion/wms", "layers": "ei_gp_combustion"},
        "Plantas Industriales de Incineración o Coincineración": {"url": f"{BASE_GISMITECO}/evaluacionambiental/ei_incineracion/wms", "layers": "ei_incineracion"},
        "Índice de sensibilidad ambiental - Energía eólica": {"url": f"{BASE_GISMITECO}/evaluacionambiental/ea_energia_eolica/wms", "layers": "ea_energia_eolica"},
        "Índice de sensibilidad ambiental - Energía fotovoltaica": {"url": f"{BASE_GISMITECO}/evaluacionambiental/ea_energia_fotovoltaica/wms", "layers": "ea_energia_fotovoltaica"},
        "Mapa de sensibilidad ambiental - Energía eólica": {"url": f"{BASE_GISMITECO}/evaluacionambiental/ea_clasificacion_energia_eolica/wms", "layers": "ea_clasificacion_energia_eolica"},
        "Mapa de sensibilidad ambiental - Energía fotovoltaica": {"url": f"{BASE_GISMITECO}/evaluacionambiental/ea_clasificacion_energia_fotovoltaica/wms", "layers": "ea_clasificacion_energia_fotovoltaica"},
        "Mercurio": {"url": f"{BASE_GISMITECO}/evaluacionambiental/re_mercurio/wms", "layers": "re_mercurio"},
        "Instalaciones de gestión de residuos de industrias extractivas": {"url": f"{BASE_GISMITECO}/evaluacionambiental/re_inst_gst_industrias_extr/wms", "layers": "re_inst_gst_industrias_extr"},
        "Parcelas agrícolas de aplicación de lodos de EDAR (2024)": {"url": f"{BASE_GISMITECO}/evaluacionambiental/re_parcela_agricola_lodos_2024/wms", "layers": "re_parcela_agricola_lodos_2024"},
        "Poblaciones aisladas (RD 1481/2001)": {"url": f"{BASE_GISMITECO}/evaluacionambiental/re_poblacion_aislada/wms", "layers": "re_poblacion_aislada"},
        "Vertederos de residuos": {"url": f"{BASE_GISMITECO}/evaluacionambiental/re_vertedero/wms", "layers": "re_vertedero"}
    },
    "[DGCEA] Ruido Ambiental (UME y MER)": {
        "UME - Aeropuertos": {"url": f"{BASE_GISMITECO}/evaluacionambiental/ume_aeropuerto/wms", "layers": "ume_aeropuerto"},
        "UME - Aglomeraciones": {"url": f"{BASE_GISMITECO}/evaluacionambiental/ume_aglomeracion/wms", "layers": "ume_aglomeracion"},
        "UME - Carreteras": {"url": f"{BASE_GISMITECO}/evaluacionambiental/ume_carretera/wms", "layers": "ume_carretera"},
        "UME - Líneas ferroviarias": {"url": f"{BASE_GISMITECO}/evaluacionambiental/ume_ferrocarril/wms", "layers": "ume_ferrocarril"},
        "MER - Aeropuertos Lden": {"url": f"{BASE_GISMITECO}/evaluacionambiental/mer_aeropuerto_lden/wms", "layers": "mer_aeropuerto_lden"},
        "MER - Aeropuertos Ln": {"url": f"{BASE_GISMITECO}/evaluacionambiental/mer_aeropuerto_ln/wms", "layers": "mer_aeropuerto_ln"},
        "MER - Aglomeraciones Lden": {"url": f"{BASE_GISMITECO}/evaluacionambiental/mer_aglomeracion_lden/wms", "layers": "mer_aglomeracion_lden"},
        "MER - Aglomeraciones Ln": {"url": f"{BASE_GISMITECO}/evaluacionambiental/mer_aglomeracion_ln/wms", "layers": "mer_aglomeracion_ln"},
        "MER - Carreteras Lden": {"url": f"{BASE_GISMITECO}/evaluacionambiental/mer_carretera_lden/wms", "layers": "mer_carretera_lden"},
        "MER - Carreteras Ln": {"url": f"{BASE_GISMITECO}/evaluacionambiental/mer_carretera_ln/wms", "layers": "mer_carretera_ln"},
        "MER - Líneas ferroviarias Lden": {"url": f"{BASE_GISMITECO}/evaluacionambiental/mer_ferrocarril_lden/wms", "layers": "mer_ferrocarril_lden"},
        "MER - Líneas ferroviarias Ln": {"url": f"{BASE_GISMITECO}/evaluacionambiental/mer_ferrocarril_ln/wms", "layers": "mer_ferrocarril_ln"}
    },

    # =========================================================================
    # [COPERNICUS / EXTERNOS]
    # =========================================================================
    "[IGN] PNOA Histórico": {
        "PNOA 2024": {"url": "https://www.ign.es/wms/pnoa-historico", "layers": "PNOA2024"},
        "PNOA 2023": {"url": "https://www.ign.es/wms/pnoa-historico", "layers": "PNOA2023"},
        "PNOA 2022": {"url": "https://www.ign.es/wms/pnoa-historico", "layers": "PNOA2022"},
        "PNOA 2021": {"url": "https://www.ign.es/wms/pnoa-historico", "layers": "PNOA2021"},
        "PNOA 2020": {"url": "https://www.ign.es/wms/pnoa-historico", "layers": "PNOA2020"},
        "PNOA 2019": {"url": "https://www.ign.es/wms/pnoa-historico", "layers": "PNOA2019"},
        "PNOA 2018": {"url": "https://www.ign.es/wms/pnoa-historico", "layers": "PNOA2018"},
        "PNOA 2017": {"url": "https://www.ign.es/wms/pnoa-historico", "layers": "PNOA2017"},
        "PNOA 2016": {"url": "https://www.ign.es/wms/pnoa-historico", "layers": "PNOA2016"},
        "PNOA 2015": {"url": "https://www.ign.es/wms/pnoa-historico", "layers": "PNOA2015"},
        "PNOA 2014": {"url": "https://www.ign.es/wms/pnoa-historico", "layers": "PNOA14"},
        "PNOA 2013": {"url": "https://www.ign.es/wms/pnoa-historico", "layers": "PNOA2013"},
        "PNOA 2012": {"url": "https://www.ign.es/wms/pnoa-historico", "layers": "PNOA2012"},
        "PNOA 2011": {"url": "https://www.ign.es/wms/pnoa-historico", "layers": "PNOA2011"},
        "PNOA 2010": {"url": "https://www.ign.es/wms/pnoa-historico", "layers": "PNOA2010"},
        "PNOA 2009": {"url": "https://www.ign.es/wms/pnoa-historico", "layers": "PNOA2009"},
        "PNOA 2008": {"url": "https://www.ign.es/wms/pnoa-historico", "layers": "PNOA2008"},
        "PNOA 2007": {"url": "https://www.ign.es/wms/pnoa-historico", "layers": "PNOA2007"},
        "PNOA 2006": {"url": "https://www.ign.es/wms/pnoa-historico", "layers": "PNOA2006"},
        "PNOA 2005": {"url": "https://www.ign.es/wms/pnoa-historico", "layers": "PNOA2005"},
        "PNOA 2004": {"url": "https://www.ign.es/wms/pnoa-historico", "layers": "PNOA2004"},
        "Vuelo Interministerial (1973-1986)": {"url": "https://www.ign.es/wms/pnoa-historico", "layers": "Interministerial_1973-1986"},
        "Vuelo Nacional (1981-1986)": {"url": "https://www.ign.es/wms/pnoa-historico", "layers": "Nacional_1981-1986"},
        "Vuelo OLISTAT (1997-1998)": {"url": "https://www.ign.es/wms/pnoa-historico", "layers": "OLISTAT"},
        "Vuelo SIGPAC (1997-2003)": {"url": "https://www.ign.es/wms/pnoa-historico", "layers": "SIGPAC"},
        "Vuelo Americano Serie B (1956-1957)": {"url": "https://www.ign.es/wms/pnoa-historico", "layers": "AMS_1956-1957"}
    },
    "[IGN] Redes de Transporte - Carreteras": {
        "Enlace de Carretera": {"url": BASE_IGN_TRANSPORTES, "layers": "TN.RoadTransportNetwork.RoadLink"},
        "Área de Servicio de Carretera": {"url": BASE_IGN_TRANSPORTES, "layers": "TN.RoadTransportNetwork.RoadServiceArea"},
    },

    "[IGN] Redes de Transporte - Ferroviario": {
        "Enlace Ferroviario": {"url": BASE_IGN_TRANSPORTES, "layers": "TN.RailTransportNetwork.RailwayLink"},
        "Área de Estación Ferroviaria": {"url": BASE_IGN_TRANSPORTES, "layers": "TN.RailTransportNetwork.RailwayStationArea"},
    },

    "[IGN] Redes de Transporte - Aéreo": {
        "Área de Aeródromo": {"url": BASE_IGN_TRANSPORTES, "layers": "TN.AirTransportNetwork.AerodromeArea"},
        "Área de Pista": {"url": BASE_IGN_TRANSPORTES, "layers": "TN.AirTransportNetwork.RunwayArea"},
        "Área de Calle de Rodaje": {"url": BASE_IGN_TRANSPORTES, "layers": "TN.AirTransportNetwork.TaxiwayArea"},
        "Área de Plataforma": {"url": BASE_IGN_TRANSPORTES, "layers": "TN.AirTransportNetwork.ApronArea"},
    },

    "[IGN] Redes de Transporte - Marítimo": {
        "Área Portuaria": {"url": BASE_IGN_TRANSPORTES, "layers": "TN.WaterTransportNetwork.PortArea"},
    },
    "[COPERNICUS] Corine Land Cover & Backbone": {
        "CLC 2018": {"url": "https://image.discomap.eea.europa.eu/arcgis/services/Corine/CLC2018_WM/MapServer/WMSServer?", "layers": "12"},
        "CLC 2012": {"url": "https://image.discomap.eea.europa.eu/arcgis/services/Corine/CLC2012_WM/MapServer/WMSServer?", "layers": "Corine_Land_Cover_2012_raster59601"},
        "CLC 2006": {"url": "https://image.discomap.eea.europa.eu/arcgis/services/Corine/CLC2006_WM/MapServer/WMSServer?", "layers": "Corine_Land_Cover_2006_raster43084"},
        "CLC 2000": {"url": "https://image.discomap.eea.europa.eu/arcgis/services/Corine/CLC2000_WM/MapServer/WMSServer?", "layers": "Corine_Land_Cover_2000_raster11306"},
        "CLC 1990": {"url": "https://image.discomap.eea.europa.eu/arcgis/services/Corine/CLC1990_WM/MapServer/WMSServer?", "layers": "Corine_Land_Cover_1990_raster17001"},
        "CLC+ 2023": {"url": "https://geoserver.geoville.com/geoserver/clcp/ows?", "layers": "CLMS_CLCplus_RASTER_2023_010m_eu"},
        "CLC+ 2021": {"url": "https://copernicus.discomap.eea.europa.eu/arcgis/services/CLC_plus/CLMS_CLCplus_RASTER_2021_010m_eu/ImageServer/WMSServer?", "layers": "CLMS_CLCplus_RASTER_2021_010m_eu"},
        "CLC+ 2018": {"url": "https://copernicus.discomap.eea.europa.eu/arcgis/services/CLC_plus/CLMS_CLCplus_RASTER_2018_010m_eu/ImageServer/WMSServer?", "layers": "CLMS_CLCplus_RASTER_2018_010m_eu"}
    },
    "[COPERNICUS] High Resolution Layers (HRL) & Locales": {
        "Densidad Arbórea (TCD) % - 2015": {"url": "https://image.discomap.eea.europa.eu/arcgis/services/GioLandPublic/HRL_TreeCoverDensity_2015/MapServer/WMSServer?", "layers": "0"},
        "Densidad Arbórea (TCD) % - 2012": {"url": "https://image.discomap.eea.europa.eu/arcgis/services/GioLandPublic/HRL_Tree_Cover_Density_2012/MapServer/WMSServer?", "layers": "Tree_Cover_Density_2012_20m55952"},
        "Tipo de Hoja (DLT) - 2015": {"url": "https://image.discomap.eea.europa.eu/arcgis/services/GioLandPublic/HRL_DominantLeafType_2015/ImageServer/WMSServer?request", "layers": "HRL_DominantLeafType_2015"},
        "Tipo de Hoja (DLT) - 2012": {"url": "https://image.discomap.eea.europa.eu/arcgis/services/GioLandPublic/HRL_DominantLeafType_2012/MapServer/WMSServer?", "layers": "0"},
        "Agua y Humedales - 2018": {"url": "https://image.discomap.eea.europa.eu/arcgis/services/GioLandPublic/HRL_WaterWetness_2018/ImageServer/WMSServer?", "layers": "HRL_WaterWetness_2018"},
        "Zonas Costeras (CZ) - 2018": {"url": "https://image.discomap.eea.europa.eu/arcgis/services/CoastalZones/CZ_CoastalZones_2018/MapServer/WMSServer?", "layers": "Coastal_Zones_2018_raster65095"},
        "Zonas Riparias (RZ) - 2018": {"url": "https://copernicus.discomap.eea.europa.eu/arcgis/services/RiparianZones/RZ_2018/MapServer/WMSServer?", "layers": "0"},
        "Natura 2000 (N2K) - 2018": {"url": "https://copernicus.discomap.eea.europa.eu/arcgis/services/Natura2000/N2K_2018/MapServer/WMSServer?", "layers": "0"},
        "Urban Atlas - Arbolado Urbano - 2018": {"url": "https://image.discomap.eea.europa.eu/arcgis/services/UrbanAtlas/UA_StreetTreeLayer_2018/MapServer/WMSServer?", "layers": "STL_2018_Raster30934"}
    }
}

# --- API EIDOS (species.py) ---
API_DISTRIBUCION = f"{BASE_API_EIDOS}/especie/v_ubicacion"
API_CATALOGO = f"{BASE_API_EIDOS}/catalogo/v_listapatronespecie"
URL_FICHA_EIDOS = "https://iepnb.gob.es/areas-tematicas/especies-silvestres/eidos/"
