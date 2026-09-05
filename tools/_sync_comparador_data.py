"""Sincroniza js/sillas-comparador-data.js con el dataset maestro:
añade los productos que falten, reutilizando los MISMOS helpers del
generador original para que su HTML salga con el formato idéntico al de
los que ya estaban.

Sustituye a tools/_add_missing_mobile_products.py, que escribia el array
inline dentro de los HTML. Desde el refactor (31-ago-2026) los datos
viven SOLO en js/sillas-comparador-data.js, compartido por
comparador-sillas-coche.html y comparar-sillas.html.

Añade tambien el parametro de afiliado a los enlaces de Amazon de los
productos nuevos (?tag=laude09-21), igual que los que ya estaban.
"""
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_comparativa_prototipo_v61 as gen

RAIZ = Path(__file__).resolve().parent.parent
DATASET = RAIZ / "tools/output/auditoria_30_candidatos.json"
DATA_JS = RAIZ / "js/sillas-comparador-data.js"
TAG = "?tag=laude09-21"


def con_tag(html):
    """Añade ?tag=laude09-21 a los enlaces de Amazon que no lo lleven."""
    return re.sub(
        r'(https://www\.amazon\.es/dp/[A-Z0-9]+)(?!\?tag=)',
        lambda m: m.group(1) + TAG,
        html,
    )


def main():
    productos = json.loads(DATASET.read_text(encoding="utf-8"))["productos"]
    texto = DATA_JS.read_text(encoding="utf-8")

    m = re.search(r"const MOBILE_PRODUCTS = (\[.*?\]);", texto, re.S)
    actual = json.loads(m.group(1))
    ya = {p["asin"] for p in actual}

    faltan = [p for p in productos if p["asin"] not in ya]
    if not faltan:
        print(f"sin cambios (ya estan los {len(actual)})")
        return

    nuevos = []
    for p in faltan:
        payload = gen.build_mobile_product_payload(p)
        for campo in ("vsSlotHtml", "summaryHtml", "resultCardHtml"):
            payload[campo] = con_tag(payload[campo])
        nuevos.append(payload)

    completo = actual + nuevos
    texto = texto.replace(
        m.group(0),
        "const MOBILE_PRODUCTS = " + json.dumps(completo, ensure_ascii=False) + ";",
        1,
    )
    DATA_JS.write_text(texto, encoding="utf-8")

    sin_tag = sum(
        1 for p in completo for c in ("vsSlotHtml",) if "amazon.es/dp/" in p[c] and TAG not in p[c]
    )
    print(f"js/sillas-comparador-data.js: {len(actual)} -> {len(completo)}  | sin tag de afiliado: {sin_tag}")
    for p in faltan:
        print(f"   + {p['asin']}  {p['marca']} {p['modelo']}")


if __name__ == "__main__":
    main()
