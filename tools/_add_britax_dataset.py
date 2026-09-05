"""Añade los 7 Britax Römer que faltaban (>40 valoraciones) al dataset
maestro, con DOS correcciones manuales sobre lo que dedujo el extractor:
en ambos casos su emparejado por palabra clave leyo mal el texto.

1. ADVENTURE PLUS 2 (B0BDBX11ZY): el extractor puso ISOFIX = Si porque
   la palabra "ISOFIX" aparece en el bullet, pero la frase dice lo
   contrario -- "al ser facil de instalar con el cinturon de seguridad
   del coche, es una opcion especialmente adecuada para vehiculos que NO
   estan equipados con puntos de anclaje ISOFIX". Confirmado ademas en
   la ficha oficial de Britax Romer, cuya tabla de especificaciones dice
   Instalacion: "CON CINTURON" y "Visto bueno: i-Size (R129) Group 2/3"
   (ese ultimo dato rellena tambien el grupo, que Amazon no daba).

2. KIDFIX PRO M (B0DGY3YPG6): el extractor puso ISOFIX = No porque leyo
   el "sin" de "con y sin ISOFIX" del titulo. Es un falso negativo: esa
   frase significa que se puede usar con o sin ISOFIX. Corroborado por
   dos resenas reales que describen usarlo ("Si sacas el Isofix un poco
   para adelante...", "Totes tres tenen isofix"). Mismo tratamiento que
   KIDFIX 2 Z-LINE, que lleva la misma frase y si se clasifico bien.

El resto de campos salen tal cual del extractor; donde no hay evidencia
se queda "Sin especificar" (nunca se convierte ausencia en "No").
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _add_marca_dataset import construir  # misma logica, sin duplicarla

RAIZ = Path(__file__).resolve().parent.parent
BUSQUEDA = RAIZ / "tools/output/_tmp_britax_busqueda.json"
DATASET = RAIZ / "tools/output/auditoria_30_candidatos.json"
LOOKUP = RAIZ / "tools/fabricante_lookup.json"

MODELOS = {
    "B0C3HJNK2M": "EVOLVAFIX",
    "B0BDBYLMYR": "DISCOVERY PLUS 2",
    "B0BDBX11ZY": "ADVENTURE PLUS 2",
    "B0CL7TWRCS": "KIDFIX 2 Z-LINE",
    "B0BDC9QNXM": "DUALFIX PLUS",
    "B0CL7GK9NZ": "ADVANSAFIX 2 Z-LINE",
    "B0DGY3YPG6": "KIDFIX PRO M",
}

NOTA = "Añadido 31-ago-2026 (ampliación Britax Römer, fuente Amazon)."

CORRECCIONES = {
    "B0BDBX11ZY": {
        "isofix": "No",
        "tipo_instalacion": "Cinturón del vehículo",
        "grupo": "Grupo 2/3",
        "estado_auditoria": (
            "Añadido 31-ago-2026 (ampliación Britax Römer). CORRECCIÓN manual: el "
            "extractor había marcado ISOFIX=Sí por emparejado de palabra clave, pero "
            "el bullet dice que se instala con el cinturón y que es adecuada para "
            "vehículos SIN anclajes ISOFIX. La ficha oficial de Britax Römer lo "
            "confirma (Instalación: \"CON CINTURÓN\") y aporta el grupo "
            "(\"Visto bueno: i-Size (R129) Group 2/3\"), que Amazon no daba."
        ),
    },
    "B0DGY3YPG6": {
        "isofix": "Sí (opcional, también cinturón)",
        "tipo_instalacion": "ISOFIX",
        "estado_auditoria": (
            "Añadido 31-ago-2026 (ampliación Britax Römer). CORRECCIÓN manual: el "
            "extractor había marcado ISOFIX=No por leer el \"sin\" de \"con y sin "
            "ISOFIX\" del título de Amazon; esa frase significa que admite ambas "
            "instalaciones. Corroborado por reseñas reales que describen usar el "
            "ISOFIX de esta silla. Mismo criterio que KIDFIX 2 Z-LINE. La ficha "
            "oficial no pudo consultarse (su bloque de especificaciones no carga)."
        ),
    },
}


def main():
    busqueda = json.loads(BUSQUEDA.read_text(encoding="utf-8"))
    por_asin = {p["asin"]: p for p in busqueda["productos"]}
    datos = json.loads(DATASET.read_text(encoding="utf-8"))
    existentes = {p["asin"] for p in datos["productos"]}

    nuevos = []
    for asin, modelo in MODELOS.items():
        if asin in existentes:
            print(f"[SKIP] {asin} ya estaba")
            continue
        entrada = construir(por_asin[asin], "Britax Römer", modelo, NOTA)
        entrada.update(CORRECCIONES.get(asin, {}))
        nuevos.append(entrada)

    datos["productos"].extend(nuevos)
    DATASET.write_text(json.dumps(datos, ensure_ascii=False, indent=2), encoding="utf-8")

    # Entrada de fabricante para ADVENTURE PLUS 2 (identidad verificada por
    # 3 senales: mismo nombre de modelo, mismo rango 100-150 cm y mismo
    # peso de producto 5,2 kg en Amazon y en la ficha oficial).
    lookup = json.loads(LOOKUP.read_text(encoding="utf-8"))
    lookup["B0BDBX11ZY"] = {
        "marca_fabricante": "Britax Römer",
        "modelo_fabricante": "ADVENTURE PLUS 2",
        "url_fabricante": "https://www.britax-romer.es/sillas-de-coche/nino/adventure-plus-2/1171.html",
        "nombre_amazon": "BRITAX RÖMER Silla de coche ADVENTURE PLUS 2",
        "nombre_fabricante": "ADVENTURE PLUS 2",
        "identidad_verificada": True,
        "aviso_nombre_diferente": False,
        "motivo_equivalencia": (
            "Mismo nombre de modelo, mismo rango 100-150 cm y mismo peso de producto "
            "(5,2 kg) en la ficha de Amazon y en la oficial."
        ),
        "hallazgos": {
            "tipo_instalacion": {
                "valor": "cinturon_seguridad",
                "texto_fuente": "Instalación — CON CINTURÓN (tabla de especificaciones de la ficha oficial).",
            },
            "isofix": {
                "valor": False,
                "texto_fuente": "Al ser fácil de instalar con el cinturón de seguridad del coche, es una opción especialmente adecuada para vehículos que no están equipados con puntos de anclaje ISOFIX.",
            },
            "grupo_r44": {
                "valor": "2/3",
                "texto_fuente": "Visto bueno: i-Size (R129) Group 2/3",
            },
        },
        "fecha_consulta": "2026-08-31",
    }
    LOOKUP.write_text(json.dumps(lookup, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"\nDataset: {len(existentes)} -> {len(datos['productos'])}")
    for n in nuevos:
        print(f"  + {n['asin']}  {n['modelo']:20} {n['valoracion']} / {n['n_val']:4} val | isofix: {n['isofix']}")


if __name__ == "__main__":
    main()
