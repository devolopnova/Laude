#!/usr/bin/env python3
"""
audit_sillas_na.py

Auditoria de solo lectura: revisita las fichas de un lote ya extraido con
amazon_sillas_coche.py y guarda el texto crudo (titulo, bullets,
descripcion, tabla de detalles) que el extractor tiene disponible para
normalizar atributos. No se persiste ese texto crudo en el JSON final del
lote, asi que hace falta volver a visitar Amazon para poder citar el texto
exacto de cada caso de FALSO N/A vs N/A REAL.

Reutiliza (import, sin copiar ni modificar) las funciones ya existentes de
amazon_sillas_coche.py: no altera ese archivo ni amazon_import.py.

Uso:
    python tools/audit_sillas_na.py <final.json> <salida.json>
"""

import json
import random
import sys
import time

sys.path.insert(0, "tools")
from amazon_sillas_coche import (  # noqa: E402
    USER_AGENT, warmup_session, get_product_title, extract_bullets,
    get_description, extract_table_rows, extract_detail_bullets, _log,
)


def main() -> None:
    if len(sys.argv) != 3:
        print("uso: python tools/audit_sillas_na.py <final.json> <salida.json>", file=sys.stderr)
        sys.exit(2)

    final_path, out_path = sys.argv[1:3]
    with open(final_path, encoding="utf-8") as f:
        data = json.load(f)

    from playwright.sync_api import sync_playwright
    from playwright_stealth import Stealth

    results = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(user_agent=USER_AGENT, locale="es-ES", viewport={"width": 1920, "height": 1080})
        Stealth(navigator_languages_override=("es-ES", "es")).apply_stealth_sync(context)
        page = context.new_page()
        warmup_session(page)

        for prod in data["productos"]:
            asin, url = prod["asin"], prod["url"]
            try:
                page.goto(url, wait_until="domcontentloaded", timeout=45000)
                page.wait_for_selector("#productTitle", timeout=20000)
            except Exception as e:
                _log(f"[WARN] fallo cargando {asin}: {e}")
                results.append({"asin": asin, "error": str(e)})
                continue

            title = get_product_title(page)
            bullets = extract_bullets(page)
            description = get_description(page)
            detail_rows = extract_table_rows(page, "#productDetails_techSpec_section_1") \
                + extract_table_rows(page, "#productOverview_feature_div") \
                + extract_detail_bullets(page)

            results.append({
                "asin": asin, "titulo": title, "bullets": bullets,
                "descripcion": description, "detalle": detail_rows,
            })
            _log(f"[INFO] {asin} OK ({len(bullets)} bullets, {len(detail_rows)} filas detalle)")
            time.sleep(random.uniform(2.0, 4.0))

        browser.close()

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"OK: {len(results)} productos -> {out_path}")


if __name__ == "__main__":
    main()
