"""Genera /sitemap.xml a partir de las páginas HTML públicas del proyecto.

Uso: python tools/generate_sitemap.py

Reglas (ver tarea de Search Console / CLAUDE.md):
- Home (guia-regalos-juguetes.html) se publica como https://www.lauderem.com/
  (nunca como .../guia-regalos-juguetes.html), acorde al rewrite de vercel.json.
- Excluye páginas de prueba/preview que no están enlazadas desde el sitio
  público (footer-preview.html, simulacion-fotos-edades.html) y cualquier
  cosa fuera de la raíz (tools/, css/, images/).
- priority/changefreq por tipo de página; lastmod = fecha de modificación
  real del archivo en disco.
"""
import datetime
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
DOMAIN = "https://www.lauderem.com"

HOME_FILE = "guia-regalos-juguetes.html"

# Páginas de prueba / preview, nunca enlazadas desde el sitio público.
EXCLUDE = {
    "footer-preview.html",
    "simulacion-fotos-edades.html",
}

# Prefijos de páginas de prueba/preview cuyo número de versión cambia
# constantemente (p.ej. iteraciones del prototipo de comparativa de
# sillas de coche, todavía en desarrollo: ver memoria
# project_sillas_coche_comparador_prototipo.md). Se excluyen por prefijo
# en vez de listarlas una a una para no tener que tocar este archivo en
# cada nueva iteración.
EXCLUDE_PREFIXES = (
    "prototipo-comparativa-sillas",
)

# Páginas "guía" (contenido pilar, no ficha de categoría de producto).
GUIDES = {
    "guia-montessori.html",
    "vida-en-familia.html",
    "comprar-mejor.html",
    "organizacion-y-hogar.html",
    "cumpleanos-y-celebraciones.html",
    "lectura-y-cultura-infantil.html",
    "pantallas-y-ocio.html",
    "viajes-y-vacaciones.html",
    "consumo-responsable.html",
    "guia-0-6-meses.html",
    "guia-6-12-meses.html",
    "guia-1-ano.html",
    "guia-2-anos.html",
    "guia-3-anos.html",
    "guia-4-anos.html",
    "guia-5-anos.html",
    "guia-6-anos.html",
    "guia-7-anos.html",
    "guia-8-anos.html",
    "guia-9-anos.html",
    "guia-10-anos.html",
    "puzzle-3d.html",
    "puzzles-y-rompecabezas.html",
    "puzzles-3d-madera.html",
    "puzzles-3d-animales-dinosaurios.html",
    "puzzles-3d-harry-potter.html",
    "puzzles-3d-star-wars.html",
    "puzzles-3d-superheroes.html",
    "puzzles-3d-pokemon.html",
    "puzzles-3d-disney.html",
    "puzzles-3d-torre-eiffel.html",
    "puzzles-3d-big-ben.html",
    "puzzles-3d-camp-nou.html",
    "puzzles-3d-bernabeu.html",
    "puzzles-3d-coches-deportivos.html",
    "puzzles-3d-titanic.html",
    "puzzles-3d-ravensburger.html",
    "juguetes-montessori.html",
    "juguetes-montessori-6-12-meses.html",
    "juguetes-montessori-1-ano.html",
    "juguetes-montessori-2-anos.html",
    "juguetes-montessori-3-anos.html",
    "juguetes-montessori-4-6-anos.html",
}

# Páginas legales / institucionales (no son ni home, ni guía, ni categoría).
LEGAL = {
    "afiliacion-y-transparencia.html",
    "aviso-legal.html",
    "contacto.html",
    "politica-de-cookies.html",
    "politica-de-privacidad.html",
    "sobre-nosotros.html",
}


def classify(name: str):
    if name == HOME_FILE:
        return 1.0, "weekly"
    if name in GUIDES:
        return 0.9, "monthly"
    if name in LEGAL:
        return 0.2, "yearly"
    return 0.8, "monthly"


def public_url(name: str) -> str:
    if name == HOME_FILE:
        return f"{DOMAIN}/"
    return f"{DOMAIN}/{name}"


def lastmod_of(path: pathlib.Path) -> str:
    ts = path.stat().st_mtime
    return datetime.datetime.fromtimestamp(ts, tz=datetime.timezone.utc).strftime("%Y-%m-%d")


def main():
    html_files = sorted(
        p for p in ROOT.glob("*.html")
        if p.is_file()
        and p.name not in EXCLUDE
        and not p.name.startswith(EXCLUDE_PREFIXES)
    )

    entries = []
    for p in html_files:
        priority, changefreq = classify(p.name)
        entries.append({
            "loc": public_url(p.name),
            "lastmod": lastmod_of(p),
            "changefreq": changefreq,
            "priority": priority,
            "is_home": p.name == HOME_FILE,
        })

    # Home primero, luego orden alfabético por URL.
    entries.sort(key=lambda e: (not e["is_home"], e["loc"]))

    lines = ['<?xml version="1.0" encoding="UTF-8"?>']
    lines.append('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">')
    for e in entries:
        lines.append("  <url>")
        lines.append(f"    <loc>{e['loc']}</loc>")
        lines.append(f"    <lastmod>{e['lastmod']}</lastmod>")
        lines.append(f"    <changefreq>{e['changefreq']}</changefreq>")
        lines.append(f"    <priority>{e['priority']:.1f}</priority>")
        lines.append("  </url>")
    lines.append("</urlset>")

    out_path = ROOT / "sitemap.xml"
    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"sitemap.xml generado con {len(entries)} URLs -> {out_path}")


if __name__ == "__main__":
    main()
