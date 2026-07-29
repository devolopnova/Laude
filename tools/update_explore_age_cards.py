#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Corrige las tarjetas "Ver regalos para <edad>" del bloque EXPLORAR MAS
(bottom-nav-explore) en cada pagina de categoria: actualmente estan
hardcodeadas a 0-6 meses / 2 anos en TODAS las paginas, sin importar la
edad real de la pagina. Este script las hace dinamicas: para cada pagina,
calcula la edad anterior y la edad siguiente a la suya (segun el orden real
de bandas a0..a11 en guia-regalos-juguetes.html) y genera href + texto
correctos. Si no existe edad anterior (a0) o edad posterior (a11), esa
tarjeta simplemente no se genera (solo aplica al extremo a11, ya que las
paginas de a0 no llevan este componente).
"""
import re
from pathlib import Path
from update_bottom_nav_dynamic import extract_bands, ROOT, LANDING

def extract_age_labels(html):
    labels = {}
    for m in re.finditer(r"\{id:'(a\d+)', num:'([^']*)', unit:'([^']*)'", html):
        band_id, num, unit = m.groups()
        labels[band_id] = f"{num} {unit}"
    return labels

def band_sort_key(band_id):
    return int(band_id[1:])

def build_explore_div(prev_band, next_band, labels):
    cards = []
    if prev_band:
        cards.append(
            f'<a class="bottom-nav-explore-card bne-prev-age" href="guia-regalos-juguetes.html#{prev_band}">\n'
            f'        <strong class="bottom-nav-explore-name">Ver regalos para<br>{labels[prev_band]}</strong>\n'
            f'      </a>'
        )
    if next_band:
        cards.append(
            f'<a class="bottom-nav-explore-card bne-next-age" href="guia-regalos-juguetes.html#{next_band}">\n'
            f'        <strong class="bottom-nav-explore-name">Ver regalos para<br>{labels[next_band]}</strong>\n'
            f'      </a>'
        )
    cards.append(
        '<a class="bottom-nav-explore-card bne-montessori" href="guia-montessori.html">\n'
        '        <strong class="bottom-nav-explore-name">Descubre la<br>Guía Montessori</strong>\n'
        '      </a>'
    )
    return '<div class="bottom-nav-explore">\n      ' + '\n      '.join(cards) + '\n    </div>'

def main():
    html = LANDING.read_text(encoding="utf-8")
    bands = extract_bands(html)
    labels = extract_age_labels(html)
    order = sorted(labels.keys(), key=band_sort_key)

    explore_pattern = re.compile(r'<div class="bottom-nav-explore">.*?</div>', re.DOTALL)

    report = []
    for band_id, ordered in bands:
        idx = order.index(band_id)
        prev_band = order[idx - 1] if idx > 0 else None
        next_band = order[idx + 1] if idx < len(order) - 1 else None
        new_div = build_explore_div(prev_band, next_band, labels)

        for name, fname in ordered:
            path = ROOT / fname
            if not path.exists():
                report.append(f"{band_id} {fname}: ARCHIVO NO EXISTE")
                continue
            text = path.read_text(encoding="utf-8")
            new_text, n = explore_pattern.subn(new_div, text, count=1)
            if n == 0:
                report.append(f"{band_id} {fname}: sin bloque bottom-nav-explore")
                continue
            if new_text != text:
                path.write_text(new_text, encoding="utf-8")
                report.append(f"{band_id} {fname}: OK")
            else:
                report.append(f"{band_id} {fname}: unchanged")

    print("\n".join(report))

if __name__ == "__main__":
    main()
