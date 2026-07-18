"""Inserta, debajo de la navegacion entre categorias (cat-pager, ya existente
y NO tocada por este script), dos bloques nuevos al pie de cada pagina de
categoria:
  1. Navegacion "edad anterior / edad siguiente" hacia la MISMA categoria en
     otra franja de edad (agrupando paginas por slug de archivo; "vehiculos"
     y "coches" se tratan como la misma familia porque son la misma
     categoria real con nombre distinto segun la edad).
  2. Un chip discreto de acceso a guia-montessori.html (en TODAS las
     paginas de categoria, tengan o no navegacion de edad).

Uso: python tools/add_age_pager.py [--dry-run]
"""
import re, sys

SRC = "guia-regalos-juguetes.html"
SLUG_MERGE = {"vehiculos": "coches"}  # slug -> slug canonico

def parse_bands():
    src = open(SRC, encoding="utf-8").read()
    m = re.search(r"const bands = \[(.*?)\n  \];", src, re.S)
    bands_src = m.group(1)
    starts = [mm.start() for mm in re.finditer(r"\{id:'a\d+',", bands_src)]
    starts.append(len(bands_src))
    bands = []
    for i in range(len(starts) - 1):
        text = bands_src[starts[i]:starts[i+1]]
        bid = re.search(r"id:'(a\d+)'", text).group(1)
        num = re.search(r"num:'([^']*)'", text).group(1)
        unit = re.search(r"unit:'([^']*)'", text).group(1)
        chips_m = re.search(r"chips:\[(.*?)\]", text, re.S)
        chips = re.findall(r"'((?:[^'\\]|\\.)*)'", chips_m.group(1)) if chips_m else []
        pages_m = re.search(r"chipPages:\{(.*?)\n\s*\},", text, re.S)
        pages = {}
        if pages_m:
            for km in re.finditer(r"'((?:[^'\\]|\\.)*)':'((?:[^'\\]|\\.)*)'", pages_m.group(1)):
                pages[km.group(1)] = km.group(2)
        ordered = [(c, pages[c]) for c in chips if c in pages]
        bands.append({"id": bid, "num": num, "unit": unit, "items": ordered})
    return bands

def slug_of(page):
    base = page[:-5]
    base = re.sub(r"-\d+-anos?$", "", base)
    base = re.sub(r"-6-12-meses$", "", base)
    return SLUG_MERGE.get(base, base)

def age_label(band):
    return f"{band['num']} {band['unit']}"

def main():
    dry = "--dry-run" in sys.argv
    bands = parse_bands()

    # slug -> lista de (bandIndex, page) en orden de edad (orden de bands)
    groups = {}
    page_seen = set()
    for bi, band in enumerate(bands):
        for label, page in band["items"]:
            if page in page_seen:
                continue  # una pagina solo pertenece a un grupo de edad
            page_seen.add(page)
            groups.setdefault(slug_of(page), []).append((bi, page))

    # pagina -> (prev_page, prev_label, next_page, next_label)
    age_nav = {}
    for slug, items in groups.items():
        if len(items) < 2:
            continue
        for i, (bi, page) in enumerate(items):
            prev_item = items[i-1] if i > 0 else None
            next_item = items[i+1] if i < len(items)-1 else None
            age_nav[page] = (
                (prev_item[1], age_label(bands[prev_item[0]])) if prev_item else None,
                (next_item[1], age_label(bands[next_item[0]])) if next_item else None,
            )

    all_pages = sorted(page_seen)
    updated, missing = [], []
    for page in all_pages:
        try:
            content = open(page, encoding="utf-8").read()
        except FileNotFoundError:
            missing.append(page)
            continue
        if 'class="age-pager' in content or 'class="mont-chip' in content:
            continue  # ya aplicado, no duplicar
        if '<nav class="cat-pager wrap">' not in content:
            missing.append(page + " (sin cat-pager)")
            continue

        block = ""
        nav = age_nav.get(page)
        if nav:
            prev_pair, next_pair = nav
            prev_link = f'<a class="cat-pager-link prev" href="{prev_pair[0]}">← Ver regalos para {prev_pair[1]}</a>' if prev_pair else ''
            next_link = f'<a class="cat-pager-link next" href="{next_pair[0]}">Ver regalos para {next_pair[1]} →</a>' if next_pair else ''
            block += f'<nav class="age-pager wrap">\n  {prev_link}\n  {next_link}\n</nav>\n\n'
        block += '<p class="mont-chip wrap"><a href="guia-montessori.html">📖 Descubre la Guía Montessori</a></p>\n\n'

        # Insertar justo despues del cierre del cat-pager ya existente
        idx = content.index('<nav class="cat-pager wrap">')
        close_idx = content.index('</nav>', idx) + len('</nav>')
        # saltar los saltos de linea en blanco que ya siguen al cat-pager
        rest = content[close_idx:]
        rest_stripped = rest.lstrip('\n')
        new_content = content[:close_idx] + '\n\n' + block + rest_stripped
        if not dry:
            open(page, "w", encoding="utf-8").write(new_content)
        updated.append(page)

    with_age_nav = sum(1 for p in all_pages if p in age_nav)
    print(f"paginas actualizadas: {len(updated)} (con navegacion de edad: {with_age_nav})")
    if missing:
        print(f"con problemas: {len(missing)} -> {missing}")

if __name__ == "__main__":
    main()
