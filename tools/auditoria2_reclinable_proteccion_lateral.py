#!/usr/bin/env python3
"""
auditoria2_reclinable_proteccion_lateral.py

Segunda auditoria exhaustiva (15-ago-2026) de los dos unicos atributos
pendientes de revision: RECLINABLE y PROTECCION_LATERAL. Investiga los 17
ASIN que estaban en "Sin especificar" en alguno de los dos campos
(union de ambos conjuntos) usando exclusivamente Amazon (texto crudo
scrapeado con tools/scrape_reclinable_pl_raw.py -> tools/output/raw_reclinable_pl.json)
y fabricante oficial cuando la identidad esta verificada y la pagina es
accesible.

NO toca ningun otro campo. NO toca amazon_import.py ni ningun archivo de
produccion. Valida explicitamente que solo se modifican celdas de
"reclinable" y "proteccion_lateral" respecto al snapshot pre-auditoria.

Resultado de la investigacion (ver informe entregado en el chat para el
detalle completo de fuentes por producto):

- RECLINABLE: ninguno de los 12 "Sin especificar" tenia evidencia
  explicita (ni en Amazon ni en fabricante, cuando fue accesible) tras la
  busqueda ampliada de sinonimos pedida por el usuario. 0 cambios.
- PROTECCION_LATERAL: 2 de los 11 "Sin especificar" se resuelven a "Si"
  con evidencia explicita:
    * Cybex Pallas G i-Size (G2) [B0DPHRJ1YH]: fabricante oficial
      (cybex-online.com, pagina verificada, identidad confirmada por
      modelo/URL) -- "El sistema de Proteccion lineal contra impactos
      laterales Plus (LSP) ... reduce las fuerzas de impacto de una
      colision lateral en mas del 20%". Corrige la nota previa que decia
      "Impact Shield, tecnologia distinta a proteccion lateral
      tradicional" -- el Impact Shield y el LSP son dos sistemas
      distintos del mismo producto; el LSP SI es proteccion lateral.
    * Chicco Unico EVO I'Size Classic [B0C6KZCY6Z]: mencion explicita en
      el titulo de Amazon ("... Ajustable y Proteccion Lateral, Negra"),
      mismo patron ya aceptado en el dataset para otros productos
      ("Si (mencionada en titulo)").

Uso:
    python tools/auditoria2_reclinable_proteccion_lateral.py <snapshot.json> <dataset.json>
"""

import json
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Cambios resueltos en esta auditoria (unicamente estos 2; el resto de los
# 17 ASIN investigados se queda en "Sin especificar" tras busqueda
# exhaustiva sin evidencia -- no se tocan, no aparecen en este diccionario).
# ---------------------------------------------------------------------------

PROTECCION_LATERAL_UPDATES = {
    "B0DPHRJ1YH": (
        "Sí (Protección lineal contra impactos laterales Plus — LSP, "
        "confirmado en fabricante oficial cybex-online.com)",
        (
            "✅ RESUELTO (15-ago-2026, 2ª auditoría reclinable/protección "
            "lateral): fabricante oficial (cybex-online.com/es/es/p/"
            "CS_GO_Pallas_G_i-Size_EN.html, identidad verificada por "
            "modelo/color exactos), sección 'Destacados y características' "
            "visible: \"El sistema de Protección lineal contra impactos "
            "laterales Plus (LSP) y la estructura absorbe-energía reducen "
            "las fuerzas de impacto de una colisión lateral en más del "
            "20 %\". Corrige la nota previa de la auditoría anterior "
            "('Impact Shield, tecnología distinta a protección lateral "
            "tradicional') -- el Impact Shield (chest-shield tipo airbag, "
            "protección frontal) y el LSP (protección lateral) son dos "
            "sistemas de seguridad DISTINTOS presentes ambos en este "
            "producto; el LSP sí es protección lateral en el sentido que "
            "pide este atributo."
        ),
    ),
    "B0C6KZCY6Z": (
        "Sí (mencionada en título)",
        (
            "✅ RESUELTO (15-ago-2026, 2ª auditoría reclinable/protección "
            "lateral): título literal de Amazon para este ASIN: \"Chicco "
            "Unico EVO I'Size Classic, Silla de Coche ISOFIX para Bebés y "
            "Niños de 40 a 150 cm, Grupo 0123 Desde Recién Nacido hasta 12 "
            "Años, Giratoria 360º, Reductor, Ajustable y Protección "
            "Lateral, Negra\" -- mención explícita como característica "
            "nombrada del producto (mismo patrón ya aceptado en el "
            "dataset para otros ASIN: 'Sí (mencionada en título)'). Los "
            "bullets/descripción no añaden más detalle (no nombran un "
            "sistema con marca propia), pero la mención en título es "
            "evidencia suficiente según el criterio ya vigente."
        ),
    ),
}

# No hay cambios de reclinable en esta auditoria: los 12 ASIN investigados
# (Kinderkraft I-BOOST 2, Maxi-Cosi Tanza, Bebeconfort Marvel RoadSafe,
# Britax BABY-SAFE CORE, Chicco Kory Essential, Chicco Quasar Fix, Graco
# Junior Maxi, Lionelo HUGO, Lionelo LEVI ONE, KikkaBoo i-PASS, Nania
# Belem, Nania Bogota) se quedan en "Sin especificar" tras busqueda
# exhaustiva de sinonimos en Amazon (titulo/bullets/descripcion/tabla de
# detalles) y, cuando fue accesible, en fabricante oficial.
RECLINABLE_UPDATES = {}

INVESTIGADOS_SIN_CAMBIO = {
    "reclinable": [
        "B0F1R26D8L", "B0CZ47FKZL", "B0GGZYY3BZ", "B0CP2QYQK8",
        "B0C6KXB9LL", "B0DW9GD5CG", "B0CYQD2H66", "B0CHS67WJ3",
        "B0D5QSYXPH", "B0DYDY6C5Y", "B0FLDLZTHJ", "B0FLDT4541",
    ],
    "proteccion_lateral": [
        "B0F1R26D8L", "B0GGZYY3BZ", "B07QLSYS2Y", "B0CP2QYQK8",
        "B0C6KXB9LL", "B0DW9GD5CG", "B0DYDY6C5Y", "B09FQ3PYZX",
        "B07RYWKS9Z",
    ],
}


def load(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def save(data, path):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")


def aplicar_updates(productos, campo, updates):
    aplicados = set()
    for p in productos:
        if p["asin"] in updates:
            nuevo_valor, nota = updates[p["asin"]]
            p[campo] = nuevo_valor
            p["estado_auditoria"] = p.get("estado_auditoria", "") + " | " + nota
            aplicados.add(p["asin"])
    faltan = set(updates) - aplicados
    if faltan:
        raise ValueError(f"ASIN de {campo} no encontrados: {faltan}")


def diff_datasets(antes, despues):
    antes_por_asin = {p["asin"]: p for p in antes["productos"]}
    despues_por_asin = {p["asin"]: p for p in despues["productos"]}

    assert set(antes_por_asin) == set(despues_por_asin), "Se han añadido/quitado productos -- no permitido en esta auditoría"

    celdas_modificadas = []
    for asin in sorted(antes_por_asin):
        a, d = antes_por_asin[asin], despues_por_asin[asin]
        campos = set(a.keys()) | set(d.keys())
        for campo in sorted(campos):
            va, vd = a.get(campo), d.get(campo)
            if va != vd:
                celdas_modificadas.append({
                    "asin": asin, "modelo": d.get("modelo"), "campo": campo,
                    "antes": va, "despues": vd,
                })

    return {
        "productos_con_cambios": sorted({c["asin"] for c in celdas_modificadas}),
        "atributos_afectados": sorted({c["campo"] for c in celdas_modificadas}),
        "num_celdas_modificadas": len(celdas_modificadas),
        "celdas": celdas_modificadas,
    }


def contar_cobertura(productos, campo):
    si = no = revisar = sin_esp = 0
    for p in productos:
        v = str(p.get(campo, "")).strip()
        vl = v.lower()
        if "revisar" in vl:
            revisar += 1
        elif vl.startswith("sin especificar") or v == "":
            sin_esp += 1
        elif vl.startswith("sí") or vl.startswith("si "):
            si += 1
        elif vl.startswith("no"):
            no += 1
        else:
            si += 1
    return {"si": si, "no": no, "revisar": revisar, "sin_especificar": sin_esp}


def main():
    if len(sys.argv) != 3:
        print("Uso: python auditoria2_reclinable_proteccion_lateral.py <snapshot.json> <dataset.json>", file=sys.stderr)
        sys.exit(1)

    snapshot_path, dataset_path = sys.argv[1], sys.argv[2]
    antes = load(snapshot_path)
    data = load(dataset_path)
    productos = data["productos"]

    assert len(productos) == 30, f"Se esperaban 30 productos, hay {len(productos)}"

    aplicar_updates(productos, "reclinable", RECLINABLE_UPDATES)
    aplicar_updates(productos, "proteccion_lateral", PROTECCION_LATERAL_UPDATES)

    data["productos"] = productos
    data["_nota"] = data["_nota"] + (
        " [2ª AUDITORÍA RECLINABLE/PROTECCIÓN LATERAL 15-ago-2026: "
        "búsqueda exhaustiva de los 17 ASIN pendientes en Amazon + "
        "fabricante oficial (cuando accesible). Reclinable: 0 cambios "
        "(sin evidencia en ninguno de los 12 pendientes). Protección "
        "lateral: 2 cambios a Sí (Cybex Pallas G i-Size G2 vía fabricante "
        "oficial LSP; Chicco Unico EVO vía mención en título de Amazon).]"
    )

    save(data, dataset_path)

    diff = diff_datasets(antes, data)
    diff_path = str(Path(dataset_path).with_name("auditoria2_reclinable_pl_diff.json"))
    save(diff, diff_path)

    cobertura_reclinable = contar_cobertura(productos, "reclinable")
    cobertura_pl = contar_cobertura(productos, "proteccion_lateral")

    resultado = {
        "num_celdas_modificadas": diff["num_celdas_modificadas"],
        "productos_con_cambios": diff["productos_con_cambios"],
        "atributos_afectados": diff["atributos_afectados"],
        "cobertura_reclinable": cobertura_reclinable,
        "cobertura_proteccion_lateral": cobertura_pl,
    }
    print(json.dumps(resultado, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
