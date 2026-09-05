#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""DIAGNOSTICO fase 3: cuenta TODAS las subpeticiones que dispara una sola
carga de pagina de producto con Playwright en modo 'networkidle' (el mismo
metodo que usa amazon_import.py), y comprueba el fingerprint de deteccion
de automatizacion (navigator.webdriver)."""
from playwright.sync_api import sync_playwright
import time

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")

requests_log = []

def on_request(request):
    requests_log.append({"url": request.url, "method": request.method, "type": request.resource_type})

def on_response(response):
    for r in requests_log:
        if r["url"] == response.url and "status" not in r:
            r["status"] = response.status
            break

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context(user_agent=UA, locale="es-ES")
    page = context.new_page()
    page.on("request", on_request)
    page.on("response", on_response)

    # Fingerprint de deteccion de automatizacion
    webdriver_flag = page.evaluate("navigator.webdriver")
    print(f"navigator.webdriver (ANTES de navegar): {webdriver_flag}")

    t0 = time.time()
    page.goto("https://www.amazon.es/dp/B0GWHNJ8Y3", wait_until="networkidle", timeout=60000)
    elapsed = time.time() - t0

    webdriver_flag2 = page.evaluate("navigator.webdriver")
    print(f"navigator.webdriver (DESPUES de navegar): {webdriver_flag2}")
    print(f"TIEMPO TOTAL hasta networkidle: {elapsed:.2f}s")
    print(f"TITLE final: {page.title()}")
    print(f"TOTAL SUBPETICIONES disparadas: {len(requests_log)}")

    by_type = {}
    for r in requests_log:
        by_type[r["type"]] = by_type.get(r["type"], 0) + 1
    print("Desglose por tipo:", by_type)

    by_domain = {}
    for r in requests_log:
        from urllib.parse import urlparse
        dom = urlparse(r["url"]).netloc
        by_domain[dom] = by_domain.get(dom, 0) + 1
    print("Top dominios:")
    for dom, count in sorted(by_domain.items(), key=lambda x: -x[1])[:15]:
        print(f"  {count:4d}  {dom}")

    non_200 = [r for r in requests_log if r.get("status") and r["status"] != 200]
    print(f"\nSubpeticiones con status != 200: {len(non_200)}")
    for r in non_200[:20]:
        print(f"  {r.get('status')} {r['type']} {r['url'][:100]}")

    browser.close()
