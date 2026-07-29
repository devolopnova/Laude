#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Aplica el bloque 'Descubre mas juguetes para X' a todas las paginas de
categoria de una franja de edad dada, leyendo el orden de categorias y sus
paginas directamente de guia-regalos-juguetes.html (band.chips / chipPages /
chipDesigns) para no tener que mantener listas hardcodeadas por franja.

Uso: python tools/apply_discover_more.py --band a5
"""

import argparse
import re
from pathlib import Path

ROOT = Path(__file__).parent.parent
LANDING = ROOT / "guia-regalos-juguetes.html"

def normalize(name):
    import unicodedata
    n = name.lower()
    n = unicodedata.normalize('NFD', n)
    n = ''.join(c for c in n if unicodedata.category(c) != 'Mn')
    n = re.sub(r'\s+', ' ', n).strip()
    return n

def parse_chip_designs(html):
    """Extrae la biblioteca global CHIP_DESIGNS: {nombre_normalizado: icon_path}."""
    m = re.search(r'const CHIP_DESIGNS = \{(.*?)\n  \};', html, re.DOTALL)
    block = m.group(1)
    designs = {}
    for entry in re.finditer(
        r"\[normalizeCatName\('([^']+)'\)\]:\s*\{bg:'[^']*',\s*icon:'([^']+)'\}",
        block
    ):
        designs[normalize(entry.group(1))] = entry.group(2)
    return designs

def parse_band(html, band_id):
    """Extrae num, unit, chips (orden), chipPages y chipDesigns (override) de una franja."""
    m = re.search(r"\{id:'" + band_id + r"'.*?tip:'.*?'\},?\n", html, re.DOTALL)
    if not m:
        raise SystemExit(f"No se encontro la franja {band_id}")
    block = m.group(0)

    num = re.search(r"num:'([^']+)'", block).group(1)
    unit = re.search(r"unit:'([^']+)'", block).group(1)

    chips_m = re.search(r"chips:\[(.*?)\]", block)
    chips = re.findall(r"'([^']+)'", chips_m.group(1))

    pages_m = re.search(r"chipPages:\{(.*?)\}", block, re.DOTALL)
    chip_pages = dict(re.findall(r"'([^']+)':\s*'([^']+)'", pages_m.group(1))) if pages_m else {}

    designs_m = re.search(r"chipDesigns:\{(.*?)\}\s*,\s*chipPages", block, re.DOTALL)
    chip_designs = {}
    if designs_m:
        for entry in re.finditer(r"'([^']+)':\{bg:'[^']*',\s*icon:'([^']+)'\}", designs_m.group(1)):
            chip_designs[entry.group(1)] = entry.group(2)

    return {'num': num, 'unit': unit, 'chips': chips, 'chipPages': chip_pages, 'chipDesigns': chip_designs}

def resolve_icon(cat, band, global_designs):
    if cat in band['chipDesigns']:
        return band['chipDesigns'][cat]
    icon = global_designs.get(normalize(cat))
    if not icon:
        raise SystemExit(f"Sin icono para categoria '{cat}'")
    return icon

SVG_NOTE = None  # placeholder, not used

def build_discover_more_block(categories, exclude_cat, chip_pages, band):
    age_label = f"{band['num']} {band['unit'].upper()}"
    cards = []
    for cat in categories:
        if cat == exclude_cat:
            continue
        fname = chip_pages.get(cat)
        if not fname:
            continue
        icon = cat_icons[cat]
        cards.append(
            f'      <a class="discover-more-card" href="{fname}">\n'
            f'        <img class="discover-more-img" src="{icon}" alt="" width="96" height="96" loading="lazy">\n'
            f'        <span class="discover-more-name">{cat}</span>\n'
            f'        <span class="discover-more-arrow" aria-hidden="true">→</span>\n'
            f'      </a>'
        )
    cards_html = '\n'.join(cards)
    return (
        '  <section class="bottom-nav-section">\n'
        f'    <h3 class="bottom-nav-title">🏷️ DESCUBRE MÁS JUGUETES PARA {age_label}</h3>\n'
        '    <p class="discover-more-sub">Explora otras categorías de juguetes ideales para esta edad.</p>\n'
        '    <div class="discover-more-grid">\n'
        f'{cards_html}\n'
        '    </div>\n'
        '  </section>'
    )

NOTE_TEXT = 'ℹ Los enlaces llevan directamente a la ficha del producto en Amazon.es.'

# Localiza la seccion EXPLORAR MAS (con la nota dentro, patron original antes
# de aplicar el bloque discover-more) y el footer vacio justo despues.
INSERT_RE = re.compile(
    r'(<section class="bottom-nav-section">\s*'
    r'<h3 class="bottom-nav-title">🔍 EXPLORAR MÁS</h3>.*?</div>\s*)'
    r'<p class="bottom-nav-note">ℹ Los enlaces llevan directamente a la ficha del producto en Amazon\.es\.</p>\s*'
    r'</section>\s*'
    r'</div>\s*'
    r'<footer class="wrap">\s*'
    r'</footer>',
    re.DOTALL
)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--band', required=True, help="id de la franja, p.ej. a5")
    args = ap.parse_args()

    landing_html = LANDING.read_text(encoding='utf-8')
    global_designs = parse_chip_designs(landing_html)
    band = parse_band(landing_html, args.band)

    categories = band['chips']
    chip_pages = band['chipPages']

    global cat_icons
    cat_icons = {cat: resolve_icon(cat, band, global_designs) for cat in categories}

    print(f"Franja {args.band}: {band['num']} {band['unit']}")
    print(f"Categorias ({len(categories)}): {categories}")

    done = 0
    skipped = 0
    for cat in categories:
        fname = chip_pages.get(cat)
        if not fname:
            print(f'  ⏭️  {cat}: sin pagina propia (chipPages), omitida')
            continue
        fpath = ROOT / fname
        if not fpath.exists():
            print(f'  ❌ {fname}: archivo no existe')
            continue
        html = fpath.read_text(encoding='utf-8')
        if 'discover-more' in html:
            print(f'  ⏭️  {fname}: ya tiene discover-more')
            skipped += 1
            continue

        discover_block = build_discover_more_block(categories, cat, chip_pages, band)
        replacement = (
            r'\1'
            f'</section>\n\n{discover_block}\n\n'
            f'  <p class="bottom-nav-note">{NOTE_TEXT}</p>\n'
            '</div>\n\n<footer class="wrap">\n</footer>'
        )
        new_html, n = INSERT_RE.subn(lambda m: m.group(1) + '</section>\n\n' + discover_block + f'\n\n  <p class="bottom-nav-note">{NOTE_TEXT}</p>\n</div>\n\n<footer class="wrap">\n</footer>', html, count=1)
        if n == 0:
            print(f'  ❌ {fname}: patron de insercion no coincidio')
            continue
        fpath.write_text(new_html, encoding='utf-8')
        print(f'  ✅ {fname}: bloque agregado')
        done += 1

    print(f"\nTotal: {done} paginas actualizadas, {skipped} ya tenian el bloque")

if __name__ == '__main__':
    main()
