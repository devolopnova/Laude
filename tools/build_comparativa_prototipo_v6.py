#!/usr/bin/env python3
"""
build_comparativa_prototipo_v6.py

Correccion puntual sobre v5 (ver tools/build_comparativa_prototipo_v5.py)
-- MISMA fuente de datos, MISMA estructura de tabla, MISMO diseno.
Unico cambio: la columna antes llamada "Grupo + Peso" pasa a llamarse
"Rango de uso".

Motivo: el campo "grupo" del dataset (p.ej. "0+/1/2/3") es la
clasificacion tradicional por PESO (asociada a R44), mientras que la
columna "Normativa" de al lado suele decir "R129 / i-Size", que
homologa principalmente por ALTURA. Tenerlas una junto a otra bajo el
encabezado "Grupo" podia leerse como si el grupo fuera parte de la
clasificacion R129, cosa que el dataset nunca afirma. "Rango de uso" es
una etiqueta puramente editorial para presentar juntos grupo (si existe)
+ peso (si existe), sin implicar que sea una clasificacion reglamentaria
de la normativa mostrada al lado. El campo "grupo" del JSON no cambia de
nombre ni de valor -- solo cambia el TEXTO DEL ENCABEZADO en el HTML.

No re-audita, no re-extrae, no toca amazon_import.py ni ningun archivo
de produccion, no modifica tools/output/auditoria_30_candidatos.json.

Uso:
    python tools/build_comparativa_prototipo_v6.py
"""

import html as html_lib
import json
import re

SRC = "tools/output/auditoria_30_candidatos.json"
OUT = "prototipo-comparativa-sillas-v6.html"

SIN_ESPECIFICAR = "Sin especificar"
GUION = "—"

# OPCION A (heredada de v4, sigue vigente): oculta por completo cualquier
# campo secundario de la ficha tecnica cuyo valor sea "Sin especificar".
HIDE_UNSPECIFIED_IN_DETAIL = True


def es_revisar(valor: str) -> bool:
    """Detecta 'Revisar' aunque no vaya al principio del texto (p.ej.
    'Sin especificar con certeza (... -- Revisar)' de DUALFIX2 R). Se
    excluyen notas ya resueltas que citan la palabra dentro de una frase
    de cierre ('confirmado'/'resuelto')."""
    v = (valor or "").strip().lower()
    if v.startswith("revisar"):
        return True
    return "revisar" in v and "confirmado" not in v and "resuelto" not in v


def es_sin_especificar(valor: str) -> bool:
    v = (valor or "").strip()
    if es_revisar(v):
        return False
    return v.lower().startswith("sin especificar")


# Clausula de procedencia/confianza a eliminar de la presentacion (nunca
# del dataset). Cubre los patrones reales encontrados en las 30 fichas:
# "Amazon, confianza media", "Amazon + fabricante, confianza alta",
# "confirmado[/ por fabricante/ en Amazon/ en ficha/ manualmente]",
# "resuelto manualmente", "fabricante_oficial (...)".
_CLAUSE = (
    r'(?:Amazon(?:\s*\+\s*fabricante)?,\s*confianza\s+\w+'
    r'|confirmado(?:\s+(?:por|en)\s+[^,)]+)?'
    r'|resuelto manualmente'
    r'|fabricante_oficial[^)]*)'
)


def limpiar_procedencia(valor: str) -> str:
    """Quita del texto visible las notas de fuente/confianza/auditoria
    entre parentesis, sin tocar el resto del contenido (que puede ser
    informacion real del producto, p.ej. '(H-GUARD + SPS+)' o '(vía
    base)', que NO se toca). Nunca modifica 'Sin especificar' ni
    'Revisar' -- esos se gestionan aparte."""
    v = valor or ""
    if es_revisar(v) or es_sin_especificar(v):
        return v
    # Parentesis ENTERO que es solo 1+ clausulas de procedencia
    v = re.sub(rf'\s*\(\s*{_CLAUSE}(?:\s*,\s*{_CLAUSE})*\s*\)', '', v, flags=re.IGNORECASE)
    # Clausula de procedencia al final de un parentesis con mas contenido
    v = re.sub(rf',\s*{_CLAUSE}(?=\s*\))', '', v, flags=re.IGNORECASE)
    # Clausula de procedencia al inicio de un parentesis con mas contenido
    v = re.sub(rf'\(\s*{_CLAUSE}\s*,\s*', '(', v, flags=re.IGNORECASE)
    for _ in range(2):
        v = re.sub(r'\(\s*\)', '', v)
        v = re.sub(r'\(\s*,\s*', '(', v)
        v = re.sub(r',\s*\)', ')', v)
    v = re.sub(r'\s+\)', ')', v)
    v = re.sub(r'\s{2,}', ' ', v).strip()
    return v


def campo(p: dict, key: str) -> str:
    """Lee un campo del producto ya limpio de procedencia -- punto unico
    de entrada para cualquier valor que se vaya a mostrar."""
    return limpiar_procedencia(p.get(key) or SIN_ESPECIFICAR)


def fmt_precio(valor):
    if valor is None:
        return None
    return f"{valor:.2f}".replace(".", ",") + " €"


def fmt_valoracion(valor):
    if valor is None:
        return None
    return str(valor).replace(".", ",")


def fmt_n_val(valor):
    if valor is None:
        return None
    return f"{valor:,}".replace(",", ".")


def iniciales(marca):
    palabras = (marca or "?").split()
    return "".join(w[0] for w in palabras[:2]).upper()


# (etiqueta, clave en el dataset) -- campos secundarios de la ficha
# tecnica, agrupados en dos bloques con separacion visual ligera.
DETAIL_FIELDS_PRINCIPALES = [
    ("Tipo de instalación", "tipo_instalacion"),
    ("Reclinable", "reclinable"),
    ("Reposacabezas", "reposacabezas"),
    ("Arnés", "arnes"),
]
DETAIL_FIELDS_CARACTERISTICAS = [
    ("Peso silla", "peso_silla"),
    ("Protección lateral", "proteccion_lateral"),
    ("Funda lavable", "funda_lavable"),
    ("Travel system", "travel_system"),
]


def valor_badge(valor):
    """ISOFIX / 360º: check compacto. 'Sin especificar' se ve como '—'."""
    v = valor.strip()
    if es_sin_especificar(v):
        return f'<span class="chk chk--unk" title="{SIN_ESPECIFICAR}">{GUION}</span>'
    matiz = v if v not in ("Sí", "No") else ""
    title_attr = f' title="{html_lib.escape(matiz)}"' if matiz else ""
    if v.startswith("Sí"):
        return f'<span class="chk chk--yes"{title_attr}>✓</span>'
    if v.startswith("No"):
        return f'<span class="chk chk--no"{title_attr}>✕</span>'
    return f'<span class="chk chk--unk" title="{html_lib.escape(v)}">{html_lib.escape(v)}</span>'


def texto_compacto(valor):
    """Etiqueta corta ('—' si Sin especificar) + matiz completo (title).
    El recorte visual de textos largos lo hace el CSS (ellipsis)."""
    v = valor.strip()
    if es_sin_especificar(v):
        return GUION, SIN_ESPECIFICAR
    return v, v


def celda_principal(valor, col_cls=""):
    texto, matiz = texto_compacto(valor)
    estado_cls = "cell-unspecified" if texto == GUION else ("cell-revisar" if es_revisar(texto) else "")
    cls = " ".join(c for c in [col_cls, estado_cls] if c)
    cls_attr = f' class="{cls}"' if cls else ""
    title_attr = f' title="{html_lib.escape(matiz)}"' if matiz else ""
    return f"<td{cls_attr}{title_attr}>{html_lib.escape(texto)}</td>"


def detail_item(label, valor):
    v = (valor or "").strip()
    if not v:
        return None
    if HIDE_UNSPECIFIED_IN_DETAIL and es_sin_especificar(v):
        return None
    extra_cls = " cell-revisar" if es_revisar(v) else ""
    if es_revisar(v):
        texto = "Revisar"
        title_attr = f' title="{html_lib.escape(v)}"'
    else:
        texto = v
        title_attr = ""
    return (
        f'<div class="detail-item"><span class="detail-label">{html_lib.escape(label)}</span>'
        f'<span class="detail-value{extra_cls}"{title_attr}>{html_lib.escape(texto)}</span></div>'
    )


def build_row(p, idx):
    marca = p.get("marca") or SIN_ESPECIFICAR
    modelo = p.get("modelo") or SIN_ESPECIFICAR

    precio = fmt_precio(p.get("precio"))
    valoracion = fmt_valoracion(p.get("valoracion"))
    n_val = fmt_n_val(p.get("n_val"))

    grupo = campo(p, "grupo")
    peso_recomendado = campo(p, "peso_recomendado")
    altura = campo(p, "altura")
    normativa = campo(p, "normativa")
    orientacion = campo(p, "orientacion")
    isofix = campo(p, "isofix")
    giro_360 = campo(p, "giro_360")

    precio_html = (
        f'<span class="price-current">{precio}</span>'
        if precio else f'<span class="cell-unspecified">{GUION}</span>'
    )

    grupo_txt, grupo_matiz = texto_compacto(grupo)
    peso_txt, peso_matiz = texto_compacto(peso_recomendado)
    grupo_cls = "cell-unspecified" if grupo_txt == GUION else ""
    peso_cls = "cell-unspecified" if peso_txt == GUION else ""
    grupo_title = f' title="{html_lib.escape(grupo_matiz)}"' if grupo_matiz else ""
    peso_title = f' title="{html_lib.escape(peso_matiz)}"' if peso_matiz else ""
    grupo_peso_html = (
        f'<span class="grupo-main{" " + grupo_cls if grupo_cls else ""}"{grupo_title}>{html_lib.escape(grupo_txt)}</span>'
        f'<span class="grupo-peso{" " + peso_cls if peso_cls else ""}"{peso_title}>{html_lib.escape(peso_txt)}</span>'
    )

    valoracion_item = detail_item(
        "Valoración",
        f"⭐ {valoracion} · {n_val} valoraciones" if valoracion and n_val else (
            f"⭐ {valoracion}" if valoracion else None
        ),
    )
    principales = [valoracion_item] + [
        detail_item(label, limpiar_procedencia(p.get(key) or "")) for label, key in DETAIL_FIELDS_PRINCIPALES
    ]
    caracteristicas = [
        detail_item(label, limpiar_procedencia(p.get(key) or "")) for label, key in DETAIL_FIELDS_CARACTERISTICAS
    ]
    principales = [d for d in principales if d]
    caracteristicas = [d for d in caracteristicas if d]

    detail_groups = ""
    if principales:
        detail_groups += (
            '<span class="detail-group-label">Datos principales</span>\n' + "\n".join(principales)
        )
    if caracteristicas:
        detail_groups += (
            '\n<span class="detail-group-label detail-group-label--sep">Características</span>\n'
            + "\n".join(caracteristicas)
        )

    panel_id = f"detail-{idx}"

    main_row = f"""
    <tr class="main-row" data-target="{panel_id}">
      <td class="col-product">
        <div class="prod-cell">
          <div class="prod-thumb-ph">{iniciales(marca)}</div>
          <div class="prod-info">
            <span class="prod-brand">{html_lib.escape(marca)}</span>
            <span class="prod-model">{html_lib.escape(modelo)}</span>
          </div>
        </div>
      </td>
      <td class="col-price">{precio_html}</td>
      {celda_principal(normativa, "col-normativa")}
      <td class="col-grupo">{grupo_peso_html}</td>
      {celda_principal(altura, "col-altura")}
      <td class="col-isofix">{valor_badge(isofix)}</td>
      <td class="col-360">{valor_badge(giro_360)}</td>
      {celda_principal(orientacion, "col-orientacion")}
      <td class="col-action">
        <button class="btn-toggle" type="button" data-toggle="{panel_id}">Ficha técnica ▾</button>
      </td>
    </tr>"""

    detail_row = f"""
    <tr class="detail-row" id="{panel_id}" hidden>
      <td colspan="9">
        <div class="detail-grid">
          {detail_groups}
        </div>
        <div class="detail-amazon">
          <a class="btn-amazon" href="https://www.amazon.es/dp/{html_lib.escape(p['asin'])}" target="_blank" rel="nofollow sponsored noopener">Ver en Amazon →</a>
        </div>
      </td>
    </tr>"""

    return main_row + detail_row


COLUMN_HEADERS = [
    ("Producto", "col-product"),
    ("Precio", "col-price"),
    ("Normativa", "col-normativa"),
    ("Rango de uso", "col-grupo"),
    ("Altura", "col-altura"),
    ("ISOFIX", "col-isofix"),
    ("360º", "col-360"),
    ("Orientación", "col-orientacion"),
    ("", "col-action"),
]

# Identicos anchos que v4 -- no se toca la estructura de columnas.
COLUMN_WIDTHS = [260, 95, 110, 150, 115, 65, 65, 150, 150]


def main():
    with open(SRC, encoding="utf-8") as f:
        data = json.load(f)
    productos = data["productos"]

    rows_html = "\n".join(build_row(p, i) for i, p in enumerate(productos))
    headers_html = "\n".join(
        f'<th class="{cls}">{html_lib.escape(label)}</th>' for label, cls in COLUMN_HEADERS
    )
    colgroup_html = "\n".join(f'<col style="width:{w}px">' for w in COLUMN_WIDTHS)

    html_out = f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<title>PROTOTIPO v6 — Comparativa sillitas de coche</title>
<meta name="robots" content="noindex,nofollow">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Fredoka:wght@600&family=JetBrains+Mono:wght@600&display=swap" rel="stylesheet">
<style>
:root{{
  --bg:#FAFAF8; --ink:#1C1C1E; --ink-soft:#6B6B70; --line:#E4E2DC; --card:#FFFFFF;
  --accent:#FF8A65; --accent-deep:#D85A30; --revisar:#B5841C; --revisar-bg:#FBF2DE;
}}
*{{margin:0;padding:0;box-sizing:border-box;}}
body{{background:var(--bg);color:var(--ink);font-family:'Inter',sans-serif;line-height:1.5;-webkit-font-smoothing:antialiased;padding:40px 32px 80px;}}
h1,h2,h3{{font-family:'Fredoka',sans-serif;font-weight:600;letter-spacing:-0.01em;}}

.proto-banner{{background:#2C2C2A;color:#fff;font-family:'JetBrains Mono',monospace;font-size:12px;font-weight:600;letter-spacing:.04em;text-transform:uppercase;padding:10px 18px;border-radius:8px;display:inline-block;margin-bottom:14px;}}
.proto-banner b{{color:#FFB199;}}
.proto-note{{max-width:820px;font-size:13px;color:var(--ink-soft);margin-bottom:28px;line-height:1.6;}}
.proto-note code{{background:#F0EEE8;padding:1px 5px;border-radius:4px;font-size:12px;}}

.page-head{{margin-bottom:24px;}}
.eyebrow{{font-family:'JetBrains Mono',monospace;font-size:12px;font-weight:600;color:var(--accent-deep);letter-spacing:.06em;text-transform:uppercase;margin-bottom:10px;}}
.page-head h1{{font-size:30px;margin-bottom:6px;}}
.page-head p{{color:var(--ink-soft);font-size:14.5px;}}

.table-shell{{border:1px solid var(--line);border-radius:14px;overflow:hidden;background:var(--card);box-shadow:0 2px 8px rgba(0,0,0,.05);}}
.table-scroll{{overflow-x:auto;overflow-y:visible;max-width:100%;}}

table{{border-collapse:separate;border-spacing:0;table-layout:fixed;}}

thead th{{
  background:#F4F2EE; color:var(--ink); font-size:11.5px; font-weight:700;
  text-transform:uppercase; letter-spacing:.03em;
  padding:15px 12px; text-align:left; white-space:nowrap;
  border-bottom:1px solid var(--line);
}}

tbody td{{
  padding:14px 12px; font-size:14px; color:var(--ink);
  border-bottom:1px solid var(--line);
  vertical-align:middle;
}}
tbody tr.main-row:last-of-type td{{border-bottom:1px solid var(--line);}}
tbody tr.main-row:hover td{{background:#FBF6F1;cursor:pointer;}}
tbody tr.main-row td{{transition:background .12s;}}

td.col-product{{white-space:normal;}}
.prod-cell{{display:flex;align-items:center;gap:12px;}}
.prod-thumb-ph{{
  width:44px;height:44px;border-radius:9px;background:linear-gradient(135deg,#F4F2EE,#E9E6DF);
  display:flex;align-items:center;justify-content:center;flex-shrink:0;
  font-family:'JetBrains Mono',monospace;font-weight:700;font-size:12px;color:var(--ink-soft);
  border:1px solid var(--line);
}}
.prod-info{{display:flex;flex-direction:column;gap:2px;min-width:0;}}
.prod-brand{{font-size:11px;font-weight:700;color:var(--accent-deep);text-transform:uppercase;letter-spacing:.03em;}}
.prod-model{{font-size:13px;font-weight:600;color:var(--ink);white-space:normal;line-height:1.3;}}

.price-current{{font-size:14.5px;font-weight:700;color:var(--ink);white-space:nowrap;}}

td.col-normativa{{font-size:12.5px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;}}

.grupo-main{{display:block;font-size:13px;font-weight:600;color:var(--ink);overflow:hidden;text-overflow:ellipsis;white-space:nowrap;}}
.grupo-peso{{display:block;font-size:11.5px;color:var(--ink-soft);font-weight:400;margin-top:3px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;}}

td.col-altura{{font-size:13px;font-weight:500;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;}}

.cell-unspecified{{color:#9C9A93;font-weight:400;font-size:13px;}}
.cell-revisar{{color:var(--revisar);font-weight:600;}}

td.col-isofix,td.col-360{{text-align:center;}}
.chk{{display:inline-block;font-size:16px;font-weight:700;line-height:1;}}
.chk--yes{{color:#2F7A45;}}
.chk--no{{color:#B5471F;}}
.chk--unk{{color:#9C9A93;font-weight:400;font-size:13px;}}

td.col-orientacion{{font-size:13px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;}}

td.col-action{{}}
.btn-toggle{{
  display:block;background:none;border:1px solid var(--line);color:var(--ink-soft);
  font-size:12px;font-weight:600;padding:8px 14px;border-radius:8px;cursor:pointer;
  font-family:'Inter',sans-serif;transition:.15s;width:100%;
}}
.btn-toggle:hover, .btn-toggle.is-open{{border-color:var(--accent-deep);color:var(--accent-deep);background:#FFF7F3;}}

tr.detail-row td{{padding:0;}}
tr.detail-row[hidden]{{display:none;}}
.detail-grid{{
  display:grid;grid-template-columns:1fr 1fr;gap:14px 32px;
  background:#FBF9F5;padding:22px 26px 8px;border-bottom:1px solid var(--line);
}}
.detail-group-label{{
  grid-column:1 / -1; font-size:10.5px; font-weight:700; color:var(--accent-deep);
  text-transform:uppercase; letter-spacing:.05em; margin-bottom:-2px;
}}
.detail-group-label--sep{{margin-top:8px;padding-top:14px;border-top:1px solid var(--line);}}
.detail-item{{display:flex;flex-direction:column;gap:3px;white-space:normal;padding-bottom:12px;border-bottom:1px dashed var(--line);}}
.detail-label{{font-size:11px;font-weight:700;color:var(--ink-soft);text-transform:uppercase;letter-spacing:.03em;}}
.detail-value{{font-size:13.5px;color:var(--ink);font-weight:500;}}
.detail-value.cell-revisar{{color:var(--revisar);cursor:help;border-bottom:1px dotted var(--revisar);display:inline-block;width:fit-content;}}
.detail-amazon{{padding:16px 26px 22px;background:#FBF9F5;}}
.btn-amazon{{
  display:inline-block;background:var(--accent-deep);color:#fff;font-size:13px;font-weight:700;
  padding:10px 18px;border-radius:8px;white-space:nowrap;transition:background .15s;
}}
.btn-amazon:hover{{background:#B5471F;}}

.foot-note{{margin-top:18px;font-size:12px;color:var(--ink-soft);}}
</style>
</head>
<body>

<div class="proto-banner">⚠ Prototipo v6 — <b>no es la web real</b> — misma fuente que v4/v5: tools/output/auditoria_30_candidatos.json (dataset maestro consolidado 13-ago-2026)</div>
<p class="proto-note">
  Corrección puntual sobre v5, mismo dataset y misma estructura de columnas. Único cambio: la columna "Grupo + Peso" pasa a llamarse <b>"Rango de uso"</b>. Motivo: el campo <code>grupo</code> (p.ej. "0+/1/2/3") es la clasificación tradicional por peso, distinta de la normativa R129/i-Size de la columna de al lado, que homologa principalmente por altura — llamarla "Grupo" junto a "Normativa" podía leerse como si el grupo fuera parte de la clasificación R129. "Rango de uso" es una etiqueta editorial para mostrar juntos grupo (si existe) + peso (si existe), sin implicar relación normativa. El campo del dataset sigue llamándose <code>grupo</code> y su valor no cambia.
</p>

<div class="page-head">
  <div class="eyebrow">Comparador de sillitas de coche · Prototipo PC</div>
  <h1>Comparativa de sillitas de coche</h1>
  <p>{len(productos)} modelos</p>
</div>

<div class="table-shell">
  <div class="table-scroll">
    <table>
      <colgroup>
        {colgroup_html}
      </colgroup>
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

<p class="foot-note">Prototipo generado por tools/build_comparativa_prototipo_v6.py a partir de tools/output/auditoria_30_candidatos.json — no modifica ningún archivo de producción ni el dataset auditado.</p>

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

// Autocomprobacion (visible en consola del navegador)
(function selfCheck() {{
  const rows = document.querySelectorAll('tr.main-row').length;
  const panels = document.querySelectorAll('tr.detail-row').length;
  const toggles = document.querySelectorAll('.btn-toggle').length;
  console.log(`[prototipo v6] filas de producto: ${{rows}} | paneles de ficha: ${{panels}} | botones toggle: ${{toggles}}`);
  console.assert(rows === {len(productos)}, `Se esperaban {len(productos)} productos, hay ${{rows}}`);
  console.assert(rows === panels && panels === toggles, 'Descuadre entre filas, paneles y botones');
}})();
</script>

</body>
</html>
"""

    with open(OUT, "w", encoding="utf-8") as f:
        f.write(html_out)
    print(f"OK: {OUT} generado con {len(productos)} productos.")


if __name__ == "__main__":
    main()
