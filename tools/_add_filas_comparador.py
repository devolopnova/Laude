"""Añade a la tabla de comparador-sillas-coche.html las filas de los
productos del dataset que aun no tengan, reutilizando build_row() del
generador original, y actualiza el contador "<p>N modelos</p>".

Reemplaza a tools/_add_maxicosi_rows.py, que tambien escribia en
comparador-sillas-coche-prototipo-pc.html; ese prototipo quedo abandonado
(excluido del sitemap y sin enlazar), asi que ya NO se toca.

Los enlaces de Amazon de las filas nuevas se generan con el parametro de
afiliado ?tag=laude09-21, igual que los que ya estaban.
"""
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_comparativa_prototipo_v61 as gen

RAIZ = Path(__file__).resolve().parent.parent
DATASET = RAIZ / "tools/output/auditoria_30_candidatos.json"
DESTINO = RAIZ / "comparador-sillas-coche.html"
TAG = "?tag=laude09-21"


def con_tag(html):
    return re.sub(
        r'(https://www\.amazon\.es/dp/[A-Z0-9]+)(?!\?tag=)',
        lambda m: m.group(1) + TAG,
        html,
    )


def main():
    productos = json.loads(DATASET.read_text(encoding="utf-8"))["productos"]
    texto = DESTINO.read_text(encoding="utf-8")

    ya = set(
        re.findall(
            r'<tr class="main-row".*?btn-amazon-row" href="https://www\.amazon\.es/dp/([A-Z0-9]+)',
            texto,
            re.S,
        )
    )
    faltan = [p for p in productos if p["asin"] not in ya]
    if not faltan:
        print("sin filas que anadir")
        return

    indices = [int(i) for i in re.findall(r'data-orig-index="(\d+)"', texto)]
    siguiente = max(indices) + 1 if indices else 0

    filas = [con_tag(gen.build_row(p, siguiente + i)) for i, p in enumerate(faltan)]
    bloque = "\n".join(filas)

    if "      </tbody>" not in texto:
        print("no encuentro </tbody>, no toco el archivo")
        return
    texto = texto.replace("      </tbody>", bloque + "\n      </tbody>", 1)

    total = texto.count('class="main-row"')
    texto = re.sub(r"<p>\d+ modelos</p>", f"<p>{total} modelos</p>", texto, count=1)
    DESTINO.write_text(texto, encoding="utf-8")

    sin_tag = len(re.findall(r'amazon\.es/dp/[A-Z0-9]+"', texto))
    print(f"{DESTINO.name}: +{len(faltan)} filas -> {total} | enlaces sin tag: {sin_tag}")
    for p in faltan:
        print(f"   + {p['asin']}  {p['marca']} {p['modelo']}")


if __name__ == "__main__":
    main()
