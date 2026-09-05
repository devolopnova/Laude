#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""DIAGNOSTICO (no toca amazon_import.py). Prueba controlada: en UNA sola
sesion (browser/context/page reutilizados, con stealth activo, igual que el
script real) navega de forma "humana" -> portada -> espera 30s -> categoria
-> ficha de producto, y documenta en que paso exacto aparece el muro
'Seguir comprando'."""
import time
import sys
from playwright.sync_api import sync_playwright
from playwright_stealth import Stealth

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")

WALL_MARKER = "seguir comprando"

def check_wall(page, step_name):
    title = page.title()
    body = page.inner_text("body")[:300].replace("\n", " ")
    is_wall = WALL_MARKER in body.lower()
    status = "MURO 'SEGUIR COMPRANDO'" if is_wall else "OK (contenido normal)"
    print(f"\n=== PASO: {step_name} ===")
    print(f"  URL actual: {page.url}")
    print(f"  TITLE: {title}")
    print(f"  RESULTADO: {status}")
    print(f"  BODY (primeros 300 chars): {body}")
    return is_wall

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context(user_agent=UA, locale="es-ES", viewport={"width": 1920, "height": 1080})
    Stealth(navigator_languages_override=("es-ES", "es")).apply_stealth_sync(context)
    page = context.new_page()
    print(f"navigator.webdriver = {page.evaluate('navigator.webdriver')}")

    # PASO 1: portada de Amazon
    page.goto("https://www.amazon.es", wait_until="networkidle", timeout=60000)
    wall1 = check_wall(page, "1. Portada de Amazon (www.amazon.es)")
    if wall1:
        print("\n>>> El muro aparece YA en la portada, antes de tocar ningun producto.")
        browser.close()
        sys.exit(0)

    # PASO 2: esperar 30s
    print("\n=== PASO: 2. Esperando 30 segundos... ===")
    time.sleep(30)

    # PASO 3: navegar a una categoria cualquiera (Juguetes y juegos)
    page.goto("https://www.amazon.es/gp/browse.html?node=599372031", wait_until="networkidle", timeout=60000)
    wall3 = check_wall(page, "3. Categoria (Juguetes y juegos)")
    if wall3:
        print("\n>>> El muro aparece al navegar a una CATEGORIA, antes de abrir ninguna ficha de producto.")
        browser.close()
        sys.exit(0)

    # PASO 4: abrir una ficha de producto real
    page.goto("https://www.amazon.es/dp/B0C53DM9Y2", wait_until="networkidle", timeout=60000)
    wall4 = check_wall(page, "4. Ficha de producto (dp/B0C53DM9Y2)")
    if wall4:
        print("\n>>> El muro aparece al abrir la FICHA DE PRODUCTO, no antes.")
    else:
        print("\n>>> Ningun paso mostro el muro. Sesion completa sin bloqueo.")

    browser.close()
