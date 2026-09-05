#!/usr/bin/env python3
"""
build_comparativa_prototipo_v2.py

Prototipo v2 de la comparativa de sillitas de coche, a partir de lo
aprendido evaluando el prototipo v1 (tools/build_comparativa_prototipo.py):
con las 20 columnas originales en una tabla plana, en un viewport de
escritorio estandar (1280px) solo 7 columnas eran visibles sin scroll
horizontal, y 3 columnas resultaron inutiles para este lote (Travel
system: 0/15 con dato; grupo_r44/"clasificacion": 0/15 con dato, porque
las 15 sillas son R129/i-Size, no R44; Marca: duplicada, ya se muestra en
la celda de producto).

v2 separa las columnas en dos grupos:
- Esenciales (fijas, sin scroll): Producto, Precio, Valoracion, Edad,
  ISOFIX, Orientacion, CTA.
- Secundarias (panel desplegable por fila, "Ver ficha tecnica"): Altura
  R129, Peso recomendado, Homologacion, Tipo de instalacion, Reclinable,
  Giratoria 360, Reposacabezas, Arnes, Peso silla, Proteccion lateral,
  Funda lavable.

No modifica ningun archivo de produccion ni el extractor.

Uso:
    python tools/build_comparativa_prototipo_v2.py
"""

import json
import html as html_lib

SRC = "tools/output/lote1_final.json"
OUT = "prototipo-comparativa-sillas-v2.html"


def fmt(campo):
    if not campo:
        return "—"
    mostrar = campo.get("mostrar")
    if not mostrar:
        return "—"
    low = mostrar.lower()
    if "no determinado" in low or "no confirmado" in low or "posible variante" in low:
        return "—"
    return mostrar


def fmt_precio(valor):
    if valor is None or valor == "N/A":
        return None
    return f"{valor:.2f}".replace(".", ",") + " €"


def fmt_valoracion_estrellas(puntuacion):
    if puntuacion is None:
        return None
    return str(puntuacion).replace(".", ",")


def fmt_numero_valoraciones(n):
    if n is None:
        return None
    return f"{n:,}".replace(",", ".")


def iniciales(marca):
    palabras = (marca or "?").split()
    return "".join(w[0] for w in palabras[:2]).upper()


SECONDARY_FIELDS = [
    ("Altura R129", "altura_r129"),
    ("Peso recomendado", "peso"),
    ("Homologación", "normativa"),
    ("Tipo de instalación", "tipo_instalacion"),
    ("Reclinable", "reclinable"),
    ("Giratoria 360º", "giro_360"),
    ("Reposacabezas", "reposacabezas"),
    ("Arnés / protección", "arnes"),
    ("Peso silla", "peso_silla"),
    ("Protección lateral", "proteccion_lateral"),
    ("Funda lavable", "funda_lavable"),
]


def build_row(p, idx):
    c = p["clasificacion"]
    asin = p["asin"]
    marca = p.get("marca") or "—"
    modelo = p.get("modelo") or p.get("titulo_amazon") or "—"
    modelo_corto = modelo if len(modelo) <= 70 else modelo[:67] + "…"

    precio_actual = fmt_precio(p["precio"].get("actual"))
    precio_anterior = fmt_precio(p["precio"].get("anterior"))

    puntuacion = fmt_valoracion_estrellas(p["valoraciones"].get("puntuacion"))
    num_valoraciones = fmt_numero_valoraciones(p["valoraciones"].get("numero"))

    url = p.get("url") or "#"

    precio_html = (
        f'<span class="price-current">{precio_actual}</span>'
        if precio_actual else '<span class="cell-empty">—</span>'
    )
    if precio_actual and precio_anterior:
        precio_html += f'<span class="price-old">{precio_anterior}</span>'

    if puntuacion:
        val_html = f'<span class="rating-star">★ {puntuacion}</span>'
        if num_valoraciones:
            val_html += f'<span class="rating-count">{num_valoraciones} valoraciones</span>'
    else:
        val_html = '<span class="cell-empty">—</span>'

    img_block = f'<div class="prod-thumb-ph">{iniciales(marca)}</div>'

    def td(value, extra_class=""):
        empty = value == "—"
        cls = " ".join(x for x in [extra_class, "cell-empty" if empty else ""] if x)
        cls_attr = f' class="{cls}"' if cls else ""
        return f"<td{cls_attr}>{html_lib.escape(value)}</td>"

    detail_items = "\n".join(
        f'<div class="detail-item"><span class="detail-label">{html_lib.escape(label)}</span>'
        f'<span class="detail-value{" cell-empty" if fmt(c.get(key)) == "—" else ""}">{html_lib.escape(fmt(c.get(key)))}</span></div>'
        for label, key in SECONDARY_FIELDS
    )

    panel_id = f"detail-{idx}"

    main_row = f"""
    <tr class="main-row" data-target="{panel_id}">
      <td class="col-product">
        <div class="prod-cell">
          {img_block}
          <div class="prod-info">
            <span class="prod-brand">{html_lib.escape(marca)}</span>
            <span class="prod-model" title="{html_lib.escape(modelo)}">{html_lib.escape(modelo_corto)}</span>
          </div>
        </div>
      </td>
      <td class="col-price">{precio_html}</td>
      <td class="col-rating">{val_html}</td>
      {td(fmt(c["edad"]))}
      {td(fmt(c["isofix"]))}
      {td(fmt(c["orientacion"]))}
      <td class="col-action">
        <a class="btn-amazon" href="{html_lib.escape(url)}" target="_blank" rel="nofollow sponsored noopener">Ver en Amazon →</a>
        <button class="btn-toggle" type="button" data-toggle="{panel_id}">Ficha técnica ▾</button>
      </td>
    </tr>"""

    detail_row = f"""
    <tr class="detail-row" id="{panel_id}" hidden>
      <td colspan="7">
        <div class="detail-grid">
          {detail_items}
        </div>
      </td>
    </tr>"""

    return main_row + detail_row


COLUMN_HEADERS = [
    ("Producto", "col-product"),
    ("Precio", "col-price"),
    ("Valoración", "col-rating"),
    ("Edad", ""),
    ("ISOFIX", ""),
    ("Orientación", ""),
    ("", "col-action"),
]


def main():
    with open(SRC, encoding="utf-8") as f:
        data = json.load(f)
    productos = data["productos"]

    rows_html = "\n".join(build_row(p, i) for i, p in enumerate(productos))
    headers_html = "\n".join(
        f'<th class="{cls}">{html_lib.escape(label)}</th>' for label, cls in COLUMN_HEADERS
    )

    html_out = f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<title>PROTOTIPO v2 — Comparativa sillitas de coche</title>
<meta name="robots" content="noindex,nofollow">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Fredoka:wght@600&family=JetBrains+Mono:wght@600&display=swap" rel="stylesheet">
<style>
:root{{
  --bg:#FAFAF8; --ink:#1C1C1E; --ink-soft:#6B6B70; --line:#E4E2DC; --card:#FFFFFF;
  --accent:#FF8A65; --accent-deep:#D85A30;
}}
*{{margin:0;padding:0;box-sizing:border-box;}}
body{{background:var(--bg);color:var(--ink);font-family:'Inter',sans-serif;line-height:1.5;-webkit-font-smoothing:antialiased;padding:40px 32px 80px;}}
h1,h2,h3{{font-family:'Fredoka',sans-serif;font-weight:600;letter-spacing:-0.01em;}}

.proto-banner{{background:#2C2C2A;color:#fff;font-family:'JetBrains Mono',monospace;font-size:12px;font-weight:600;letter-spacing:.04em;text-transform:uppercase;padding:10px 18px;border-radius:8px;display:inline-block;margin-bottom:14px;}}
.proto-banner b{{color:#FFB199;}}
.proto-note{{max-width:760px;font-size:13px;color:var(--ink-soft);margin-bottom:28px;line-height:1.6;}}
.proto-note code{{background:#F0EEE8;padding:1px 5px;border-radius:4px;font-size:12px;}}

.page-head{{margin-bottom:28px;}}
.eyebrow{{font-family:'JetBrains Mono',monospace;font-size:12px;font-weight:600;color:var(--accent-deep);letter-spacing:.06em;text-transform:uppercase;margin-bottom:10px;}}
.page-head h1{{font-size:30px;margin-bottom:6px;}}
.page-head p{{color:var(--ink-soft);font-size:14.5px;}}

.filters{{display:flex;flex-wrap:wrap;gap:10px;margin-bottom:20px;}}
.filter-pill{{background:var(--card);border:1px solid var(--line);border-radius:8px;padding:9px 14px;font-size:13px;font-weight:500;color:var(--ink);display:flex;align-items:center;gap:6px;cursor:default;user-select:none;}}
.filter-pill:after{{content:"▾";color:var(--ink-soft);font-size:10px;}}
.filter-note{{font-size:12px;color:var(--ink-soft);align-self:center;font-style:italic;}}

.table-shell{{border:1px solid var(--line);border-radius:12px;overflow:hidden;background:var(--card);box-shadow:0 1px 3px rgba(0,0,0,.04);}}

table{{border-collapse:separate;border-spacing:0;width:100%;}}

thead th{{
  background:#F4F2EE; color:var(--ink); font-size:12px; font-weight:700;
  text-transform:uppercase; letter-spacing:.03em;
  padding:14px 16px; text-align:left; white-space:nowrap;
  border-bottom:1px solid var(--line); border-right:1px solid var(--line);
}}
thead th:last-child{{border-right:none;}}

tbody td{{
  padding:14px 16px; font-size:14px; color:var(--ink);
  border-bottom:1px solid var(--line); border-right:1px solid var(--line);
  vertical-align:middle; white-space:nowrap;
}}
tbody tr.main-row:last-of-type td{{border-bottom:none;}}
tbody tr.main-row:hover td{{background:#FBF6F1;cursor:pointer;}}
tbody tr.main-row:nth-of-type(4n+1) td{{background:#FCFCFA;}}
tbody tr.main-row:nth-of-type(4n+1):hover td{{background:#FBF6F1;}}

td.col-product{{min-width:260px;max-width:320px;white-space:normal;}}

.prod-cell{{display:flex;align-items:center;gap:12px;}}
.prod-thumb-ph{{
  width:52px;height:52px;border-radius:8px;background:linear-gradient(135deg,#F4F2EE,#E9E6DF);
  display:flex;align-items:center;justify-content:center;flex-shrink:0;
  font-family:'JetBrains Mono',monospace;font-weight:700;font-size:13px;color:var(--ink-soft);
  border:1px solid var(--line);
}}
.prod-info{{display:flex;flex-direction:column;gap:2px;min-width:0;}}
.prod-brand{{font-size:12px;font-weight:700;color:var(--accent-deep);text-transform:uppercase;letter-spacing:.02em;}}
.prod-model{{font-size:13.5px;font-weight:600;color:var(--ink);white-space:normal;line-height:1.3;}}

td.col-price{{min-width:110px;}}
.price-current{{display:block;font-size:15px;font-weight:700;color:var(--ink);}}
.price-old{{display:block;font-size:12px;color:var(--ink-soft);text-decoration:line-through;margin-top:2px;}}

td.col-rating{{min-width:150px;}}
.rating-star{{display:block;font-size:14px;font-weight:700;color:#B8860B;}}
.rating-count{{display:block;font-size:11.5px;color:var(--ink-soft);margin-top:2px;font-weight:400;}}

.cell-empty{{color:#C7C4BC;font-weight:400;}}

td.col-action{{min-width:160px;white-space:normal;}}
.btn-amazon{{
  display:inline-block;background:var(--accent-deep);color:#fff;font-size:12.5px;font-weight:700;
  padding:9px 14px;border-radius:7px;white-space:nowrap;transition:background .15s;margin-bottom:6px;
}}
.btn-amazon:hover{{background:#B5471F;}}
.btn-toggle{{
  display:block;background:none;border:1px solid var(--line);color:var(--ink-soft);
  font-size:12px;font-weight:600;padding:6px 12px;border-radius:7px;cursor:pointer;
  font-family:'Inter',sans-serif;transition:.15s;
}}
.btn-toggle:hover, .btn-toggle.is-open{{border-color:var(--accent-deep);color:var(--accent-deep);}}

tr.detail-row td{{padding:0;border-right:none;}}
tr.detail-row[hidden]{{display:none;}}
.detail-grid{{
  display:grid;grid-template-columns:repeat(4,1fr);gap:16px 24px;
  background:#FBF9F5;padding:20px 24px;border-bottom:1px solid var(--line);
}}
.detail-item{{display:flex;flex-direction:column;gap:3px;white-space:normal;}}
.detail-label{{font-size:11px;font-weight:700;color:var(--ink-soft);text-transform:uppercase;letter-spacing:.03em;}}
.detail-value{{font-size:13.5px;color:var(--ink);font-weight:500;}}

.foot-note{{margin-top:18px;font-size:12px;color:var(--ink-soft);}}
</style>
</head>
<body>

<div class="proto-banner">⚠ Prototipo v2 — <b>no es la web real</b> — datos de tools/output/lote1_final.json tal cual</div>
<p class="proto-note">
  v2, tras medir el v1: en un viewport de 1280px solo 7 de 20 columnas eran
  visibles sin hacer scroll horizontal. Aquí las 7 columnas esenciales
  (Producto, Precio, Valoración, Edad, ISOFIX, Orientación, CTA) quedan
  fijas y sin scroll; el resto vive en el panel <code>Ficha técnica ▾</code>
  de cada fila. Se han eliminado 3 columnas del v1 sin valor real en este
  lote: <b>Travel system</b> (0/15 con dato), <b>Marca</b> (duplicada — ya
  aparece en la celda de producto) y <b>Clasificación/grupo R44</b> (0/15
  con dato: las 15 sillas son R129/i-Size, no R44).
</p>

<div class="page-head">
  <div class="eyebrow">Comparador de sillitas de coche</div>
  <h1>Comparativa de sillitas de coche</h1>
  <p>15 modelos</p>
</div>

<div class="filters">
  <span class="filter-pill">Precio</span>
  <span class="filter-pill">Edad</span>
  <span class="filter-pill">ISOFIX</span>
  <span class="filter-pill">Orientación</span>
  <span class="filter-pill">Giratoria 360º</span>
  <span class="filter-pill">Marca</span>
  <span class="filter-pill">Valoración</span>
  <span class="filter-note">(filtros de prueba, sin funcionalidad todavía)</span>
</div>

<div class="table-shell">
    <table>
      <thead>
        <tr>
          {headers_html}
        </tr>
      </thead>
      <tbody>
        {rows_html}
      </tbody>
    </table>
</div>

<p class="foot-note">Prototipo generado por tools/build_comparativa_prototipo_v2.py — no modifica ningún archivo de producción.</p>

<script>
document.querySelectorAll('.btn-toggle').forEach(btn => {{
  btn.addEventListener('click', (e) => {{
    e.stopPropagation();
    const panel = document.getElementById(btn.dataset.toggle);
    const isOpen = !panel.hasAttribute('hidden');
    if (isOpen) {{ panel.setAttribute('hidden', ''); btn.classList.remove('is-open'); btn.textContent = 'Ficha técnica ▾'; }}
    else {{ panel.removeAttribute('hidden'); btn.classList.add('is-open'); btn.textContent = 'Ficha técnica ▴'; }}
  }});
}});
document.querySelectorAll('tr.main-row').forEach(row => {{
  row.addEventListener('click', () => {{
    row.querySelector('.btn-toggle').click();
  }});
}});
</script>

</body>
</html>
"""

    with open(OUT, "w", encoding="utf-8") as f:
        f.write(html_out)
    print(f"OK: {OUT} generado con {len(productos)} productos.")


if __name__ == "__main__":
    main()
