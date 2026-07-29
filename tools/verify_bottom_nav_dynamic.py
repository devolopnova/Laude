#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Verifica que el bottom-nav-grid de cada pagina coincide con la cadena
circular esperada segun el array bands de guia-regalos-juguetes.html."""
import re
from pathlib import Path
from update_bottom_nav_dynamic import extract_bands, ROOT, LANDING

prev_pattern = re.compile(
    r'<a class="bottom-nav-card bottom-nav-prev" href="([^"]*)">\s*'
    r'<span class="bottom-nav-icon">←</span>\s*'
    r'<span class="bottom-nav-label">([^<]*)</span>\s*</a>'
)
next_pattern = re.compile(
    r'<a class="bottom-nav-card bottom-nav-next" href="([^"]*)">\s*'
    r'<span class="bottom-nav-label">([^<]*)</span>\s*'
    r'<span class="bottom-nav-icon">→</span>\s*</a>'
)

def main():
    html = LANDING.read_text(encoding="utf-8")
    bands = extract_bands(html)
    problems = 0
    checked = 0
    for band_id, ordered in bands:
        n = len(ordered)
        if n < 2:
            continue
        for i, (name, fname) in enumerate(ordered):
            path = ROOT / fname
            if not path.exists():
                print(f"{band_id} {fname}: ARCHIVO NO EXISTE")
                problems += 1
                continue
            text = path.read_text(encoding="utf-8")
            pm = prev_pattern.search(text)
            nm = next_pattern.search(text)
            if not pm or not nm:
                print(f"{band_id} {fname}: sin bloque bottom-nav-prev/next")
                continue
            checked += 1
            exp_prev_name, exp_prev_file = ordered[(i - 1) % n]
            exp_next_name, exp_next_file = ordered[(i + 1) % n]
            if pm.group(1) != exp_prev_file or pm.group(2) != exp_prev_name:
                print(f"{band_id} {fname}: PREV esperado ({exp_prev_file!r},{exp_prev_name!r}) obtenido ({pm.group(1)!r},{pm.group(2)!r})")
                problems += 1
            if nm.group(1) != exp_next_file or nm.group(2) != exp_next_name:
                print(f"{band_id} {fname}: NEXT esperado ({exp_next_file!r},{exp_next_name!r}) obtenido ({nm.group(1)!r},{nm.group(2)!r})")
                problems += 1
    print(f"\nRevisadas {checked} paginas con bottom-nav-grid. Problemas: {problems}")

if __name__ == "__main__":
    main()
