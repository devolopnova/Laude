"""Inserta en la tabla grande de ambos comparadores las filas de los
productos del dataset que todavia no tienen fila, reutilizando
build_row() del generador original para que el HTML salga identico al
de las filas ya existentes (mismos data-sort-*, misma ficha tecnica,
mismos textos recortados).

Tambien actualiza el contador "<p>N modelos</p>" al numero real de
filas resultante.
"""
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_comparativa_prototipo_v61 as gen

RAIZ = Path(__file__).resolve().parent.parent
DATASET = RAIZ / "tools/output/auditoria_30_candidatos.json"
OBJETIVOS = [
    RAIZ / "comparador-sillas-coche-prototipo-pc.html",
    RAIZ / "comparador-sillas-coche.html",
]


def main():
    productos = json.loads(DATASET.read_text(encoding="utf-8"))["productos"]

    for destino in OBJETIVOS:
        texto = destino.read_text(encoding="utf-8")

        # ASIN ya representados en la tabla (por el enlace de Amazon de
        # cada fila principal).
        ya = set(
            re.findall(
                r'<tr class="main-row".*?btn-amazon-row" href="https://www\.amazon\.es/dp/([A-Z0-9]+)"',
                texto,
                re.S,
            )
        )
        faltan = [p for p in productos if p["asin"] not in ya]
        if not faltan:
            print(f"{destino.name}: sin filas que anadir")
            continue

        # El indice de cada fila (data-orig-index / id del panel) debe
        # continuar la numeracion existente, no reiniciarse.
        indices = [int(i) for i in re.findall(r'data-orig-index="(\d+)"', texto)]
        siguiente = max(indices) + 1 if indices else 0

        filas = []
        for offset, p in enumerate(faltan):
            filas.append(gen.build_row(p, siguiente + offset))
        bloque = "\n".join(filas)

        if "      </tbody>" not in texto:
            print(f"{destino.name}: no encuentro </tbody>, no toco el archivo")
            continue
        texto = texto.replace("      </tbody>", bloque + "\n      </tbody>", 1)

        total_filas = texto.count('class="main-row"')
        texto = re.sub(r"<p>\d+ modelos</p>", f"<p>{total_filas} modelos</p>", texto, count=1)

        destino.write_text(texto, encoding="utf-8")
        print(f"{destino.name}: +{len(faltan)} filas -> {total_filas} en total")
        for p in faltan:
            print(f"   + {p['asin']}  {p['marca']} {p['modelo']}")


if __name__ == "__main__":
    main()
