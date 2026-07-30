#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Inserta la tarjeta de 'Musica' en el bloque discover-more-grid de las 8
paginas existentes de la franja 1 año, en la posicion correcta segun el
orden real de chips (justo antes de Libros; en libros-1-ano.html, que no
tiene tarjeta de si mismo, se inserta justo despues de Vehiculos)."""

import re
from pathlib import Path

ROOT = Path(__file__).parent.parent

PAGES = [
    'correpasillos-1-ano.html', 'construcciones-1-ano.html', 'vehiculos-1-ano.html',
    'libros-1-ano.html', 'puzzles-1-ano.html', 'pintura-y-creatividad-1-ano.html',
    'peluches-1-ano.html', 'juguetes-de-bano-1-ano.html',
]

MUSICA_CARD = '''      <a class="discover-more-card" href="musica-1-ano.html">
        <img class="discover-more-img" src="images/icons-3d/musica-cutout.webp" alt="" width="96" height="96" loading="lazy">
        <span class="discover-more-name">Música</span>
        <span class="discover-more-arrow" aria-hidden="true">→</span>
      </a>
'''

LIBROS_CARD_RE = re.compile(
    r'      <a class="discover-more-card" href="libros-1-ano\.html">.*?</a>\n',
    re.DOTALL
)
VEHICULOS_CARD_RE = re.compile(
    r'(      <a class="discover-more-card" href="vehiculos-1-ano\.html">.*?</a>\n)',
    re.DOTALL
)

for fname in PAGES:
    fpath = ROOT / fname
    html = fpath.read_text(encoding='utf-8')

    if 'href="musica-1-ano.html"' in html:
        print(f'⏭️  {fname}: ya tiene la tarjeta de Música')
        continue

    if LIBROS_CARD_RE.search(html):
        # Insertar ANTES de la tarjeta de Libros
        new_html, n = LIBROS_CARD_RE.subn(lambda m: MUSICA_CARD + m.group(0), html, count=1)
        if n == 1:
            fpath.write_text(new_html, encoding='utf-8')
            print(f'✅ {fname}: Música insertada antes de Libros')
            continue

    # Caso especial: libros-1-ano.html no tiene tarjeta de si mismo,
    # se inserta justo despues de la tarjeta de Vehiculos
    if VEHICULOS_CARD_RE.search(html):
        new_html, n = VEHICULOS_CARD_RE.subn(lambda m: m.group(1) + MUSICA_CARD, html, count=1)
        if n == 1:
            fpath.write_text(new_html, encoding='utf-8')
            print(f'✅ {fname}: Música insertada después de Vehículos (caso especial)')
            continue

    print(f'❌ {fname}: no se encontró ancla (ni Libros ni Vehículos) para insertar')
