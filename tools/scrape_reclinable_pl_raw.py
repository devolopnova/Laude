#!/usr/bin/env python3
"""
scrape_reclinable_pl_raw.py

Script AUXILIAR de solo lectura para la segunda auditoria exhaustiva de
RECLINABLE y PROTECCION_LATERAL sobre el dataset definitivo de sillitas de
coche. Reutiliza (importa) las funciones de scraping de
`amazon_sillas_coche.py` -- no la modifica ni duplica su logica -- para
descargar el texto crudo (titulo, bullets, descripcion, filas de detalle,
resenas) de una lista fija de ASIN y volcarlo a JSON. La clasificacion
editorial (Si/No/Revisar/Sin especificar) la hace Claude Code a mano
leyendo este JSON, no este script.

Uso:
    python tools/scrape_reclinable_pl_raw.py
"""

import importlib.util
import json
import random
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
spec = importlib.util.spec_from_file_location("amazon_sillas_coche", Path(__file__).parent / "amazon_sillas_coche.py")
asc = importlib.util.module_from_spec(spec)
spec.loader.exec_module(asc)

ASINS = [
    ("B0F1R26D8L", "Kinderkraft I-BOOST 2"),
    ("B0CZ47FKZL", "Maxi-Cosi Tanza"),
    ("B0GGZYY3BZ", "Bebe Confort Marvel RoadSafe"),
    ("B0CP2QYQK8", "Britax Romer BABY-SAFE CORE"),
    ("B0C6KXB9LL", "Chicco Kory i-Size Essential"),
    ("B0DW9GD5CG", "Chicco Quasar Fix i-Size"),
    ("B0CYQD2H66", "Graco Junior Maxi i-Size"),
    ("B0CHS67WJ3", "Lionelo HUGO i-Size"),
    ("B0D5QSYXPH", "Lionelo LEVI ONE i-Size"),
    ("B0DYDY6C5Y", "KikkaBoo i-PASS"),
    ("B0FLDLZTHJ", "Nania Belem"),
    ("B0FLDT4541", "Nania Bogota"),
    ("B0DPHRJ1YH", "Cybex Pallas G i-Size (G2)"),
    ("B07QLSYS2Y", "Britax Romer DUALFIX2 R"),
    ("B0C6KZCY6Z", "Chicco Unico EVO I'Size Classic"),
    ("B09FQ3PYZX", "Jovikids Alzador Coche Grupo 2/3"),
    ("B07RYWKS9Z", "Babify Onboard"),
]

OUT_PATH = Path(__file__).parent / "output" / "raw_reclinable_pl.json"


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    asc.ensure_playwright_installed()
    asc.ensure_playwright_stealth_installed()
    from playwright.sync_api import sync_playwright
    from playwright_stealth import Stealth

    resultados = {}

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent=asc.USER_AGENT,
            locale="es-ES",
            viewport={"width": 1920, "height": 1080},
        )
        stealth = Stealth(navigator_languages_override=("es-ES", "es"))
        stealth.apply_stealth_sync(context)
        page = context.new_page()

        asc.warmup_session(page)

        for asin, nombre in ASINS:
            url = f"https://www.amazon.es/dp/{asin}"
            time.sleep(random.uniform(2.0, 4.0))
            raw = asc.scrape_product_detail(page, url)
            if raw is None:
                print(f"[FALLO] {asin} {nombre}")
                resultados[asin] = {"nombre": nombre, "error": "no se pudo cargar la ficha"}
                continue
            resultados[asin] = {
                "nombre": nombre,
                "title": raw["title"],
                "bullets": raw["bullets"],
                "description": raw["description"],
                "detail_rows": raw["detail_rows"],
                "reviews_muestra": raw["reviews"],
            }
            print(f"[OK] {asin} {nombre}")

        browser.close()

    OUT_PATH.parent.mkdir(exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(resultados, f, ensure_ascii=False, indent=2)
    print(f"Guardado en {OUT_PATH}")


if __name__ == "__main__":
    main()
