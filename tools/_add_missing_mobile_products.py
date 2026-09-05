"""Añade al array MOBILE_PRODUCTS los productos del dataset maestro que
falten, reutilizando los MISMOS helpers del generador original
(build_comparativa_prototipo_v61.py) para que el HTML de cada producto
salga byte a byte con el mismo formato que los que ya estaban.

Motivo (30-ago-2026): la tabla grande se amplió a mano con 6 productos
(2 Cybex + 4 Chicco) que nunca entraron en MOBILE_PRODUCTS, así que el
buscador/selector de 2 sillitas solo ofrecía 33 de los 39 del dataset.

No recalcula ni reinterpreta ningún dato: cada payload se construye con
build_mobile_product_payload() a partir del producto tal cual está en
tools/output/auditoria_30_candidatos.json.
"""
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_comparativa_prototipo_v61 as gen

RAIZ = Path(__file__).resolve().parent.parent
SRC = RAIZ / "tools/output/auditoria_30_candidatos.json"
OBJETIVOS = [
    RAIZ / "comparador-sillas-coche-prototipo-pc.html",
    RAIZ / "comparador-sillas-coche.html",
]


def main():
    productos = json.loads(SRC.read_text(encoding="utf-8"))["productos"]
    por_asin = {p["asin"]: p for p in productos}

    for destino in OBJETIVOS:
        texto = destino.read_text(encoding="utf-8")
        linea = next(
            l for l in texto.splitlines() if l.startswith("const MOBILE_PRODUCTS")
        )
        actual = json.loads(linea[linea.index("[") : linea.rindex("];") + 1])
        ya = {p["asin"] for p in actual}

        faltan = [p for p in productos if p["asin"] not in ya]
        if not faltan:
            print(f"{destino.name}: sin cambios (ya estan los {len(actual)})")
            continue

        nuevos = [gen.build_mobile_product_payload(p) for p in faltan]
        completo = actual + nuevos
        linea_nueva = "const MOBILE_PRODUCTS = " + json.dumps(
            completo, ensure_ascii=False
        ) + ";"
        texto = texto.replace(linea, linea_nueva, 1)
        destino.write_text(texto, encoding="utf-8")

        print(f"{destino.name}: {len(actual)} -> {len(completo)}")
        for p in faltan:
            print(f"   + {p['asin']}  {p.get('marca')} {p.get('modelo')}")


if __name__ == "__main__":
    main()
