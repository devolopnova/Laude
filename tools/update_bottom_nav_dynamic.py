#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Actualiza las tarjetas "Categoria anterior" / "Siguiente categoria" del bloque
bottom-nav-grid en cada pagina de categoria, para que naveguen de forma
circular SOLO entre las categorias de la misma franja de edad (usando el
orden y las paginas definidos en el array `bands` de
guia-regalos-juguetes.html), y muestren el nombre real de la categoria
destino en vez del texto generico "Categoria anterior"/"Siguiente categoria".
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LANDING = ROOT / "guia-regalos-juguetes.html"

def extract_bands(html):
    bands = []
    # Delimitar cada banda por su propio bloque {id:'aN' ... hasta el siguiente
    # {id:'aM' (o el cierre del array bands), para que chips/chipPages nunca
    # se lean cruzando a la banda siguiente (algunas bandas tienen bloques
    # intermedios como chipDesigns entre chips y chipPages).
    starts = [(m.start(), m.group(1)) for m in re.finditer(r"\{id:'(a\d+)'", html)]
    for i, (start, band_id) in enumerate(starts):
        end = starts[i + 1][0] if i + 1 < len(starts) else len(html)
        block = html[start:end]
        chips_m = re.search(r"chips:\[(.*?)\],", block, re.DOTALL)
        pages_m = re.search(r"chipPages:\{(.*?)\},", block, re.DOTALL)
        if not chips_m or not pages_m:
            bands.append((band_id, []))
            continue
        chips = re.findall(r"'((?:[^'\\]|\\.)*)'", chips_m.group(1))
        pages = dict(re.findall(r"'((?:[^'\\]|\\.)*)'\s*:\s*'((?:[^'\\]|\\.)*)'", pages_m.group(1)))
        ordered = [(name, pages[name]) for name in chips if name in pages]
        bands.append((band_id, ordered))
    return bands

def update_file(path, prev_name, prev_file, next_name, next_file):
    text = path.read_text(encoding="utf-8")
    orig = text

    prev_pattern = re.compile(
        r'(<a class="bottom-nav-card bottom-nav-prev" href=")[^"]*('
        r'"\s*>\s*<span class="bottom-nav-icon">←</span>\s*'
        r'<span class="bottom-nav-label">)[^<]*(</span>\s*</a>)'
    )
    next_pattern = re.compile(
        r'(<a class="bottom-nav-card bottom-nav-next" href=")[^"]*('
        r'"\s*>\s*<span class="bottom-nav-label">)[^<]*('
        r'</span>\s*<span class="bottom-nav-icon">→</span>\s*</a>)'
    )

    text, n1 = prev_pattern.subn(lambda m: m.group(1) + prev_file + m.group(2) + prev_name + m.group(3), text)
    text, n2 = next_pattern.subn(lambda m: m.group(1) + next_file + m.group(2) + next_name + m.group(3), text)

    if n1 == 0 or n2 == 0:
        return f"SKIP (no bottom-nav-prev/next found: prev={n1} next={n2})"
    if text != orig:
        path.write_text(text, encoding="utf-8")
        return "OK"
    return "unchanged"

def main():
    html = LANDING.read_text(encoding="utf-8")
    bands = extract_bands(html)

    report = []
    for band_id, ordered in bands:
        n = len(ordered)
        if n < 2:
            continue
        missing = [f for _, f in ordered if not (ROOT / f).exists()]
        if missing:
            report.append(f"{band_id}: SKIP banda entera, faltan archivos: {missing}")
            continue
        for i, (name, fname) in enumerate(ordered):
            prev_name, prev_file = ordered[(i - 1) % n]
            next_name, next_file = ordered[(i + 1) % n]
            result = update_file(ROOT / fname, prev_name, prev_file, next_name, next_file)
            report.append(f"{band_id} {fname}: {result}")

    print("\n".join(report))

if __name__ == "__main__":
    main()
