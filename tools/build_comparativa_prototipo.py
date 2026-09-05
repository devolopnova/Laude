#!/usr/bin/env python3
"""
build_comparativa_prototipo.py

Genera una vista de PROTOTIPO (no produccion) de la tabla comparativa de
sillitas de coche, a partir de tools/output/lote1_final.json tal cual esta
hoy. No modifica ningun archivo de la web real, ni amazon_import.py, ni el
extractor. Es un HTML autocontenido (CSS inline, sin dependencias externas)
para poder evaluar densidad de informacion / columnas antes de decidir que
pasa a produccion.

Uso:
    python tools/build_comparativa_prototipo.py
"""

import json
import html as html_lib

SRC = "tools/output/lote1_final.json"
OUT = "prototipo-comparativa-sillas.html"


def fmt(campo):
    """Nunca convierte N/A en 'No': solo se muestra 'No' si el valor
    normalizado es explicitamente False/negativo. Cualquier variante de
    'no determinado'/'no confirmado'/'posible variante' se muestra como
    guion largo, nunca como 'No'."""
    if not campo:
        return "—"
    mostrar = campo.get("mostrar")
    if not mostrar:
        return "—"
    low = mostrar.lower()
    if "no determinado" in low or "no confirmado" in low or "posible variante" in low:
        return "—"
    return mostrar


def fmt_plain(valor):
    if valor is None or valor == "N/A":
        return "—"
    return valor


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


def build_row(p):
    c = p["clasificacion"]
    asin = p["asin"]
    marca = p.get("marca") or "—"
    modelo = p.get("modelo") or p.get("titulo_amazon") or "—"
    modelo_corto = modelo if len(modelo) <= 70 else modelo[:67] + "…"

    precio_actual = fmt_precio(p["precio"].get("actual"))
    precio_anterior = fmt_precio(p["precio"].get("anterior"))

    puntuacion = fmt_valoracion_estrellas(p["valoraciones"].get("puntuacion"))
    num_valoraciones = fmt_numero_valoraciones(p["valoraciones"].get("numero"))

    travel_system = fmt_plain(p["caracteristicas"].get("travel_system"))

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
        cls = f'class="{extra_class} cell-empty"' if empty and extra_class else (
            'class="cell-empty"' if empty else (f'class="{extra_class}"' if extra_class else "")
        )
        return f"<td {cls}>{html_lib.escape(value)}</td>"

    return f"""
    <tr>
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
      {td(fmt(c["peso"]))}
      {td(fmt(c["altura_r129"]))}
      {td(fmt(c["isofix"]))}
      {td(fmt(c["tipo_instalacion"]))}
      {td(fmt(c["orientacion"]))}
      {td(fmt(c["reclinable"]))}
      {td(fmt(c["normativa"]))}
      {td(fmt(c["giro_360"]))}
      {td(fmt(c["reposacabezas"]))}
      {td(fmt(c["arnes"]))}
      {td(fmt(c["peso_silla"]))}
      {td(fmt(c["proteccion_lateral"]))}
      {td(fmt(c["funda_lavable"]))}
      {td(travel_system)}
      <td>{html_lib.escape(marca)}</td>
      <td class="col-action"><a class="btn-amazon" href="{html_lib.escape(url)}" target="_blank" rel="nofollow sponsored noopener">Ver en Amazon →</a></td>
    </tr>"""


COLUMN_HEADERS = [
    ("Producto", "col-product"),
    ("Precio", "col-price"),
    ("Valoración", "col-rating"),
    ("Grupo / edad", ""),
    ("Peso recomendado", ""),
    ("Altura R129", ""),
    ("ISOFIX", ""),
    ("Tipo de instalación", ""),
    ("Orientación", ""),
    ("Reclinable", ""),
    ("Homologación", ""),
    ("Giratoria 360º", ""),
    ("Reposacabezas", ""),
    ("Arnés / protección", ""),
    ("Peso silla", ""),
    ("Protección lateral", ""),
    ("Funda lavable", ""),
    ("Travel system", ""),
    ("Marca", ""),
    ("", "col-action"),
]


def main():
    with open(SRC, encoding="utf-8") as f:
        data = json.load(f)
    productos = data["productos"]

    rows_html = "\n".join(build_row(p) for p in productos)
    headers_html = "\n".join(
        f'<th class="{cls}">{html_lib.escape(label)}</th>' for label, cls in COLUMN_HEADERS
    )

    html_out = f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<title>PROTOTIPO — Comparativa sillitas de coche</title>
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

.proto-banner{{background:#2C2C2A;color:#fff;font-family:'JetBrains Mono',monospace;font-size:12px;font-weight:600;letter-spacing:.04em;text-transform:uppercase;padding:10px 18px;border-radius:8px;display:inline-block;margin-bottom:28px;}}
.proto-banner b{{color:#FFB199;}}

.page-head{{margin-bottom:28px;}}
.eyebrow{{font-family:'JetBrains Mono',monospace;font-size:12px;font-weight:600;color:var(--accent-deep);letter-spacing:.06em;text-transform:uppercase;margin-bottom:10px;}}
.page-head h1{{font-size:30px;margin-bottom:6px;}}
.page-head p{{color:var(--ink-soft);font-size:14.5px;}}

.filters{{display:flex;flex-wrap:wrap;gap:10px;margin-bottom:20px;}}
.filter-pill{{background:var(--card);border:1px solid var(--line);border-radius:8px;padding:9px 14px;font-size:13px;font-weight:500;color:var(--ink);display:flex;align-items:center;gap:6px;cursor:default;user-select:none;}}
.filter-pill:after{{content:"▾";color:var(--ink-soft);font-size:10px;}}
.filter-note{{font-size:12px;color:var(--ink-soft);align-self:center;font-style:italic;}}

.table-shell{{border:1px solid var(--line);border-radius:12px;overflow:hidden;background:var(--card);box-shadow:0 1px 3px rgba(0,0,0,.04);}}
.table-scroll{{overflow-x:auto;overflow-y:visible;max-width:100%;}}

table{{border-collapse:separate;border-spacing:0;width:max-content;min-width:100%;}}

thead th{{
  position:sticky; top:0; z-index:3;
  background:#F4F2EE; color:var(--ink); font-size:12px; font-weight:700;
  text-transform:uppercase; letter-spacing:.03em;
  padding:14px 16px; text-align:left; white-space:nowrap;
  border-bottom:1px solid var(--line); border-right:1px solid var(--line);
}}
thead th.col-product{{left:0; z-index:5;}}
thead th:last-child{{border-right:none;}}

tbody td{{
  padding:14px 16px; font-size:14px; color:var(--ink);
  border-bottom:1px solid var(--line); border-right:1px solid var(--line);
  vertical-align:middle; white-space:nowrap;
}}
tbody tr:last-child td{{border-bottom:none;}}
tbody tr:hover td{{background:#FBF6F1;}}
tbody tr:nth-child(even) td{{background:#FCFCFA;}}
tbody tr:nth-child(even):hover td{{background:#FBF6F1;}}

td.col-product, th.col-product{{
  position:sticky; left:0; z-index:2;
  background:var(--card); min-width:260px; max-width:260px;
  white-space:normal;
}}
tbody tr:nth-child(even) td.col-product{{background:#FCFCFA;}}
tbody tr:hover td.col-product{{background:#FBF6F1;}}
td.col-product{{box-shadow:2px 0 4px rgba(0,0,0,.03);}}

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

td.col-action{{min-width:150px;}}
.btn-amazon{{
  display:inline-block;background:var(--accent-deep);color:#fff;font-size:12.5px;font-weight:700;
  padding:9px 14px;border-radius:7px;white-space:nowrap;transition:background .15s;
}}
.btn-amazon:hover{{background:#B5471F;}}

.foot-note{{margin-top:18px;font-size:12px;color:var(--ink-soft);}}
</style>
</head>
<body>

<div class="proto-banner">⚠ Prototipo visual — <b>no es la web real</b> — datos de tools/output/lote1_final.json tal cual</div>

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
  <div class="table-scroll">
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
</div>

<p class="foot-note">Prototipo generado por tools/build_comparativa_prototipo.py — no modifica ningún archivo de producción.</p>

</body>
</html>
"""

    with open(OUT, "w", encoding="utf-8") as f:
        f.write(html_out)
    print(f"OK: {OUT} generado con {len(productos)} productos.")


if __name__ == "__main__":
    main()
