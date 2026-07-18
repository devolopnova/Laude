"""Inserta navegacion "categoria anterior / siguiente" al pie de cada pagina
de categoria, basandose en el orden real de los chips de cada franja de edad
en guia-regalos-juguetes.html (bands[].chips filtrado por bands[].chipPages).

Uso: python tools/add_cat_pager.py [--dry-run]
"""
import re, sys

SRC = "guia-regalos-juguetes.html"

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
        chips_m = re.search(r"chips:\[(.*?)\]", text, re.S)
        chips = re.findall(r"'((?:[^'\\]|\\.)*)'", chips_m.group(1)) if chips_m else []
        pages_m = re.search(r"chipPages:\{(.*?)\n\s*\},", text, re.S)
        pages = {}
        if pages_m:
            for km in re.finditer(r"'((?:[^'\\]|\\.)*)':'((?:[^'\\]|\\.)*)'", pages_m.group(1)):
                pages[km.group(1)] = km.group(2)
        ordered = [(c, pages[c]) for c in chips if c in pages]
        bands.append((bid, ordered))
    return bands

def pager_html(prev_pair, next_pair):
    prev_link = f'<a class="cat-pager-link prev" href="{prev_pair[1]}">← {prev_pair[0]}</a>' if prev_pair else ''
    next_link = f'<a class="cat-pager-link next" href="{next_pair[1]}">{next_pair[0]} →</a>' if next_pair else ''
    return f'<nav class="cat-pager wrap">\n  {prev_link}\n  {next_link}\n</nav>\n\n'

def main():
    dry = "--dry-run" in sys.argv
    bands = parse_bands()
    updated, skipped_missing, skipped_existing = [], [], []
    for bid, ordered in bands:
        for i, (label, page) in enumerate(ordered):
            try:
                content = open(page, encoding="utf-8").read()
            except FileNotFoundError:
                skipped_missing.append(page)
                continue
            if 'class="cat-pager' in content:
                skipped_existing.append(page)
                continue
            if '<footer class="wrap">' not in content:
                skipped_missing.append(page + " (sin <footer class=\"wrap\">)")
                continue
            prev_pair = ordered[i-1] if i > 0 else None
            next_pair = ordered[i+1] if i < len(ordered)-1 else None
            nav = pager_html(prev_pair, next_pair)
            new_content = content.replace('<footer class="wrap">', nav + '<footer class="wrap">', 1)
            if not dry:
                open(page, "w", encoding="utf-8").write(new_content)
            updated.append(page)
    print(f"actualizadas: {len(updated)}")
    if skipped_existing:
        print(f"ya tenian pager, omitidas: {len(skipped_existing)} -> {skipped_existing}")
    if skipped_missing:
        print(f"con problemas: {len(skipped_missing)} -> {skipped_missing}")

if __name__ == "__main__":
    main()
