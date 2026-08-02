"""Instala el snippet de Google Analytics 4 (gtag.js) en el <head> de todas
las páginas HTML públicas del proyecto (raíz del repo).

No existe ningún sistema de plantilla/include compartido para el <head> en
este proyecto (cada .html es un documento independiente), así que la
instalación se hace página por página, insertando el snippet justo después
de la etiqueta de apertura <head>, tal y como recomienda Google.

Excluye tools/*.html porque son fragmentos de referencia (plantillas de
componente) sin <html>/<head> propio, no páginas navegables.

Uso: python tools/install_ga4.py
"""
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parent.parent
MEASUREMENT_ID = "G-88T9H9C650"

SNIPPET_LINES = [
    f'<script async src="https://www.googletagmanager.com/gtag/js?id={MEASUREMENT_ID}"></script>',
    "<script>",
    "  window.dataLayer = window.dataLayer || [];",
    "  function gtag(){dataLayer.push(arguments);}",
    "  gtag('js', new Date());",
    "",
    f"  gtag('config', '{MEASUREMENT_ID}');",
    "</script>",
]

HEAD_OPEN_RE = re.compile(r"(<head[^>]*>)(\r?\n)([ \t]*)")


def build_snippet(indent: str) -> str:
    return "".join(f"{indent}{line}\n" for line in SNIPPET_LINES)


def main():
    html_files = sorted(p for p in ROOT.glob("*.html") if p.is_file())

    changed, already_had, skipped_no_head, ga_or_gtm_hits = [], [], [], []

    for path in html_files:
        text = path.read_text(encoding="utf-8")

        if "googletagmanager.com/gtag/js" in text or "googletagmanager.com/gtm.js" in text or MEASUREMENT_ID in text:
            already_had.append(path.name)
            continue

        m = HEAD_OPEN_RE.search(text)
        if not m:
            skipped_no_head.append(path.name)
            continue

        indent = m.group(3)
        snippet = build_snippet(indent)
        insert_at = m.end(2)  # justo tras el salto de línea que sigue a <head>
        new_text = text[:insert_at] + snippet + text[insert_at:]

        path.write_text(new_text, encoding="utf-8")
        changed.append(path.name)

    print(f"Modificados: {len(changed)}")
    for n in changed:
        print(f"  + {n}")
    if already_had:
        print(f"\nYa tenían GA/GTM (sin tocar): {len(already_had)}")
        for n in already_had:
            print(f"  = {n}")
    if skipped_no_head:
        print(f"\nSin <head> detectable (omitidos): {len(skipped_no_head)}")
        for n in skipped_no_head:
            print(f"  ! {n}")

    print(f"\nTotal páginas HTML en raíz: {len(html_files)}")


if __name__ == "__main__":
    main()
