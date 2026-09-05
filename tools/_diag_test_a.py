#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""PRUEBA A: nueva sesion (browser nuevo) por cada intento, acceso DIRECTO
a una URL /dp/ sin calentar la sesion. 5 productos distintos."""
import time
import json
from playwright.sync_api import sync_playwright
from playwright_stealth import Stealth

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")
WALL_MARKER = "seguir comprando"

PRODUCTS = ["B0GWHNJ8Y3", "B0F7X6ML9X", "B0F7XCZGH6", "B0CCV62QZ7", "B0F1F9T8WH"]

def is_wall(page):
    body = page.inner_text("body")[:300].lower()
    return WALL_MARKER in body

results = []
for i, asin in enumerate(PRODUCTS, 1):
    t0 = time.time()
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(user_agent=UA, locale="es-ES", viewport={"width": 1920, "height": 1080})
        Stealth(navigator_languages_override=("es-ES", "es")).apply_stealth_sync(context)
        page = context.new_page()
        try:
            page.goto(f"https://www.amazon.es/dp/{asin}", wait_until="networkidle", timeout=60000)
            elapsed = time.time() - t0
            blocked = is_wall(page)
        except Exception as e:
            elapsed = time.time() - t0
            blocked = f"ERROR: {e}"
        finally:
            browser.close()
    result = {"sesion": i, "metodo": "A (directo)", "producto": asin, "bloqueado": blocked, "tiempo_s": round(elapsed, 2)}
    results.append(result)
    print(f"[A-{i}] ASIN={asin} bloqueado={blocked} tiempo={elapsed:.2f}s")
    time.sleep(3)

with open("_diag_results_a.json", "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=2)
print("\nGuardado en _diag_results_a.json")
