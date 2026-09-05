#!/usr/bin/env python3
"""
reextraccion_lote1_clasificacion.py

Vuelve a ejecutar los 15 productos del Lote 1 a traves de la logica de
clasificacion (Amazon + fabricante oficial) de amazon_sillas_coche.py,
reutilizando el material crudo ya verificado en la auditoria
(tools/output/lote1_audit_raw.json) en vez de volver a golpear Amazon: el
texto de Amazon no cambia en minutos y esto aisla el efecto puro del cambio
de codigo. Actualiza el bloque "clasificacion" de tools/output/lote1_final.json
(no toca "caracteristicas", que sigue igual) y genera un diagnostico de
calidad completo (cobertura antes/despues, listado de revisar=true,
identidades verificadas, aportes del fabricante).

No modifica amazon_import.py. No vuelve a visitar Amazon.

Uso:
    python tools/reextraccion_lote1_clasificacion.py
"""

import json
import sys
from collections import OrderedDict

sys.path.insert(0, "tools")
from amazon_sillas_coche import build_clasificacion, load_fabricante_lookup  # noqa: E402

# clave clasificacion -> etiqueta legible + clave "antes" correspondiente en
# caracteristicas (raw, solo detector de Amazon, None si no aplica un
# equivalente 1:1 directo).
ATRIBUTOS = OrderedDict([
    ("isofix", ("ISOFIX", "isofix")),
    ("tipo_instalacion", ("Tipo de instalacion", None)),
    ("normativa", ("Normativa", "homologacion")),
    ("grupo_r44", ("Grupo R44", None)),
    ("altura_r129", ("Altura (R129)", None)),
    ("peso", ("Peso recomendado", "peso_recomendado")),
    ("edad", ("Edad", "grupo_edad")),
    ("orientacion", ("Orientacion", "orientacion")),
    ("giro_360", ("Giro 360º", "giro_360")),
    ("reclinable", ("Reclinable", "reclinable")),
    ("reposacabezas", ("Reposacabezas regulable", "reposacabezas_regulable")),
    ("arnes", ("Arnes / proteccion", "tipo_arnes_proteccion")),
    ("peso_silla", ("Peso de la silla", "peso_silla")),
    ("proteccion_lateral", ("Proteccion lateral", "proteccion_lateral")),
    ("funda_lavable", ("Funda lavable", "funda_lavable")),
])


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")

    audit = json.load(open("tools/output/lote1_audit_raw.json", encoding="utf-8"))
    final = json.load(open("tools/output/lote1_final.json", encoding="utf-8"))
    lookup = load_fabricante_lookup()
    audit_by_asin = {p["asin"]: p for p in audit}

    n = len(final["productos"])
    cobertura = {k: {"confirmados": 0, "na": 0, "revisar": 0} for k in ATRIBUTOS}
    revisar_rows = []
    identidad_verificada_list = []
    fabricante_aporta_list = []

    for prod in final["productos"]:
        asin = prod["asin"]
        p = audit_by_asin[asin]
        raw = {
            "title": p.get("titulo"),
            "bullets": p.get("bullets", []),
            "description": p.get("descripcion", ""),
            "detail_rows": [tuple(row) for row in p.get("detalle", [])],
        }
        fab_entry = lookup.get(asin)
        clasificacion = build_clasificacion(raw, asin, lookup)
        prod["clasificacion"] = clasificacion

        etiqueta = f"{prod['marca']} — {prod['modelo'][:60]}"

        if fab_entry and fab_entry.get("identidad_verificada"):
            identidad_verificada_list.append({
                "asin": asin, "marca_modelo": etiqueta,
                "nombre_amazon": fab_entry.get("nombre_amazon"),
                "nombre_fabricante": fab_entry.get("nombre_fabricante"),
                "aviso_nombre_diferente": fab_entry.get("aviso_nombre_diferente"),
                "motivo_equivalencia": fab_entry.get("motivo_equivalencia"),
            })

        for clave, (etiqueta_attr, clave_antes) in ATRIBUTOS.items():
            campo = clasificacion[clave]
            if campo["revisar"]:
                cobertura[clave]["revisar"] += 1
                revisar_rows.append({
                    "asin": asin,
                    "marca_modelo": etiqueta,
                    "atributo": etiqueta_attr,
                    "valor_actual": campo["mostrar"],
                    "fuente": campo["fuente"],
                    "url_fuente": campo["url_fuente"],
                    "evidencia": campo["texto_fuente"],
                    "motivo_revision": (
                        "Posible variante/producto diferente (identidad fabricante no confirmada)"
                        if campo["mostrar"] == "Posible variante/producto diferente — no confirmado"
                        else "Contradiccion Amazon vs. fabricante oficial (o ambigueedad marcada en el lookup)"
                    ),
                })
            elif campo["normalizado"] is not None:
                cobertura[clave]["confirmados"] += 1
                if campo["fuente"] == "fabricante_oficial":
                    fabricante_aporta_list.append({
                        "asin": asin, "marca_modelo": etiqueta,
                        "atributo": etiqueta_attr, "valor": campo["mostrar"],
                        "url_fuente": campo["url_fuente"],
                    })
            else:
                cobertura[clave]["na"] += 1

    with open("tools/output/lote1_final.json", "w", encoding="utf-8") as f:
        json.dump(final, f, ensure_ascii=False, indent=2)

    diagnostico = {
        "total_productos": n,
        "cobertura": {
            k: {
                **v,
                "cobertura_pct": round(100 * v["confirmados"] / n, 1),
            }
            for k, v in cobertura.items()
        },
        "revisar": revisar_rows,
        "identidad_verificada": identidad_verificada_list,
        "fabricante_aporta_dato_que_amazon_no_tenia": fabricante_aporta_list,
    }
    with open("tools/output/lote1_diagnostico.json", "w", encoding="utf-8") as f:
        json.dump(diagnostico, f, ensure_ascii=False, indent=2)

    print(f"OK: clasificacion completa (15 atributos) recalculada para {n} productos.")
    print("JSON maestro: tools/output/lote1_final.json")
    print("Diagnostico: tools/output/lote1_diagnostico.json")
    print()
    print(f"{'Atributo':<28} {'Confirmados':>12} {'N/A':>6} {'Revisar':>8} {'Cobertura %':>12}")
    for k, (etiqueta_attr, _) in ATRIBUTOS.items():
        v = diagnostico["cobertura"][k]
        print(f"{etiqueta_attr:<28} {v['confirmados']:>12} {v['na']:>6} {v['revisar']:>8} {v['cobertura_pct']:>11}%")
    print()
    print(f"Casos revisar=true: {len(revisar_rows)}")
    print(f"Identidad Amazon/fabricante verificada: {len(identidad_verificada_list)} productos")
    print(f"Datos aportados solo por el fabricante: {len(fabricante_aporta_list)}")


if __name__ == "__main__":
    main()
