"""Añade al dataset maestro los 8 Maxi-Cosi seleccionados (los mas
representativos de los 15 que faltaban con >50 valoraciones, uno por
familia de la gama).

Los valores salen de tools/output/_tmp_maxicosi_busqueda.json (capa
`clasificacion` + `caracteristicas` del extractor). NADA se infiere:
donde no hay evidencia textual se escribe "Sin especificar", segun la
regla de CLAUDE.md y feedback_sillas_coche_criterio_editorial.

Unica excepcion documentada: Nomad Plus, cuyos campos de instalacion no
los confirmaba Amazon y se resolvieron leyendo la ficha OFICIAL de
Maxi-Cosi (contenido visible del cuerpo, nunca <title>/meta), ver
NOMAD_FABRICANTE mas abajo. Su normativa NO aparece en ningun punto del
texto visible de esa ficha, asi que se queda en "Sin especificar".
"""
import json
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
BUSQUEDA = RAIZ / "tools/output/_tmp_maxicosi_busqueda.json"
DATASET = RAIZ / "tools/output/auditoria_30_candidatos.json"
LOOKUP = RAIZ / "tools/fabricante_lookup.json"

SELECCION = [
    "B07RP2XR8J",  # Kore i-Size
    "B0CKZC1WZG",  # RodiFix M i-Size
    "B09LVM4ZF5",  # CabrioFix i-Size
    "B0CHYBHS31",  # Nomad Plus
    "B0CZ12Q54X",  # Titan S i-Size
    "B09BDJ6G8B",  # Pebble 360
    "B0BXY35J5N",  # Mica Pro Eco i-Size
    "B0DJBR1TYR",  # Mica 360 S
]

# Nombre corto editorial (el titulo de Amazon nunca se usa tal cual).
MODELOS = {
    "B07RP2XR8J": "Kore i-Size",
    "B0CKZC1WZG": "RodiFix M i-Size",
    "B09LVM4ZF5": "CabrioFix i-Size",
    "B0CHYBHS31": "Nomad Plus",
    "B0CZ12Q54X": "Titan S i-Size",
    "B09BDJ6G8B": "Pebble 360",
    "B0BXY35J5N": "Mica Pro Eco i-Size",
    "B0DJBR1TYR": "Mica 360 S",
}

SIN = "Sin especificar"

# Datos que Amazon NO confirmaba y si confirma la ficha oficial de
# Maxi-Cosi (https://www.maxi-cosi.es/sillas-de-coche/nomad-plus),
# leidos del cuerpo visible de la pagina el 31-ago-2026.
NOMAD_FABRICANTE = {
    "isofix": "No (fabricante: se instala con el cinturón de seguridad)",
    "tipo_instalacion": "Cinturón del vehículo",
    "arnes": "Arnés de 5 puntos (confirmado por fabricante)",
    "reposacabezas": "Sí",
    # La ficha oficial no menciona R129/i-Size/R44 en ningun punto de su
    # texto visible -> no se rellena por inferencia.
    "normativa": SIN,
}


def limpio(valor):
    if valor in (None, "", "N/A", "No determinado", "No confirmado", "Sin especificar"):
        return SIN
    return valor


def mostrar(clasificacion, campo):
    bloque = (clasificacion or {}).get(campo) or {}
    if bloque.get("revisar"):
        return "Revisar"
    return limpio(bloque.get("mostrar"))


def construir(p):
    asin = p["asin"]
    c = p.get("caracteristicas") or {}
    cl = p.get("clasificacion") or {}
    val = p.get("valoraciones") or {}
    precio = (p.get("precio") or {}).get("actual")

    entrada = {
        "asin": asin,
        "marca": "Maxi-Cosi",
        "modelo": MODELOS[asin],
        "actual_lote1": False,
        "precio": precio,
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
        "estado_auditoria": "Añadido 31-ago-2026 (ampliación Maxi-Cosi, fuente Amazon)",
    }

    if asin == "B0CHYBHS31":
        entrada.update(NOMAD_FABRICANTE)
        entrada["estado_auditoria"] = (
            "Añadido 31-ago-2026 (ampliación Maxi-Cosi). Instalación, arnés y "
            "reposacabezas confirmados en la ficha oficial de Maxi-Cosi "
            "(cuerpo visible, no metadatos); su normativa no aparece en esa "
            "ficha ni en Amazon, queda Sin especificar."
        )

    return entrada


def main():
    productos_busqueda = {
        p["asin"]: p for p in json.loads(BUSQUEDA.read_text(encoding="utf-8"))["productos"]
    }
    datos = json.loads(DATASET.read_text(encoding="utf-8"))
    existentes = {p["asin"] for p in datos["productos"]}

    nuevos = []
    for asin in SELECCION:
        if asin in existentes:
            print(f"[SKIP] {asin} ya estaba")
            continue
        nuevos.append(construir(productos_busqueda[asin]))

    datos["productos"].extend(nuevos)
    DATASET.write_text(json.dumps(datos, ensure_ascii=False, indent=2), encoding="utf-8")

    # Entrada de fabricante para Nomad Plus (identidad verificada por 3
    # senales independientes: mismo nombre de modelo, mismo rango de
    # altura 76-105 cm y mismo rango de edad 15 meses-4 anos).
    lookup = json.loads(LOOKUP.read_text(encoding="utf-8"))
    lookup["B0CHYBHS31"] = {
        "marca_fabricante": "Maxi-Cosi",
        "modelo_fabricante": "Nomad Plus",
        "url_fabricante": "https://www.maxi-cosi.es/sillas-de-coche/nomad-plus",
        "nombre_amazon": "Maxi-Cosi Nomad Plus",
        "nombre_fabricante": "Maxi-Cosi Nomad Plus",
        "identidad_verificada": True,
        "aviso_nombre_diferente": False,
        "motivo_equivalencia": (
            "Mismo nombre de modelo en Amazon y fabricante, mismo rango de altura "
            "(76-105 cm) y misma edad (15 meses - 4 años) en ambas fichas."
        ),
        "hallazgos": {
            "tipo_instalacion": {
                "valor": "cinturon_seguridad",
                "texto_fuente": "Nomad Plus de Maxi-Cosi se adapta a cualquier coche porque se instala con el cinturón de seguridad.",
            },
            "arnes": {
                "valor": "5 puntos",
                "texto_fuente": "Un arnés de seguridad de 5 puntos asegura que tu pequeño siempre esté sentado de forma segura.",
            },
            "reposacabezas": {
                "valor": "Sí",
                "texto_fuente": "Nomad Plus de Maxi-Cosi tiene un reposacabezas que se extiende hacia arriba.",
            },
            "normativa": {
                "valor": None,
                "texto_fuente": "No se menciona R129/i-Size ni R44 en ningún punto del texto visible de la ficha oficial.",
            },
        },
        "fecha_consulta": "2026-08-31",
    }
    LOOKUP.write_text(json.dumps(lookup, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"\nDataset: {len(existentes)} -> {len(datos['productos'])}")
    for n in nuevos:
        print(f"  + {n['asin']}  {n['modelo']:22} {n['valoracion']} / {n['n_val']} val")


if __name__ == "__main__":
    main()
