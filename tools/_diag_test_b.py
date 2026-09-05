#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""PRUEBA B: nueva sesion (browser nuevo) por cada intento, con calentamiento:
portada -> espera 15-30s -> categoria -> espera 10-20s -> mismo producto."""
import time
import json
import random
from playwright.sync_api import sync_playwright
from playwright_stealth import Stealth

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")
WALL_MARKER = "seguir comprando"
PRODUCT = "B0CKQWZ59X"
CATEGORY_URL = "https://www.amazon.es/gp/browse.html?node=599372031"

def is_wall(page):
    body = page.inner_text("body")[:300].lower()
    return WALL_MARKER in body

results = []
for i in range(1, 6):
    t0 = time.time()
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(user_agent=UA, locale="es-ES", viewport={"width": 1920, "height": 1080})
        Stealth(navigator_languages_override=("es-ES", "es")).apply_stealth_sync(context)
        page = context.new_page()
        try:
            page.goto("https://www.amazon.es", wait_until="networkidle", timeout=60000)
            wait1 = random.uniform(15, 30)
            time.sleep(wait1)
            page.goto(CATEGORY_URL, wait_until="networkidle", timeout=60000)
            wait2 = random.uniform(10, 20)
            time.sleep(wait2)
            page.goto(f"https://www.amazon.es/dp/{PRODUCT}", wait_until="networkidle", timeout=60000)
            elapsed = time.time() - t0
            blocked = is_wall(page)
        except Exception as e:
            elapsed = time.time() - t0
            blocked = f"ERROR: {e}"
            wait1 = wait2 = 0
        finally:
            browser.close()
    result = {
        "sesion": i, "metodo": "B (calentado)", "producto": PRODUCT,
        "bloqueado": blocked, "tiempo_s": round(elapsed, 2),
        "espera1_s": round(wait1, 1), "espera2_s": round(wait2, 1),
    }
    results.append(result)
    print(f"[B-{i}] ASIN={PRODUCT} espera1={wait1:.1f}s espera2={wait2:.1f}s bloqueado={blocked} tiempo_total={elapsed:.2f}s")

with open("_diag_results_b.json", "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=2)
print("\nGuardado en _diag_results_b.json")
