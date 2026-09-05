#!/usr/bin/env python3
"""
build_comparativa_prototipo_v3.py

Prototipo v3 de la comparativa de sillitas de coche. Parte del prototipo
v2 (ver snapshot tools/build_comparativa_prototipo_v2.snapshot.py /
prototipo-comparativa-sillas-v2.snapshot.html) y aplica solo cambios de
PRESENTACION pedidos por el usuario. No re-extrae Amazon/fabricante, no
toca amazon_import.py, no modifica tools/output/lote1_final.json ni la
clasificacion de ningun producto.

Cambios v2 -> v3:
1. Nueva columna "Grupo" (R44: 0+/1/2/3...) en la fila principal, tomada
   tal cual de clasificacion.grupo_r44 (nunca inferida de edad/peso/altura,
   nunca convertida desde R129/i-Size).
2. "Giratoria 360º" sube a la fila principal como indicador visible
   (antes vivia solo en la ficha tecnica). Ya no se duplica en la ficha
   tecnica.
3. Fila principal: Producto | Precio | Valoracion | Edad | Grupo | ISOFIX
   | Orientacion | 360º | CTA.
4. Se elimina el uso de guiones ("-", "N/A") como sustituto visual de
   "dato auditado pero no determinado". La funcion fmt() ahora devuelve
   el texto "Sin especificar" en ese caso, igual que ya hacen la mayoria
   de campos en el JSON (que ya traen literalmente mostrar="Sin
   especificar"); solo remapea los pocos casos que aun quedaban como
   "No determinado" en crudo.
5. Ficha tecnica ya no incluye Grupo/Edad/Orientacion/360º (ahora en la
   fila principal, ver regla de "no duplicar" del usuario) y mantiene:
   Altura R129, Peso recomendado, Homologacion, Tipo de instalacion,
   Reclinable, Reposacabezas, Arnes, Peso silla, Proteccion lateral,
   Funda lavable.

Uso:
    python tools/build_comparativa_prototipo_v3.py
"""

import json
import html as html_lib

SRC = "tools/output/lote1_final.json"
OUT = "prototipo-comparativa-sillas-v3.html"

SIN_ESPECIFICAR = "Sin especificar"


def fmt(campo):
    """Nunca usa guiones/N.A. como estado visual. 'auditado mas no
    determinado' se muestra siempre como 'Sin especificar' -- ya sea
    porque el campo entero no existe, porque mostrar es None, o porque
    el texto crudo todavia dice 'No determinado'/'no confirmado'/
    'posible variante'. El resto de valores (incluido un 'Sin
    especificar' o 'Revisar' que ya venga literal en el JSON) se
    muestran tal cual, sin tocarlos."""
    if not campo:
        return SIN_ESPECIFICAR
    mostrar = campo.get("mostrar")
    if not mostrar:
        return SIN_ESPECIFICAR
    low = mostrar.lower()
    if "no determinado" in low or "no confirmado" in low or "posible variante" in low:
        return SIN_ESPECIFICAR
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
    ("Reposacabezas", "reposacabezas"),
    ("Arnés", "arnes"),
    ("Peso silla", "peso_silla"),
    ("Protección lateral", "proteccion_lateral"),
    ("Funda lavable", "funda_lavable"),
]


def badge_360(valor):
    if valor == "Sí":
        return '<span class="badge-360 badge-360--yes">↻ 360º</span>'
    if valor == "No":
        return '<span class="badge-360 badge-360--no">No 360º</span>'
    return f'<span class="badge-360 badge-360--unk">{html_lib.escape(valor)}</span>'


def build_row(p, idx):
    c = p["clasificacion"]
    marca = p.get("marca") or SIN_ESPECIFICAR
    modelo = p.get("modelo") or p.get("titulo_amazon") or SIN_ESPECIFICAR
    modelo_corto = modelo if len(modelo) <= 70 else modelo[:67] + "…"

    precio_actual = fmt_precio(p["precio"].get("actual"))
    precio_anterior = fmt_precio(p["precio"].get("anterior"))

    puntuacion = fmt_valoracion_estrellas(p["valoraciones"].get("puntuacion"))
    num_valoraciones = fmt_numero_valoraciones(p["valoraciones"].get("numero"))

    url = p.get("url") or "#"

    precio_html = (
        f'<span class="price-current">{precio_actual}</span>'
        if precio_actual else f'<span class="cell-unspecified">{SIN_ESPECIFICAR}</span>'
    )
    if precio_actual and precio_anterior:
        precio_html += f'<span class="price-old">{precio_anterior}</span>'

    if puntuacion:
        val_html = f'<span class="rating-star">★ {puntuacion}</span>'
        if num_valoraciones:
            val_html += f'<span class="rating-count">{num_valoraciones} valoraciones</span>'
    else:
        val_html = f'<span class="cell-unspecified">{SIN_ESPECIFICAR}</span>'

    img_block = f'<div class="prod-thumb-ph">{iniciales(marca)}</div>'

    def td(value, extra_class=""):
        unspecified = value == SIN_ESPECIFICAR
        cls = " ".join(x for x in [extra_class, "cell-unspecified" if unspecified else ""] if x)
        cls_attr = f' class="{cls}"' if cls else ""
        return f"<td{cls_attr}>{html_lib.escape(value)}</td>"

    detail_items = "\n".join(
        f'<div class="detail-item"><span class="detail-label">{html_lib.escape(label)}</span>'
        f'<span class="detail-value{" cell-unspecified" if fmt(c.get(key)) == SIN_ESPECIFICAR else ""}">{html_lib.escape(fmt(c.get(key)))}</span></div>'
        for label, key in SECONDARY_FIELDS
    )

    panel_id = f"detail-{idx}"

    grupo_val = fmt(c.get("grupo_r44"))
    giro_val = fmt(c.get("giro_360"))

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
      {td(grupo_val, "col-grupo")}
      {td(fmt(c["isofix"]))}
      {td(fmt(c["orientacion"]))}
      <td class="col-360">{badge_360(giro_val)}</td>
      <td class="col-action">
        <a class="btn-amazon" href="{html_lib.escape(url)}" target="_blank" rel="nofollow sponsored noopener">Ver en Amazon →</a>
        <button class="btn-toggle" type="button" data-toggle="{panel_id}">Ficha técnica ▾</button>
      </td>
    </tr>"""

    detail_row = f"""
    <tr class="detail-row" id="{panel_id}" hidden>
      <td colspan="9">
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
    ("Grupo", "col-grupo"),
    ("ISOFIX", ""),
    ("Orientación", ""),
    ("360º", "col-360"),
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
<title>PROTOTIPO v3 — Comparativa sillitas de coche</title>
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
.proto-note{{max-width:780px;font-size:13px;color:var(--ink-soft);margin-bottom:28px;line-height:1.6;}}
.proto-note code{{background:#F0EEE8;padding:1px 5px;border-radius:4px;font-size:12px;}}
.proto-note ul{{margin:8px 0 0 18px;}}

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

td.col-product{{min-width:250px;max-width:300px;white-space:normal;}}

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

td.col-grupo{{min-width:90px;}}

.cell-unspecified{{color:#9C9A93;font-weight:400;font-style:italic;font-size:13px;}}

td.col-360{{min-width:120px;}}
.badge-360{{display:inline-block;font-size:12px;font-weight:700;padding:5px 10px;border-radius:999px;white-space:nowrap;}}
.badge-360--yes{{background:#EAF3EC;color:#2F7A45;border:1px solid #BEE0C6;}}
.badge-360--no{{background:#F4F2EE;color:var(--ink-soft);border:1px solid var(--line);font-weight:600;}}
.badge-360--unk{{background:transparent;color:#9C9A93;font-weight:400;font-style:italic;font-size:12px;padding:5px 0;}}

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

<div class="proto-banner">⚠ Prototipo v3 — <b>no es la web real</b> — datos de tools/output/lote1_final.json tal cual, sin re-extraer</div>
<p class="proto-note">
  Cambios respecto a v2:
  <ul>
    <li><b>Grupo</b> (R44: 0+/1/2/3…) añadido a la fila principal — leído tal cual de <code>clasificacion.grupo_r44</code>, nunca inferido de edad/peso/altura ni derivado de R129/i-Size. En este lote no hay ningún producto con grupo R44 clasificado todavía, por eso las 15 filas muestran "Sin especificar" en esta columna — es un hueco de clasificación pendiente, no un fallo de este prototipo.</li>
    <li><b>Giratoria 360º</b> sube de la ficha técnica a la fila principal como indicador (badge verde "↻ 360º" / gris "No 360º" / "Sin especificar"), ya no se repite en la ficha técnica.</li>
    <li>Se elimina el guion "—" como estado editorial: cualquier dato auditado pero no determinado se muestra como <b>"Sin especificar"</b> (cursiva gris), nunca como guion ni "N/A".</li>
  </ul>
</p>

<div class="page-head">
  <div class="eyebrow">Comparador de sillitas de coche</div>
  <h1>Comparativa de sillitas de coche</h1>
  <p>15 modelos</p>
</div>

<div class="filters">
  <span class="filter-pill">Precio</span>
  <span class="filter-pill">Edad</span>
  <span class="filter-pill">Grupo</span>
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

<p class="foot-note">Prototipo generado por tools/build_comparativa_prototipo_v3.py — no modifica ningún archivo de producción ni la clasificación de los productos.</p>

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
