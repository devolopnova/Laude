#!/usr/bin/env python3
"""
auditoria3_edad_completar.py

Punto 7.3 (16-ago-2026): completa UNICAMENTE los dos valores de "edad"
que quedaban "Sin especificar" en el dataset de 30 sillitas de coche.
No toca ningun otro atributo, ni de estos dos productos ni de ningun
otro. Sigue el mismo patron reproducible que
tools/auditoria2_reclinable_proteccion_lateral.py: carga el dataset,
aplica los cambios desde un diccionario, valida contra el snapshot
pre-cambio que SOLO se modificaron las celdas esperadas, y escribe un
diff completo.

Cambios:
  1. Kinderkraft SAFETY FIX 3 PRO [B0FGDM2ZTS]: edad -> "15 meses - 12
     años". Valor decidido manualmente por el usuario (16-ago-2026).
  2. Lionelo LEVI ONE i-Size [B0D5QSYXPH]: edad -> "15 meses - 12 años".
     Derivado del propio dataset: LEVI ONE tiene altura "76-150 cm"
     (sin cambios). Los otros 3 productos del dataset con esa MISMA
     altura exacta -- Cybex Pallas G i-Size (G2) [B0DPHRJ1YH], KikkaBoo
     i-PASS [B0DYDY6C5Y] y KikkaBoo i-FLIT [B0DS6C4XR8] -- tienen los
     3 la misma edad "15 meses - 12 años" (unanimidad 3/3 en las
     referencias disponibles). No se recalcula ni se inventa: se
     aplica el patron ya existente en el propio dataset.

Uso:
    python tools/auditoria3_edad_completar.py <snapshot.json> <dataset.json>
"""

import json
import sys
from pathlib import Path

EDAD_UPDATES = {
    "B0FGDM2ZTS": (
        "15 meses - 12 años",
        (
            "✅ RESUELTO (16-ago-2026, punto 7.3): edad establecida "
            "manualmente por el usuario -- \"15 meses - 12 años\". No se "
            "modifica altura/grupo/peso de este producto."
        ),
    ),  # Kinderkraft SAFETY FIX 3 PRO
    "B0D5QSYXPH": (
        "15 meses - 12 años",
        (
            "✅ RESUELTO (16-ago-2026, punto 7.3): edad derivada del "
            "propio dataset, sin inventar ni recalcular. Este producto "
            "tiene altura \"76-150 cm\" (sin cambios). Los otros 3 "
            "productos del dataset con esa MISMA altura exacta -- Cybex "
            "Pallas G i-Size (G2) [B0DPHRJ1YH], KikkaBoo i-PASS "
            "[B0DYDY6C5Y] y KikkaBoo i-FLIT [B0DS6C4XR8] -- tienen los 3 "
            "la edad \"15 meses - 12 años\" (unanimidad 3/3 referencias "
            "disponibles en el dataset). Se aplica el mismo valor por "
            "coherencia con el patron ya auditado, no por calculo "
            "propio. No se modifica altura/grupo/peso de este producto."
        ),
    ),  # Lionelo LEVI ONE i-Size
}

# Campos que NO deben cambiar para ninguno de los 30 productos en esta
# auditoria -- se usan solo para la validacion final, no se tocan aqui.
CAMPOS_PROTEGIDOS = [
    "altura", "grupo", "peso_recomendado", "precio", "valoracion", "n_val",
    "isofix", "giro_360", "orientacion", "arnes", "normativa",
    "tipo_instalacion", "reclinable", "reposacabezas", "proteccion_lateral",
    "funda_lavable", "travel_system",
]


def load(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def save(data, path):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")


def aplicar_edad_updates(productos):
    aplicados = set()
    for p in productos:
        if p["asin"] in EDAD_UPDATES:
            nuevo_valor, nota = EDAD_UPDATES[p["asin"]]
            p["edad"] = nuevo_valor
            p["estado_auditoria"] = p.get("estado_auditoria", "") + " | " + nota
            aplicados.add(p["asin"])
    faltan = set(EDAD_UPDATES) - aplicados
    if faltan:
        raise ValueError(f"ASIN de edad no encontrados: {faltan}")


def diff_datasets(antes, despues):
    antes_por_asin = {p["asin"]: p for p in antes["productos"]}
    despues_por_asin = {p["asin"]: p for p in despues["productos"]}
    assert set(antes_por_asin) == set(despues_por_asin), "Se han añadido/quitado productos -- no permitido"

    celdas = []
    for asin in sorted(antes_por_asin):
        a, d = antes_por_asin[asin], despues_por_asin[asin]
        for campo in sorted(set(a.keys()) | set(d.keys())):
            va, vd = a.get(campo), d.get(campo)
            if va != vd:
                celdas.append({"asin": asin, "modelo": d.get("modelo"), "campo": campo, "antes": va, "despues": vd})
    return {
        "productos_con_cambios": sorted({c["asin"] for c in celdas}),
        "atributos_afectados": sorted({c["campo"] for c in celdas}),
        "num_celdas_modificadas": len(celdas),
        "celdas": celdas,
    }


def validar_solo_edad_y_estado(diff):
    permitido = {"edad", "estado_auditoria"}
    extra = set(diff["atributos_afectados"]) - permitido
    if extra:
        raise ValueError(f"Se han modificado atributos no permitidos: {extra}")
    if set(diff["productos_con_cambios"]) != set(EDAD_UPDATES):
        raise ValueError(
            f"Productos con cambios ({diff['productos_con_cambios']}) no coincide "
            f"con lo esperado ({sorted(EDAD_UPDATES)})"
        )


def main():
    if len(sys.argv) != 3:
        print("Uso: python auditoria3_edad_completar.py <snapshot.json> <dataset.json>", file=sys.stderr)
        sys.exit(1)

    snapshot_path, dataset_path = sys.argv[1], sys.argv[2]
    antes = load(snapshot_path)
    data = load(dataset_path)
    productos = data["productos"]
    assert len(productos) == 30, f"Se esperaban 30 productos, hay {len(productos)}"

    aplicar_edad_updates(productos)

    data["productos"] = productos
    data["_nota"] = data["_nota"] + (
        " [PUNTO 7.3 (16-ago-2026): completadas las 2 edades pendientes -- "
        "Kinderkraft SAFETY FIX 3 PRO (decision manual del usuario) y "
        "Lionelo LEVI ONE i-Size (derivada del patron de altura 76-150cm "
        "ya presente en el dataset). Ningun otro atributo modificado.]"
    )
    save(data, dataset_path)

    diff = diff_datasets(antes, data)
    validar_solo_edad_y_estado(diff)
    diff_path = str(Path(dataset_path).with_name("auditoria3_edad_diff.json"))
    save(diff, diff_path)

    print(json.dumps({
        "num_celdas_modificadas": diff["num_celdas_modificadas"],
        "productos_con_cambios": diff["productos_con_cambios"],
        "atributos_afectados": diff["atributos_afectados"],
        "validacion": "OK: solo edad/estado_auditoria modificados, en exactamente los 2 ASIN esperados",
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
