#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""DIAGNOSTICO (solo lectura, no toca amazon_import.py).
Test 1: peticion HTTP cruda (urllib, sin navegador/JS) a cada URL,
para ver el codigo HTTP real que devuelve el edge de Amazon antes de
que intervenga ningun renderizado ni deteccion basada en JS."""
import urllib.request
import time
import ssl

URLS = [
    "https://amzn.eu/d/01dSVCh2",
    "https://amzn.eu/d/01T4GUxQ",
    "https://amzn.eu/d/07hhdKOK",
    "https://amzn.eu/d/016TYrG2",
    "https://amzn.eu/d/0cl13CZ7",
    "https://amzn.eu/d/06rS7uZI",
    "https://amzn.eu/d/01Dg6Xb1",
    "https://www.amazon.es/dp/B0CKQWZ59X",
]

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")

ctx = ssl.create_default_context()

for i, url in enumerate(URLS, 1):
    req = urllib.request.Request(url, headers={
        "User-Agent": UA,
        "Accept-Language": "es-ES,es;q=0.9",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    })
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=20, context=ctx) as resp:
            elapsed = time.time() - t0
            body = resp.read()
            print(f"[{i}] {url}")
            print(f"    STATUS: {resp.status}  FINAL_URL: {resp.geturl()}")
            print(f"    TIME: {elapsed:.2f}s  SIZE: {len(body)} bytes")
            print(f"    HEADERS: Server={resp.headers.get('Server')} "
                  f"X-Amz-Rid={resp.headers.get('X-Amz-Rid')} "
                  f"Set-Cookie={'yes' if resp.headers.get('Set-Cookie') else 'no'} "
                  f"Retry-After={resp.headers.get('Retry-After')}")
            snippet = body[:200].decode('utf-8', errors='replace').replace('\n', ' ')
            print(f"    BODY_SNIPPET: {snippet}")
    except urllib.error.HTTPError as e:
        elapsed = time.time() - t0
        body = e.read()
        print(f"[{i}] {url}")
        print(f"    HTTP ERROR: {e.code} {e.reason}  TIME: {elapsed:.2f}s  SIZE: {len(body)} bytes")
        print(f"    HEADERS: {dict(e.headers)}")
    except Exception as e:
        elapsed = time.time() - t0
        print(f"[{i}] {url}")
        print(f"    EXCEPTION: {type(e).__name__}: {e}  TIME: {elapsed:.2f}s")
    print()
    time.sleep(2)
