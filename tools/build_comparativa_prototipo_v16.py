#!/usr/bin/env python3
"""
build_comparativa_prototipo_v16.py

Evolucion sobre v15 (ver tools/build_comparativa_prototipo_v15.py) --
AMPLIA UNICAMENTE el sistema de ORDENACION (16-ago-2026), añadiendo 4
criterios de tipo "caracteristica" (prioridad categorica, no asc/desc):

  8. ISOFIX            -> "ISOFIX: Sí primero" / "ISOFIX: No primero"
  9. 360º              -> "360º: Sí primero" / "360º: No primero"
  10. Orientación       -> "Ambas primero" / "A contramarcha primero" /
                           "A favor de la marcha primero"
  11. Arnés             -> "5 puntos primero" / "3 puntos primero" /
                           "Cinturón del vehículo primero"

Los 7 criterios numericos ya existentes (Precio/Valoración/Nº
valoraciones/Altura/Edad/Grupo/Peso) NO se tocan -- su logica
(compareRows, SIMPLE_CRITERIA, MINMAX_CRITERIA) sigue intacta; los 4
nuevos criterios se añaden como ramas nuevas en compareRows, sin
modificar ninguna de las existentes.

Logica de las categorias:
- ISOFIX/360º son binarios (Sí/No en el dataset): la opcion elegida
  ("Sí primero"/"No primero") pasa a rango 0, la otra a rango 1.
- Orientación/Arnés tienen 3 categorias: la elegida pasa a rango -1
  (primera); las otras 2 conservan su orden relativo de un orden base
  fijo (Orientación: Ambas > A contramarcha > A favor de la marcha;
  Arnés: 5 puntos > 3 puntos > Cinturón), sin inventar un orden nuevo
  para las no elegidas -- asi "Ambas primero" da exactamente Ambas >
  contramarcha > favor, tal como pidio el usuario en su ejemplo.
- "Sin especificar" (o valor no clasificable, p.ej. un Arnés con un
  valor compuesto/mixto de dos tramos) va SIEMPRE al final, en
  cualquier prioridad elegida.
- Estabilidad: en empate de prioridad, se conserva el orden original
  del dataset (data-orig-index), igual que en los criterios numericos.

El selector "Ordenar por" se reorganiza en 2 grupos visuales ("Datos
numéricos" / "Características"), pedido explicito del usuario -- es la
UNICA reestructuracion del select; no se toca su logica de disparo
('change' -> applySort). El Punto 7.1 (cabecera: Precio/Valoración/
Rango de uso con ↕) se mantiene intacto, sin rediseñar y sin añadir
indicadores nuevos a ISOFIX/360º/Orientación/Arnés (pedido explicito:
eso se valorara en el repaso estetico posterior).

No se modifica ningun dato del dataset, ningun JSON, ninguna columna,
ni filas/celdas/botones/ficha tecnica/enlaces Amazon. No se toca
amazon_import.py ni ningun archivo de produccion.

Uso:
    python tools/build_comparativa_prototipo_v16.py
"""

import html as html_lib
import json
import re

SRC = "tools/output/auditoria_30_candidatos.json"
OUT = "prototipo-comparativa-sillas-v16.html"

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
    # "Arnés" NO va en esta lista generica -- se anade condicionalmente
    # en build_row() solo cuando aporta algo mas de lo que ya se ve en
    # la tabla principal (ver arnes_tiene_matiz_oculto, v10).
]
DETAIL_FIELDS_CARACTERISTICAS = [
    ("Peso silla", "peso_silla"),
    ("Protección lateral", "proteccion_lateral"),
    # "Funda lavable" y "Travel system" se retiran de la ficha tecnica del
    # comparador (decision 15-ago-2026): Funda lavable se reserva para una
    # futura ficha individual de producto; Travel system se saca de toda
    # la interfaz por ahora. Ninguno de los dos se borra del dataset.
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
    """Etiqueta corta ('—' si Sin especificar, 'Revisar' si Revisar) +
    matiz completo (title). El recorte visual de textos largos lo hace
    el CSS (ellipsis)."""
    v = valor.strip()
    if es_sin_especificar(v):
        return GUION, SIN_ESPECIFICAR
    if es_revisar(v):
        return "Revisar", v
    return v, v


def rango_uso_html(altura, edad, grupo, peso):
    """Fusiona Altura + Edad + Grupo + Peso en una sola celda, en ese
    orden de jerarquia (altura = dato principal). Cada linea SOLO
    aparece si el dato existe -- nunca se rellena el hueco con guion ni
    con el texto 'Sin especificar', simplemente no se genera esa linea."""
    lineas = []
    campos = (
        (altura, "rango-altura"),
        (edad, "rango-edad"),
        (grupo, "rango-grupo"),
        (peso, "rango-peso"),
    )
    for valor_campo, css_cls in campos:
        texto, matiz = texto_compacto(valor_campo)
        if texto == GUION:
            continue
        title_attr = f' title="{html_lib.escape(matiz)}"' if matiz and matiz != texto else ""
        lineas.append(f'<span class="{css_cls}"{title_attr}>{html_lib.escape(texto)}</span>')
    if not lineas:
        return f'<span class="cell-unspecified">{GUION}</span>'
    return "\n".join(lineas)


def arnes_compacto(valor):
    """Version SOLO para la tabla principal: quita cualquier matiz entre
    parentesis del arnes (p.ej. '(3 puntos)', '(guías de cinturón)',
    '(76-105cm)') para que la columna 'Puntos anclaje' quede limpia. El
    dato real no cambia -- el texto integro sigue disponible en el
    title (tooltip) de la celda, y en la ficha tecnica se sigue
    mostrando completo."""
    texto, matiz = texto_compacto(valor)
    if texto in (GUION, "Revisar"):
        return texto, matiz
    limpio = re.sub(r'\s*\([^)]*\)', '', texto).strip()
    limpio = re.sub(r'\s{2,}', ' ', limpio)
    if limpio and limpio != texto:
        return limpio, valor.strip()
    return texto, matiz


def arnes_compacto_tabla(valor):
    """SOLO para la celda de la tabla principal (no afecta a la ficha
    tecnica ni a arnes_tiene_matiz_oculto): ademas de quitar parentesis
    (arnes_compacto), recorta un par de palabras funcionales para ganar
    espacio -- 'Arnés de 5 puntos' -> 'Arnés 5 puntos', 'Cinturón del
    vehículo' -> 'Cinturón vehículo'. Puramente cosmetico, el dato real
    (y el tooltip) no cambian."""
    texto, matiz = arnes_compacto(valor)
    if texto in (GUION, "Revisar"):
        return texto, matiz
    compacto = re.sub(r'\bde (\d+ puntos)\b', r'\1', texto, flags=re.IGNORECASE)
    compacto = re.sub(r'\bdel vehículo\b', 'vehículo', compacto, flags=re.IGNORECASE)
    return compacto, matiz


def arnes_tiene_matiz_oculto(valor) -> bool:
    """True cuando la tabla principal ('Puntos anclaje') esconde algo
    del valor real de arnes -- un matiz entre parentesis quitado, o el
    caso 'Revisar' (que en tabla se acorta a esa palabra). En ese caso
    SI se muestra 'Arnés' en la ficha tecnica, con el texto completo.
    False para texto llano sin parentesis o 'Sin especificar' -- ahi NO
    se muestra en la ficha, seria duplicar la tabla sin aportar nada."""
    v = (valor or "").strip()
    if es_sin_especificar(v):
        return False
    if es_revisar(v):
        return True
    compacto, completo = arnes_compacto(v)
    return compacto != completo


def celda_principal(valor, col_cls="", compactor=texto_compacto):
    texto, matiz = compactor(valor)
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



# ---------------------------------------------------------------------------
# PUNTO 6 -- valores numericos auxiliares para el selector "Ordenar por".
# Ninguno de estos parsers modifica el texto mostrado al usuario; solo
# calculan un valor auxiliar para poder comparar. Devuelven None (o
# (None, None)) cuando no hay evidencia suficiente -- ese producto se
# coloca al final en el criterio correspondiente.
# ---------------------------------------------------------------------------

def parse_altura_rango(valor):
    """('40-150 cm' -> (40.0, 150.0)). None si no hay un rango 'N-N cm'
    explicito (p.ej. 'Sin especificar (0-18kg, sin cm explícito)')."""
    if es_sin_especificar(valor) or es_revisar(valor):
        return None, None
    m = re.search(r'(\d+(?:[.,]\d+)?)\s*-\s*(\d+(?:[.,]\d+)?)\s*cm', (valor or "").lower())
    if not m:
        return None, None
    return float(m.group(1).replace(",", ".")), float(m.group(2).replace(",", "."))


def parse_edad_rango_meses(valor):
    """Convierte el rango de edad a MESES (para poder comparar '15 meses
    - 12 años' con '0-12 años' de forma correcta) sin cambiar el texto
    mostrado. None si no hay rango reconocible."""
    if es_sin_especificar(valor) or es_revisar(valor):
        return None, None
    v = (valor or "").lower().replace("recién nacido", "0").replace("recien nacido", "0")
    m = re.match(r'\s*([\d.,]+)\s*(mes(?:es)?|años?)?\s*-\s*([\d.,]+)\s*(mes(?:es)?|años?)?', v)
    if not m:
        return None, None
    num1, unit1, num2, unit2 = m.groups()
    unit1 = unit1 or unit2
    unit2 = unit2 or unit1
    if not unit1 or not unit2:
        return None, None

    def to_months(num, unit):
        n = float(num.replace(",", "."))
        return n if unit.startswith("mes") else n * 12

    return to_months(num1, unit1), to_months(num2, unit2)


def parse_grupo_amplitud(valor):
    """Numero de etapas cubiertas por el grupo ('0+/1/2/3' -> 4,
    'Grupo 3' -> 1) + valor numerico del primer grupo de la secuencia
    (para el desempate). (None, None) si es 'Sin especificar'/'Revisar'
    o no hay prefijo 'Grupo '."""
    v = (valor or "").strip()
    if es_sin_especificar(v) or es_revisar(v):
        return None, None
    m = re.match(r'Grupo\s+([\d+/]+)', v)
    if not m:
        return None, None
    token = m.group(1)
    if "/" in token:
        parts = token.split("/")
    elif "+" in token:
        parts = [token]
    elif len(token) > 1 and token.isdigit():
        parts = list(token)  # p.ej. "0123" -> 4 etapas de un digito
    else:
        parts = [token]
    num_grupos = len(parts)
    first_digits = re.sub(r"\D", "", parts[0])
    first_num = float(first_digits) if first_digits else 0.0
    return num_grupos, first_num


def parse_peso_max(valor):
    """Peso maximo del rango ('9-36 kg' -> 36.0, 'Hasta 25 kg' -> 25.0).
    None si es 'Sin especificar'/'Revisar' o no hay ningun kg parseable."""
    if es_sin_especificar(valor) or es_revisar(valor):
        return None
    v = (valor or "").lower()
    m = re.search(r'(\d+(?:[.,]\d+)?)\s*-\s*(\d+(?:[.,]\d+)?)\s*kg', v)
    if m:
        return float(m.group(2).replace(",", "."))
    m = re.search(r'hasta\s*(\d+(?:[.,]\d+)?)\s*kg', v)
    if m:
        return float(m.group(1).replace(",", "."))
    return None


def num_attr(name, value):
    """Atributo data-* numerico -- se OMITE por completo si value es
    None, para que en JS `row.dataset.x === undefined` marque 'sin
    dato' de forma inequivoca (nunca se usa 0 ni '' como relleno)."""
    if value is None:
        return ""
    return f' data-{name}="{value}"'


def str_attr(name, value):
    """Igual que num_attr pero para valores de texto categoricos
    ('si'/'no'/'ambas'/'5puntos'...). Tambien se omite si value es
    None."""
    if value is None:
        return ""
    return f' data-{name}="{html_lib.escape(str(value))}"'


# ---------------------------------------------------------------------------
# Ordenacion por CARACTERISTICAS (punto 7 ampliado, 16-ago-2026) -- ISOFIX,
# 360º, Orientación, Arnés. No son asc/desc numerico: son prioridades
# categoricas (p.ej. "ISOFIX: Sí primero"). Estos parsers solo clasifican
# el valor ya existente en el dataset -- nunca lo modifican ni lo
# reinterpretan.
# ---------------------------------------------------------------------------

def parse_bool_categoria(valor):
    """'Sí'/'Sí (matiz)' -> 'si'; 'No'/'No (matiz)' -> 'no'; cualquier
    otra cosa (Sin especificar, Revisar) -> None. Usado por ISOFIX y
    360º, que ya son campos Sí/No/Sin especificar puros en el dataset."""
    v = (valor or "").strip()
    if es_sin_especificar(v) or es_revisar(v):
        return None
    if v.startswith("Sí"):
        return "si"
    if v.startswith("No"):
        return "no"
    return None


def parse_orientacion_categoria(valor):
    """'Ambas'/'Ambas (matiz)' -> 'ambas'; 'A contramarcha...' ->
    'contramarcha'; 'A favor de la marcha...' -> 'favor'; resto -> None."""
    v = (valor or "").strip()
    if es_sin_especificar(v) or es_revisar(v):
        return None
    if v.startswith("Ambas"):
        return "ambas"
    if v.startswith("A contramarcha"):
        return "contramarcha"
    if v.startswith("A favor de la marcha"):
        return "favor"
    return None


def parse_arnes_categoria(valor):
    """'Arnés de 5 puntos...' -> '5puntos'; 'Arnés de 3 puntos...' ->
    '3puntos'; 'Cinturón del vehículo...' -> 'cinturon'. Un valor
    compuesto/mixto (contiene ' / ', p.ej. un producto que usa arnés de
    5 puntos en un tramo de altura y cinturón en otro) NO se fuerza a
    ninguna categoria -> None, va al final (no se puede afirmar una
    prioridad unica para ese producto sin tergiversar el dato)."""
    v = (valor or "").strip()
    if es_sin_especificar(v) or es_revisar(v):
        return None
    if " / " in v:
        return None
    if v.startswith("Arnés de 5 puntos"):
        return "5puntos"
    if v.startswith("Arnés de 3 puntos"):
        return "3puntos"
    if v.startswith("Cinturón del vehículo"):
        return "cinturon"
    return None


def build_row(p, idx):
    marca = p.get("marca") or SIN_ESPECIFICAR
    modelo = p.get("modelo") or SIN_ESPECIFICAR

    precio = fmt_precio(p.get("precio"))
    valoracion = fmt_valoracion(p.get("valoracion"))
    n_val = fmt_n_val(p.get("n_val"))

    grupo = campo(p, "grupo")
    peso_recomendado = campo(p, "peso_recomendado")
    altura = campo(p, "altura")
    edad = campo(p, "edad")
    normativa = campo(p, "normativa")
    orientacion = campo(p, "orientacion")
    isofix = campo(p, "isofix")
    giro_360 = campo(p, "giro_360")
    arnes = campo(p, "arnes")

    precio_html = (
        f'<span class="price-current">{precio}</span>'
        if precio else f'<span class="cell-unspecified">{GUION}</span>'
    )

    if valoracion:
        valoracion_html = f'<span class="val-star">⭐ {valoracion}</span>'
        if n_val:
            valoracion_html += f'<span class="val-count">{n_val}</span>'
    else:
        valoracion_html = f'<span class="cell-unspecified">{GUION}</span>'

    rango_html = rango_uso_html(altura, edad, grupo, peso_recomendado)

    valoracion_item = detail_item(
        "Valoración",
        f"⭐ {valoracion} · {n_val} valoraciones" if valoracion and n_val else (
            f"⭐ {valoracion}" if valoracion else None
        ),
    )
    arnes_item = detail_item("Arnés", arnes) if arnes_tiene_matiz_oculto(arnes) else None
    principales = [valoracion_item, arnes_item] + [
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

    # Valores auxiliares para el selector "Ordenar por" (punto 6) -- no
    # se muestran, solo se usan para comparar. None -> atributo omitido
    # (num_attr) -> ese producto va al final en ese criterio.
    altura_min, altura_max = parse_altura_rango(altura)
    edad_min, edad_max = parse_edad_rango_meses(edad)
    grupo_num, grupo_first = parse_grupo_amplitud(grupo)
    peso_max = parse_peso_max(peso_recomendado)
    # Nuevas categorias de ordenacion (16-ago-2026): ISOFIX, 360º,
    # Orientación, Arnés -- prioridades categoricas, no asc/desc.
    isofix_cat = parse_bool_categoria(isofix)
    v360_cat = parse_bool_categoria(giro_360)
    orientacion_cat = parse_orientacion_categoria(orientacion)
    arnes_cat = parse_arnes_categoria(arnes)
    sort_attrs = (
        f'{num_attr("orig-index", idx)}'
        f'{num_attr("sort-precio", p.get("precio"))}'
        f'{num_attr("sort-valoracion", p.get("valoracion"))}'
        f'{num_attr("sort-nval", p.get("n_val"))}'
        f'{num_attr("sort-altura-min", altura_min)}'
        f'{num_attr("sort-altura-max", altura_max)}'
        f'{num_attr("sort-edad-min", edad_min)}'
        f'{num_attr("sort-edad-max", edad_max)}'
        f'{num_attr("sort-grupo-num", grupo_num)}'
        f'{num_attr("sort-grupo-first", grupo_first)}'
        f'{num_attr("sort-peso-max", peso_max)}'
        f'{str_attr("sort-isofix-cat", isofix_cat)}'
        # OJO: "sort-giro360-cat" (no "sort-360-cat") a proposito -- un
        # guion seguido de un DIGITO no se convierte a camelCase segun
        # el algoritmo de dataset del HTML Living Standard (el guion se
        # queda literal), asi que "data-sort-360-cat" NO seria accesible
        # como row.dataset.sort360Cat en JS. Con una letra antes del
        # numero ("giro360") todos los guiones van seguidos de una
        # letra minuscula y el atributo se lee como sortGiro360Cat.
        f'{str_attr("sort-giro360-cat", v360_cat)}'
        f'{str_attr("sort-orientacion-cat", orientacion_cat)}'
        f'{str_attr("sort-arnes-cat", arnes_cat)}'
    )

    main_row = f"""
    <tr class="main-row" data-target="{panel_id}"{sort_attrs}>
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
      <td class="col-valoracion">{valoracion_html}</td>
      {celda_principal(normativa, "col-normativa")}
      <td class="col-rango">{rango_html}</td>
      <td class="col-isofix">{valor_badge(isofix)}</td>
      {celda_principal(orientacion, "col-orientacion")}
      <td class="col-360">{valor_badge(giro_360)}</td>
      {celda_principal(arnes, "col-anclaje", arnes_compacto_tabla)}
      <td class="col-action">
        <div class="action-group">
          <a class="btn-amazon-row" href="https://www.amazon.es/dp/{html_lib.escape(p['asin'])}" target="_blank" rel="nofollow sponsored noopener">Ver en Amazon →</a>
          <button class="btn-toggle" type="button" data-toggle="{panel_id}">Ficha técnica ▾</button>
        </div>
      </td>
    </tr>"""

    detail_row = f"""
    <tr class="detail-row" id="{panel_id}" hidden>
      <td colspan="10">
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
    ("Valoración", "col-valoracion"),
    ("Normativa", "col-normativa"),
    ("Rango de uso", "col-rango"),
    ("ISOFIX", "col-isofix"),
    ("Orientación", "col-orientacion"),
    ("360º", "col-360"),
    ("Arnés", "col-anclaje"),
    ("Acciones", "col-action"),
]

# Cabecera renombrada 15-ago-2026: "Puntos anclaje" -> "Arnés" (se
# confirmo que el campo representa el arnes, no un anclaje distinto de
# ISOFIX). El dato, su compactacion en tabla y los anchos de columna NO
# cambian respecto a v11.
# col-action se ensancha de 130 a 160px (unico ancho que cambia) para dar
# sitio a las dos acciones apiladas (Ver en Amazon + Ficha tecnica) sin
# romper el texto -- el resto de columnas mantiene su ancho de v11/v12.
COLUMN_WIDTHS = [250, 85, 70, 90, 190, 55, 120, 55, 150, 160]

# Menu de "Rango de uso": 4 sub-criterios x 2 sentidos, con la misma
# etiqueta y misma clave (data-sort-key) que ya usa el <select> "Ordenar
# por" -- no se inventa ninguna clave nueva.
RANGO_MENU_ITEMS = [
    ("Altura", "altura-asc", "menor → mayor"),
    ("Altura", "altura-desc", "mayor → menor"),
    ("Edad", "edad-asc", "menor → mayor"),
    ("Edad", "edad-desc", "mayor → menor"),
    ("Grupo", "grupo-desc", "más grupos → menos"),
    ("Grupo", "grupo-asc", "menos grupos → más"),
    ("Peso", "peso-asc", "menor → mayor"),
    ("Peso", "peso-desc", "mayor → menor"),
]


def build_header_cell(label, cls):
    """Punto 7.1: cabeceras planas (sin indicador) salvo Precio,
    Valoración y Rango de uso -- las 3 unicas columnas que son criterio
    de ordenacion. Precio/Valoración alternan asc/desc al hacer clic.
    Rango de uso abre un menu compacto con sus 4 sub-criterios (Altura/
    Edad/Grupo/Peso), cada uno con sus 2 sentidos, para no meter 8
    indicadores sueltos en la cabecera."""
    if cls == "col-price":
        return f'''<th class="{cls} is-sortable">
      <button type="button" class="th-sort-btn" data-sort-toggle="precio">{html_lib.escape(label)}<span class="th-sort-icon" data-sort-icon="precio">↕</span></button>
    </th>'''
    if cls == "col-valoracion":
        return f'''<th class="{cls} is-sortable">
      <button type="button" class="th-sort-btn" data-sort-toggle="valoracion">{html_lib.escape(label)}<span class="th-sort-icon" data-sort-icon="valoracion">↕</span></button>
    </th>'''
    if cls == "col-rango":
        menu_html = "\n".join(
            f'      <div class="th-sort-menu-group"><span class="th-sort-menu-label">{html_lib.escape(campo)}</span>'
            f'<button type="button" class="th-sort-menu-btn" data-sort-key="{key}">{html_lib.escape(texto)}</button></div>'
            for campo, key, texto in RANGO_MENU_ITEMS
        )
        return f'''<th class="{cls} is-sortable">
      <button type="button" class="th-sort-btn" data-menu-toggle="rango-menu">{html_lib.escape(label)}<span class="th-sort-icon" data-sort-icon="rango">↕</span></button>
      <div class="th-sort-menu" id="rango-menu" hidden>
{menu_html}
      </div>
    </th>'''
    return f'<th class="{cls}">{html_lib.escape(label)}</th>'


def main():
    with open(SRC, encoding="utf-8") as f:
        data = json.load(f)
    productos = data["productos"]

    rows_html = "\n".join(build_row(p, i) for i, p in enumerate(productos))
    headers_html = "\n".join(
        build_header_cell(label, cls) for label, cls in COLUMN_HEADERS
    )
    colgroup_html = "\n".join(f'<col style="width:{w}px">' for w in COLUMN_WIDTHS)

    html_out = f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<title>PROTOTIPO v16 — Comparativa sillitas de coche</title>
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

.sort-toolbar{{display:flex;align-items:center;gap:10px;margin-bottom:18px;}}
.sort-toolbar label{{font-size:13px;font-weight:700;color:var(--ink);}}
.sort-toolbar select{{
  font-family:'Inter',sans-serif;font-size:13.5px;font-weight:600;color:var(--ink);
  background:var(--card);border:1px solid var(--line);border-radius:8px;
  padding:8px 12px;cursor:pointer;min-width:260px;
}}
.sort-toolbar select:focus{{outline:2px solid var(--accent-deep);outline-offset:1px;}}

.table-shell{{border:1px solid var(--line);border-radius:14px;overflow:hidden;background:var(--card);box-shadow:0 2px 8px rgba(0,0,0,.05);}}
.table-scroll{{overflow-x:auto;overflow-y:visible;max-width:100%;}}

table{{border-collapse:separate;border-spacing:0;table-layout:fixed;}}

/* Punto 7.1 -- rediseño de cabecera (16-ago-2026): mas aire vertical,
   tipografia un punto mas grande y con mas letter-spacing, mismo fondo
   diferenciado (#F4F2EE) que ya existia. Producto se queda a la
   izquierda (valor por defecto); el resto de columnas se centra mas
   abajo con selectores especificos. */
thead th{{
  background:#F4F2EE; color:var(--ink); font-size:12.5px; font-weight:700;
  text-transform:uppercase; letter-spacing:.045em;
  padding:19px 14px; text-align:left; white-space:nowrap;
  border-bottom:1px solid var(--line);
  position:relative; /* ancla para el menu de "Rango de uso" en modo fallback */
}}
thead th.col-price, thead th.col-valoracion, thead th.col-normativa,
thead th.col-rango, thead th.col-isofix, thead th.col-orientacion,
thead th.col-360, thead th.col-anclaje, thead th.col-action{{
  text-align:center;
}}

/* Cabeceras ordenables (Precio/Valoración/Rango de uso): el nombre de
   columna es un boton "fantasma" (sin fondo/borde propios) con el
   mismo tamaño/peso que el resto de cabeceras, mas un indicador ↕
   discreto. El resto de cabeceras (Normativa/ISOFIX/Orientación/360º/
   Arnés/Acciones) no llevan boton ni indicador -- texto plano igual
   que antes. */
th.is-sortable{{padding:0;}}
.th-sort-btn{{
  display:inline-flex; align-items:center; gap:5px; justify-content:center;
  width:100%; height:100%; padding:19px 14px; margin:0; border:0; background:none;
  font-family:'Inter',sans-serif; font-size:12.5px; font-weight:700; color:var(--ink);
  text-transform:uppercase; letter-spacing:.045em; cursor:pointer; transition:color .15s;
}}
.th-sort-btn:hover{{color:var(--accent-deep);}}
.th-sort-icon{{font-size:11px;font-weight:400;color:#B3B0A8;transition:color .15s;}}
.th-sort-btn:hover .th-sort-icon{{color:var(--accent-deep);}}
.th-sort-icon.is-active{{color:var(--accent-deep);font-weight:700;}}
th.is-sortable.is-active-sort .th-sort-btn{{color:var(--accent-deep);}}

/* Menu compacto de "Rango de uso" -- position:fixed calculado por JS
   (para no quedar recortado por el overflow-x:auto de .table-scroll) y
   movido a <body> al abrirse. */
.th-sort-menu{{
  position:fixed; z-index:40; background:var(--card); border:1px solid var(--line);
  border-radius:10px; box-shadow:0 8px 24px rgba(0,0,0,.12); padding:8px; min-width:210px;
  text-align:left;
}}
.th-sort-menu[hidden]{{display:none;}}
.th-sort-menu-group{{display:flex;align-items:center;justify-content:space-between;gap:8px;padding:4px 6px;}}
.th-sort-menu-label{{font-size:11px;font-weight:700;color:var(--ink-soft);text-transform:uppercase;letter-spacing:.03em;width:44px;flex-shrink:0;}}
.th-sort-menu-btn{{
  flex:1; text-align:left; background:none; border:0; border-radius:6px; padding:6px 8px;
  font-family:'Inter',sans-serif; font-size:12.5px; font-weight:500; color:var(--ink);
  cursor:pointer; text-transform:none; letter-spacing:normal;
}}
.th-sort-menu-btn:hover{{background:#FFF7F3;color:var(--accent-deep);}}
.th-sort-menu-btn.is-active{{background:#FFF1EA;color:var(--accent-deep);font-weight:700;}}

tbody td{{
  padding:14px 12px; font-size:14px; color:var(--ink);
  border-bottom:1px solid var(--line);
  vertical-align:middle;
}}
tbody tr.main-row:last-of-type td{{border-bottom:1px solid var(--line);}}
tbody tr.main-row:hover td{{background:#FBF6F1;cursor:pointer;}}
tbody tr.main-row td{{transition:background .12s;}}

td.col-product{{white-space:normal;max-width:250px;}}
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

/* Valoracion: puntuacion como dato principal, nº de valoraciones debajo
   con menor jerarquia -- columna estrecha a proposito. */
td.col-valoracion{{text-align:left;white-space:normal;max-width:70px;}}
.val-star{{display:block;font-size:13.5px;font-weight:700;color:var(--ink);white-space:nowrap;}}
.val-count{{display:block;font-size:11px;font-weight:400;color:var(--ink-soft);margin-top:2px;white-space:nowrap;}}

td.col-normativa{{font-size:12.5px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;max-width:90px;}}

/* "Rango de uso": Altura (dato principal) > Edad > Grupo > Peso,
   jerarquia tipografica descendente. Cada linea solo existe en el HTML
   si el dato esta presente (ver rango_uso_html en el script) -- aqui
   solo se define el estilo de cada nivel cuando aparece. */
td.col-rango{{white-space:normal;max-width:190px;}}
.rango-altura{{display:block;font-size:14.5px;font-weight:700;color:var(--ink);overflow:hidden;text-overflow:ellipsis;white-space:nowrap;}}
.rango-edad{{display:block;font-size:12px;font-weight:500;color:var(--ink-soft);margin-top:3px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;}}
.rango-grupo{{display:block;font-size:12px;font-weight:500;color:var(--ink-soft);margin-top:3px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;}}
.rango-peso{{display:block;font-size:11px;font-weight:400;color:var(--ink-soft);margin-top:2px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;}}

.cell-unspecified{{color:#9C9A93;font-weight:400;font-size:13px;}}
.cell-revisar{{color:var(--revisar);font-weight:600;}}

td.col-isofix,td.col-360{{text-align:center;max-width:55px;}}
.chk{{display:inline-block;font-size:16px;font-weight:700;line-height:1;}}
.chk--yes{{color:#2F7A45;}}
.chk--no{{color:#B5471F;}}
.chk--unk{{color:#9C9A93;font-weight:400;font-size:13px;}}

td.col-orientacion{{font-size:13px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;max-width:120px;}}

td.col-anclaje{{font-size:12.5px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;max-width:150px;}}

td.col-action{{max-width:160px;}}

/* Dos acciones apiladas: "Ver en Amazon" (CTA principal, solido) arriba,
   "Ficha técnica" (accion secundaria, outline) debajo -- jerarquia
   visual clara para que no parezcan del mismo nivel de importancia. */
.action-group{{display:flex;flex-direction:column;gap:8px;}}

.btn-amazon-row{{
  display:block;background:var(--accent-deep);color:#fff;text-align:center;text-decoration:none;
  font-size:12.5px;font-weight:700;padding:9px 12px;border-radius:8px;
  font-family:'Inter',sans-serif;transition:background .15s;white-space:nowrap;width:100%;
}}
.btn-amazon-row:hover{{background:#B5471F;}}

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

<div class="proto-banner">⚠ Prototipo v16 — <b>no es la web real</b> — misma fuente que v4-v15: tools/output/auditoria_30_candidatos.json (sin cambios de dato en esta versión, solo ampliación de la ordenación)</div>
<p class="proto-note">
  Cambio sobre v15 (16-ago-2026): el selector <b>"Ordenar por"</b> añade 4 criterios de característica — ISOFIX, 360º, Orientación y Arnés — con prioridades categóricas ("X primero") en vez de menor/mayor, reorganizado en dos grupos (Datos numéricos / Características). Los 7 criterios numéricos y la integración en cabecera del punto 7.1 (Precio/Valoración/Rango de uso con ↕) no se han tocado. "Sin especificar" sigue siempre al final, en cualquier criterio.
</p>

<div class="page-head">
  <div class="eyebrow">Comparador de sillitas de coche · Prototipo PC</div>
  <h1>Comparativa de sillitas de coche</h1>
  <p>{len(productos)} modelos</p>
</div>

<div class="sort-toolbar">
  <label for="sortSelect">Ordenar por</label>
  <select id="sortSelect">
    <option value="default" selected>Sin ordenar (orden original)</option>
    <optgroup label="Datos numéricos">
      <option value="precio-asc">Precio: menor → mayor</option>
      <option value="precio-desc">Precio: mayor → menor</option>
      <option value="valoracion-desc">Valoración: mayor → menor</option>
      <option value="valoracion-asc">Valoración: menor → mayor</option>
      <option value="nval-desc">Nº de valoraciones: mayor → menor</option>
      <option value="nval-asc">Nº de valoraciones: menor → mayor</option>
      <option value="altura-asc">Altura: menor → mayor</option>
      <option value="altura-desc">Altura: mayor → menor</option>
      <option value="edad-asc">Edad: menor → mayor</option>
      <option value="edad-desc">Edad: mayor → menor</option>
      <option value="grupo-desc">Grupo: más grupos → menos grupos</option>
      <option value="grupo-asc">Grupo: menos grupos → más grupos</option>
      <option value="peso-asc">Peso: menor → mayor</option>
      <option value="peso-desc">Peso: mayor → menor</option>
    </optgroup>
    <optgroup label="Características">
      <option value="isofix-si">ISOFIX: Sí primero</option>
      <option value="isofix-no">ISOFIX: No primero</option>
      <option value="360-si">360º: Sí primero</option>
      <option value="360-no">360º: No primero</option>
      <option value="orientacion-ambas">Orientación: Ambas primero</option>
      <option value="orientacion-contramarcha">Orientación: A contramarcha primero</option>
      <option value="orientacion-favor">Orientación: A favor de la marcha primero</option>
      <option value="arnes-5">Arnés: 5 puntos primero</option>
      <option value="arnes-3">Arnés: 3 puntos primero</option>
      <option value="arnes-cinturon">Arnés: Cinturón del vehículo primero</option>
    </optgroup>
  </select>
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

<p class="foot-note">Prototipo generado por tools/build_comparativa_prototipo_v16.py a partir de tools/output/auditoria_30_candidatos.json — no modifica ningún archivo de producción ni el dataset auditado.</p>

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
// "Ver en Amazon" de la fila no debe disparar tambien el toggle de ficha
// tecnica (el click en cualquier punto de la fila abre la ficha, ver mas
// abajo) -- solo debe abrir el enlace.
document.querySelectorAll('.btn-amazon-row').forEach(link => {{
  link.addEventListener('click', (e) => {{ e.stopPropagation(); }});
}});
document.querySelectorAll('tr.main-row').forEach(row => {{
  row.addEventListener('click', () => {{
    row.querySelector('.btn-toggle').click();
  }});
}});

// ---------------------------------------------------------------------
// PUNTO 6 -- "Ordenar por". Lee los data-sort-* incrustados por Python
// (ver parse_altura_rango / parse_edad_rango_meses / parse_grupo_amplitud
// / parse_peso_max, definidos mas arriba en este mismo archivo) y reordena las
// filas en el DOM. No toca ningun dato, no recarga la pagina.
// ---------------------------------------------------------------------
(function setupSort() {{
  const select = document.getElementById('sortSelect');
  const tbody = document.querySelector('tbody');

  function getNum(row, attr) {{
    const v = row.dataset[attr];
    return (v === undefined || v === '') ? null : parseFloat(v);
  }}

  function getStr(row, attr) {{
    const v = row.dataset[attr];
    return (v === undefined || v === '') ? null : v;
  }}

  // Un solo campo numerico, misma columna para ambos sentidos (Precio,
  // Valoracion, Nº de valoraciones, Peso -- Peso SIEMPRE usa el maximo,
  // en los dos sentidos, tal como pidio el usuario).
  const SIMPLE_CRITERIA = {{
    'precio-asc':      {{attr: 'sortPrecio',     dir: 1}},
    'precio-desc':     {{attr: 'sortPrecio',     dir: -1}},
    'valoracion-desc': {{attr: 'sortValoracion', dir: -1}},
    'valoracion-asc':  {{attr: 'sortValoracion', dir: 1}},
    'nval-desc':       {{attr: 'sortNval',       dir: -1}},
    'nval-asc':        {{attr: 'sortNval',       dir: 1}},
    'peso-asc':        {{attr: 'sortPesoMax',    dir: 1}},
    'peso-desc':       {{attr: 'sortPesoMax',    dir: -1}},
  }};

  // Altura/Edad: el campo usado cambia segun el sentido (minimo para
  // "menor -> mayor", maximo para "mayor -> menor"), pedido explicito
  // del usuario -- no es un simple cambio de signo del mismo valor.
  const MINMAX_CRITERIA = {{
    'altura-asc':  {{attr: 'sortAlturaMin', dir: 1}},
    'altura-desc': {{attr: 'sortAlturaMax', dir: -1}},
    'edad-asc':    {{attr: 'sortEdadMin',   dir: 1}},
    'edad-desc':   {{attr: 'sortEdadMax',   dir: -1}},
  }};

  // ---- Ampliacion 16-ago-2026: ordenacion por CARACTERISTICAS ----
  // No son asc/desc: son prioridades categoricas que definimos
  // nosotros (p.ej. "ISOFIX: Sí primero"). ISOFIX/360º son binarios
  // (Sí/No); Orientación/Arnés tienen 3 categorias -- el criterio
  // elegido pasa a prioridad 0, el resto conserva su orden relativo de
  // base (BASE_ORDER), sin inventar un orden nuevo para las no
  // elegidas. "Sin especificar" (dato ausente) va SIEMPRE al final.
  const CATEGORY_BINARY = {{
    'isofix-si': {{attr: 'sortIsofixCat', first: 'si'}},
    'isofix-no': {{attr: 'sortIsofixCat', first: 'no'}},
    '360-si':    {{attr: 'sortGiro360Cat', first: 'si'}},
    '360-no':    {{attr: 'sortGiro360Cat', first: 'no'}},
  }};
  const ORIENTACION_BASE = ['ambas', 'contramarcha', 'favor'];
  const ORIENTACION_KEYS = {{
    'orientacion-ambas':        'ambas',
    'orientacion-contramarcha': 'contramarcha',
    'orientacion-favor':        'favor',
  }};
  const ARNES_BASE = ['5puntos', '3puntos', 'cinturon'];
  const ARNES_KEYS = {{
    'arnes-5':        '5puntos',
    'arnes-3':         '3puntos',
    'arnes-cinturon': 'cinturon',
  }};

  function compareCategoryBinary(a, b, key, origA, origB) {{
    const cfg = CATEGORY_BINARY[key];
    const va = getStr(a, cfg.attr), vb = getStr(b, cfg.attr);
    if (va === null && vb === null) return origA - origB;
    if (va === null) return 1;
    if (vb === null) return -1;
    const rank = v => v === cfg.first ? 0 : 1;
    const ra = rank(va), rb = rank(vb);
    if (ra !== rb) return ra - rb;
    return origA - origB;
  }}

  function compareRotate(a, b, key, attr, baseOrder, keysMap, origA, origB) {{
    const selected = keysMap[key];
    const va = getStr(a, attr), vb = getStr(b, attr);
    if (va === null && vb === null) return origA - origB;
    if (va === null) return 1;
    if (vb === null) return -1;
    const rank = v => v === selected ? -1 : baseOrder.indexOf(v);
    const ra = rank(va), rb = rank(vb);
    if (ra !== rb) return ra - rb;
    return origA - origB;
  }}

  function compareRows(a, b, key) {{
    const origA = parseInt(a.dataset.origIndex, 10);
    const origB = parseInt(b.dataset.origIndex, 10);

    if (key === 'default') {{
      return origA - origB;
    }}

    if (key === 'grupo-asc' || key === 'grupo-desc') {{
      const dir = key === 'grupo-asc' ? 1 : -1;
      const ga = getNum(a, 'sortGrupoNum'), gb = getNum(b, 'sortGrupoNum');
      // "Sin especificar" (sin prefijo "Grupo ") siempre al final, en
      // los dos sentidos.
      if (ga === null && gb === null) return origA - origB;
      if (ga === null) return 1;
      if (gb === null) return -1;
      if (ga !== gb) return dir * (ga - gb);
      // Empate en nº de etapas -> desempate por el primer grupo de la
      // secuencia, SIEMPRE de menor a mayor (regla fija, no depende del
      // sentido elegido).
      const fa = getNum(a, 'sortGrupoFirst'), fb = getNum(b, 'sortGrupoFirst');
      if (fa !== fb) return fa - fb;
      return origA - origB;
    }}

    if (CATEGORY_BINARY[key]) {{
      return compareCategoryBinary(a, b, key, origA, origB);
    }}
    if (ORIENTACION_KEYS[key]) {{
      return compareRotate(a, b, key, 'sortOrientacionCat', ORIENTACION_BASE, ORIENTACION_KEYS, origA, origB);
    }}
    if (ARNES_KEYS[key]) {{
      return compareRotate(a, b, key, 'sortArnesCat', ARNES_BASE, ARNES_KEYS, origA, origB);
    }}

    const cfg = SIMPLE_CRITERIA[key] || MINMAX_CRITERIA[key];
    if (!cfg) return origA - origB;
    const va = getNum(a, cfg.attr), vb = getNum(b, cfg.attr);
    // Sin dato para este criterio -> siempre al final, en los dos
    // sentidos (no se multiplica por dir).
    if (va === null && vb === null) return origA - origB;
    if (va === null) return 1;
    if (vb === null) return -1;
    if (va !== vb) return cfg.dir * (va - vb);
    return origA - origB;
  }}

  function applySort(key) {{
    // Cerrar cualquier ficha abierta al reordenar (mas limpio, no rompe
    // nada: cada boton conserva su propio panel_id y sigue funcionando
    // igual despues de reordenar).
    document.querySelectorAll('.btn-toggle.is-open').forEach(btn => btn.click());

    const rows = Array.from(document.querySelectorAll('tr.main-row'));
    rows.sort((a, b) => compareRows(a, b, key));
    rows.forEach(row => {{
      const panel = document.getElementById(row.dataset.target);
      tbody.appendChild(row);   // mover al final reinserta en el nuevo orden
      tbody.appendChild(panel); // su ficha tecnica le sigue inmediatamente detras
    }});
  }}

  select.addEventListener('change', () => applySort(select.value));
}})();

// ---------------------------------------------------------------------
// PUNTO 7.1 -- integracion visual de la ordenacion en la cabecera.
// NO reimplementa la ordenacion: unicamente cambia el `value` del
// <select id="sortSelect"> ya existente y dispara el mismo evento
// 'change' que ya escuchaba setupSort() de arriba -- el motor de
// ordenacion (compareRows/applySort) es exactamente el mismo. Esto es
// solo una segunda interfaz para disparar las mismas 14 claves.
// ---------------------------------------------------------------------
(function setupHeaderSort() {{
  const select = document.getElementById('sortSelect');

  function triggerSort(key) {{
    select.value = key;
    select.dispatchEvent(new Event('change'));
  }}

  const ICONS = {{
    precio: document.querySelector('[data-sort-icon="precio"]'),
    valoracion: document.querySelector('[data-sort-icon="valoracion"]'),
    rango: document.querySelector('[data-sort-icon="rango"]'),
  }};
  const THS = {{
    precio: document.querySelector('th.col-price'),
    valoracion: document.querySelector('th.col-valoracion'),
    rango: document.querySelector('th.col-rango'),
  }};
  const RANGO_KEYS = new Set([
    'altura-asc', 'altura-desc', 'edad-asc', 'edad-desc',
    'grupo-asc', 'grupo-desc', 'peso-asc', 'peso-desc',
  ]);

  function keyGroup(key) {{
    if (key === 'precio-asc' || key === 'precio-desc') return 'precio';
    if (key === 'valoracion-asc' || key === 'valoracion-desc') return 'valoracion';
    if (RANGO_KEYS.has(key)) return 'rango';
    return null;
  }}

  // Refleja en la cabecera cual es el criterio activo -- sea cual sea
  // el origen del cambio (select de toda la vida, boton de Precio/
  // Valoración, o item del menu de Rango de uso).
  function updateIndicators(key) {{
    Object.keys(ICONS).forEach(g => {{
      ICONS[g].textContent = '↕';
      ICONS[g].classList.remove('is-active');
      THS[g].classList.remove('is-active-sort');
    }});
    document.querySelectorAll('.th-sort-menu-btn.is-active').forEach(b => b.classList.remove('is-active'));

    const group = keyGroup(key);
    if (!group) return; // 'default' u otra clave -> cabecera neutra
    const dir = key.endsWith('-asc') ? '↑' : '↓';
    ICONS[group].textContent = dir;
    ICONS[group].classList.add('is-active');
    THS[group].classList.add('is-active-sort');
    if (group === 'rango') {{
      const btn = document.querySelector(`.th-sort-menu-btn[data-sort-key="${{key}}"]`);
      if (btn) btn.classList.add('is-active');
    }}
  }}
  select.addEventListener('change', () => updateIndicators(select.value));

  // Precio / Valoración: clic directo en la cabecera, alterna entre
  // los 2 sentidos ya existentes de ese criterio (mismo orden por
  // defecto que ya tenia el <select>: Precio empieza menor->mayor,
  // Valoración empieza mayor->menor).
  document.querySelector('[data-sort-toggle="precio"]').addEventListener('click', () => {{
    triggerSort(select.value === 'precio-asc' ? 'precio-desc' : 'precio-asc');
  }});
  document.querySelector('[data-sort-toggle="valoracion"]').addEventListener('click', () => {{
    triggerSort(select.value === 'valoracion-desc' ? 'valoracion-asc' : 'valoracion-desc');
  }});

  // Rango de uso: menu compacto con Altura/Edad/Grupo/Peso x 2 sentidos.
  // Se saca del <th> y se ancla a <body> con position:fixed calculado
  // por JS, para que el overflow:hidden de .table-shell / el
  // overflow-x:auto de .table-scroll no lo recorten.
  const menu = document.getElementById('rango-menu');
  const menuToggle = document.querySelector('[data-menu-toggle="rango-menu"]');
  document.body.appendChild(menu);

  function closeMenu() {{ menu.setAttribute('hidden', ''); }}
  function openMenu() {{
    const rect = menuToggle.getBoundingClientRect();
    const maxLeft = window.innerWidth - 226;
    menu.style.top = `${{rect.bottom + 6}}px`;
    menu.style.left = `${{Math.max(8, Math.min(rect.left, maxLeft))}}px`;
    menu.removeAttribute('hidden');
  }}
  menuToggle.addEventListener('click', (e) => {{
    e.stopPropagation();
    if (menu.hasAttribute('hidden')) openMenu(); else closeMenu();
  }});
  menu.querySelectorAll('.th-sort-menu-btn').forEach(btn => {{
    btn.addEventListener('click', (e) => {{
      e.stopPropagation();
      triggerSort(btn.dataset.sortKey);
      closeMenu();
    }});
  }});
  document.addEventListener('click', (e) => {{
    if (!menu.contains(e.target) && e.target !== menuToggle) closeMenu();
  }});
  document.addEventListener('keydown', (e) => {{
    if (e.key === 'Escape') closeMenu();
  }});
}})();

// Autocomprobacion (visible en consola del navegador)
(function selfCheck() {{
  const rows = document.querySelectorAll('tr.main-row').length;
  const panels = document.querySelectorAll('tr.detail-row').length;
  const toggles = document.querySelectorAll('.btn-toggle').length;
  const amazonRowBtns = document.querySelectorAll('.btn-amazon-row').length;
  const sortableHeaders = document.querySelectorAll('th.is-sortable').length;
  const rangoMenuItems = document.querySelectorAll('.th-sort-menu-btn').length;
  const selectOptions = document.querySelectorAll('#sortSelect option').length;
  console.log(`[prototipo v16] filas de producto: ${{rows}} | paneles de ficha: ${{panels}} | botones toggle: ${{toggles}} | botones Ver en Amazon (fila): ${{amazonRowBtns}} | cabeceras ordenables: ${{sortableHeaders}} | items menu Rango de uso: ${{rangoMenuItems}} | opciones select: ${{selectOptions}}`);
  console.assert(rows === {len(productos)}, `Se esperaban {len(productos)} productos, hay ${{rows}}`);
  console.assert(rows === panels && panels === toggles, 'Descuadre entre filas, paneles y botones');
  console.assert(rows === amazonRowBtns, 'Descuadre entre filas y botones "Ver en Amazon"');
  console.assert(sortableHeaders === 3, `Se esperaban 3 cabeceras ordenables (Precio/Valoración/Rango de uso), hay ${{sortableHeaders}}`);
  console.assert(rangoMenuItems === 8, `Se esperaban 8 items en el menu de Rango de uso, hay ${{rangoMenuItems}}`);
  console.assert(selectOptions === 25, `Se esperaban 25 opciones en el select (1 default + 14 numericas + 10 caracteristicas), hay ${{selectOptions}}`);
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
