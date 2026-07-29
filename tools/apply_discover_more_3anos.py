#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Aplica el bloque 'Descubre más juguetes' a todas las categorías de 3 años,
replicando EXACTAMENTE la estructura ya usada en construcciones/cocinitas."""

import re
from pathlib import Path

ROOT = Path(__file__).parent.parent

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

# Icono exacto usado por cada categoria (tal como aparece en construcciones/cocinitas)
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

# Paginas que ya tienen la estructura CORRECTA (no tocar)
ALREADY_CORRECT = {'construcciones-3-anos.html', 'cocinitas-3-anos.html'}

SECTION_RE = re.compile(
    r'\s*<section class="(?:discover-more|bottom-nav-section)">\s*'
    r'<h3 class="(?:discover-more-title|bottom-nav-title)">.*?</section>\n?',
    re.DOTALL
)

def build_block(exclude_category):
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
        '  </section>\n'
    )

def main():
    for cat_name, fname in CATEGORIES_3ANOS:
        if fname in ALREADY_CORRECT:
            print(f'⏭️  {fname}: estructura ya correcta, no se toca')
            continue

        fpath = ROOT / fname
        if not fpath.exists():
            print(f'❌ {fname}: archivo no existe')
            continue

        html = fpath.read_text(encoding='utf-8')

        new_block = build_block(cat_name)
        new_html, n = SECTION_RE.subn(new_block, html, count=1)

        if n == 0:
            print(f'❌ {fname}: no se encontró el bloque a reemplazar')
            continue

        fpath.write_text(new_html, encoding='utf-8')
        print(f'✅ {fname}: bloque corregido')

if __name__ == '__main__':
    main()
