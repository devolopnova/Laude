"""Añade al dataset maestro un conjunto de productos ya extraidos,
tomando los valores de la capa `clasificacion` + `caracteristicas` del
extractor. NADA se infiere: donde no hay evidencia textual se escribe
"Sin especificar" (regla de CLAUDE.md y
feedback_sillas_coche_criterio_editorial), y una contradiccion marcada
por el extractor se traduce a "Revisar", nunca se resuelve sola.

Uso:
    python tools/_add_marca_dataset.py <json_busqueda> <modelos.json> <nota_auditoria>

<modelos.json> es un {ASIN: "nombre corto editorial"} -- el titulo de
Amazon nunca se usa tal cual.
"""
import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
DATASET = RAIZ / "tools/output/auditoria_30_candidatos.json"
SIN = "Sin especificar"


def limpio(valor):
    if valor in (None, "", "N/A", "No determinado", "No confirmado", "Sin especificar"):
        return SIN
    return valor


def mostrar(clasificacion, campo):
    bloque = (clasificacion or {}).get(campo) or {}
    if bloque.get("revisar"):
        return "Revisar"
    return limpio(bloque.get("mostrar"))


def construir(p, marca, modelo, nota):
    c = p.get("caracteristicas") or {}
    cl = p.get("clasificacion") or {}
    val = p.get("valoraciones") or {}

    # Si algun campo se apoyo en la ficha oficial del fabricante, se deja
    # constancia en estado_auditoria (nunca se presenta como "inferido").
    fuentes = {
        campo: (cl.get(campo) or {}).get("fuente")
        for campo in ("isofix", "tipo_instalacion", "normativa", "grupo_r44", "edad")
    }
    con_fabricante = sorted(k for k, v in fuentes.items() if v and "fabricante" in str(v))
    detalle = nota
    if con_fabricante:
        detalle += f" Campos confirmados con la ficha oficial del fabricante: {', '.join(con_fabricante)}."

    return {
        "asin": p["asin"],
        "marca": marca,
        "modelo": modelo,
        "actual_lote1": False,
        "precio": (p.get("precio") or {}).get("actual"),
        "valoracion": val.get("puntuacion"),
        "n_val": val.get("numero"),
        "grupo": mostrar(cl, "grupo_r44"),
        "edad": mostrar(cl, "edad"),
        "altura": mostrar(cl, "altura_r129"),
        "peso_recomendado": mostrar(cl, "peso"),
        "isofix": mostrar(cl, "isofix"),
        "tipo_instalacion": mostrar(cl, "tipo_instalacion"),
        "orientacion": limpio(c.get("orientacion")),
        "reclinable": limpio(c.get("reclinable")),
        "giro_360": limpio(c.get("giro_360")),
        "normativa": mostrar(cl, "normativa"),
        "reposacabezas": limpio(c.get("reposacabezas_regulable")),
        "arnes": limpio(c.get("tipo_arnes_proteccion")),
        "peso_silla": limpio(c.get("peso_silla")),
        "proteccion_lateral": limpio(c.get("proteccion_lateral")),
        "funda_lavable": limpio(c.get("funda_lavable")),
        "travel_system": limpio(c.get("travel_system")),
        "estado_auditoria": detalle,
    }


def main():
    if len(sys.argv) != 4:
        print(__doc__)
        sys.exit(1)
    busqueda = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    modelos = json.loads(Path(sys.argv[2]).read_text(encoding="utf-8"))
    nota = sys.argv[3]

    por_asin = {p["asin"]: p for p in busqueda["productos"]}
    datos = json.loads(DATASET.read_text(encoding="utf-8"))
    existentes = {p["asin"] for p in datos["productos"]}

    nuevos = []
    for asin, modelo in modelos.items():
        if asin in existentes:
            print(f"[SKIP] {asin} ya estaba")
            continue
        p = por_asin[asin]
        nuevos.append(construir(p, p.get("marca"), modelo, nota))

    datos["productos"].extend(nuevos)
    DATASET.write_text(json.dumps(datos, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"Dataset: {len(existentes)} -> {len(datos['productos'])}")
    for n in nuevos:
        print(f"  + {n['asin']}  {n['modelo']:22} {n['valoracion']} / {n['n_val']} val  | isofix: {n['isofix']}")


if __name__ == "__main__":
    main()
