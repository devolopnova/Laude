#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Migra las 10 paginas de la franja 0-6 meses (a0) del formato de
navegacion inferior ANTIGUO (cat-pager / age-pager / mont-chip / pie con
texto suelto) al formato NUEVO usado por el resto del sitio (a1..a11):
bottom-nav-section con NAVEGAR ENTRE CATEGORIAS + EXPLORAR MAS +
DESCUBRE MAS JUGUETES, seguido de la nota unica y el footer vacio.

Solo toca la navegacion inferior: NO modifica las fichas de producto
(que en a0 siguen en formato .product-card antiguo, fuera de alcance
de esta tarea) ni el resto de la pagina.
"""

import re
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent))
from apply_discover_more import parse_chip_designs, parse_band, resolve_icon, normalize

ROOT = Path(__file__).parent.parent
LANDING = ROOT / "guia-regalos-juguetes.html"

NOTE_TEXT = 'ℹ Los enlaces llevan directamente a la ficha del producto en Amazon.es.'

def build_nav_categorias(categories, chip_pages, idx):
    n = len(categories)
    prev_name = categories[(idx - 1) % n]
    next_name = categories[(idx + 1) % n]
    prev_file = chip_pages[prev_name]
    next_file = chip_pages[next_name]
    return (
        '  <section class="bottom-nav-section">\n'
        '    <h3 class="bottom-nav-title">⊞ NAVEGAR ENTRE CATEGORÍAS</h3>\n'
        '    <div class="bottom-nav-grid">\n'
        f'      <a class="bottom-nav-card bottom-nav-prev" href="{prev_file}">\n'
        '        <span class="bottom-nav-icon">←</span>\n'
        f'        <span class="bottom-nav-label">{prev_name}</span>\n'
        '      </a>\n'
        '      <a class="bottom-nav-card bottom-nav-center" href="guia-regalos-juguetes.html">\n'
        '        <span class="bottom-nav-icon">⊞</span>\n'
        '        <span class="bottom-nav-title-main">Todas las categorías</span>\n'
        '      </a>\n'
        f'      <a class="bottom-nav-card bottom-nav-next" href="{next_file}">\n'
        f'        <span class="bottom-nav-label">{next_name}</span>\n'
        '        <span class="bottom-nav-icon">→</span>\n'
        '      </a>\n'
        '    </div>\n'
        '  </section>'
    )

def build_explorar_mas(next_band_id, next_label):
    # a0 es la primera franja: nunca hay prev-age.
    return (
        '  <section class="bottom-nav-section">\n'
        '    <h3 class="bottom-nav-title">🔍 EXPLORAR MÁS</h3>\n'
        '    <div class="bottom-nav-explore">\n'
        f'      <a class="bottom-nav-explore-card bne-next-age" href="guia-regalos-juguetes.html#{next_band_id}">\n'
        f'        <strong class="bottom-nav-explore-name">Ver regalos para<br>{next_label}</strong>\n'
        '      </a>\n'
        '      <a class="bottom-nav-explore-card bne-montessori" href="guia-montessori.html">\n'
        '        <strong class="bottom-nav-explore-name">Descubre la<br>Guía Montessori</strong>\n'
        '      </a>\n'
        '    </div>\n'
        '  </section>'
    )

def build_discover_more(categories, exclude_cat, chip_pages, cat_icons, age_label):
    cards = []
    for cat in categories:
        if cat == exclude_cat:
            continue
        fname = chip_pages[cat]
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
        f'    <h3 class="bottom-nav-title">🏷️ DESCUBRE MÁS JUGUETES PARA {age_label.upper()}</h3>\n'
        '    <p class="discover-more-sub">Explora otras categorías de juguetes ideales para esta edad.</p>\n'
        '    <div class="discover-more-grid">\n'
        f'{cards_html}\n'
        '    </div>\n'
        '  </section>'
    )

# Bloque antiguo completo a eliminar: desde <nav class="cat-pager...
# hasta el cierre del footer viejo, inclusive.
OLD_BLOCK_RE = re.compile(
    r'<nav class="cat-pager wrap">.*?</footer>\s*',
    re.DOTALL
)

def main():
    landing_html = LANDING.read_text(encoding='utf-8')
    global_designs = parse_chip_designs(landing_html)
    band = parse_band(landing_html, 'a0')
    categories = band['chips']
    chip_pages = band['chipPages']
    age_label = f"{band['num']} {band['unit']}"

    cat_icons = {cat: resolve_icon(cat, band, global_designs) for cat in categories}

    # Etiqueta de la franja siguiente (a1) para EXPLORAR MAS
    next_m = re.search(r"\{id:'a1', num:'([^']*)', unit:'([^']*)'", landing_html)
    next_label = f"{next_m.group(1)} {next_m.group(2)}"

    print(f"Franja a0: {age_label} ({len(categories)} categorias)")

    done = 0
    for idx, cat in enumerate(categories):
        fname = chip_pages[cat]
        fpath = ROOT / fname
        if not fpath.exists():
            print(f'  ❌ {fname}: no existe')
            continue
        html = fpath.read_text(encoding='utf-8')

        if 'bottom-nav-section' in html:
            print(f'  ⏭️  {fname}: ya migrado')
            continue

        nav_block = build_nav_categorias(categories, chip_pages, idx)
        explore_block = build_explorar_mas('a1', next_label)
        discover_block = build_discover_more(categories, cat, chip_pages, cat_icons, age_label)

        new_bottom_nav = (
            '<div class="bottom-nav wrap">\n'
            f'{nav_block}\n\n'
            f'{explore_block}\n\n'
            f'{discover_block}\n\n'
            f'  <p class="bottom-nav-note">{NOTE_TEXT}</p>\n'
            '</div>\n\n'
            '<footer class="wrap">\n</footer>\n'
        )

        new_html, n = OLD_BLOCK_RE.subn(new_bottom_nav, html, count=1)
        if n == 0:
            print(f'  ❌ {fname}: patron antiguo no encontrado')
            continue

        fpath.write_text(new_html, encoding='utf-8')
        print(f'  ✅ {fname}: migrado')
        done += 1

    print(f"\nTotal migradas: {done}/{len(categories)}")

if __name__ == '__main__':
    main()
