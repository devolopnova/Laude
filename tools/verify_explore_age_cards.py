#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Verifica que las tarjetas 'Ver regalos para <edad>' de cada pagina
apuntan a la edad anterior/siguiente correcta segun el orden real a0..a11."""
import re
from update_bottom_nav_dynamic import extract_bands, ROOT, LANDING
from update_explore_age_cards import extract_age_labels, band_sort_key

card_pattern = re.compile(
    r'<a class="bottom-nav-explore-card bne-([a-z-]+)" href="([^"]*)">\s*'
    r'<strong class="bottom-nav-explore-name">([^<]*(?:<br>[^<]*)?)</strong>'
)

def main():
    html = LANDING.read_text(encoding="utf-8")
    bands = extract_bands(html)
    labels = extract_age_labels(html)
    order = sorted(labels.keys(), key=band_sort_key)

    problems = 0
    checked = 0
    for band_id, ordered in bands:
        idx = order.index(band_id)
        prev_band = order[idx - 1] if idx > 0 else None
        next_band = order[idx + 1] if idx < len(order) - 1 else None
        for name, fname in ordered:
            path = ROOT / fname
            text = path.read_text(encoding="utf-8")
            cards = {role: (href, label) for role, href, label in card_pattern.findall(text)}
            if not cards:
                continue
            checked += 1
            if prev_band:
                exp = (f"guia-regalos-juguetes.html#{prev_band}", f"Ver regalos para<br>{labels[prev_band]}")
                got = cards.get("prev-age")
                if got != exp:
                    print(f"{band_id} {fname}: PREV-AGE esperado {exp} obtenido {got}")
                    problems += 1
            elif "prev-age" in cards:
                print(f"{band_id} {fname}: no deberia tener prev-age")
                problems += 1
            if next_band:
                exp = (f"guia-regalos-juguetes.html#{next_band}", f"Ver regalos para<br>{labels[next_band]}")
                got = cards.get("next-age")
                if got != exp:
                    print(f"{band_id} {fname}: NEXT-AGE esperado {exp} obtenido {got}")
                    problems += 1
            elif "next-age" in cards:
                print(f"{band_id} {fname}: no deberia tener next-age")
                problems += 1
            if "montessori" not in cards:
                print(f"{band_id} {fname}: falta tarjeta montessori")
                problems += 1
    print(f"\nRevisadas {checked} paginas. Problemas: {problems}")

if __name__ == "__main__":
    main()
