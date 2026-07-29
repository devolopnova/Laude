#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Repara el desaguisado del script anterior: restaura el bloque
'NAVEGAR ENTRE CATEGORIAS' que fue sobrescrito por error, y coloca
'DESCUBRE MAS JUGUETES' en su sitio correcto (tras EXPLORAR MAS,
con el bottom-nav-note al final), eliminando el bloque roto del footer."""

import re
from pathlib import Path

ROOT = Path(__file__).parent.parent

# Orden real de categorias en la franja de 3 anos (band a4)
CATEGORIES_3ANOS = [
    ('Bicicletas y patinetes', 'bicicletas-y-patinetes-3-anos.html'),
    ('Construcciones', 'construcciones-3-anos.html'),
    ('Cocinitas', 'cocinitas-3-anos.html'),
    ('Disfraces', 'disfraces-3-anos.html'),
    ('Manualidades', 'manualidades-3-anos.html'),
    ('Juegos de mesa', 'juegos-de-mesa-3-anos.html'),
    ('Libros', 'libros-3-anos.html'),
    ('Figuras y animales', 'figuras-y-animales-3-anos.html'),
    ('Coches teledirigidos', 'coches-teledirigidos-3-anos.html'),
    ('Puzzles', 'puzzles-3-anos.html'),
    ('Coches', 'coches-3-anos.html'),
]

ICON_MAP = {
    'Bicicletas y patinetes': 'bicicletas-y-patinetes-3-anos.png',
    'Construcciones': 'construcciones-cutout.webp',
    'Cocinitas': 'cocinitas-3-anos.png',
    'Disfraces': 'disfraces-cutout.webp',
    'Manualidades': 'manualidades-fixed.webp',
    'Juegos de mesa': 'juegos-de-mesa-fixed.webp',
    'Libros': 'libros-cutout.webp',
    'Figuras y animales': 'figuras-y-animales-cutout.webp',
    'Coches teledirigidos': 'coches-teledirigidos-completo.png',
    'Puzzles': 'puzzles-cutout.webp',
    'Coches': 'coches-cutout.webp',
}

# Las 9 paginas que quedaron rotas por el script anterior
BROKEN_FILES = [
    'bicicletas-y-patinetes-3-anos.html',
    'disfraces-3-anos.html',
    'manualidades-3-anos.html',
    'juegos-de-mesa-3-anos.html',
    'libros-3-anos.html',
    'figuras-y-animales-3-anos.html',
    'coches-teledirigidos-3-anos.html',
    'puzzles-3-anos.html',
    'coches-3-anos.html',
]

NOTE = '  <p class="bottom-nav-note">ℹ Los enlaces llevan directamente a la ficha del producto en Amazon.es.</p>'

def build_nav_categories_block(idx):
    n = len(CATEGORIES_3ANOS)
    prev_name, prev_file = CATEGORIES_3ANOS[(idx - 1) % n]
    next_name, next_file = CATEGORIES_3ANOS[(idx + 1) % n]
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

def build_discover_more_block(exclude_category):
    cards = []
    for cat_name, cat_file in CATEGORIES_3ANOS:
        if cat_name == exclude_category:
            continue
        icon = ICON_MAP[cat_name]
        cards.append(
            f'      <a class="discover-more-card" href="{cat_file}">\n'
            f'        <img class="discover-more-img" src="images/icons-3d/{icon}" alt="" width="96" height="96" loading="lazy">\n'
            f'        <span class="discover-more-name">{cat_name}</span>\n'
            f'        <span class="discover-more-arrow" aria-hidden="true">→</span>\n'
            f'      </a>'
        )
    cards_html = '\n'.join(cards)
    return (
        '  <section class="bottom-nav-section">\n'
        '    <h3 class="bottom-nav-title">🏷️ DESCUBRE MÁS JUGUETES PARA 3 AÑOS</h3>\n'
        '    <p class="discover-more-sub">Explora otras categorías de juguetes ideales para esta edad.</p>\n'
        '    <div class="discover-more-grid">\n'
        f'{cards_html}\n'
        '    </div>\n'
        '  </section>'
    )

# Pattern A: la seccion mal colocada (con markup CORRECTO <img class=discover-more-img>)
# que quedo en el lugar de "NAVEGAR ENTRE CATEGORIAS", justo tras abrir bottom-nav wrap.
PATTERN_A = re.compile(
    r'(<div class="bottom-nav wrap">)\s*'
    r'<section class="bottom-nav-section">\s*'
    r'<h3 class="bottom-nav-title">🏷️ DESCUBRE MÁS JUGUETES PARA 3 AÑOS</h3>\s*'
    r'<p class="discover-more-sub">.*?</p>\s*'
    r'<div class="discover-more-grid">.*?</div>\s*'
    r'</section>\s*'
    r'(<section class="bottom-nav-section">\s*<h3 class="bottom-nav-title">🔍 EXPLORAR MÁS</h3>)',
    re.DOTALL
)

# Pattern B: nota dentro de EXPLORAR MAS + cierre + footer con el bloque ROTO viejo
# (markup incorrecto: <span class="discover-more-img"><img ...></span>)
PATTERN_B = re.compile(
    r'<p class="bottom-nav-note">ℹ Los enlaces llevan directamente a la ficha del producto en Amazon\.es\.</p>\s*'
    r'</section>\s*'
    r'</div>\s*'
    r'<footer class="wrap">\s*'
    r'<section class="discover-more">\s*'
    r'<h3 class="discover-more-title">.*?</h3>.*?'
    r'</section>\s*'
    r'</footer>',
    re.DOTALL
)

def main():
    for idx, (cat_name, fname) in enumerate(CATEGORIES_3ANOS):
        if fname not in BROKEN_FILES:
            continue

        fpath = ROOT / fname
        html = fpath.read_text(encoding='utf-8')

        nav_block = build_nav_categories_block(idx)
        new_html, nA = PATTERN_A.subn(lambda m: f'{m.group(1)}\n{nav_block}\n\n  {m.group(2)}', html, count=1)
        if nA == 0:
            print(f'❌ {fname}: PATTERN_A no coincidió (bloque mal colocado no encontrado)')
            continue

        discover_block = build_discover_more_block(cat_name)
        replacement_B = (
            f'  </section>\n\n{discover_block}\n\n{NOTE}\n'
            '</div>\n\n<footer class="wrap">\n</footer>'
        )
        new_html, nB = PATTERN_B.subn(replacement_B, new_html, count=1)
        if nB == 0:
            print(f'❌ {fname}: PATTERN_B no coincidió (nota/footer roto no encontrado)')
            continue

        fpath.write_text(new_html, encoding='utf-8')
        print(f'✅ {fname}: reparado (prev/next correctos, discover-more bien colocado, footer limpio)')

if __name__ == '__main__':
    main()
