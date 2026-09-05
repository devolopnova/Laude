#!/usr/bin/env python3
"""Script temporal, NO forma parte del pipeline permanente. Descarga
resenas reales de Amazon para un ASIN dado, reutilizando
tools/amazon_sillas_coche.py (scrape_product_detail). Uso:
    python tools/_fetch_reviews.py <ASIN> <archivo_salida.txt>
"""
import sys
import importlib.util

spec = importlib.util.spec_from_file_location("amazon_sillas_coche", "tools/amazon_sillas_coche.py")
asc = importlib.util.module_from_spec(spec)
spec.loader.exec_module(asc)

from playwright.sync_api import sync_playwright
from playwright_stealth import Stealth

asin = sys.argv[1]
out_path = sys.argv[2]

asc.ensure_playwright_installed()
asc.ensure_playwright_stealth_installed()

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context(user_agent=asc.USER_AGENT, viewport={"width": 1280, "height": 900}, locale="es-ES")
    Stealth().apply_stealth_sync(context)
    page = context.new_page()
    try:
        asc.warmup_session(page)
    except Exception as e:
        print("warmup fallo:", e)
    raw = asc.scrape_product_detail(page, f"https://www.amazon.es/dp/{asin}")
    reviews = (raw.get("reviews") or []) if raw else []
    print(len(reviews), "resenas")
    with open(out_path, "w", encoding="utf-8") as f:
        for r in reviews:
            f.write(r + "\n\n")
    browser.close()
