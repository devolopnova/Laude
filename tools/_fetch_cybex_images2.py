#!/usr/bin/env python3
"""Script temporal, NO forma parte del pipeline permanente. Descarga y
procesa (WebP 600x600) la imagen principal de los 2 ASIN Cybex nuevos
aprobados por el usuario (Solution G2, CBX Solution B i-Fix).
Uso: python tools/_fetch_cybex_images2.py
"""
import importlib.util
import json

spec = importlib.util.spec_from_file_location("asc", "tools/amazon_sillas_coche.py")
asc = importlib.util.module_from_spec(spec)
spec.loader.exec_module(asc)

from playwright.sync_api import sync_playwright
from playwright_stealth import Stealth

TARGETS = {
    "B0DJMCGDP8": "cybex-solution-g2",
    "B0C69TG122": "cbx-cybex-solution-b-ifix",
}

asc.ensure_playwright_installed()
asc.ensure_playwright_stealth_installed()

results = {}
with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context(user_agent=asc.USER_AGENT, viewport={"width": 1280, "height": 900}, locale="es-ES")
    Stealth().apply_stealth_sync(context)
    page = context.new_page()
    try:
        asc.warmup_session(page)
    except Exception as e:
        print("warmup fallo:", e)

    for asin, slug in TARGETS.items():
        url = f"https://www.amazon.es/dp/{asin}"
        raw = asc.scrape_product_detail(page, url)
        if not raw or not raw.get("image_url"):
            print(asin, "SIN image_url, raw:", bool(raw))
            results[asin] = {"ok": False}
            continue
        final_path = asc.download_and_process_image(raw["image_url"], asin, slug)
        print(asin, "->", final_path)
        results[asin] = {"ok": bool(final_path), "path": final_path}

    browser.close()

with open("tools/output/_tmp_cybex2_images_result.json", "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=1)
print("done")
