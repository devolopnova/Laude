"""Inserta <link rel="canonical"> en el <head> de todas las páginas HTML
públicas del proyecto (raíz del repo), justo después de <title>.

Cada página apunta a su propia URL absoluta bajo el dominio canónico:
- guia-regalos-juguetes.html -> https://www.lauderem.com/ (es la home,
  acorde al rewrite de vercel.json; nunca .../guia-regalos-juguetes.html)
- el resto -> https://www.lauderem.com/<archivo>.html

Excluye tools/*.html porque son fragmentos de referencia sin <head>
propio, no páginas navegables.

Uso: python tools/add_canonical.py
"""
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parent.parent
DOMAIN = "https://www.lauderem.com"
HOME_FILE = "guia-regalos-juguetes.html"

TITLE_RE = re.compile(r"([ \t]*)(<title>.*?</title>)(\r?\n)")


def canonical_url(name: str) -> str:
    if name == HOME_FILE:
        return f"{DOMAIN}/"
    return f"{DOMAIN}/{name}"


def main():
    html_files = sorted(p for p in ROOT.glob("*.html") if p.is_file())

    changed, already_had, skipped_no_title = [], [], []

    for path in html_files:
        text = path.read_text(encoding="utf-8")

        if 'rel="canonical"' in text:
            already_had.append(path.name)
            continue

        m = TITLE_RE.search(text)
        if not m:
            skipped_no_title.append(path.name)
            continue

        indent = m.group(1)
        url = canonical_url(path.name)
        tag_line = f'{indent}<link rel="canonical" href="{url}">\n'
        insert_at = m.end(3)
        new_text = text[:insert_at] + tag_line + text[insert_at:]

        path.write_text(new_text, encoding="utf-8")
        changed.append(path.name)

    print(f"Modificados: {len(changed)}")
    if already_had:
        print(f"Ya tenían canonical (sin tocar): {len(already_had)} -> {already_had}")
    if skipped_no_title:
        print(f"Sin <title> detectable (omitidos): {len(skipped_no_title)} -> {skipped_no_title}")
    print(f"Total páginas HTML en raíz: {len(html_files)}")


if __name__ == "__main__":
    main()
