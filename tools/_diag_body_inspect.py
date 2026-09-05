#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""DIAGNOSTICO fase 2: inspecciona el CONTENIDO completo de una respuesta
'corta' (3789 bytes) y una 'larga' (~1MB) para clasificar que es cada una."""
import urllib.request
import re

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")

def fetch(url):
    req = urllib.request.Request(url, headers={
        "User-Agent": UA,
        "Accept-Language": "es-ES,es;q=0.9",
    })
    with urllib.request.urlopen(req, timeout=20) as resp:
        return resp.read().decode('utf-8', errors='replace'), resp.status, resp.geturl()

print("=== CASO CORTO (3789 bytes) — amzn.eu/d/01dSVCh2 ===")
body, status, final = fetch("https://amzn.eu/d/01dSVCh2")
print(f"status={status} final={final}")
print(body)
print("\n\n=== CASO LARGO (~1MB) — amzn.eu/d/016TYrG2 ===")
body2, status2, final2 = fetch("https://amzn.eu/d/016TYrG2")
print(f"status={status2} final={final2} size={len(body2)}")
# Buscar marcadores clave de bot-detection o de contenido real de producto
markers = [
    "productTitle", "landingImage", "Robot Check", "captcha", "Type the characters",
    "Sorry, we just need to make sure", "seguir comprando", "api-services-support",
    "errors.amazon", "Enter the characters",
]
for m in markers:
    count = body2.lower().count(m.lower())
    print(f"  marcador '{m}': aparece {count} veces")
