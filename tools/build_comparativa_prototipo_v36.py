#!/usr/bin/env python3
"""
build_comparativa_prototipo_v36.py

Evolucion sobre v35 (ver tools/build_comparativa_prototipo_v35.py) --
CORRECCION del bug reportado en la Fase 1 del responsive movil: en
DevTools (430x932, "iPhone 15 Pro Max") seguia viendose la tabla de PC
completa encogida, no la comparativa VS de 2 productos.

Causa raiz: faltaba la etiqueta

    <meta name="viewport" content="width=device-width, initial-scale=1.0">

en el <head>. Sin ella, el navegador (y el emulador de dispositivo de
DevTools) renderiza la pagina sobre un viewport de LAYOUT por defecto
(~980px en Chrome/Edge) y despues la escala para caber en la pantalla
fisica del dispositivo -- de ahi el aspecto de "tabla de escritorio
encogida". Los media queries (`@media (max-width:768px)`) evaluan ese
ancho de LAYOUT, no el ancho fisico del dispositivo: sin la etiqueta,
el layout nunca baja de ~980px por mucho que el movil sea de
375/390/430px, asi que `.table-shell{{display:none}}` /
`.mobile-compare{{display:block}}` nunca llegaban a aplicarse. La logica
de la Fase 1 (build_mobile_compare, el CSS .mobile-compare/.mc-*, el
propio media query) era correcta desde v35 -- simplemente nunca se
activaba por esta etiqueta ausente.

Cambio UNICO: se añade esa etiqueta <meta name="viewport"> al <head>.
Nada mas se toca -- ni la tabla de PC, ni las tarjetas VS ya creadas,
ni el dataset, ni las ordenaciones, ni ningun otro contenido.

Uso:
    python tools/build_comparativa_prototipo_v36.py
"""

import html as html_lib
import json
import re

SRC = "tools/output/auditoria_30_candidatos.json"
OUT = "prototipo-comparativa-sillas-v36.html"

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


# Responsive movil -- Fase 1 (18-ago-2026): comparativa de 2 sillitas
# enfrentadas (VS), estructura especifica para movil (NO la tabla de PC
# comprimida). Los 2 ASIN son de ejemplo -- cualquiera de los 30 del
# dataset vale, la arquitectura queda lista para que una fase futura
# permita elegir que 2 comparar. Las imagenes son fotos REALES
# descargadas de la propia ficha de Amazon de cada producto (mismo
# pipeline de tools/amazon_sillas_coche.py: descarga + recuadre 600x600
# sin deformar), guardadas en images/sillas-coche/ -- el dataset JSON no
# tenia ningun campo de imagen todavia, asi que no habia ninguna imagen
# real ya disponible en el proyecto para estos productos antes de esto.
DEMO_COMPARE_ASINS = ["B0B97Z1C6M", "B0CZ47FKZL"]
DEMO_COMPARE_IMAGES = {
    "B0B97Z1C6M": "images/sillas-coche/B0B97Z1C6M.webp",
    "B0CZ47FKZL": "images/sillas-coche/B0CZ47FKZL.webp",
}


def build_mobile_compare(productos):
    """Construye el bloque VS de 2 productos para movil, usando
    EXACTAMENTE el mismo dataset y los mismos helpers de formato
    (fmt_precio/fmt_valoracion/fmt_n_val) que ya usa build_row() para la
    tabla de PC -- ningun dato nuevo, ninguna duplicacion manual."""
    por_asin = {p["asin"]: p for p in productos}
    columnas = []
    for asin in DEMO_COMPARE_ASINS:
        p = por_asin[asin]
        marca = p.get("marca") or SIN_ESPECIFICAR
        modelo = p.get("modelo") or SIN_ESPECIFICAR
        precio = fmt_precio(p.get("precio")) or SIN_ESPECIFICAR
        valoracion = fmt_valoracion(p.get("valoracion"))
        n_val = fmt_n_val(p.get("n_val"))
        rating_html = (
            f'<span class="mc-product-rating">★ {valoracion}</span>'
            if valoracion else
            f'<span class="mc-product-rating cell-unspecified">{SIN_ESPECIFICAR}</span>'
        )
        reviews_html = (
            f'<span class="mc-product-reviews">{n_val} valoraciones</span>'
            if n_val else ""
        )
        alt = html_lib.escape(f"{marca} {modelo}")
        columnas.append(f'''      <div class="mc-product">
        <img class="mc-product-img" src="{DEMO_COMPARE_IMAGES[asin]}" alt="{alt}" width="140" height="140" loading="lazy">
        <span class="mc-product-brand">{html_lib.escape(marca)}</span>
        <span class="mc-product-model">{html_lib.escape(modelo)}</span>
        {rating_html}
        {reviews_html}
        <span class="mc-product-price">{html_lib.escape(precio)}</span>
      </div>''')

    return f'''<div class="mobile-compare">
  <div class="mc-vs-card">
{columnas[0]}
    <div class="mc-divider"></div>
    <div class="mc-vs">VS</div>
{columnas[1]}
  </div>
  <!-- Fase 2 (pendiente): matriz de caracteristicas (Precio/Normativa/
       Rango de uso/Altura/Grupo/Peso/ISOFIX/Orientación/360º/Arnés/
       Ficha técnica) para estos 2 productos. Contenedor preparado, sin
       contenido todavia -- se rellenara en la siguiente fase. -->
  <div class="mc-features" id="mc-features"></div>
</div>'''


# Punto 7.8 (16-ago-2026): rediseño completo de la ficha tecnica.
# Los 6 campos "principales" de la ficha, en este orden fijo -- SIEMPRE
# se muestran los 6 (incluido "Sin especificar" cuando no hay dato), no
# se ocultan silenciosamente. Nunca se repite en la ficha nada que ya
# este perfectamente representado en la tabla principal (Valoracion,
# Nº valoraciones, Normativa, ISOFIX/360º/Orientacion basicos, Edad/
# Altura/Grupo/Peso maximo, Arnes basico).
FICHA_CAMPOS_PRINCIPALES = [
    ("Reclinable", "reclinable"),
    ("Reposacabezas", "reposacabezas"),
    ("Protección lateral", "proteccion_lateral"),
    ("Peso de la silla", "peso_silla"),
    ("Funda lavable", "funda_lavable"),
    ("Travel System", "travel_system"),
]

# Valores de "tipo_instalacion" que NO aportan nada mas alla de lo que
# ya dice la columna ISOFIX (Sí/No) de la tabla -- se consideran
# triviales y no se muestran como particularidad.
_INSTALACION_TRIVIAL_SI = {"isofix"}
_INSTALACION_TRIVIAL_NO = {"cinturón", "cinturón de seguridad"}


def instalacion_particularidad(tipo_instalacion: str, isofix: str):
    """Devuelve el texto de 'tipo_instalacion' SOLO si aporta un matiz
    mas alla de lo que ya se ve en la columna ISOFIX de la tabla (p.ej.
    'ISOFIX + Top Tether', 'ISOFIX (vía base)', 'Cinturón + ISOFIX
    opcional'). Si el valor es simplemente 'ISOFIX' (cuando ISOFIX=Sí)
    o 'Cinturón'/'Cinturón de seguridad' (cuando ISOFIX=No) -- es decir,
    una repeticion trivial del dato ya normalizado en la tabla -- ,
    devuelve None y no se muestra nada. Nunca inventa texto: solo
    decide si mostrar o no el dato ya existente."""
    v = (tipo_instalacion or "").strip()
    if es_sin_especificar(v) or es_revisar(v):
        return None
    vl = v.lower()
    isofix_si = (isofix or "").strip().startswith("Sí")
    if isofix_si and vl in _INSTALACION_TRIVIAL_SI:
        return None
    if not isofix_si and vl in _INSTALACION_TRIVIAL_NO:
        return None
    return v


def valor_badge(valor, sin_especificar_como_guion=False):
    """ISOFIX / 360º (punto 7.6, 16-ago-2026): texto explicito "Sí"/"No"
    en vez de simbolos ✓/✕ -- solo cambia la presentacion, el dato
    origen (v.startswith("Sí")/"No") es el mismo que ya se usaba para
    decidir el simbolo antes.

    "Sin especificar": por defecto se muestra el texto completo, pero
    360º (16-ago-2026, ajuste tras revisar v22) vuelve a mostrarlo como
    "—", igual que antes del punto 7.6 -- decision explicita del
    usuario solo para esta columna. ISOFIX se queda con el texto
    completo (aunque en la practica nunca lo necesita: 0/30 productos
    tienen ISOFIX "Sin especificar")."""
    v = valor.strip()
    if es_sin_especificar(v):
        if sin_especificar_como_guion:
            return f'<span class="txt-plain txt-plain--unk" title="{SIN_ESPECIFICAR}">{GUION}</span>'
        return f'<span class="txt-plain txt-plain--unk" title="{SIN_ESPECIFICAR}">{SIN_ESPECIFICAR}</span>'
    matiz = v if v not in ("Sí", "No") else ""
    title_attr = f' title="{html_lib.escape(matiz)}"' if matiz else ""
    if v.startswith("Sí"):
        return f'<span class="txt-plain"{title_attr}>Sí</span>'
    if v.startswith("No"):
        return f'<span class="txt-plain"{title_attr}>No</span>'
    return f'<span class="txt-plain txt-plain--unk" title="{html_lib.escape(v)}">{html_lib.escape(v)}</span>'


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


def normalizar_recien_nacido(texto: str) -> str:
    """Punto 7.11 (16-ago-2026): en la representacion visual de Edad,
    'Recién nacido' se muestra como '0' (se entiende como el inicio del
    rango dentro de la columna Edad). Cambio puramente de
    presentacion -- no toca el dato del dataset ni otros calculos
    (p.ej. parse_edad_rango_meses, usado para ordenar, ya trataba
    'recién nacido' como 0 meses de forma independiente)."""
    return re.sub(r'Recién nacido', '0', texto, flags=re.IGNORECASE)


def rango_uso_html(altura, edad, grupo, peso):
    """Fusiona Edad + Altura + Grupo + Peso en una sola celda. Jerarquia
    visual del punto 7.3 corregida (16-ago-2026): SOLO 2 niveles, no 4.
    Edad y Altura son ambos datos PRINCIPALES -- mismo tamaño, mismo
    peso tipografico, misma clase CSS ("rango-primary"); Edad va antes
    porque es el primer dato del bloque, no porque destaque mas. Grupo
    y Peso son ambos datos SECUNDARIOS (misma clase "rango-secondary").
    Cada linea SOLO aparece si el dato existe -- nunca se rellena el
    hueco con guion ni con el texto 'Sin especificar', simplemente no
    se genera esa linea. El espaciado entre lineas lo resuelve el CSS
    con selectores de hermano adyacente (ver td.col-rango), asi que
    sigue siendo correcto aunque falte alguno de los 4 campos.

    Punto 7.11: las lineas se envuelven en un <div class="rango-block">
    para que el centrado vertical se aplique al BLOQUE COMPLETO como
    una unidad (no linea a linea) -- ver CSS de .rango-block."""
    lineas = []
    campos = (
        (normalizar_recien_nacido(edad), "rango-primary"),
        (altura, "rango-primary"),
        (grupo, "rango-secondary"),
        (peso, "rango-secondary"),
    )
    for valor_campo, css_cls in campos:
        texto, matiz = texto_compacto(valor_campo)
        if texto == GUION:
            continue
        title_attr = f' title="{html_lib.escape(matiz)}"' if matiz and matiz != texto else ""
        lineas.append(f'<span class="{css_cls}"{title_attr}>{html_lib.escape(texto)}</span>')
    if not lineas:
        return f'<span class="cell-unspecified">{GUION}</span>'
    return '<div class="rango-block">' + "\n".join(lineas) + "</div>"


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


def orientacion_compacto_tabla(valor):
    """SOLO para la celda de la tabla principal (16-ago-2026): recorta
    'A favor de la marcha' -> 'A favor' para evitar que se trunque
    visualmente ('A favor de la ma...'). 'Ambas' y 'A contramarcha' no
    cambian. Puramente cosmetico -- el dato real (dataset, ordenacion,
    ficha tecnica) sigue siendo 'A favor de la marcha'; el tooltip
    conserva el texto completo cuando se recorta."""
    texto, matiz = texto_compacto(valor)
    if texto in (GUION, "Revisar"):
        return texto, matiz
    compacto = re.sub(r'^A favor de la marcha\b', 'A favor', texto)
    if compacto != texto:
        return compacto, valor.strip()
    return texto, matiz


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
    """Punto 7.16 (16-ago-2026): el texto va envuelto en un
    <span class="cell-block"> (display:block) para que
    vertical-align:middle (heredado de "tbody td") centre el contenido
    con precision de pixel -- igual patron ya usado en Rango de uso
    (.rango-block) y Acciones (.action-group). Sin el envoltorio, el
    texto (contenido inline suelto) queda descentrado 2-3px por las
    metricas de line-height/fuente, en vez de por el propio
    vertical-align. No cambia alineacion horizontal, tamaño, color ni
    ningun otro estilo -- solo el layout interno para el centrado
    vertical."""
    texto, matiz = compactor(valor)
    estado_cls = "cell-unspecified" if texto == GUION else ("cell-revisar" if es_revisar(texto) else "")
    cls = " ".join(c for c in [col_cls, estado_cls] if c)
    cls_attr = f' class="{cls}"' if cls else ""
    title_attr = f' title="{html_lib.escape(matiz)}"' if matiz else ""
    return f'<td{cls_attr}{title_attr}><span class="cell-block">{html_lib.escape(texto)}</span></td>'


def detail_item(label, valor, siempre_mostrar=False):
    """Punto 7.8 (16-ago-2026), ajustado tras revisar v26: TODAS las
    filas de la ficha (los 6 campos principales y, cuando existan, las
    particularidades de instalación/arnés) comparten exactamente el
    mismo estilo -- no hay un formato especial para particularidades,
    se integran como una fila normal mas de la misma lista.
    siempre_mostrar=True (los 6 campos principales) NUNCA se oculta --
    si no hay dato, se muestra literalmente "Sin especificar" (para
    que el usuario sepa que no hemos podido determinarlo, en vez de
    ocultarlo en silencio). Las particularidades solo se llaman cuando
    YA se ha comprobado que existen (instalacion_particularidad /
    arnes_tiene_matiz_oculto), asi que nunca se ocultan tampoco."""
    v = (valor or "").strip()
    if not v:
        v = SIN_ESPECIFICAR
    if not siempre_mostrar and HIDE_UNSPECIFIED_IN_DETAIL and es_sin_especificar(v):
        return None
    extra_cls = " cell-revisar" if es_revisar(v) else ""
    if es_revisar(v):
        texto = "Revisar"
        title_attr = f' title="{html_lib.escape(v)}"'
    elif es_sin_especificar(v):
        # Se normaliza al texto generico "Sin especificar" (sin
        # matices tipo "explícito") -- son distinciones internas de
        # auditoria, no aportan nada al padre que lee la ficha. El
        # matiz completo se conserva en el tooltip.
        texto = SIN_ESPECIFICAR
        title_attr = f' title="{html_lib.escape(v)}"' if v != SIN_ESPECIFICAR else ""
    else:
        texto = v
        title_attr = ""
    if es_sin_especificar(v):
        extra_cls += " detail-value--unk"
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

    # Punto 7.2 (16-ago-2026): jerarquia visual -- puntuacion protagonista
    # arriba, nº de valoraciones secundario debajo, con la palabra
    # "valoraciones" (antes solo el numero suelto). Los valores (valoracion,
    # n_val) son exactamente los mismos que ya se formateaban con
    # fmt_valoracion/fmt_n_val -- no se recalcula ni redondea nada, solo
    # cambia el marcado/CSS.
    if valoracion:
        valoracion_html = f'<span class="val-star">⭐ {valoracion}</span>'
        if n_val:
            valoracion_html += f'<span class="val-count">{n_val} valoraciones</span>'
    else:
        valoracion_html = f'<span class="cell-unspecified">{GUION}</span>'

    rango_html = rango_uso_html(altura, edad, grupo, peso_recomendado)

    # Punto 7.8 (16-ago-2026): ficha tecnica rediseñada -- SOLO los 6
    # campos complementarios (siempre visibles, "Sin especificar"
    # incluido) + particularidades de instalacion/arnes cuando aporten
    # algo mas alla de lo ya normalizado en la tabla principal. Ya NO
    # se muestran Valoracion/Nº valoraciones/Tipo de instalacion basico
    # /Arnes basico -- estan duplicados con la tabla o se sustituyen
    # por su version "particularidad".
    #
    # Ajuste 16-ago-2026 (tras revisar v26): las particularidades ya NO
    # forman un bloque visual aparte (titulo naranja + seccion propia)
    # -- se integran como una fila mas dentro de la MISMA lista, con
    # exactamente el mismo estilo que Reclinable/Reposacabezas/etc.
    # Etiquetas alineadas con el nombre habitual del dato ("Tipo de
    # instalación", "Arnés") en vez de "Particularidad de...".
    ficha_campos = [
        detail_item(label, limpiar_procedencia(p.get(key) or ""), siempre_mostrar=True)
        for label, key in FICHA_CAMPOS_PRINCIPALES
    ]

    tipo_instalacion = campo(p, "tipo_instalacion")
    particularidad_instalacion = instalacion_particularidad(tipo_instalacion, isofix)
    if particularidad_instalacion:
        ficha_campos.append(detail_item("Tipo de instalación", particularidad_instalacion, siempre_mostrar=True))
    if arnes_tiene_matiz_oculto(arnes):
        ficha_campos.append(detail_item("Arnés", arnes, siempre_mostrar=True))

    detail_groups = '<div class="ficha-grid">' + "\n".join(ficha_campos) + "</div>"

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
      {celda_principal(orientacion, "col-orientacion", orientacion_compacto_tabla)}
      <td class="col-360">{valor_badge(giro_360, sin_especificar_como_guion=True)}</td>
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
        <div class="ficha-header">
          <span class="ficha-title">Ficha técnica</span>
          <button type="button" class="ficha-close" data-close-panel="{panel_id}" aria-label="Cerrar ficha técnica">✕</button>
        </div>
        {detail_groups}
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
# col-action se ensancha de 130 a 160px (unico ancho que cambia en v13)
# para dar sitio a las dos acciones apiladas (Ver en Amazon + Ficha
# tecnica). col-valoracion pasa de 70 a 84px en v18 (punto 7.2) para que
# quepa la palabra "valoraciones" sin desbordar. col-isofix/col-360
# subieron de 55 a 76px en v22 (punto 7.6) para que "especificar"
# (~66px a 12.5px) cupiera sin desbordar; en v23 el usuario pidio
# volver a mostrar 360º "Sin especificar" como "—" (no como texto), asi
# que ninguna de las dos columnas vuelve a necesitar el ancho extra --
# vuelven a 55px, su ancho original. El resto de columnas mantiene su
# ancho.
COLUMN_WIDTHS = [250, 85, 84, 90, 190, 55, 120, 55, 150, 160]

# Menu de "Rango de uso": 4 sub-criterios x 2 sentidos, con las mismas
# claves (data-sort-key) que ya entiende el motor de ordenacion (JS) --
# no se inventa ninguna clave nueva.
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

# Menus de "Orientación" y "Arnés" (16-ago-2026, a peticion del usuario
# tras revisar v16): 3 prioridades categoricas cada uno, mismas claves
# que entiende el motor de ordenacion.
ORIENTACION_MENU_ITEMS = [
    ("orientacion-ambas", "Ambas primero"),
    ("orientacion-contramarcha", "A contramarcha primero"),
    ("orientacion-favor", "A favor primero"),
]
ARNES_MENU_ITEMS = [
    ("arnes-5", "5 puntos primero"),
    ("arnes-3", "3 puntos primero"),
    ("arnes-cinturon", "Cinturón del vehículo primero"),
]

# Menu de "Valoración" (Ajuste, 18-ago-2026): dos criterios INDEPENDIENTES
# -- Valoración y Nº de valoraciones -- cada uno con sus 2 sentidos, sin
# desempate cruzado entre ellos (mismas claves que ya entendia el motor
# de ordenacion: valoracion-asc/desc ya existian, nval-asc/desc tambien
# existian desde antes pero sin punto de entrada en la interfaz).
VALORACION_MENU_ITEMS = [
    ("valoracion-desc", "Valoración: mayor → menor"),
    ("valoracion-asc", "Valoración: menor → mayor"),
    ("nval-desc", "Nº valoraciones: mayor → menor"),
    ("nval-asc", "Nº valoraciones: menor → mayor"),
]


def build_simple_menu(items):
    return "\n".join(
        f'      <button type="button" class="th-sort-menu-btn th-sort-menu-btn--block" data-sort-key="{key}">{html_lib.escape(texto)}</button>'
        for key, texto in items
    )


def build_header_cell(label, cls):
    """Punto 7.1 + ampliacion 16-ago-2026: TODAS las columnas que son
    criterio de ordenacion llevan indicador ↕ clicable -- Precio/
    Valoración/ISOFIX/360º alternan directamente sus 2 sentidos; Rango
    de uso/Orientación/Arnés abren un menu compacto (para no meter 8/3/3
    indicadores sueltos en la cabecera). Normativa y Acciones se quedan
    como texto plano (no son criterio de ordenacion)."""
    if cls == "col-price":
        return f'''<th class="{cls} is-sortable">
      <button type="button" class="th-sort-btn" data-sort-toggle="precio">{html_lib.escape(label)}<span class="th-sort-icon" data-sort-icon="precio">↕</span></button>
    </th>'''
    if cls == "col-valoracion":
        return f'''<th class="{cls} is-sortable">
      <button type="button" class="th-sort-btn" data-menu-toggle="valoracion-menu">{html_lib.escape(label)}<span class="th-sort-icon" data-sort-icon="valoracion">↕</span></button>
      <div class="th-sort-menu" id="valoracion-menu" hidden>
{build_simple_menu(VALORACION_MENU_ITEMS)}
      </div>
    </th>'''
    if cls == "col-isofix":
        return f'''<th class="{cls} is-sortable">
      <button type="button" class="th-sort-btn" data-sort-toggle="isofix">{html_lib.escape(label)}<span class="th-sort-icon" data-sort-icon="isofix">↕</span></button>
    </th>'''
    if cls == "col-360":
        return f'''<th class="{cls} is-sortable">
      <button type="button" class="th-sort-btn" data-sort-toggle="giro360">{html_lib.escape(label)}<span class="th-sort-icon" data-sort-icon="giro360">↕</span></button>
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
    if cls == "col-orientacion":
        return f'''<th class="{cls} is-sortable">
      <button type="button" class="th-sort-btn" data-menu-toggle="orientacion-menu">{html_lib.escape(label)}<span class="th-sort-icon" data-sort-icon="orientacion">↕</span></button>
      <div class="th-sort-menu" id="orientacion-menu" hidden>
{build_simple_menu(ORIENTACION_MENU_ITEMS)}
      </div>
    </th>'''
    if cls == "col-anclaje":
        return f'''<th class="{cls} is-sortable">
      <button type="button" class="th-sort-btn" data-menu-toggle="arnes-menu">{html_lib.escape(label)}<span class="th-sort-icon" data-sort-icon="arnes">↕</span></button>
      <div class="th-sort-menu" id="arnes-menu" hidden>
{build_simple_menu(ARNES_MENU_ITEMS)}
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
    mobile_compare_html = build_mobile_compare(productos)

    html_out = f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<!-- Correccion Fase 1 responsive (18-ago-2026): faltaba esta etiqueta.
     Sin ella, el navegador (y el emulador de dispositivo de DevTools)
     renderiza la pagina sobre un viewport de layout por defecto (~980px
     en Chrome/Edge) y luego la escala para caber en la pantalla fisica
     -- por eso se veia la tabla de escritorio encogida en vez de
     activarse @media (max-width:768px): los media queries evaluan el
     ANCHO DE LAYOUT, no el ancho fisico del dispositivo, y sin esta
     etiqueta ese ancho de layout nunca baja de ~980px por mucho que el
     movil sea de 375/390/430px. -->
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>PROTOTIPO v36 — Comparativa sillitas de coche</title>
<meta name="robots" content="noindex,nofollow">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Fredoka:wght@600&family=JetBrains+Mono:wght@600&display=swap" rel="stylesheet">
<style>
:root{{
  --bg:#FAFAF8; --ink:#1C1C1E; --ink-soft:#6B6B70; --line:#E4E2DC; --card:#FFFFFF;
  --accent:#FF8A65; --accent-deep:#D85A30; --revisar:#B5841C; --revisar-bg:#FBF2DE;
  /* Pulido estetico (18-ago-2026): version mas suave de --line, solo
     para los separadores horizontales ENTRE FILAS del cuerpo de la
     tabla (nunca sustituye a --line en el resto de usos: borde de
     .table-shell, borde bajo la cabecera, bordes de menus, etc., que
     mantienen el contraste original). */
  --line-row:color-mix(in srgb, var(--line) 55%, var(--card));
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

/* Responsive movil -- Fase 1 (18-ago-2026): comparativa VS de 2
   productos, estructura pensada especificamente para movil (NO la
   tabla de PC comprimida con scroll horizontal). Oculta por defecto
   (fuera del breakpoint movil, mas abajo, coexiste sin verse); el
   media query al final de este bloque intercambia .table-shell <->
   .mobile-compare -- en escritorio la tabla se ve exactamente igual
   que antes, en movil desaparece y aparece esta comparativa. */
.mobile-compare{{display:none;}}
.mc-vs-card{{
  position:relative; display:flex; align-items:stretch;
  background:var(--card); border:1px solid var(--line); border-radius:14px;
  box-shadow:0 2px 8px rgba(0,0,0,.05); overflow:hidden;
}}
.mc-product{{
  flex:1 1 50%; min-width:0; display:flex; flex-direction:column; align-items:center;
  text-align:center; gap:3px; padding:20px 12px 22px;
}}
.mc-product-img{{width:100%; max-width:132px; aspect-ratio:1/1; object-fit:contain; margin-bottom:8px;}}
.mc-product-brand{{font-size:11px; font-weight:700; color:var(--accent-deep); text-transform:uppercase; letter-spacing:.03em;}}
.mc-product-model{{font-size:14px; font-weight:600; color:var(--ink); line-height:1.3; margin-bottom:4px;}}
.mc-product-rating{{font-size:13px; font-weight:700; color:var(--ink);}}
.mc-product-reviews{{font-size:11.5px; font-weight:400; color:var(--ink-soft); margin-bottom:6px;}}
.mc-product-price{{font-size:16px; font-weight:700; color:var(--ink);}}
/* Linea vertical central sutil (mismo tono ya usado para separadores
   discretos, --line-row del Pulido estetico) + insignia circular "VS"
   encima, mismo lenguaje visual que el resto del comparador (borde
   var(--line), sombra suave, texto en --accent-deep). */
.mc-divider{{position:absolute; top:18px; bottom:18px; left:50%; width:1px; background:var(--line-row);}}
.mc-vs{{
  position:absolute; top:50%; left:50%; transform:translate(-50%,-50%);
  width:32px; height:32px; border-radius:50%; background:var(--card);
  border:1px solid var(--line); box-shadow:0 2px 6px rgba(0,0,0,.1);
  display:flex; align-items:center; justify-content:center;
  font-family:'JetBrains Mono',monospace; font-size:11px; font-weight:700; color:var(--accent-deep);
}}
/* Fase 2 (pendiente): aqui ira la matriz de caracteristicas, debajo de
   la tarjeta VS -- de momento el contenedor esta vacio y sin estilos
   propios de contenido. */
.mc-features{{margin-top:20px;}}

@media (max-width:768px){{
  .table-shell{{display:none;}}
  .mobile-compare{{display:block;}}
}}

table{{border-collapse:separate;border-spacing:0;table-layout:fixed;}}

/* Punto 7.1 -- rediseño de cabecera (16-ago-2026): mas aire vertical,
   tipografia un punto mas grande y con mas letter-spacing, mismo fondo
   diferenciado (#F4F2EE) que ya existia. Producto se queda a la
   izquierda (valor por defecto); el resto de columnas se centra mas
   abajo con selectores especificos. */
thead th{{
  background:#F4F2EE; color:var(--ink); font-size:12.5px; font-weight:700;
  text-transform:uppercase; letter-spacing:.045em;
  /* Pulido estetico (18-ago-2026): 19px->15px, para que la cabecera
     pese menos visualmente ahora que el cuerpo tambien es mas compacto
     (ver tbody td mas abajo) -- misma reduccion aplicada en .th-sort-btn
     para que el boton siga rellenando todo el <th> sin descuadrarse. */
  padding:15px 14px; text-align:left; white-space:nowrap;
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
  width:100%; height:100%; padding:15px 14px; margin:0; border:0; background:none;
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
/* Menus de un solo campo con 3 prioridades (Orientación/Arnés): sin el
   agrupador "campo + 2 sentidos" de Rango de uso, cada boton ocupa toda
   la fila. */
.th-sort-menu-btn--block{{display:block;width:100%;margin:1px 0;}}

/* Pulido estetico (18-ago-2026): 14px->11px de padding vertical (mas
   compacta, sin llegar a apretada -- Rango de uso, la celda mas alta
   con sus 4 lineas posibles, se sigue leyendo comoda) y separador entre
   filas mas sutil (--line-row en vez de --line, ver :root) para que no
   pese como una cuadricula administrativa. El padding horizontal (12px)
   NO se toca: varias columnas tienen ancho fijo estrecho (55px ISOFIX/
   360º, 84px Valoración) y ensancharlo arriesgaria desbordar texto. La
   alineacion vertical (vertical-align:middle) tampoco cambia. */
tbody td{{
  padding:11px 12px; font-size:14px; color:var(--ink);
  border-bottom:1px solid var(--line-row);
  vertical-align:middle;
}}
tbody tr.main-row:last-of-type td{{border-bottom:1px solid var(--line-row);}}
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
/* Pulido estetico (18-ago-2026): 2px->3px de aire entre MARCA y MODELO
   -- ajuste minimo pedido explicitamente, sin tocar tipografias ni
   colores. */
.prod-info{{display:flex;flex-direction:column;gap:3px;min-width:0;}}
.prod-brand{{font-size:11px;font-weight:700;color:var(--accent-deep);text-transform:uppercase;letter-spacing:.03em;}}
.prod-model{{font-size:13px;font-weight:600;color:var(--ink);white-space:normal;line-height:1.3;}}

td.col-price{{text-align:center;}}
.price-current{{font-size:14.5px;font-weight:700;color:var(--ink);white-space:nowrap;}}

/* Punto 7.2 (16-ago-2026): jerarquia visual clara entre puntuacion (dato
   protagonista) y nº de valoraciones (secundario), ambos centrados en la
   columna. Ancho +14px (70->84) respecto a v17 -- lo justo para que quepa
   la palabra "valoraciones" sin desbordar ni envolver a media palabra;
   sigue siendo una columna compacta. */
/* Punto 7.x (16-ago-2026): TAMAÑO BASE UNIFICADO para todas las
   columnas de informacion (Normativa/Rango de uso/ISOFIX/Orientación/
   360º/Arnés/Valoración) = 12.5px, tomando como referencia el tamaño
   que ya tenia Normativa ("R129 / i-Size"). La jerarquia visual se
   consigue SOLO con font-weight (negrita donde tiene sentido), nunca
   con tamaños de fuente distintos. Unica excepcion explicita: el nº de
   valoraciones (.val-count), que sigue mas pequeño por ser dato
   secundario. */
td.col-valoracion{{text-align:center;white-space:normal;max-width:84px;}}
.val-star{{display:block;font-size:12.5px;font-weight:700;color:var(--ink);white-space:nowrap;line-height:1.2;}}
.val-count{{display:block;font-size:11.5px;font-weight:400;color:var(--ink-soft);margin-top:4px;line-height:1.3;}}

td.col-normativa{{font-size:12.5px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;max-width:90px;text-align:center;}}

/* "Rango de uso" -- Edad y Altura son datos PRINCIPALES: mismo tamaño
   BASE (12.5px, igual que Normativa) que Grupo/Peso, la diferencia es
   solo font-weight (700 vs 400) y color (ink vs ink-soft) -- ya NO hay
   dos tamaños de fuente distintos dentro de la columna. El espaciado
   entre lineas sigue via selectores de hermano adyacente (sin cambios
   respecto a v20): separacion pequeña DENTRO del mismo nivel
   (Edad->Altura, o Grupo->Peso), separacion algo mayor en el cambio de
   nivel (de Edad/Altura a Grupo/Peso).
   Punto 7.11 (16-ago-2026): el centrado vertical del BLOQUE COMPLETO
   (no linea a linea) se apoya en vertical-align:middle de la celda
   (ya heredado de "tbody td") + el envoltorio .rango-block, que agrupa
   las 2-4 lineas en una unica caja para que se centren juntas como un
   solo bloque, sea cual sea el numero de lineas presentes. */
td.col-rango{{white-space:normal;max-width:190px;text-align:center;}}
.rango-block{{display:block;}}
.rango-primary{{display:block;font-size:12.5px;font-weight:700;color:var(--ink);overflow:hidden;text-overflow:ellipsis;white-space:nowrap;}}
.rango-secondary{{display:block;font-size:12.5px;font-weight:400;color:var(--ink-soft);overflow:hidden;text-overflow:ellipsis;white-space:nowrap;}}
.rango-primary + .rango-primary,
.rango-secondary + .rango-secondary{{margin-top:2px;}}
.rango-primary + .rango-secondary,
.rango-secondary + .rango-primary{{margin-top:5px;}}

.cell-unspecified{{color:#9C9A93;font-weight:400;font-size:13px;}}
.cell-revisar{{color:var(--revisar);font-weight:600;}}

/* Punto 7.16 (16-ago-2026): envoltorio de bloque para centrado vertical
   de precision -- ver celda_principal() en el script. Sin display
   propio distinto de "block" no cambia nada mas (tamaño/color/peso se
   heredan del <td> padre). */
.cell-block{{display:block;}}

/* ISOFIX/360º -- punto 7.6 (16-ago-2026): texto explicito "Sí"/"No" en
   vez de simbolos ✓/✕. Mismo tamaño base (12.5px) que Normativa/
   Orientación/Arnés, texto plano sin negrita ni color. Ajuste v23: 360º
   "Sin especificar" vuelve a mostrarse como "—" (decision del usuario
   tras revisar v22) -- ninguna de las dos columnas necesita ya el
   ancho/padding extra que se añadio en v22 para la palabra
   "especificar", asi que vuelven a max-width:55px y al padding
   estandar de la tabla (sin override). Punto 7.16: display pasa de
   inline-block a block para el mismo centrado vertical de precision
   (el text-align:center de la celda ya centra el texto igual que
   antes, wq el bloque ocupa todo el ancho disponible). */
td.col-isofix,td.col-360{{text-align:center;max-width:55px;}}
.txt-plain{{display:block;font-size:12.5px;font-weight:400;color:var(--ink);line-height:1.3;}}
.txt-plain--unk{{color:#9C9A93;}}

td.col-orientacion{{font-size:12.5px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;max-width:120px;text-align:center;}}

td.col-anclaje{{font-size:12.5px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;max-width:150px;text-align:center;}}

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
.btn-amazon-row:hover{{background:#B5471F;text-decoration:none;}}

.btn-toggle{{
  display:block;background:none;border:1px solid var(--line);color:var(--ink-soft);
  font-size:12px;font-weight:600;padding:8px 14px;border-radius:8px;cursor:pointer;
  font-family:'Inter',sans-serif;transition:.15s;width:100%;
}}
.btn-toggle:hover, .btn-toggle.is-open{{border-color:var(--accent-deep);color:var(--accent-deep);background:#FFF7F3;}}

tr.detail-row td{{padding:0;}}
tr.detail-row[hidden]{{display:none;}}

/* Punto 7.8 (16-ago-2026): ficha tecnica rediseñada -- bloque compacto,
   sin lineas horizontales entre cada campo, cabecera clara con cierre
   propio. Mismo fondo que antes (#FBF9F5), sin tarjetas ni bordes
   innecesarios. */
.ficha-header{{
  display:flex;align-items:center;justify-content:space-between;
  background:#FBF9F5;padding:16px 26px 4px;
}}
.ficha-title{{font-size:11.5px;font-weight:700;color:var(--accent-deep);text-transform:uppercase;letter-spacing:.05em;}}
.ficha-close{{
  background:none;border:0;color:var(--ink-soft);font-size:13px;line-height:1;cursor:pointer;
  padding:4px 6px;border-radius:6px;transition:.15s;
}}
.ficha-close:hover{{color:var(--accent-deep);background:#FFF1EA;}}

.ficha-grid{{
  display:grid;grid-template-columns:1fr 1fr;gap:2px 32px;
  background:#FBF9F5;padding:10px 26px 14px;
}}
/* Campos principales -- ajuste 16-ago-2026 (punto 7.8.x): nombre y
   valor van JUNTOS como una sola unidad (antes "justify-content:
   space-between" empujaba el valor al extremo derecho de la columna,
   dejando un hueco enorme). Ahora es un flex normal con un gap fijo y
   corto (10px) entre nombre y valor, sin borde debajo de cada campo. */
.detail-item{{
  display:flex;align-items:baseline;justify-content:flex-start;gap:10px;
  padding:6px 0;white-space:normal;
}}
.detail-label{{font-size:12px;font-weight:600;color:var(--ink-soft);flex-shrink:0;}}
.detail-value{{font-size:12.5px;color:var(--ink);font-weight:400;text-align:left;}}
.detail-value--unk{{color:#9C9A93;font-weight:400;font-style:italic;}}
.detail-value.cell-revisar{{color:var(--revisar);cursor:help;border-bottom:1px dotted var(--revisar);}}

/* Ajuste 16-ago-2026 (tras revisar v26): las particularidades de
   instalación/arnés ya NO llevan bloque/titulo propio -- se integran
   como filas normales dentro de .ficha-grid, con el mismo
   .detail-item/.detail-label/.detail-value que Reclinable,
   Reposacabezas, etc. (sin reglas CSS aparte). */

.detail-amazon{{padding:16px 26px 22px;background:#FBF9F5;}}
.btn-amazon{{
  display:inline-block;background:var(--accent-deep);color:#fff;font-size:13px;font-weight:700;
  padding:10px 18px;border-radius:8px;white-space:nowrap;transition:background .15s;text-decoration:none;
}}
.btn-amazon:hover{{background:#B5471F;text-decoration:none;}}

@media (max-width:640px){{
  .ficha-grid{{grid-template-columns:1fr;}}
}}

.foot-note{{margin-top:18px;font-size:12px;color:var(--ink-soft);}}
</style>
</head>
<body>

<div class="proto-banner">⚠ Prototipo v36 — <b>no es la web real</b> — misma fuente que v4-v35: tools/output/auditoria_30_candidatos.json (sin cambios de dato en esta versión)</div>
<p class="proto-note">
  Corrección (18-ago-2026): faltaba <code>&lt;meta name="viewport"&gt;</code> en el <code>&lt;head&gt;</code> — sin ella el breakpoint móvil (≤768px) nunca se activaba y se veía la tabla de escritorio encogida. Ya corregido: en móvil (≤768px) aparece la comparativa <b>2 sillitas enfrentadas (VS)</b>; en escritorio, la tabla PC exactamente igual que antes.
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

{mobile_compare_html}

<p class="foot-note">Prototipo generado por tools/build_comparativa_prototipo_v36.py a partir de tools/output/auditoria_30_candidatos.json — no modifica ningún archivo de producción ni la web real.</p>

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

// Punto 7.8 -- boton "✕" DENTRO de la ficha tecnica para cerrarla. No
// duplica logica: simplemente simula un clic en el boton "Ficha
// técnica" de la fila (mismo panel_id), que ya sabe abrir/cerrar.
document.querySelectorAll('.ficha-close').forEach(btn => {{
  btn.addEventListener('click', (e) => {{
    e.stopPropagation();
    const toggle = document.querySelector(`.btn-toggle[data-toggle="${{btn.dataset.closePanel}}"]`);
    if (toggle) toggle.click();
  }});
}});

// ---------------------------------------------------------------------
// PUNTO 6 -- "Ordenar por". Lee los data-sort-* incrustados por Python
// (ver parse_altura_rango / parse_edad_rango_meses / parse_grupo_amplitud
// / parse_peso_max, definidos mas arriba en este mismo archivo) y reordena las
// filas en el DOM. No toca ningun dato, no recarga la pagina.
// ---------------------------------------------------------------------
(function setupSort() {{
  // Punto 7.14 (16-ago-2026): se elimino el <select id="sortSelect">
  // "Ordenar por" -- el estado de ordenacion actual ahora vive en esta
  // variable en vez de en select.value. setupSort() y la integracion
  // de cabecera (antes "setupHeaderSort", punto 7.1) comparten este
  // mismo scope para poder leerla/actualizarla sin un elemento
  // intermedio en el DOM.
  let currentSortKey = 'default';
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
  // Valoración, Nº de valoraciones, Peso -- Peso SIEMPRE usa el maximo,
  // en los dos sentidos, tal como pidio el usuario). Valoración y Nº de
  // valoraciones son criterios INDEPENDIENTES (Ajuste 18-ago-2026): cada
  // uno ordena solo por su propio campo, sin desempatar con el otro --
  // en empate cae directo al "return origA - origB" de mas abajo, igual
  // que el resto de esta tabla.
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
    currentSortKey = key;
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

  // ---------------------------------------------------------------------
  // PUNTO 7.1 -- integracion visual de la ordenacion en la cabecera.
  // Unico punto de entrada a la ordenacion (punto 7.14: ya no hay
  // <select> intermedio) -- cada icono/menu de cabecera llama
  // directamente a applySort() + updateIndicators() a traves de
  // triggerSort(). El motor de ordenacion (compareRows/applySort) es
  // exactamente el mismo de siempre.
  // ---------------------------------------------------------------------
  function triggerSort(key) {{
    applySort(key);
    updateIndicators(key);
  }}

  const ICONS = {{
    precio: document.querySelector('[data-sort-icon="precio"]'),
    valoracion: document.querySelector('[data-sort-icon="valoracion"]'),
    rango: document.querySelector('[data-sort-icon="rango"]'),
    isofix: document.querySelector('[data-sort-icon="isofix"]'),
    giro360: document.querySelector('[data-sort-icon="giro360"]'),
    orientacion: document.querySelector('[data-sort-icon="orientacion"]'),
    arnes: document.querySelector('[data-sort-icon="arnes"]'),
  }};
  const THS = {{
    precio: document.querySelector('th.col-price'),
    valoracion: document.querySelector('th.col-valoracion'),
    rango: document.querySelector('th.col-rango'),
    isofix: document.querySelector('th.col-isofix'),
    giro360: document.querySelector('th.col-360'),
    orientacion: document.querySelector('th.col-orientacion'),
    arnes: document.querySelector('th.col-anclaje'),
  }};
  const RANGO_KEYS = new Set([
    'altura-asc', 'altura-desc', 'edad-asc', 'edad-desc',
    'grupo-asc', 'grupo-desc', 'peso-asc', 'peso-desc',
  ]);

  function keyGroup(key) {{
    if (key === 'precio-asc' || key === 'precio-desc') return 'precio';
    if (key === 'valoracion-asc' || key === 'valoracion-desc' || key === 'nval-asc' || key === 'nval-desc') return 'valoracion';
    if (RANGO_KEYS.has(key)) return 'rango';
    if (key === 'isofix-si' || key === 'isofix-no') return 'isofix';
    if (key === '360-si' || key === '360-no') return 'giro360';
    if (key === 'orientacion-ambas' || key === 'orientacion-contramarcha' || key === 'orientacion-favor') return 'orientacion';
    if (key === 'arnes-5' || key === 'arnes-3' || key === 'arnes-cinturon') return 'arnes';
    return null;
  }}

  // Grupos cuyo indicador es binario (↑/↓ segun sentido asc/desc real).
  // ISOFIX/360º son prioridades categoricas (Sí/No primero), no tienen
  // "sentido" asc/desc -- su icono activo se queda fijo (↕ resaltado en
  // color), igual que Orientación/Arnés.
  const DIRECTIONAL_GROUPS = new Set(['precio', 'valoracion', 'rango']);

  // Refleja en la cabecera cual es el criterio activo -- sea cual sea
  // el origen del cambio (boton directo o item de alguno de los menus).
  function updateIndicators(key) {{
    Object.keys(ICONS).forEach(g => {{
      ICONS[g].textContent = '↕';
      ICONS[g].classList.remove('is-active');
      THS[g].classList.remove('is-active-sort');
    }});
    document.querySelectorAll('.th-sort-menu-btn.is-active').forEach(b => b.classList.remove('is-active'));

    const group = keyGroup(key);
    if (!group) return; // 'default' u otra clave -> cabecera neutra
    ICONS[group].textContent = DIRECTIONAL_GROUPS.has(group) ? (key.endsWith('-asc') ? '↑' : '↓') : '↕';
    ICONS[group].classList.add('is-active');
    THS[group].classList.add('is-active-sort');
    const btn = document.querySelector(`.th-sort-menu-btn[data-sort-key="${{key}}"]`);
    if (btn) btn.classList.add('is-active');
  }}

  // Precio / Valoración / ISOFIX / 360º: clic directo en la cabecera,
  // alterna entre los 2 sentidos/prioridades ya existentes de ese
  // criterio (mismo orden por defecto que ya tenia el <select> antes
  // de eliminarse en el punto 7.14).
  function wireToggle(name, onKey, offKey) {{
    document.querySelector(`[data-sort-toggle="${{name}}"]`).addEventListener('click', () => {{
      triggerSort(currentSortKey === onKey ? offKey : onKey);
    }});
  }}
  wireToggle('precio', 'precio-asc', 'precio-desc');
  wireToggle('isofix', 'isofix-si', 'isofix-no');
  wireToggle('giro360', '360-si', '360-no');

  // Rango de uso / Orientación / Arnés / Valoración: menu compacto. Cada menu se
  // saca del <th> y se ancla a <body> con position:fixed calculado por
  // JS, para que el overflow:hidden de .table-shell / el
  // overflow-x:auto de .table-scroll no lo recorten. Solo un menu
  // puede estar abierto a la vez.
  let openMenuEl = null;
  function closeOpenMenu() {{
    if (openMenuEl) {{ openMenuEl.setAttribute('hidden', ''); openMenuEl = null; }}
  }}
  function wireMenu(menuId, toggleSelector) {{
    const menu = document.getElementById(menuId);
    const toggle = document.querySelector(toggleSelector);
    document.body.appendChild(menu);

    function open() {{
      closeOpenMenu();
      const rect = toggle.getBoundingClientRect();
      const maxLeft = window.innerWidth - 226;
      menu.style.top = `${{rect.bottom + 6}}px`;
      menu.style.left = `${{Math.max(8, Math.min(rect.left, maxLeft))}}px`;
      menu.removeAttribute('hidden');
      openMenuEl = menu;
    }}
    toggle.addEventListener('click', (e) => {{
      e.stopPropagation();
      if (menu.hasAttribute('hidden')) open(); else closeOpenMenu();
    }});
    menu.querySelectorAll('.th-sort-menu-btn').forEach(btn => {{
      btn.addEventListener('click', (e) => {{
        e.stopPropagation();
        triggerSort(btn.dataset.sortKey);
        closeOpenMenu();
      }});
    }});
    return {{menu, toggle}};
  }}
  const menus = [
    wireMenu('rango-menu', '[data-menu-toggle="rango-menu"]'),
    wireMenu('orientacion-menu', '[data-menu-toggle="orientacion-menu"]'),
    wireMenu('arnes-menu', '[data-menu-toggle="arnes-menu"]'),
    wireMenu('valoracion-menu', '[data-menu-toggle="valoracion-menu"]'),
  ];
  document.addEventListener('click', (e) => {{
    if (!openMenuEl) return;
    const stillInside = menus.some(m => m.menu === openMenuEl && (m.menu.contains(e.target) || m.toggle === e.target));
    if (!stillInside) closeOpenMenu();
  }});
  document.addEventListener('keydown', (e) => {{
    if (e.key === 'Escape') closeOpenMenu();
  }});
}})();

// Autocomprobacion (visible en consola del navegador)
(function selfCheck() {{
  const rows = document.querySelectorAll('tr.main-row').length;
  const panels = document.querySelectorAll('tr.detail-row').length;
  const toggles = document.querySelectorAll('.btn-toggle').length;
  const amazonRowBtns = document.querySelectorAll('.btn-amazon-row').length;
  const sortableHeaders = document.querySelectorAll('th.is-sortable').length;
  const totalMenuItems = document.querySelectorAll('.th-sort-menu-btn').length;
  const sortSelectRestante = document.querySelectorAll('#sortSelect, .sort-toolbar').length;
  const fichaCampos = document.querySelectorAll('.ficha-grid .detail-item').length;
  const fichaBloquesSueltos = document.querySelectorAll('.ficha-particularidades, .detail-item--particularidad').length;
  const fichaCloseBtns = document.querySelectorAll('.ficha-close').length;
  console.log(`[prototipo v36] filas de producto: ${{rows}} | paneles de ficha: ${{panels}} | botones toggle: ${{toggles}} | botones Ver en Amazon (fila): ${{amazonRowBtns}} | cabeceras ordenables: ${{sortableHeaders}} | items en menus de cabecera: ${{totalMenuItems}} | campos ficha (min 6x30): ${{fichaCampos}} | botones cerrar ficha: ${{fichaCloseBtns}} | bloques de particularidad sueltos (deben ser 0): ${{fichaBloquesSueltos}} | restos del selector "Ordenar por" (debe ser 0): ${{sortSelectRestante}}`);
  console.assert(rows === {len(productos)}, `Se esperaban {len(productos)} productos, hay ${{rows}}`);
  console.assert(rows === panels && panels === toggles, 'Descuadre entre filas, paneles y botones');
  console.assert(rows === amazonRowBtns, 'Descuadre entre filas y botones "Ver en Amazon"');
  console.assert(sortableHeaders === 7, `Se esperaban 7 cabeceras ordenables (Precio/Valoración/Rango de uso/ISOFIX/360º/Orientación/Arnés), hay ${{sortableHeaders}}`);
  console.assert(totalMenuItems === 18, `Se esperaban 18 items en total (8 Rango de uso + 3 Orientación + 3 Arnés + 4 Valoración), hay ${{totalMenuItems}}`);
  console.assert(fichaCampos >= rows * 6, `Se esperaban al menos ${{rows * 6}} campos de ficha (6 fijos por producto + particularidades opcionales), hay ${{fichaCampos}}`);
  console.assert(fichaCloseBtns === rows, `Se esperaban ${{rows}} botones de cerrar ficha, hay ${{fichaCloseBtns}}`);
  console.assert(fichaBloquesSueltos === 0, `Ya no debe existir ningun bloque de particularidad independiente, hay ${{fichaBloquesSueltos}}`);
  console.assert(sortSelectRestante === 0, `El selector "Ordenar por" debe estar completamente eliminado, quedan ${{sortSelectRestante}} restos`);
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
