"""Instala el widget de CookieScript en el <head> de todas las paginas HTML
publicas del proyecto (raiz del repo), como PRIMER <script> dentro de
<head> (antes que el snippet de GA4 y cualquier otro).

No existe ningun sistema de plantilla/include compartido para el <head> en
este proyecto (cada .html es un documento independiente), asi que la
instalacion se hace pagina por pagina, igual que tools/install_ga4.py.

Ademas, en las paginas que ya tienen un footer real con enlaces legales
(nav .footer-links + acordeon .footer-informacion), añade un enlace
"Preferencias de cookies" que reabre el widget via
CookieScript.instance.show().

Excluye tools/*.html porque son fragmentos de referencia (plantillas de
componente) sin <html>/<head> propio, no paginas navegables.

Uso: python tools/install_cookiescript.py
"""
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parent.parent

SNIPPET = '<script type="text/javascript" charset="UTF-8" src="//cdn.cookie-script.com/s/067dce5e5b2c3eeb8cc1f8f51d3c14a8.js"></script>'

HEAD_OPEN_RE = re.compile(r"(<head[^>]*>)(\r?\n)([ \t]*)")

FOOTER_CHIP_RE = re.compile(
    r'(\s*)(<a class="footer-chip" href="politica-de-cookies\.html">Cookies</a>)'
)
FOOTER_LINK_RE = re.compile(
    r'(\s*)(<a href="politica-de-cookies\.html">Cookies</a>)'
)

PREF_CHIP = '<a class="footer-chip" href="#" onclick="event.preventDefault(); if(window.CookieScript){CookieScript.instance.show();}">Preferencias de cookies</a>'
PREF_LINK = '<a href="#" onclick="event.preventDefault(); if(window.CookieScript){CookieScript.instance.show();}">Preferencias de cookies</a>'


def add_footer_pref_link(text: str) -> tuple[str, bool]:
    added = False

    def repl_chip(m):
        nonlocal added
        added = True
        return f"{m.group(1)}{m.group(2)}{m.group(1)}{PREF_CHIP}"

    def repl_link(m):
        nonlocal added
        added = True
        return f"{m.group(1)}{m.group(2)}{m.group(1)}{PREF_LINK}"

    if "Preferencias de cookies" in text:
        return text, False

    text = FOOTER_CHIP_RE.sub(repl_chip, text, count=1)
    text = FOOTER_LINK_RE.sub(repl_link, text, count=1)
    return text, added


def main():
    html_files = sorted(p for p in ROOT.glob("*.html") if p.is_file())

    changed, already_had, skipped_no_head = [], [], []
    footer_added, footer_skipped = [], []

    for path in html_files:
        text = path.read_text(encoding="utf-8")

        if "cookie-script.com" in text:
            already_had.append(path.name)
            continue

        m = HEAD_OPEN_RE.search(text)
        if not m:
            skipped_no_head.append(path.name)
            continue

        indent = m.group(3)
        snippet_line = f"{indent}{SNIPPET}\n"
        insert_at = m.end(2)
        new_text = text[:insert_at] + snippet_line + text[insert_at:]

        new_text, did_add_footer = add_footer_pref_link(new_text)
        if did_add_footer:
            footer_added.append(path.name)
        else:
            footer_skipped.append(path.name)

        path.write_text(new_text, encoding="utf-8")
        changed.append(path.name)

    print(f"Modificados: {len(changed)}")
    if already_had:
        print(f"\nYa tenian CookieScript (sin tocar): {len(already_had)}")
        for n in already_had:
            print(f"  = {n}")
    if skipped_no_head:
        print(f"\nSin <head> detectable (omitidos): {len(skipped_no_head)}")
        for n in skipped_no_head:
            print(f"  ! {n}")

    print(f"\nEnlace 'Preferencias de cookies' anadido en footer: {len(footer_added)}")
    for n in footer_added:
        print(f"  + {n}")
    print(f"Sin footer legal detectable (sin enlace anadido): {len(footer_skipped)}")

    print(f"\nTotal paginas HTML en raiz: {len(html_files)}")


if __name__ == "__main__":
    main()
