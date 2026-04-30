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
# --- CAMBIO PARA COMPATIBILIDAD QGIS 3 Y 4 ---
from qgis.PyQt.QtGui import QColor
# ---------------------------------------------

# --- SERVIDORES BASE ---
BASE_GEOSERVER = "https://geoserver.iepnb.es/geoserver"
BASE_API_EIDOS = "https://iepnb.gob.es/api"

# --- CONFIGURACIÓN PARA IDENTIFICACIÓN (identify.py) ---
CONFIG_IDENTIFY = [
    {"id": "ENP", "url": f"{BASE_GEOSERVER}/ENP/wfs", "layer": "ENP:enp", "col_nom": "nombre", "col_inf": "figura", "color": QColor(165, 214, 167)},
    {"id": "RN2000", "url": f"{BASE_GEOSERVER}/RN2000/wfs", "layer": "RN2000:rn2000", "col_nom": "nombre", "col_inf": "desc_figura", "color": QColor(144, 202, 249)},
    {"id": "IBAs", "url": f"{BASE_GEOSERVER}/espacios_protegidos/wfs", "layer": "espacios_protegidos:ibas", "col_nom": "nombre", "col_inf": "ca", "color": QColor(255, 241, 118)},
    {"id": "MUP", "url": f"{BASE_GEOSERVER}/propiedad_montes/wfs", "layer": "propiedad_montes:propiedad_montes", "col_nom": "monte", "col_inf": "monte_ca", "color": QColor(141, 110, 99)},
    {"id": "V. Pecuarias", "url": f"{BASE_GEOSERVER}/vias_pecuarias/wfs", "layer": "vias_pecuarias:rgvp_2024", "col_nom": "nb_via", "col_inf": "nb_canada", "color": QColor(240, 98, 146)},
    {"id": "Á. Marinas", "url": f"{BASE_GEOSERVER}/areas_marinas_protegidas/wfs", "layer": "areas_marinas_protegidas:rampe", "col_nom": "site_name", "col_inf": "tipo", "color": QColor(77, 182, 172)},
    {"id": "Riqueza Esp.", "url": f"{BASE_GEOSERVER}/especies/wfs", "layer": "especies:riqueza_especies", "col_nom": "id", "col_inf": "lista_idstaxon_filtro", "color": QColor(156, 39, 176)},
    {"id": "Reservas de la Biosfera", "url": f"{BASE_GEOSERVER}/convenio_internacional/wfs", "layer": "convenio_internacional:MAB", "col_nom": "nombre", "col_inf": "nombre", "color": QColor(46, 125, 50)},
    {"id": "OSPAR", "url": f"{BASE_GEOSERVER}/convenio_internacional/wfs", "layer": "convenio_internacional:OSPAR", "col_nom": "nombre", "col_inf": "nombre", "color": QColor(21, 101, 192)},
    {"id": "RAMSAR", "url": f"{BASE_GEOSERVER}/convenio_internacional/wfs", "layer": "convenio_internacional:RAMSAR", "col_nom": "nombre", "col_inf": "nombre", "color": QColor(0, 150, 136)},
    {"id": "ZEPIM", "url": f"{BASE_GEOSERVER}/convenio_internacional/wfs", "layer": "convenio_internacional:ZEPIM", "col_nom": "nombre", "col_inf": "nombre", "color": QColor(173, 20, 87)},
    {"id": "Geoparque", "url": f"{BASE_GEOSERVER}/convenio_internacional/wfs", "layer": "convenio_internacional:GEOPARQUE", "col_nom": "nombre", "col_inf": "nombre", "color": QColor(230, 81, 0)}
]

# --- CONFIGURACIÓN PARA TERRITORIO (territory.py) ---
CONFIG_TERRITORY = [
    {"id": "CCAA", "url": f"{BASE_GEOSERVER}/cartografia_base/wfs", "layer": "cartografia_base:ccaa", "col_nom": "nut2_nom", "col_inf": "id", "color": QColor(0, 0, 255)},
    {"id": "Provincia", "url": f"{BASE_GEOSERVER}/cartografia_base/wfs", "layer": "cartografia_base:provincias", "col_nom": "nut3_nom", "col_inf": "id", "color": QColor(0, 0, 255)},
    {"id": "TTMM", "url": f"{BASE_GEOSERVER}/cartografia_base/wfs", "layer": "cartografia_base:ttmm", "col_nom": "nombre", "col_inf": "municipio", "color": QColor(255, 0, 0)},
] + CONFIG_IDENTIFY

# --- SERVICIOS WMS/WMTS (services_iepnb.py) ---
CATALOGO_WMS = {
    # --- ESPACIOS PROTEGIDOS Y PROPIEDAD ---
    "Espacios Protegidos - IEPNB": {
        "Espacios Naturales Protegidos (ENP)": {"url": f"{BASE_GEOSERVER}/ENP/wms", "layers": "enp"},
        "Red Natura 2000 (RN2000)": {"url": f"{BASE_GEOSERVER}/RN2000/wms", "layers": "rn2000"},
        "IBAs (Áreas Importantes para Aves)": {"url": f"{BASE_GEOSERVER}/espacios_protegidos/wms", "layers": "ibas"},
        "Áreas Marinas Protegidas (RAMPE)": {"url": f"{BASE_GEOSERVER}/areas_marinas_protegidas/wms", "layers": "rampe"},
        "Montes de Utilidad Pública (MUP)": {"url": f"{BASE_GEOSERVER}/propiedad_montes/wms", "layers": "propiedad_montes"},
        "Vías Pecuarias": {"url": f"{BASE_GEOSERVER}/vias_pecuarias/wms", "layers": "rgvp_2024"}
    },
    # --- CONVENIOS INTERNACIONALES ---
    "Convenios Internacionales - IEPNB": {
        "Reservas de la Biosfera (MAB)": {"url": f"{BASE_GEOSERVER}/convenio_internacional/wms", "layers": "MAB"},
        "OSPAR": {"url": f"{BASE_GEOSERVER}/convenio_internacional/wms", "layers": "OSPAR"},
        "RAMSAR": {"url": f"{BASE_GEOSERVER}/convenio_internacional/wms", "layers": "RAMSAR"},
        "ZEPIM": {"url": f"{BASE_GEOSERVER}/convenio_internacional/wms", "layers": "ZEPIM"},
        "Geoparque": {"url": f"{BASE_GEOSERVER}/convenio_internacional/wms", "layers": "GEOPARQUE"}
    },
    "MFE (Foto Fija)": {
        "MFE - Tipo de Bosque": {"url": f"{BASE_GEOSERVER}/foto_fija_mfe/wms", "layers": "ff_tipo_bosque"},
        "MFE - Uso": {"url": f"{BASE_GEOSERVER}/foto_fija_mfe/wms", "layers": "ff_uso"}
    },
    # --- EIKOS - IEPNB ---
    "EIKOS - Alertas Anuales (IEPNB)": {
        "Alertas Anuales 2025": {"url": f"{BASE_GEOSERVER}/alertas_anuales_vegetacion/wms", "layers": "alertas_anuales_2025"},
        "Alertas Anuales 2024": {"url": f"{BASE_GEOSERVER}/alertas_anuales_vegetacion/wms", "layers": "alertas_anuales_2024"},
        "Alertas Anuales 2023": {"url": f"{BASE_GEOSERVER}/alertas_anuales_vegetacion/wms", "layers": "alertas_anuales_2023"},
        "Alertas Anuales 2022": {"url": f"{BASE_GEOSERVER}/alertas_anuales_vegetacion/wms", "layers": "alertas_anuales_2022"},
        "Alertas Anuales 2021": {"url": f"{BASE_GEOSERVER}/alertas_anuales_vegetacion/wms", "layers": "alertas_anuales_2021"},
        "Alertas Anuales 2020": {"url": f"{BASE_GEOSERVER}/alertas_anuales_vegetacion/wms", "layers": "alertas_anuales_2020"},
    },
    "EIKOS - Alertas Mensuales (IEPNB)": {
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

    "MITECO - Costas (DGC)": {
        "Dominio Público Marítimo-Terrestre": {
            "url": "https://wms.mapama.gob.es/sig/Costas/DPMT",
            "layers": "AM.CoastalZoneManagementArea"
        },
        "Información adicional para la Servidumbre de Protección": {
            "url": "https://wms.mapama.gob.es/sig/costas/SP",
            "layers": "AM.CoastalZoneManagementArea"
        },
        "DPMT Núcleos excluidos": {
            "url": "https://wms.mapama.gob.es/sig/Costas/NucleosExcluidos",
            "layers": "AM.CoastalZoneManagementArea"
        },
        "Terrenos íntegramente incluidos en DPMT": {
            "url": "https://wms.mapama.gob.es/sig/Costas/TerrenosIncluidos",
            "layers": "AM.CoastalZoneManagementArea"
        }
    },

    "MITECO - Agua (DGA)": {
        "Ríos (Pfafstetter)": {"url": "https://wms.mapama.gob.es/sig/Agua/RiosCompPfafs?", "layers": "HY.PhysicalWaters.Waterbodies"},
        "Demarcaciones Hidrográficas": {"url": "https://wms.mapama.es/sig/Agua/Demarcaciones?", "layers": "AM.RiverBasinDistrict"},
        "Embalses": {"url": "https://wms.mapama.gob.es/sig/agua/Embalses?", "layers": "HY.PhysicalWaters.Waterbodies"},
        "Presas": {"url": "https://wms.mapama.gob.es/sig/agua/Presas?", "layers": "HY.PhysicalWaters.ManMadeObject"}
    },
    # --- MITECO - SNCZI (Sistema Nacional de Cartografía de Zonas Inundables) ---

    "MITECO - SNCZI - Inundabilidad": {
        "Áreas con riesgo potencial significativo de inundación (ARPSI)": {
            "Áreas con riesgo potencial significativo de inundación (ARPSI)": {
                "url": "https://wms.mapama.gob.es/sig/agua/ZI_ARPSI?",
                "layers": "NZ.RiskZone",
                "type": "wms"
            }
        },
        "Inundaciones Fluviales": {
            "Peligrosidad (Fluvial)": {
                "T=10 años": {"url": "https://servicios.idee.es/wms-inspire/riesgos-naturales/inundaciones?", "layers": "NZ.Flood.FluvialT10", "type": "wms"},
                "T=100 años": {"url": "https://servicios.idee.es/wms-inspire/riesgos-naturales/inundaciones?", "layers": "NZ.Flood.FluvialT100", "type": "wms"},
                "T=500 años": {"url": "https://servicios.idee.es/wms-inspire/riesgos-naturales/inundaciones?", "layers": "NZ.Flood.FluvialT500", "type": "wms"},
                "Modelo Digital del Terreno ARPSI": {"url": "https://servicios.idee.es/wms-inspire/riesgos-naturales/inundaciones?", "layers": "EL.GridCoverage", "type": "wms"}
            },
            "Riesgo (Fluvial)": {
                "T=10 años": {
                    "Población afectada": {"url": "https://wms.mapama.gob.es/sig/Agua/Riesgo/RiesgoPob_10?", "layers": "NZ.RiskZone", "type": "wms"},
                    "Riesgo Actividad Económica": {"url": "https://wms.mapama.gob.es/sig/Agua/Riesgo/RiesgoAct_10?", "layers": "NZ.RiskZone", "type": "wms"},
                    "Puntos Especial Importancia": {"url": "https://wms.mapama.gob.es/sig/Agua/Riesgo/RiesgoPto_10?", "layers": "NZ.ExposedElement", "type": "wms"},
                    "Áreas Importancia Medioambiental": {"url": "https://wms.mapama.gob.es/sig/Agua/Riesgo/AreaImp_10?", "layers": "NZ.ExposedElement", "type": "wms"}
                },
                "T=100 años": {
                    "Población afectada": {"url": "https://wms.mapama.gob.es/sig/Agua/Riesgo/RiesgoPob_100?", "layers": "NZ.RiskZone", "type": "wms"},
                    "Riesgo Actividad Económica": {"url": "https://wms.mapama.gob.es/sig/Agua/Riesgo/RiesgoAct_100?", "layers": "NZ.RiskZone", "type": "wms"},
                    "Puntos Especial Importancia": {"url": "https://wms.mapama.gob.es/sig/Agua/Riesgo/RiesgoPto_100?", "layers": "NZ.ExposedElement", "type": "wms"},
                    "Áreas Importancia Medioambiental": {"url": "https://wms.mapama.gob.es/sig/Agua/Riesgo/AreaImp_100?", "layers": "NZ.ExposedElement", "type": "wms"}
                },
                "T=500 años": {
                    "Población afectada": {"url": "https://wms.mapama.gob.es/sig/Agua/Riesgo/RiesgoPob_500?", "layers": "NZ.RiskZone", "type": "wms"},
                    "Riesgo Actividad Económica": {"url": "https://wms.mapama.gob.es/sig/Agua/Riesgo/RiesgoAct_500?", "layers": "NZ.RiskZone", "type": "wms"},
                    "Puntos Especial Importancia": {"url": "https://wms.mapama.gob.es/sig/Agua/Riesgo/RiesgoPto_500?", "layers": "NZ.ExposedElement", "type": "wms"},
                    "Áreas Importancia Medioambiental": {"url": "https://wms.mapama.gob.es/sig/Agua/Riesgo/AreaImp_500?", "layers": "NZ.ExposedElement", "type": "wms"}
                }
            }
        },
        "Inundaciones Marinas": {
            "Nivel 3 - Peligrosidad (Marino)": {
                "T=100 años": {"url": "https://servicios.idee.es/wms-inspire/riesgos-naturales/inundaciones?", "layers": "NZ.Flood.MarinaT100", "type": "wms"},
                "T=500 años": {"url": "https://servicios.idee.es/wms-inspire/riesgos-naturales/inundaciones?", "layers": "NZ.Flood.MarinaT500", "type": "wms"}
            },
            "Riesgo (Marino)": {
                "T=100 años": {
                    "Población afectada": {"url": "https://wms.mapama.gob.es/sig/Costas/Riesgo/RiesgoPob_100?", "layers": "HH.HealthStatisticalData", "type": "wms"},
                    "Riesgo Actividad Económica": {"url": "https://wms.mapama.gob.es/sig/Costas/Riesgo/RiesgoAct_100?", "layers": "LU.ExistingLandUse", "type": "wms"},
                    "Puntos Especial Importancia": {"url": "https://wms.mapama.gob.es/sig/Costas/Riesgo/RiesgoPto_100?", "layers": "PS.ProtectedSite", "type": "wms"},
                    "Áreas Importancia Medioambiental": {"url": "https://wms.mapama.gob.es/sig/Costas/Riesgo/AreaImp_100?", "layers": "PS.ProtectedSite", "type": "wms"}
                },
                "T=500 años": {
                    "Población afectada": {"url": "https://wms.mapama.gob.es/sig/Costas/Riesgo/RiesgoPob_500?", "layers": "HH.HealthStatisticalData", "type": "wms"},
                    "Riesgo Actividad Económica": {"url": "https://wms.mapama.gob.es/sig/Costas/Riesgo/RiesgoAct_500?", "layers": "LU.ExistingLandUse", "type": "wms"},
                    "Puntos Especial Importancia": {"url": "https://wms.mapama.gob.es/sig/Costas/Riesgo/RiesgoPto_500?", "layers": "PS.ProtectedSite", "type": "wms"},
                    "Áreas Importancia Medioambiental": {"url": "https://wms.mapama.gob.es/sig/Costas/Riesgo/AreaImp_500?", "layers": "PS.ProtectedSite", "type": "wms"}
                }
            }
        }
    },
    "MITECO - Calidad y Evaluación Ambiental": {
        "Red de Estaciones de Calidad del Aire": {
            "url": "https://wms.mapama.gob.es/sig/EvaluacionAmbiental/CalidadAire/RedEstacionesCa",
            "layers": "EF.EnvironmentalMonitoringFacilities"
        },
        "Puntos de Muestreo de Calidad del Aire": {
            "url": "https://wms.mapama.gob.es/sig/EvaluacionAmbiental/CalidadAire/PuntosMuestreoCa",
            "layers": "EF.EnvironmentalMonitoringFacilities"
        },
        "DPMT Área de Modelos de Calidad del Aire": {
            "url": "https://wms.mapama.gob.es/sig/EvaluacionAmbiental/CalidadAire/AreasModelosCa",
            "layers": "AM.AirQualityManagementZone"
        },
    },


    "PNOA Histórico (IGN)": {
        "PNOA 2023": {"url": "https://www.ign.es/wms/pnoa-historico", "layers": "PNOA2023"},
        "PNOA 2022": {"url": "https://www.ign.es/wms/pnoa-historico", "layers": "PNOA2022"},
        "PNOA 2021": {"url": "https://www.ign.es/wms/pnoa-historico", "layers": "PNOA2021"},
        "PNOA 2020": {"url": "https://www.ign.es/wms/pnoa-historico", "layers": "PNOA2020"},
        "PNOA 2019": {"url": "https://www.ign.es/wms/pnoa-historico", "layers": "PNOA2019"},
        "PNOA 2018": {"url": "https://www.ign.es/wms/pnoa-historico", "layers": "PNOA2018"},
        "PNOA 2017": {"url": "https://www.ign.es/wms/pnoa-historico", "layers": "PNOA2017"},
        "PNOA 2016": {"url": "https://www.ign.es/wms/pnoa-historico", "layers": "PNOA2016"},
        "PNOA 2015": {"url": "https://www.ign.es/wms/pnoa-historico", "layers": "PNOA2015"},
        "PNOA 2014": {"url": "https://www.ign.es/wms/pnoa-historico", "layers": "PNOA2014"},
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
    "Corine Land Cover (Evolución)": {
        "CLC 2018": {"url": "https://image.discomap.eea.europa.eu/arcgis/services/Corine/CLC2018_WM/MapServer/WMSServer?", "layers": "12"},
        "CLC 2012": {"url": "https://image.discomap.eea.europa.eu/arcgis/services/Corine/CLC2012_WM/MapServer/WMSServer?", "layers": "Corine_Land_Cover_2012_raster59601"},
        "CLC 2006": {"url": "https://image.discomap.eea.europa.eu/arcgis/services/Corine/CLC2006_WM/MapServer/WMSServer?", "layers": "Corine_Land_Cover_2006_raster43084"},
        "CLC 2000": {"url": "https://image.discomap.eea.europa.eu/arcgis/services/Corine/CLC2000_WM/MapServer/WMSServer?", "layers": "Corine_Land_Cover_2000_raster11306"},
        "CLC 1990": {"url": "https://image.discomap.eea.europa.eu/arcgis/services/Corine/CLC1990_WM/MapServer/WMSServer?", "layers": "Corine_Land_Cover_1990_raster17001"}
    },
    "Corine Land Cover Backbone (Evolución)": {
        "CLC+ 2023": {"url": "https://geoserver.geoville.com/geoserver/clcp/ows?", "layers": "CLMS_CLCplus_RASTER_2023_010m_eu"},
        "CLC+ 2021": {"url": "https://copernicus.discomap.eea.europa.eu/arcgis/services/CLC_plus/CLMS_CLCplus_RASTER_2021_010m_eu/ImageServer/WMSServer?", "layers": "CLMS_CLCplus_RASTER_2021_010m_eu"},
        "CLC+ 2018": {"url": "https://copernicus.discomap.eea.europa.eu/arcgis/services/CLC_plus/CLMS_CLCplus_RASTER_2018_010m_eu/ImageServer/WMSServer?", "layers": "CLMS_CLCplus_RASTER_2018_010m_eu"}
    },
    "Copernicus HRL - Bosques (Evolución)": {
        "Densidad Arbórea (TCD) - 2021": {"url": "https://geoserver.vlcc.geoville.com/geoserver/ows", "layers": "HRL_TCF:TCD_S2021"},
        "Densidad Arbórea (TCD) - 2018": {"url": "https://geoserver.vlcc.geoville.com/geoserver/ows", "layers": "HRL_TCF:TCD_S2018"},
        "Tipo de Hoja (DLT) - 2021": {"url": "https://geoserver.vlcc.geoville.com/geoserver/ows", "layers": "HRL_TCF:DLT_S2021"},
        "Tipo de Hoja (DLT) - 2018": {"url": "https://geoserver.vlcc.geoville.com/geoserver/ows", "layers": "HRL_TCF:DLT_S2018"}
    },
    "Copernicus HRL - Agua y Humedales": {
        "Agua y Humedales - 2018": {"url": "https://image.discomap.eea.europa.eu/arcgis/services/GioLandPublic/HRL_WaterWetness_2018/ImageServer/WMSServer?", "layers": "HRL_WaterWetness_2018"}
    },
    "Copernicus HRL - Pastizales": {
        "Pastizales (Grassland) - 2018": {"url": "https://geoserver.vlcc.geoville.com/geoserver/ows", "layers": "HRL_GRA:GRA_S2018"}
    },
    "Copernicus HRL - Suelo Desnudo (Agrícola)": {
        "Suelo Desnudo - 2023": {"url": "https://geoserver.vlcc.geoville.com/geoserver/ows", "layers": "HRL_CPL:CPBSA_S2023"},
        "Suelo Desnudo - 2021": {"url": "https://geoserver.vlcc.geoville.com/geoserver/ows", "layers": "HRL_CPL:CPBSA_S2021"},
        "Suelo Desnudo - 2018": {"url": "https://geoserver.vlcc.geoville.com/geoserver/ows", "layers": "HRL_CPL:CPBSA_S2018"}
    },
    "Copernicus - Zonas Protegidas y Locales": {
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
