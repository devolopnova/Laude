#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
score_candidatos_sillas.py

FASE DE SELECCION (no modifica catalogo definitivo): calcula un score
reproducible para los modelos candidatos de las 13 marcas ya decididas
(ver conversacion), y propone hasta 3 productos por marca (2 para marcas
de "menor relevancia") maximizando popularidad + cobertura + diversidad +
calidad de datos, no solo numero de valoraciones.

Todos los datos de entrada (precio, valoracion, nº valoraciones, rango de
altura/grupo, ISOFIX, orientacion, 360, etc.) proceden de fichas reales de
Amazon.es visitadas durante esta sesion -- ningun dato esta inventado ni
inferido. Donde un dato no se pudo confirmar, se marca explicitamente como
None / "Sin especificar" y NO participa en el calculo salvo como ausencia.

No toca tools/output/lote1_final.json, no toca amazon_import.py, no toca
la interfaz web. Solo lee CANDIDATOS (mas abajo) y escribe un reporte a
tools/output/candidatos_seleccion.json.

Uso:
    python tools/score_candidatos_sillas.py
"""

import json
import math
from collections import defaultdict

# --------------------------------------------------------------------------
# 1. MARCAS: limite de catalogo por marca (decidido en conversacion previa)
# --------------------------------------------------------------------------
LIMITE_MARCA = {
    "Kinderkraft": 3, "Maxi-Cosi": 3, "Bebe Confort": 3, "Cybex": 3,
    "Britax Romer": 3, "Chicco": 3, "BabyAuto": 3,
    "Graco": 3, "Lionelo": 3, "KikkaBoo": 3, "Jovikids": 3,
    "Babify": 1, "Nania": 2,
}

# --------------------------------------------------------------------------
# 2. CANDIDATOS: datos reales recogidos de fichas de Amazon.es en esta
#    sesion. Campos:
#      marca, modelo, asin, precio_eur, valoracion (0-5), n_valoraciones,
#      altura_min_cm, altura_max_cm  (None si es un producto tipo grupo R44
#        puro sin rango de altura explicito -- no aplica aqui, todo el
#        universo rastreado es R129/i-Size con rango de altura explicito),
#      grupo (texto tal cual aparece, o None si no se menciona explicito),
#      isofix (True/False/None), orientacion ("favor","contramarcha","ambas",None),
#      giro360 (True/False), reclinable (True/False/None),
#      contramarcha (True/False - redundante con orientacion, para claridad),
#      instalacion ("isofix","cinturon","isofix_o_cinturon",None),
#      calidad_datos ("alta","media","baja") -- ver notas por producto,
#      actualidad ("alta","media","baja"),
#      nota -- texto libre con la razon de calidad/actualidad si no es "alta".
# --------------------------------------------------------------------------
CANDIDATOS = [
    # ---------------- KINDERKRAFT (ya en catalogo, 9 modelos reales tras
    # fusionar la variante de color COMFORT UP Rosa/Negro en un solo modelo) ----
    dict(marca="Kinderkraft", modelo="JUNIOR FIX 2 PRO", asin="B0FKBWNF2G", precio=79.90,
         valoracion=4.5, n_val=63, alt_min=100, alt_max=150, grupo=None, isofix=True,
         orientacion="favor", giro360=False, reclinable=None, instalacion="isofix_o_cinturon",
         calidad_datos="media", actualidad="alta", nota="Grupo no explicito"),
    dict(marca="Kinderkraft", modelo="I-COMFY", asin="B0F9YPF1V1", precio=62.90,
         valoracion=4.5, n_val=377, alt_min=76, alt_max=150, grupo=None, isofix=False,
         orientacion="favor", giro360=False, reclinable=True, instalacion="cinturon",
         calidad_datos="alta", actualidad="media", nota=None),
    dict(marca="Kinderkraft", modelo="COMFORT UP", asin="B0BYP63YCW", precio=67.00,
         valoracion=4.4, n_val=4105, alt_min=75, alt_max=150, grupo="1/2/3", isofix=False,
         orientacion="favor", giro360=False, reclinable=None, instalacion="cinturon",
         calidad_datos="alta", actualidad="alta",
         nota="Existe como 2 ASIN (Rosa/Negro) con identicas valoraciones -- mismo modelo, fusionado aqui"),
    dict(marca="Kinderkraft", modelo="I-GROW", asin="B0BZ89X9YC", precio=129.90,
         valoracion=4.5, n_val=1485, alt_min=40, alt_max=150, grupo="0+/1/2/3", isofix=True,
         orientacion="ambas", giro360=True, reclinable=True, instalacion="isofix",
         calidad_datos="alta", actualidad="alta", nota=None),
    dict(marca="Kinderkraft", modelo="I-GROW 2 PRO", asin="B0F9YR27XX", precio=149.00,
         valoracion=4.2, n_val=67, alt_min=40, alt_max=150, grupo="0+/1/2/3", isofix=True,
         orientacion="ambas", giro360=True, reclinable=True, instalacion="isofix",
         calidad_datos="alta", actualidad="alta", nota="Sucesor directo de I-GROW, casi identico"),
    dict(marca="Kinderkraft", modelo="SAFETY FIX 3 PRO", asin="B0FGDM2ZTS", precio=99.00,
         valoracion=4.5, n_val=153, alt_min=76, alt_max=150, grupo=None, isofix=True,
         orientacion=None, giro360=False, reclinable=None, instalacion="isofix",
         calidad_datos="media", actualidad="alta", nota="Grupo y edad no explicitos"),
    dict(marca="Kinderkraft", modelo="UNITY 2", asin="B0DSL7WGB2", precio=89.90,
         valoracion=4.4, n_val=234, alt_min=100, alt_max=150, grupo=None, isofix=True,
         orientacion=None, giro360=False, reclinable=True, instalacion="isofix",
         calidad_datos="media", actualidad="alta", nota=None),
    dict(marca="Kinderkraft", modelo="FIX2GO", asin="B0DP7TG8KY", precio=104.00,
         valoracion=4.5, n_val=186, alt_min=76, alt_max=150, grupo=None, isofix=True,
         orientacion="favor", giro360=False, reclinable=True, instalacion="isofix",
         calidad_datos="alta", actualidad="alta", nota=None),
    dict(marca="Kinderkraft", modelo="I-BOOST 2", asin="B0F1R26D8L", precio=24.90,
         valoracion=4.6, n_val=143, alt_min=125, alt_max=150, grupo=None, isofix=False,
         orientacion="favor", giro360=False, reclinable=False, instalacion="cinturon",
         calidad_datos="alta", actualidad="alta", nota="Silla mas ligera (1,2kg) y mas barata del universo"),

    # ---------------- MAXI-COSI ----------------
    dict(marca="Maxi-Cosi", modelo="Tanza", asin="B0CZ47FKZL", precio=99.99,
         valoracion=4.4, n_val=1385, alt_min=100, alt_max=150, grupo="2/3", isofix=True,
         orientacion="favor", giro360=False, reclinable=None, instalacion="isofix",
         calidad_datos="alta", actualidad="alta", nota=None),
    dict(marca="Maxi-Cosi", modelo="Emerald 360 S", asin="B0CWS19269", precio=386.99,
         valoracion=4.6, n_val=617, alt_min=40, alt_max=150, grupo="0+/1/2/3", isofix=True,
         orientacion="ambas", giro360=True, reclinable=True, instalacion="isofix",
         calidad_datos="alta", actualidad="alta", nota=None),
    dict(marca="Maxi-Cosi", modelo="Pearl 360", asin="B0C6R47BCV", precio=329.99,
         valoracion=4.8, n_val=1500, alt_min=61, alt_max=105, grupo=None, isofix=True,
         orientacion="contramarcha", giro360=True, reclinable=None, instalacion="isofix",
         calidad_datos="media", actualidad="alta", nota="Etapa infantil, sin grupo explicito"),
    dict(marca="Maxi-Cosi", modelo="Kore i-Size", asin="B07RS6KP8C", precio=239.99,
         valoracion=4.4, n_val=1244, alt_min=100, alt_max=150, grupo="2/3", isofix=True,
         orientacion="favor", giro360=False, reclinable=None, instalacion="isofix",
         calidad_datos="alta", actualidad="media", nota="Solapa con Tanza (mismo segmento)"),
    dict(marca="Maxi-Cosi", modelo="RodiFix M", asin="B0CKZC1WZG", precio=129.99,
         valoracion=4.4, n_val=900, alt_min=100, alt_max=150, grupo="2/3", isofix=True,
         orientacion="favor", giro360=False, reclinable=None, instalacion="isofix",
         calidad_datos="alta", actualidad="media", nota="3er producto del mismo segmento que Tanza/Kore"),
    dict(marca="Maxi-Cosi", modelo="Mica Pro Eco", asin="B0BXB1S1Z5", precio=319.00,
         valoracion=4.6, n_val=182, alt_min=40, alt_max=105, grupo=None, isofix=True,
         orientacion="ambas", giro360=True, reclinable=True, instalacion="isofix",
         calidad_datos="alta", actualidad="alta",
         nota="Confirmado en maxi-cosi.es: ambas orientaciones (contramarcha 40-105cm y favor 76-105cm), "
              "5 posiciones de reclinado, 14,7kg. Solapa con Pearl 360 (misma etapa)."),

    # ---------------- BEBE CONFORT ----------------
    dict(marca="Bebe Confort", modelo="RevolveFix Plus 360", asin="B0F3P61P8C", precio=199.99,
         valoracion=4.2, n_val=458, alt_min=40, alt_max=150, grupo="0/1/2/3", isofix=True,
         orientacion="ambas", giro360=True, reclinable=True, instalacion="isofix",
         calidad_datos="alta", actualidad="alta", nota=None),
    dict(marca="Bebe Confort", modelo="Marvel RoadSafe", asin="B0GGZYY3BZ", precio=79.99,
         valoracion=4.4, n_val=224, alt_min=100, alt_max=150, grupo=None, isofix=False,
         orientacion="favor", giro360=False, reclinable=None, instalacion="cinturon",
         calidad_datos="media", actualidad="alta",
         nota="Contradiccion ISOFIX ya detectada y resuelta (ver auditoria grupo)"),
    dict(marca="Bebe Confort", modelo="Manga i-Fix", asin="B000O6OAG0", precio=47.49,
         valoracion=4.4, n_val=837, alt_min=128, alt_max=150, grupo="3", isofix=True,
         orientacion="favor", giro360=False, reclinable=None, instalacion="isofix",
         calidad_datos="alta", actualidad="media",
         nota="Confirmado en bebeconfort.es: 128-150cm, ISOFIX, 2,1kg"),

    # ---------------- CYBEX ----------------
    dict(marca="Cybex", modelo="Solution X i-Fix", asin="B0C58QGJNG", precio=119.99,
         valoracion=4.7, n_val=1659, alt_min=100, alt_max=150, grupo=None, isofix=True,
         orientacion="favor", giro360=False, reclinable=True, instalacion="isofix_o_cinturon",
         calidad_datos="alta", actualidad="alta", nota=None),
    dict(marca="Cybex", modelo="Solution S2 i-Fix", asin="B0B97Z1C6M", precio=149.95,
         valoracion=4.8, n_val=4000, alt_min=100, alt_max=150, grupo=None, isofix=True,
         orientacion="favor", giro360=False, reclinable=None, instalacion="isofix_o_cinturon",
         calidad_datos="media", actualidad="alta", nota="Muy similar a Solution X (mismo segmento)"),
    dict(marca="Cybex", modelo="Cloud G i-Size Comfort", asin="B0DB2J1HMK", precio=229.95,
         valoracion=4.7, n_val=100, alt_min=40, alt_max=87, grupo=None, isofix=True,
         orientacion="contramarcha", giro360=False, reclinable=None, instalacion="isofix",
         calidad_datos="media", actualidad="alta", nota="Portabebe, sin grupo explicito"),
    dict(marca="Cybex", modelo="Pallas G i-Size (G2)", asin="B0DPHRJ1YH", precio=234.86,
         valoracion=4.7, n_val=295, alt_min=76, alt_max=150, grupo=None, isofix=True,
         orientacion="favor", giro360=False, reclinable=True, instalacion="isofix_o_cinturon",
         calidad_datos="media", actualidad="media", nota="Generacion previa a Pallas G3"),

    # ---------------- BRITAX ROMER ----------------
    dict(marca="Britax Romer", modelo="BABY-SAFE CORE", asin="B0CP2QYQK8", precio=135.92,
         valoracion=4.2, n_val=35, alt_min=40, alt_max=83, grupo="0+", isofix=True,
         orientacion="contramarcha", giro360=False, reclinable=None, instalacion="isofix_o_cinturon",
         calidad_datos="alta", actualidad="alta",
         nota="Confirmado en britax-roemer.com: instalacion dual, cinturon de 3 puntos o base ISOFIX opcional"),
    dict(marca="Britax Romer", modelo="DUALFIX2 R", asin="B07QLSYS2Y", precio=399.99,
         valoracion=4.7, n_val=1800, alt_min=None, alt_max=None, grupo="0+/1", isofix=True,
         orientacion="ambas", giro360=True, reclinable=True, instalacion="isofix",
         calidad_datos="alta", actualidad="media", nota="0-18kg/0-4anos, sin rango de altura explicito"),
    dict(marca="Britax Romer", modelo="EVOLVAFIX", asin="B0C3HJNK2M", precio=219.99,
         valoracion=4.5, n_val=763, alt_min=76, alt_max=150, grupo=None, isofix=True,
         orientacion="favor", giro360=False, reclinable=True, instalacion="isofix",
         calidad_datos="alta", actualidad="alta", nota=None),

    # ---------------- CHICCO ----------------
    dict(marca="Chicco", modelo="Kory i-Size Essential", asin="B0C6KXB9LL", precio=169.00,
         valoracion=4.3, n_val=71, alt_min=40, alt_max=80, grupo="0+", isofix=False,
         orientacion="contramarcha", giro360=False, reclinable=None, instalacion="cinturon",
         calidad_datos="media", actualidad="alta",
         nota="ISOFIX solo con base opcional aparte. No aparece con ese nombre exacto en el catalogo actual de "
              "chicco.es (aparece 'Kory Plus' en su lugar) -- identidad no verificada."),
    dict(marca="Chicco", modelo="Unico EVO I'Size Classic", asin="B0C6KZCY6Z", precio=229.00,
         valoracion=4.5, n_val=1230, alt_min=40, alt_max=150, grupo="0123", isofix=True,
         orientacion="ambas", giro360=True, reclinable=True, instalacion="isofix_o_cinturon",
         calidad_datos="alta", actualidad="alta", nota=None),
    dict(marca="Chicco", modelo="Quasar Fix i-Size", asin="B0DW9GD5CG", precio=55.00,
         valoracion=4.7, n_val=52, alt_min=126, alt_max=150, grupo="3", isofix=True,
         orientacion="favor", giro360=False, reclinable=False, instalacion="isofix_o_cinturon",
         calidad_datos="media", actualidad="alta",
         nota="No aparece con ese nombre exacto en chicco.es (aparecen 'Quizy'/'Fold&Go S' en rango similar) "
              "-- identidad no verificada."),

    # ---------------- BABYAUTO ----------------
    dict(marca="BabyAuto", modelo="Rodia Plus i-Size", asin="B0CQP3VKSK", precio=159.00,
         valoracion=4.4, n_val=142, alt_min=40, alt_max=150, grupo=None, isofix=True,
         orientacion="ambas", giro360=True, reclinable=True, instalacion="isofix",
         calidad_datos="media", actualidad="alta",
         nota="Probable coincidencia con 'Rodia Fix' de babyauto.com (mismas specs: 0-36kg, RWF hasta 18kg, "
              "ISOFIX o cinturon, giratoria) pero el nombre no coincide exacto -- identidad no verificada al 100%."),
    # LOLO retirada de la lista (decision del usuario, 2026-08-13): ASIN no
    # confirmado inicialmente y sin pagina propia localizable en
    # shop.babyauto.com bajo ese nombre.

    # ---------------- GRACO ----------------
    dict(marca="Graco", modelo="Junior Maxi i-Size", asin="B0CYQD2H66", precio=54.00,
         valoracion=4.5, n_val=3484, alt_min=100, alt_max=150, grupo=None, isofix=False,
         orientacion="favor", giro360=False, reclinable=False, instalacion="cinturon",
         calidad_datos="alta", actualidad="alta", nota=None),
    dict(marca="Graco", modelo="SlimFit R129", asin="B0BMGN89G3", precio=197.53,
         valoracion=4.7, n_val=85, alt_min=40, alt_max=145, grupo=None, isofix=False,
         orientacion="ambas", giro360=False, reclinable=True, instalacion="cinturon",
         calidad_datos="alta", actualidad="alta", nota=None),

    # ---------------- LIONELO ----------------
    dict(marca="Lionelo", modelo="HUGO i-Size", asin="B0CHS67WJ3", precio=84.99,
         valoracion=4.6, n_val=1500, alt_min=100, alt_max=150, grupo="2/3", isofix=True,
         orientacion="favor", giro360=False, reclinable=None, instalacion="isofix_o_cinturon",
         calidad_datos="alta", actualidad="alta",
         nota="Confirmado en lionelo.com: 100-150cm, ISOFIX o cinturon, solo favor de la marcha, "
              "reposacabezas 8 posiciones. Opcion Amazon."),
    dict(marca="Lionelo", modelo="LEVI ONE i-Size", asin="B0D5QSYXPH", precio=74.99,
         valoracion=4.6, n_val=1062, alt_min=76, alt_max=150, grupo="1/2/3", isofix=False,
         orientacion="favor", giro360=False, reclinable=None, instalacion="cinturon",
         calidad_datos="alta", actualidad="alta",
         nota="Confirmado en lionelo.com: 76-150cm, solo cinturon (sin ISOFIX), solo favor de la marcha, "
              "reposacabezas 10 posiciones."),
    dict(marca="Lionelo", modelo="Bastiaan i-Size", asin="B0CJCC2YYP", precio=154.99,
         valoracion=4.5, n_val=614, alt_min=40, alt_max=150, grupo=None, isofix=True,
         orientacion="ambas", giro360=True, reclinable=True, instalacion="isofix_o_cinturon",
         calidad_datos="alta", actualidad="alta",
         nota="Corregido tras verificar lionelo.com: altura real 40-150cm (no 40-140cm). ISOFIX+TopTether+cinturon, "
              "reclinable (4 posiciones favor + semi-reclinado contramarcha), reposacabezas 7 posiciones."),
    dict(marca="Lionelo", modelo="NAVY i-Size", asin="B0DG2MBP6Z", precio=179.99,
         valoracion=4.5, n_val=174, alt_min=40, alt_max=150, grupo="0+1/2/3", isofix=True,
         orientacion="ambas", giro360=True, reclinable=None, instalacion="isofix",
         calidad_datos="media", actualidad="alta", nota="Solapa mucho con Bastiaan (no verificado en fabricante)"),

    # ---------------- KIKKABOO ----------------
    dict(marca="KikkaBoo", modelo="i-MOOVE 2", asin="B0FL7MMYHN", precio=139.90,
         valoracion=4.1, n_val=209, alt_min=40, alt_max=150, grupo="0/1/2/3", isofix=True,
         orientacion="ambas", giro360=True, reclinable=True, instalacion="isofix",
         calidad_datos="alta", actualidad="alta",
         nota="Confirmado en kikkaboo.com: RWF 40-105cm + FWF 76-150cm, ISOFIX. Opcion Amazon, reposacabezas 24 posiciones"),
    dict(marca="KikkaBoo", modelo="i-PASS", asin="B0DYDY6C5Y", precio=69.90,
         valoracion=4.3, n_val=780, alt_min=76, alt_max=150, grupo="1/2/3", isofix=None,
         orientacion=None, giro360=False, reclinable=None, instalacion=None,
         calidad_datos="baja", actualidad="media",
         nota="Instalacion no especificada en ficha de Amazon. No aparece con ese nombre exacto en kikkaboo.com "
              "(indicio circunstancial: TODOS los modelos 76-150cm del catalogo oficial -i-Cross, i-Bronn- llevan "
              "ISOFIX+TopTether, pero no llega a identidad verificada) -- se mantiene Sin especificar."),
    dict(marca="KikkaBoo", modelo="i-FLIT", asin="B0DS6C4XR8", precio=99.90,
         valoracion=4.5, n_val=462, alt_min=76, alt_max=150, grupo="1/2/3", isofix=True,
         orientacion="favor", giro360=False, reclinable=None, instalacion="isofix",
         calidad_datos="alta", actualidad="alta",
         nota="Confirmado en kikkaboo.com: 76-150cm, ISOFIX+TopTether, 9-36kg"),

    # ---------------- JOVIKIDS ----------------
    dict(marca="Jovikids", modelo="Alzador Coche Grupo 2/3", asin="B09FQ3PYZX", precio=55.99,
         valoracion=4.7, n_val=2991, alt_min=125, alt_max=150, grupo="2/3", isofix=True,
         orientacion="favor", giro360=False, reclinable=False, instalacion="isofix_o_cinturon",
         calidad_datos="alta", actualidad="alta",
         nota="Confirmado en jovikids.com (identidad verificada por 3 senales: 125-150cm/6-12anos/15-36kg): "
              "ISOFIX se usa como refuerzo de estabilidad junto al cinturon, no como sujecion principal -- "
              "resuelve la contradiccion inicial de Amazon. Unico modelo de la marca encontrado."),

    # ---------------- NANIA (menor relevancia, limite 2) ----------------
    dict(marca="Nania", modelo="Belem", asin="B0FLDLZTHJ", precio=59.99,
         valoracion=4.7, n_val=224, alt_min=100, alt_max=150, grupo="2/3", isofix=False,
         orientacion="favor", giro360=False, reclinable=None, instalacion="cinturon",
         calidad_datos="alta", actualidad="media",
         nota="Corregido tras verificar fuente independiente (nania.fr/comparativas): Belem NO lleva ISOFIX, "
              "solo cinturon de 3 puntos. 3,4kg, el mas ligero de la gama."),
    dict(marca="Nania", modelo="Bogota", asin="B0FLDT4541", precio=65.99,
         valoracion=4.8, n_val=176, alt_min=100, alt_max=150, grupo="2/3", isofix=True,
         orientacion="favor", giro360=False, reclinable=None, instalacion="isofix_o_cinturon",
         calidad_datos="alta", actualidad="media",
         nota="Confirmado: es literalmente 'Belem + ISOFIX' segun fuente independiente. Reposacabezas 9 posiciones. "
              "Ya NO se considera redundante con Belem (con/sin ISOFIX es una diferencia real)."),
    dict(marca="Nania", modelo="diversluxe", asin="B0CN9MM6ZW", precio=65.99,
         valoracion=4.7, n_val=65, alt_min=100, alt_max=150, grupo="2/3", isofix=True,
         orientacion="favor", giro360=False, reclinable=None, instalacion="isofix_o_cinturon",
         calidad_datos="media", actualidad="media", nota="3er producto identico en segmento a Belem/Bogota"),

    # ---------------- BABIFY (menor relevancia, limite 1) ----------------
    dict(marca="Babify", modelo="Onboard", asin="B07RYWKS9Z", precio=149.99,
         valoracion=4.4, n_val=7143, alt_min=40, alt_max=150, grupo="0123", isofix=True,
         orientacion="ambas", giro360=True, reclinable=True, instalacion="isofix",
         calidad_datos="media", actualidad="alta",
         nota="Opcion Amazon, el mayor volumen de todo el rastreo. Sin web de fabricante oficial independiente "
              "localizable (marca de marketplace); specs corroboradas via manual de instrucciones del producto, "
              "no via ficha oficial -- calidad de datos bajada de alta a media por este motivo."),
    dict(marca="Babify", modelo="Silla Isofix 15-36kg", asin="B08BY2XL1M", precio=74.99,
         valoracion=4.3, n_val=202, alt_min=100, alt_max=150, grupo=None, isofix=True,
         orientacion="favor", giro360=False, reclinable=None, instalacion="isofix_o_cinturon",
         calidad_datos="baja", actualidad="media",
         nota="ALERTA IDENTIDAD: tabla de specs de Amazon dice Marca=Star Ibaby, no Babify -- revisar antes de dar por bueno"),
    dict(marca="Babify", modelo="FlexiFit Basic", asin="B0F1TVJ463", precio=79.99,
         valoracion=4.2, n_val=13, alt_min=None, alt_max=None, grupo="2/3", isofix=True,
         orientacion="favor", giro360=False, reclinable=None, instalacion="isofix",
         calidad_datos="baja", actualidad="alta", nota="Muy pocas valoraciones, sin altura explicita"),
]

QUALITY_SCORE = {"alta": 100, "media": 60, "baja": 25}
ACTUALIDAD_SCORE = {"alta": 100, "media": 60, "baja": 25}
PRECIO_BUCKETS = [(0, 100, "entrada"), (100, 200, "medio"), (200, 10_000, "premium")]


def precio_segmento(precio):
    for lo, hi, label in PRECIO_BUCKETS:
        if lo <= precio < hi:
            return label
    return "premium"


def cobertura_util(c):
    """Amplitud del rango de altura normalizada sobre 110cm (40-150, el
    maximo real observado en este universo). Si no hay altura explicita,
    usa el numero de segmentos de grupo (si hay grupo) como proxy debil;
    si no hay ninguno de los dos, cobertura = 0 (nunca se infiere)."""
    if c["alt_min"] is not None and c["alt_max"] is not None:
        amplitud = c["alt_max"] - c["alt_min"]
        return round(min(100, amplitud / 110 * 100), 1)
    if c["grupo"]:
        segmentos = len([s for s in c["grupo"].replace("+", "").split("/") if s])
        return round(min(100, segmentos / 4 * 100), 1)
    return 0.0


def build_dataset():
    max_reviews_global = max(c["n_val"] for c in CANDIDATOS)
    max_log_global = math.log10(max_reviews_global + 1)
    by_marca_max = defaultdict(int)
    by_marca_rows = defaultdict(list)
    for c in CANDIDATOS:
        by_marca_max[c["marca"]] = max(by_marca_max[c["marca"]], c["n_val"])
        by_marca_rows[c["marca"]].append(c)

    rows = []
    for c in CANDIDATOS:
        pop_log = math.log10(c["n_val"] + 1)
        pop_score = round(pop_log / max_log_global * 100, 1)
        pop_relativa_marca = round(c["n_val"] / by_marca_max[c["marca"]] * 100, 1)
        cob = cobertura_util(c)
        calidad = QUALITY_SCORE[c["calidad_datos"]]
        actualidad = ACTUALIDAD_SCORE[c["actualidad"]]
        valoracion_score = round(c["valoracion"] / 5 * 100, 1)
        segmento = precio_segmento(c["precio"])
        # precio_score: score individual neutro (no penaliza ni premia un
        # precio concreto); la diversidad de SEGMENTO se premia aparte, en
        # valor_incremental (selection-time), no aqui.
        precio_score = 70.0
        rows.append(dict(
            c, pop_score=pop_score, pop_relativa_marca=pop_relativa_marca,
            cobertura_util=cob, calidad_score=calidad, actualidad_score=actualidad,
            valoracion_score=valoracion_score, segmento=segmento, precio_score=precio_score,
        ))

    # caracteristicas_diferenciales: rareza GLOBAL (en todo el universo de
    # 45 candidatos) de isofix/giro360/reclinable/orientacion -- mide cuan
    # poco comun es un rasgo en el mercado en general.
    flags = ["isofix", "giro360", "reclinable"]
    orient_flags = {"contramarcha": lambda r: r["orientacion"] == "contramarcha",
                     "ambas": lambda r: r["orientacion"] == "ambas"}
    total = len(rows)
    rarity = {}
    for f in flags:
        n_true = sum(1 for r in rows if r.get(f) is True)
        rarity[f] = 1 - (n_true / total)
    for name, fn in orient_flags.items():
        n_true = sum(1 for r in rows if fn(r))
        rarity[name] = 1 - (n_true / total)
    for r in rows:
        score = 0.0
        for f in flags:
            if r.get(f) is True:
                score += rarity[f]
        for name, fn in orient_flags.items():
            if fn(r):
                score += rarity[name]
        r["caracteristicas_score"] = round(min(100, score / 3 * 100), 1)

    # complementariedad_potencial: rareza LOCAL, dentro de la propia marca
    # -- cuanto se aparta este producto del perfil tipico de SUS HERMANOS
    # de marca en instalacion/orientacion/giro360. Es una propiedad
    # intrinseca del producto (no depende de que se haya seleccionado
    # nada todavia); el VALOR_INCREMENTAL, mas abajo, es el que si depende
    # de la seleccion parcial en curso.
    facets_local = ["instalacion", "orientacion", "giro360"]
    for r in rows:
        hermanos = [h for h in by_marca_rows[r["marca"]] if h is not r]
        if not hermanos:
            r["complementariedad_potencial"] = 50.0  # unico de su marca: neutro
            continue
        difs = 0
        for f in facets_local:
            difs += sum(1 for h in hermanos if h.get(f) != r.get(f))
        r["complementariedad_potencial"] = round(
            min(100, difs / (len(hermanos) * len(facets_local)) * 100), 1)

    return rows


WEIGHTS = dict(
    cobertura_util=0.20, pop_score=0.20, complementariedad_potencial=0.15,
    calidad_score=0.15, caracteristicas_score=0.10, actualidad_score=0.10,
    valoracion_score=0.05, precio_score=0.05,
)
assert abs(sum(WEIGHTS.values()) - 1.0) < 1e-9


def score_individual(r):
    return round(sum(WEIGHTS[k] * r[k] for k in WEIGHTS), 2)


def etapa_de(r):
    """'Infantil' = rango corto (<=70cm) que termina pronto (<=110cm), sea
    que empiece en 40cm (recien nacido) o mas tarde (Pearl 360 empieza en
    61cm pero sigue siendo etapa infantil, no evolutiva completa).
    Corregido tras el cruce con fabricante: un umbral <=90cm metia a Pearl
    360/Mica Pro Eco en el mismo cubo que Emerald 360S (40-150)."""
    if r["alt_min"] is None:
        return "grupo:" + (r["grupo"] or "?")
    amplitud = r["alt_max"] - r["alt_min"]
    if r["alt_max"] <= 110 and amplitud <= 70:
        return "infantil"
    if r["alt_min"] >= 95:
        return "elevador"
    return "evolutiva"


FACET_WEIGHTS = dict(etapa=25.0, instalacion=20.0, orientacion=20.0, giro360=15.0, segmento=10.0, rango=10.0)


def rango_nuevo_pct(r, seleccionados):
    """Fraccion (0-1) del rango de altura de r que NO esta ya cubierta por
    la UNION de los rangos de los productos ya seleccionados. Si r no
    tiene rango de altura explicito, devuelve 0 (no se infiere)."""
    if r["alt_min"] is None:
        return 0.0
    intervalos = [(s["alt_min"], s["alt_max"]) for s in seleccionados if s["alt_min"] is not None]
    if not intervalos:
        return 1.0
    total_cm = r["alt_max"] - r["alt_min"]
    if total_cm <= 0:
        return 0.0
    cubierto = 0
    paso = 1
    for cm in range(r["alt_min"], r["alt_max"], paso):
        if any(lo <= cm < hi for lo, hi in intervalos):
            cubierto += paso
    return max(0.0, 1 - cubierto / total_cm)


def valor_incremental(r, seleccionados):
    """Cuanto valor NUEVO aporta el candidato r frente a lo que YA esta
    seleccionado (no frente a todo el universo). Dos partes:

    1. bonus_complementariedad (0-100): suma de pesos de las facetas
       (etapa/instalacion/orientacion/giro360/segmento/rango-de-altura)
       que r aporta y que NINGUN seleccionado tiene todavia.
    2. penalizacion_redundancia (0-100): penaliza fuerte cuando r se
       parece MUCHO (en las facetas de mayor peso) a un producto YA
       seleccionado en concreto -- no por coincidir en un par de facetas
       sueltas (p.ej. mismo segmento de precio), sino por ser
       practicamente el mismo producto en la practica.

    valor_incremental = clamp(bonus - penalizacion, 0, 100).

    Si `seleccionados` esta vacio (se esta eligiendo el producto #1 de la
    marca), no hay nada frente a lo que ser incremental: devuelve
    (0, 0, 0) y la seleccion de ese primer hueco se hace solo por
    score_individual."""
    if not seleccionados:
        return 0.0, 0.0, 0.0

    etapa_r = etapa_de(r)
    etapas_ya = {etapa_de(s) for s in seleccionados}
    instal_ya = {s["instalacion"] for s in seleccionados}
    orient_ya = {s["orientacion"] for s in seleccionados}
    giro_ya = {s["giro360"] for s in seleccionados}
    seg_ya = {s["segmento"] for s in seleccionados}

    bonus = 0.0
    if etapa_r not in etapas_ya:
        bonus += FACET_WEIGHTS["etapa"]
    if r["instalacion"] not in instal_ya:
        bonus += FACET_WEIGHTS["instalacion"]
    if r["orientacion"] not in orient_ya:
        bonus += FACET_WEIGHTS["orientacion"]
    if r["giro360"] not in giro_ya:
        bonus += FACET_WEIGHTS["giro360"]
    if r["segmento"] not in seg_ya:
        bonus += FACET_WEIGHTS["segmento"]
    bonus += FACET_WEIGHTS["rango"] * rango_nuevo_pct(r, seleccionados)

    # Penalizacion: solapamiento PONDERADO (mismas facetas y pesos de
    # arriba) contra CADA seleccionado por separado -- solo penaliza
    # fuerte cuando la mayoria de facetas de peso alto coinciden con UN
    # mismo producto concreto (clon funcional), no cuando coincide un par
    # de facetas sueltas repartidas entre varios seleccionados distintos.
    penal = 0.0
    for s in seleccionados:
        solapa = 0.0
        if etapa_r == etapa_de(s):
            solapa += FACET_WEIGHTS["etapa"]
        if r["instalacion"] == s["instalacion"]:
            solapa += FACET_WEIGHTS["instalacion"]
        if r["orientacion"] == s["orientacion"]:
            solapa += FACET_WEIGHTS["orientacion"]
        if r["giro360"] == s["giro360"]:
            solapa += FACET_WEIGHTS["giro360"]
        if r["segmento"] == s["segmento"]:
            solapa += FACET_WEIGHTS["segmento"]
        # Solo penaliza cuando el solape ponderado supera 55/100 -- es
        # decir, cuando coincide en la mayoria de facetas de peso alto.
        # Con 40 como umbral, un candidato que solo difiere en
        # instalacion (20 pts) pero coincide en etapa+orientacion+giro360
        # +segmento (75 pts) quedaba anulado aunque esa unica diferencia
        # (ISOFIX si/no) sea justo el tipo de diferencia que el usuario
        # marco como mas valiosa (ver ejemplo Nania Belem/Bogota: la
        # unica diferencia real entre ambas es ISOFIX, y con el umbral
        # antiguo Bogota quedaba descartada pese a ser una comparativa
        # genuinamente util para el lector "con ISOFIX vs sin ISOFIX").
        penal = max(penal, max(0.0, solapa - 60.0))

    bonus = round(min(100.0, bonus), 1)
    penal = round(min(100.0, penal), 1)
    incremental = round(max(0.0, min(100.0, bonus - penal)), 1)
    return incremental, bonus, penal


UMBRAL_VALOR_INCREMENTAL_MINIMO = 10.0  # por debajo de esto, no forzar el hueco


def select_por_marca(rows_marca, limite):
    """Seleccion SECUENCIAL en `limite` pasos (nunca ordenar por
    score_individual y coger los N primeros):

      Paso 1: producto = mejor score_individual en solitario.
      Paso 2: producto = el que maximiza 0.5*score_individual +
              0.5*valor_incremental frente al paso 1 ya elegido.
      Paso 3: idem frente a los pasos 1+2 ya elegidos.

    Si el mejor candidato restante en un paso >=2 no llega a un
    valor_incremental minimo (UMBRAL_VALOR_INCREMENTAL_MINIMO), se corta
    la seleccion ahi -- no se rellena artificialmente hasta el limite."""
    restantes = list(rows_marca)
    seleccion = []

    while restantes and len(seleccion) < limite:
        es_primero = not seleccion
        mejor = None
        mejor_datos = None
        for r in restantes:
            incremental, bonus, penal = valor_incremental(r, seleccion)
            if es_primero:
                sel_score = r["score_individual"]
            else:
                sel_score = round(0.5 * r["score_individual"] + 0.5 * incremental, 2)
            if mejor is None or sel_score > mejor_datos[0]:
                mejor = r
                mejor_datos = (sel_score, incremental, bonus, penal)

        sel_score, incremental, bonus, penal = mejor_datos
        if not es_primero and incremental < UMBRAL_VALOR_INCREMENTAL_MINIMO:
            # El mejor candidato restante no aporta suficiente valor nuevo:
            # se corta la seleccion de esta marca aqui, sin forzar el hueco.
            break

        mejor["bonus_complementariedad"] = bonus
        mejor["penalizacion_redundancia"] = penal
        mejor["valor_incremental"] = incremental
        mejor["score_seleccion"] = sel_score
        seleccion.append(mejor)
        restantes.remove(mejor)

    descartados = restantes
    for r in descartados:
        incremental, bonus, penal = valor_incremental(r, seleccion)
        r["bonus_complementariedad"] = bonus
        r["penalizacion_redundancia"] = penal
        r["valor_incremental"] = incremental
        r["score_seleccion"] = round(0.5 * r["score_individual"] + 0.5 * incremental, 2) if seleccion else r["score_individual"]
    return seleccion, descartados


def main():
    rows = build_dataset()
    for r in rows:
        r["score_individual"] = score_individual(r)

    by_marca = defaultdict(list)
    for r in rows:
        by_marca[r["marca"]].append(r)

    resultado = {}
    for marca, rows_marca in by_marca.items():
        limite = LIMITE_MARCA.get(marca, 2)
        seleccion, descartados = select_por_marca(rows_marca, limite)
        resultado[marca] = dict(
            limite=limite,
            n_analizados=len(rows_marca),
            n_seleccionados=len(seleccion),
            seleccion=seleccion,
            descartados=descartados,
        )

    with open("tools/output/candidatos_seleccion.json", "w", encoding="utf-8") as f:
        json.dump(resultado, f, ensure_ascii=False, indent=2)

    print(f"OK: {len(rows)} candidatos analizados en {len(by_marca)} marcas.")
    print("Reporte: tools/output/candidatos_seleccion.json")
    for marca, data in resultado.items():
        print(f"\n{marca} (limite {data['limite']}, analizados {data['n_analizados']}, seleccionados {data['n_seleccionados']}):")
        for i, r in enumerate(data["seleccion"], 1):
            print(f"  #{i} {r['modelo']:<28} score_ind={r['score_individual']:>6.1f}  "
                  f"pop={r['pop_score']:>5.1f} cob={r['cobertura_util']:>5.1f} calidad={r['calidad_score']:>5.1f}  "
                  f"val_incr={r['valor_incremental']:>5.1f} (bonus={r['bonus_complementariedad']:>5.1f} "
                  f"-penal={r['penalizacion_redundancia']:>5.1f})  score_sel={r['score_seleccion']:>6.1f}  n_val={r['n_val']}")

    # Revision global de diversidad (punto 9): concentracion del catalogo
    # final en 360/ISOFIX/evolutiva-completa, para detectar si el
    # resultado agregado queda demasiado homogeneo pese a la
    # diversificacion dentro de cada marca.
    seleccionados_todos = [r for data in resultado.values() for r in data["seleccion"]]
    n = len(seleccionados_todos)
    n_360 = sum(1 for r in seleccionados_todos if r["giro360"])
    n_isofix_puro = sum(1 for r in seleccionados_todos if r["instalacion"] == "isofix")
    n_sin_isofix = sum(1 for r in seleccionados_todos if r["instalacion"] == "cinturon")
    n_evolutiva_completa = sum(1 for r in seleccionados_todos if etapa_de(r) == "evolutiva"
                                and r["alt_min"] is not None and r["alt_max"] - r["alt_min"] >= 100)
    print(f"\n=== REVISION GLOBAL DE DIVERSIDAD ({n} productos seleccionados en total) ===")
    print(f"  Con giro 360º:        {n_360}/{n} ({round(100*n_360/n)}%)")
    print(f"  Instalacion ISOFIX puro: {n_isofix_puro}/{n} ({round(100*n_isofix_puro/n)}%)")
    print(f"  Sin ISOFIX (solo cinturon): {n_sin_isofix}/{n} ({round(100*n_sin_isofix/n)}%)")
    print(f"  Evolutiva de rango >=100cm: {n_evolutiva_completa}/{n} ({round(100*n_evolutiva_completa/n)}%)")


if __name__ == "__main__":
    main()
