#!/usr/bin/env python3
"""
build_comparativa_prototipo_v51.py

Evolucion sobre v50 (ver tools/build_comparativa_prototipo_v50.py) --
CORRECCION acordada con el usuario (18-ago-2026): con "Filtrar por
edad" activo (p.ej. "2 años"), si el usuario queria volver a ver todos
los productos usando el buscador GENERAL ("Buscar por marca o modelo",
el de fuera de los slots), el filtro de edad seguia aplicado -- los
resultados se quedaban limitados a esa edad aunque el usuario ya no
quisiera filtrar por edad.

Diagnostico: el buscador general SI reseteaba el filtro de edad cuando
ABRIA el panel desde cero (resetPanelState(), corregido en v49) -- pero
si el panel YA estaba abierto (p.ej. porque el usuario acababa de usar
"Filtrar por edad" DENTRO del panel) y volvia a escribir en el buscador
general, `handleTopSearch()` entraba directamente en la rama de "panel
ya abierto", que solo sincronizaba el texto y volvia a pintar
resultados SIN tocar el filtro de edad -- de ahi que se quedara
"pegado".

Cambio (unico, en handleTopSearch()): se añade una rama `else` para el
caso "panel ya abierto" que limpia `ageFilter` (y el `<select>`) antes
de re-renderizar. El buscador GENERAL pasa a ser siempre la via rapida
para "ver todos los productos que coincidan con este texto", sin
arrastrar un filtro de edad dejado activo. El buscador Y el filtro de
edad DENTRO del panel (el campo de busqueda propio del panel +
"Filtrar por edad") siguen siendo acumulativos entre si exactamente
igual que antes -- este cambio solo afecta al campo de fuera de los
slots.

No se toca: el reseteo de estado ya corregido en v49
(resetPanelState()), la correccion de foco de v50, la logica del
filtro de edad en si (passesAgeFilter, AGE_FILTER_OPTIONS), la logica
de asignacion de slot, el diseño de las tarjetas de resultado, la
tabla de PC, el dataset, la matriz de caracteristicas, la ficha
tecnica, la tarjeta VS, las imagenes, la logica de comparacion ni las
ordenaciones.

Uso:
    python tools/build_comparativa_prototipo_v51.py
"""

import html as html_lib
import json
import re

SRC = "tools/output/auditoria_30_candidatos.json"
OUT = "prototipo-comparativa-sillas-v51.html"

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


# Fase 2 (18-ago-2026): filas de la matriz de caracteristicas movil, en
# el orden pedido. "attr" es una clave interna (no un campo del
# dataset) que build_mobile_feature_values() usa para saber que
# fragmento HTML devolver -- la fuente real de cada valor sigue siendo
# exactamente la misma funcion/campo que ya usa build_row() para la
# tabla de PC (definida justo debajo).
# Ajuste (18-ago-2026): "Precio" se elimina de la matriz -- ya se
# muestra en la tarjeta VS superior, no hace falta duplicarlo. "Rango
# de uso" deja de ser una sola fila combinada (Edad/Altura/Grupo/Peso
# apilados en una sola celda, con altura variable segun cuantas lineas
# tuviera cada sillita -- eso era lo que desalineaba Sillita 1 y
# Sillita 2 entre si) y pasa a 4 filas independientes, una por
# atributo, en el orden pedido por el usuario (Edad, Altura, Peso,
# Grupo -- distinto del orden interno de rango_uso_html, que es Edad/
# Altura/Grupo/Peso). Al ser filas de grid normales (igual que
# Normativa/ISOFIX/etc.), cada atributo comparte fila/altura entre las
# 2 columnas automáticamente -- ya no se puede desalinear.
# Ajuste (18-ago-2026): las 2 ultimas filas cambian de orden -- Arnés
# antes que 360º (antes era al reves). Solo afecta a esta lista (el
# orden de columnas de la tabla de PC, COLUMN_HEADERS, no se toca).
MOBILE_FEATURE_ROWS = [
    ("Normativa", "normativa"),
    ("Edad", "edad"),
    ("Altura", "altura"),
    ("Peso", "peso"),
    ("Grupo", "grupo"),
    ("ISOFIX", "isofix"),
    ("Orientación", "orientacion"),
    ("Arnés", "arnes"),
    ("360º", "giro360"),
]


def _mc_valor_compacto(valor, compactor=texto_compacto):
    """Version SIN <td> de celda_principal() (esa devuelve un <td>
    completo, aqui hace falta solo el <span> interior para poder
    colocarlo dentro de una celda de la matriz de movil) -- misma
    logica exacta (mismo compactor, mismas clases cell-unspecified/
    cell-revisar, mismo title con el matiz), solo cambia el envoltorio
    HTML.

    Ajuste (18-ago-2026), SOLO movil: cuando no hay dato, el texto
    visible pasa de "—" (GUION) a "No especificado" -- pedido explicito
    del usuario, unicamente para esta matriz. texto_compacto() (PC y
    movil) sigue devolviendo GUION internamente sin cambios -- esta
    funcion es la unica que decide como se PRESENTA ese GUION, y solo
    se usa aqui (nunca en la tabla de PC, que sigue mostrando "—" via
    celda_principal(), sin tocar)."""
    texto, matiz = compactor(valor)
    if texto == GUION:
        return '<span class="cell-unspecified">No especificado</span>'
    estado_cls = "cell-revisar" if es_revisar(texto) else ""
    cls_attr = f' class="{estado_cls}"' if estado_cls else ""
    title_attr = f' title="{html_lib.escape(matiz)}"' if matiz else ""
    return f'<span{cls_attr}{title_attr}>{html_lib.escape(texto)}</span>'


def _mc_valor_badge(valor):
    """Version SOLO movil de valor_badge() -- misma deteccion Sí/No que
    la funcion compartida con PC (valor_badge(), que NO se toca: ISOFIX
    y 360º de la tabla de PC siguen exactamente igual), pero cuando no
    hay dato el texto es "No especificado" en vez de "Sin especificar"/
    "—". Usada unicamente en build_mobile_feature_values() (ISOFIX y
    360º de la matriz movil)."""
    v = valor.strip()
    if es_sin_especificar(v):
        return '<span class="txt-plain txt-plain--unk">No especificado</span>'
    matiz = v if v not in ("Sí", "No") else ""
    title_attr = f' title="{html_lib.escape(matiz)}"' if matiz else ""
    if v.startswith("Sí"):
        return f'<span class="txt-plain"{title_attr}>Sí</span>'
    if v.startswith("No"):
        return f'<span class="txt-plain"{title_attr}>No</span>'
    return f'<span class="txt-plain txt-plain--unk" title="{html_lib.escape(v)}">{html_lib.escape(v)}</span>'


def _mc_rango_campo(valor):
    """UN atributo individual de Edad/Altura/Peso/Grupo para la matriz
    movil. Regla EXPLICITA pedida por el usuario (18-ago-2026), distinta
    del resto del prototipo: si no hay dato, la celda se deja
    COMPLETAMENTE VACIA -- sin guion, sin "Sin especificar", sin ningun
    texto -- para no sugerir que la sillita "no tiene" ese atributo
    cuando en realidad es que no tenemos el dato. La celda en si (el
    <div class="mc-feat-val">) se sigue generando igual, vacia, para
    que la fila no pierda su altura ni se desalinee con la otra
    columna. "Revisar" SI se muestra (no es una ausencia de dato, es un
    dato marcado para revisar -- mismo criterio que en el resto de la
    app)."""
    texto, matiz = texto_compacto(valor)
    if texto == GUION:
        return ""
    if es_revisar(texto):
        return f'<span class="cell-revisar" title="{html_lib.escape(matiz)}">Revisar</span>'
    title_attr = f' title="{html_lib.escape(matiz)}"' if matiz and matiz != texto else ""
    return f'<span{title_attr}>{html_lib.escape(texto)}</span>'


def build_mobile_feature_values(p):
    """Un valor renderizado por cada fila de MOBILE_FEATURE_ROWS, para
    UN producto. Reutiliza exactamente los mismos campos (campo()) que
    ya usa build_row() para la tabla de PC -- ningun dato nuevo,
    ninguna segunda fuente de informacion. "Precio" ya no se calcula
    aqui (se elimino de la matriz, se muestra solo en la tarjeta VS).
    Edad/Altura/Peso/Grupo usan _mc_rango_campo() -- celda vacia si no
    hay dato, en vez de "Sin especificar"/"—" (pedido explicito del
    usuario para estos 4 campos, distinto del resto de la app y NO
    afectado por el ajuste de "No especificado" mas abajo -- ver su
    propio docstring); Edad normaliza "Recién nacido" -> "0" igual que
    ya hace rango_uso_html() para la tabla de PC. ISOFIX/360º usan
    _mc_valor_badge() (version movil de valor_badge()) y Normativa/
    Orientación/Arnés usan _mc_valor_compacto() -- ambas muestran
    "No especificado" en vez de "—"/"Sin especificar" cuando no hay
    dato, SOLO en esta matriz movil (ver sus docstrings)."""
    normativa = campo(p, "normativa")
    altura = campo(p, "altura")
    edad = campo(p, "edad")
    grupo = campo(p, "grupo")
    peso_recomendado = campo(p, "peso_recomendado")
    isofix = campo(p, "isofix")
    orientacion = campo(p, "orientacion")
    giro_360 = campo(p, "giro_360")
    arnes = campo(p, "arnes")

    return {
        "normativa": _mc_valor_compacto(normativa),
        "edad": _mc_rango_campo(normalizar_recien_nacido(edad)),
        "altura": _mc_rango_campo(altura),
        "peso": _mc_rango_campo(peso_recomendado),
        "grupo": _mc_rango_campo(grupo),
        "isofix": _mc_valor_badge(isofix),
        "orientacion": _mc_valor_compacto(orientacion, orientacion_compacto_tabla),
        "giro360": _mc_valor_badge(giro_360),
        "arnes": _mc_valor_compacto(arnes, arnes_compacto_tabla),
    }


def build_mobile_features(productos_ab):
    """Matriz CARACTERÍSTICA | SILLITA A | SILLITA B (grid de 3
    columnas -- cada fila son 3 <div> consecutivos, ver CSS
    .mc-features). Los valores de las 2 columnas de producto son los
    mismos que ya calcula build_mobile_feature_values() a partir del
    dataset real -- no hay ningun dato escrito a mano aqui.

    Selector de sillitas (fase siguiente, 18-ago-2026): cada celda de
    valor lleva `data-feat`/`data-slot` para que el selector movil
    pueda localizarla y sustituir su contenido cuando el usuario cambia
    de sillita, sin tocar la logica de calculo de valores (sigue
    siendo build_mobile_feature_values(), la misma de siempre)."""
    valores = [build_mobile_feature_values(p) for p in productos_ab]
    filas = []
    for label, attr in MOBILE_FEATURE_ROWS:
        filas.append(f'''  <div class="mc-feat-label">{html_lib.escape(label)}</div>
  <div class="mc-feat-val" data-feat="{attr}" data-slot="a">{valores[0][attr]}</div>
  <div class="mc-feat-val" data-feat="{attr}" data-slot="b">{valores[1][attr]}</div>''')
    return '<div class="mc-features" id="mc-features">\n' + "\n".join(filas) + '\n</div>'


# Fase 2 -- Ficha tecnica movil (18-ago-2026): 5 campos EXCLUSIVOS de la
# ficha (no repiten nada de MOBILE_FEATURE_ROWS/la matriz principal).
# Travel System queda fuera a peticion expresa del usuario (solo 4/30
# productos con dato, 13% de cobertura).
# Ajuste (18-ago-2026), SOLO movil: la etiqueta de "Reposacabezas" pasa
# a "Reposacabezas: altura regulable" para dejar claro que el dato
# compara si es regulable en altura, no simplemente si la sillita tiene
# reposacabezas -- el campo/valor (reposacabezas, Sí/No/No especificado)
# no cambia, solo el texto de la etiqueta. .mc-feat-label ya envuelve el
# texto de forma natural (sin white-space:nowrap ni ellipsis), asi que
# no hace falta ningun cambio de CSS para que se vea en 2 lineas.
MOBILE_FICHA_ROWS = [
    ("Reposacabezas: altura regulable", "reposacabezas"),
    ("Peso de la silla", "peso_silla"),
    ("Protección lateral", "proteccion_lateral"),
    ("Reclinable", "reclinable"),
    ("Funda lavable", "funda_lavable"),
]


def _mc_medida(valor):
    """Para 'Peso de la silla' (unico campo de la ficha movil que NO es
    Si/No, es una medida) -- mismo criterio Revisar que el resto del
    prototipo (cell-revisar), el valor no se reduce a Si/No porque no
    tiene sentido para un peso.

    Ajuste (18-ago-2026), SOLO movil: sin dato, el texto pasa de
    "Sin especificar" a "No especificado" -- para unificar con el resto
    de la matriz movil (mismo cambio ya hecho en _mc_valor_compacto()/
    _mc_valor_badge()). Esta funcion ya era exclusiva de movil (no la
    usa la tabla de PC), asi que el cambio es directo aqui."""
    v = (valor or "").strip()
    if es_sin_especificar(v):
        return '<span class="cell-unspecified">No especificado</span>'
    if es_revisar(v):
        return f'<span class="cell-revisar" title="{html_lib.escape(v)}">Revisar</span>'
    return f'<span>{html_lib.escape(v)}</span>'


def build_mobile_ficha_values(p):
    """Un valor por cada fila de MOBILE_FICHA_ROWS, para UN producto.
    Los 4 campos Si/No (Reposacabezas/Protección lateral/Reclinable/
    Funda lavable) usan _mc_valor_badge() -- version movil de
    valor_badge() (que la tabla de PC sigue usando tal cual para
    ISOFIX/360º, sin tocar) -- distingue los 3 estados: 'Sí' (dato
    confirma que existe), 'No' (dato confirma explicitamente que no
    existe -- nunca inventado, solo aparece si el dataset ya trae un
    'No' literal) y "No especificado" (sin dato) en gris discreto
    (clase txt-plain--unk, ya usada en toda la app) -- nunca se
    convierte una ausencia en 'No'.

    Ajuste (18-ago-2026): antes usaba valor_badge() (texto "Sin
    especificar" para el caso sin dato); ahora usa _mc_valor_badge()
    para unificar con el resto de la matriz movil, que ya decia "No
    especificado" desde el ajuste anterior -- mismo cambio de texto,
    ninguna otra logica distinta."""
    reposacabezas = campo(p, "reposacabezas")
    peso_silla = campo(p, "peso_silla")
    proteccion_lateral = campo(p, "proteccion_lateral")
    reclinable = campo(p, "reclinable")
    funda_lavable = campo(p, "funda_lavable")
    return {
        "reposacabezas": _mc_valor_badge(reposacabezas),
        "peso_silla": _mc_medida(peso_silla),
        "proteccion_lateral": _mc_valor_badge(proteccion_lateral),
        "reclinable": _mc_valor_badge(reclinable),
        "funda_lavable": _mc_valor_badge(funda_lavable),
    }


def build_mobile_ficha(productos_ab):
    """Seccion 'Ficha técnica' colapsable, debajo de la matriz
    principal -- mismo lenguaje visual (misma tarjeta con borde/radio/
    sombra, mismas clases .mc-feat-label/.mc-feat-val que la matriz
    principal, reutilizadas tal cual). Empieza cerrada (hidden); el
    <script> mas abajo añade el toggle.

    Selector de sillitas: igual que en build_mobile_features(), cada
    celda lleva `data-ficha`/`data-slot` para que el selector movil
    pueda actualizarla al cambiar de sillita."""
    valores = [build_mobile_ficha_values(p) for p in productos_ab]
    filas = []
    for label, attr in MOBILE_FICHA_ROWS:
        filas.append(f'''  <div class="mc-feat-label">{html_lib.escape(label)}</div>
  <div class="mc-feat-val" data-ficha="{attr}" data-slot="a">{valores[0][attr]}</div>
  <div class="mc-feat-val" data-ficha="{attr}" data-slot="b">{valores[1][attr]}</div>''')
    panel = '<div class="mc-ficha-panel" id="mc-ficha-panel" hidden>\n' + "\n".join(filas) + '\n  </div>'
    return f'''<div class="mc-ficha">
  <button type="button" class="mc-ficha-toggle" id="mc-ficha-toggle" aria-expanded="false" aria-controls="mc-ficha-panel">
    <span>Ficha técnica</span>
    <span class="mc-ficha-toggle-icon" aria-hidden="true">▾</span>
  </button>
  {panel}
</div>'''


def build_mobile_thumb_html(p, img_cls, ph_cls=""):
    """Imagen real si ya la tenemos descargada (DEMO_COMPARE_IMAGES,
    ver comentario mas arriba -- de momento solo 2 de los 30 productos
    la tienen), o si no el MISMO fallback que ya usa la tabla de PC
    para TODOS sus productos: un recuadro con las iniciales de la
    marca (iniciales()), nunca un placeholder generico/inventado."""
    marca = p.get("marca") or SIN_ESPECIFICAR
    modelo = p.get("modelo") or SIN_ESPECIFICAR
    alt = html_lib.escape(f"{marca} {modelo}")
    imagen = DEMO_COMPARE_IMAGES.get(p["asin"])
    if imagen:
        return f'<img class="{img_cls}" src="{imagen}" alt="{alt}" width="140" height="140" loading="lazy">'
    cls = f"{img_cls} mc-thumb-ph{(' ' + ph_cls) if ph_cls else ''}"
    return f'<div class="{cls}" aria-hidden="true">{html_lib.escape(iniciales(marca))}</div>'


def build_mobile_vs_slot_inner(p):
    """Contenido interior de una columna de la tarjeta VS (imagen +
    marca + modelo + valoración + nº valoraciones + precio) para UN
    producto -- extraido a funcion propia (18-ago-2026, fase del
    selector) para poder reutilizarlo tanto en el render inicial en
    servidor (los 2 productos de ejemplo) como en el JSON que consume
    el selector movil para poder cambiar de sillita sin recargar la
    pagina. Misma logica exacta de siempre, ningun dato nuevo."""
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
    thumb_html = build_mobile_thumb_html(p, "mc-product-img")
    return f'''{thumb_html}
        <span class="mc-product-brand">{html_lib.escape(marca)}</span>
        <span class="mc-product-model">{html_lib.escape(modelo)}</span>
        {rating_html}
        {reviews_html}
        <span class="mc-product-price">{html_lib.escape(precio)}</span>'''


def build_mobile_summary_html(p):
    """Tarjeta compacta 'sillita elegida' para el selector (Sillita 1 /
    Sillita 2): miniatura + marca + modelo, nada mas -- el boton de
    quitar (✕) lo añade el JS del selector, no forma parte de este
    fragmento (asi el mismo fragmento sirve igual sin importar en que
    slot se use)."""
    marca = p.get("marca") or SIN_ESPECIFICAR
    modelo = p.get("modelo") or SIN_ESPECIFICAR
    thumb_html = build_mobile_thumb_html(p, "mc-summary-img")
    return f'''{thumb_html}
      <span class="mc-summary-info"><span class="mc-summary-brand">{html_lib.escape(marca)}</span><span class="mc-summary-model">{html_lib.escape(modelo)}</span></span>'''


def build_mobile_result_card_html(p):
    """Tarjeta de resultado dentro del panel de busqueda del selector:
    imagen, marca, modelo, rango de uso (reutiliza rango_uso_html(),
    igual que la matriz principal), valoración + nº de valoraciones,
    precio e ISOFIX (reutiliza valor_badge(), igual que la tabla de
    PC) -- ningun campo nuevo, ninguna logica de presentacion nueva."""
    marca = p.get("marca") or SIN_ESPECIFICAR
    modelo = p.get("modelo") or SIN_ESPECIFICAR
    precio = fmt_precio(p.get("precio")) or SIN_ESPECIFICAR
    valoracion = fmt_valoracion(p.get("valoracion"))
    n_val = fmt_n_val(p.get("n_val"))
    altura = campo(p, "altura")
    edad = campo(p, "edad")
    grupo = campo(p, "grupo")
    peso_recomendado = campo(p, "peso_recomendado")
    isofix = campo(p, "isofix")

    rating_html = (
        f'<span class="mc-result-rating">★ {valoracion}<span class="mc-result-reviews"> · {n_val or "0"} valoraciones</span></span>'
        if valoracion else
        f'<span class="mc-result-rating cell-unspecified">{SIN_ESPECIFICAR}</span>'
    )
    thumb_html = build_mobile_thumb_html(p, "mc-result-thumb")
    rango_html = rango_uso_html(altura, edad, grupo, peso_recomendado)
    isofix_html = valor_badge(isofix)

    return f'''{thumb_html}
      <span class="mc-result-body">
        <span class="mc-result-head"><span class="mc-result-brand">{html_lib.escape(marca)}</span><span class="mc-result-model">{html_lib.escape(modelo)}</span></span>
        <span class="mc-result-rango">{rango_html}</span>
        {rating_html}
        <span class="mc-result-foot"><span class="mc-result-price">{html_lib.escape(precio)}</span><span class="mc-result-isofix">ISOFIX: {isofix_html}</span></span>
      </span>'''


# Filtro por edad del selector movil (18-ago-2026). Los valores son
# años (convertidos a MESES en JS para comparar, igual unidad que usa
# parse_edad_rango_meses()) -- "10plus" es un caso especial ("10 años o
# mas", para no limitarlo a la franja exacta de 10 años, que ya tiene su
# propia opcion). No son datos del dataset, son las franjas del propio
# filtro (0-10 + 10+), pedidas explicitamente por el usuario.
AGE_FILTER_OPTIONS = [
    ("0", "0 años"),
    ("1", "1 año"),
    ("2", "2 años"),
    ("3", "3 años"),
    ("4", "4 años"),
    ("5", "5 años"),
    ("6", "6 años"),
    ("7", "7 años"),
    ("8", "8 años"),
    ("9", "9 años"),
    ("10", "10 años"),
    ("10plus", "10+ años"),
]


def build_mobile_product_payload(p):
    """Payload JSON de UN producto para el selector movil (JS) -- todo
    el HTML ya viene renderizado desde Python (mismos helpers que el
    resto del prototipo: campo/valor_badge/rango_uso_html/
    build_mobile_feature_values/build_mobile_ficha_values), asi que el
    JS del selector nunca recalcula ni reinterpreta un dato: solo
    coloca el fragmento ya hecho en el sitio correspondiente al cambiar
    de sillita. marca/modelo van tambien en texto plano para el
    buscador (filtrado simple por subcadena, sin logica de datos).

    edadMinMeses/edadMaxMeses (18-ago-2026, filtro por edad): el MISMO
    parse_edad_rango_meses() que ya usa la tabla de PC para ordenar por
    Edad -- ninguna logica de rango nueva, solo se expone el resultado
    ya calculado para que el JS del filtro pueda comparar (null cuando
    el campo Edad no tiene un rango reconocible, igual que en PC)."""
    edad_min, edad_max = parse_edad_rango_meses(campo(p, "edad"))
    return {
        "asin": p["asin"],
        "marca": p.get("marca") or SIN_ESPECIFICAR,
        "modelo": p.get("modelo") or SIN_ESPECIFICAR,
        "edadMinMeses": edad_min,
        "edadMaxMeses": edad_max,
        "vsSlotHtml": build_mobile_vs_slot_inner(p),
        "summaryHtml": build_mobile_summary_html(p),
        "resultCardHtml": build_mobile_result_card_html(p),
        "featureValues": build_mobile_feature_values(p),
        "fichaValues": build_mobile_ficha_values(p),
    }


def build_mobile_selector(productos):
    """Seccion 'Comparar 2 sillitas' + panel de busqueda (fase del
    selector, 18-ago-2026). Va ANTES de la tarjeta VS. El estado
    inicial (Sillita 1 / Sillita 2) lo decide el propio JS a partir de
    DEMO_ASIN_A/DEMO_ASIN_B (mismos 2 productos que ya se renderizan en
    servidor mas abajo), asi que la pagina se ve identica a v38 hasta
    que el usuario cambie algo -- los <div id="mc-slot-a/b"> se generan
    vacios aqui y el JS los rellena al cargar."""
    payload = [build_mobile_product_payload(p) for p in productos]
    payload_json = json.dumps(payload, ensure_ascii=False)
    asin_a, asin_b = DEMO_COMPARE_ASINS
    age_options_html = "\n".join(
        f'      <option value="{value}">{html_lib.escape(label)}</option>'
        for value, label in AGE_FILTER_OPTIONS
    )
    return f'''<div class="mc-selector">
  <div class="mc-selector-head">
    <span class="mc-selector-icon" aria-hidden="true">⇄</span>
    <span>
      <span class="mc-selector-title">Comparar 2 sillitas</span>
      <span class="mc-selector-sub">Elige las dos sillitas que quieres comparar</span>
    </span>
  </div>
  <input type="text" class="mc-selector-topsearch" id="mc-selector-topsearch" placeholder="Buscar por marca o modelo" autocomplete="off">
  <div class="mc-slot-group">
    <span class="mc-slot-label">Sillita 1</span>
    <div class="mc-slot" id="mc-slot-a"></div>
  </div>
  <div class="mc-slot-group">
    <span class="mc-slot-label">Sillita 2</span>
    <div class="mc-slot" id="mc-slot-b"></div>
  </div>
  <button type="button" class="mc-compare-btn" id="mc-compare-btn">Comparar sillitas</button>
</div>

<div class="mc-selector-panel" id="mc-selector-panel" hidden>
  <div class="mc-selector-panel-inner">
    <div class="mc-selector-panel-head">
      <span>Selecciona una sillita</span>
      <button type="button" class="mc-selector-panel-close" id="mc-selector-close" aria-label="Cerrar">✕</button>
    </div>
    <input type="text" class="mc-selector-search" id="mc-selector-search" placeholder="Buscar por marca o modelo" autocomplete="off">
    <label class="mc-slot-label" for="mc-selector-age">Filtrar por edad</label>
    <select class="mc-selector-age" id="mc-selector-age">
      <option value="">Selecciona la edad</option>
{age_options_html}
    </select>
    <div class="mc-selector-results" id="mc-selector-results"></div>
  </div>
</div>

<script>
const MOBILE_PRODUCTS = {payload_json};
const DEMO_ASIN_A = "{asin_a}";
const DEMO_ASIN_B = "{asin_b}";
</script>'''


def build_mobile_compare(productos):
    """Construye el bloque VS de 2 productos para movil (selector +
    tarjetas + matriz de caracteristicas + ficha tecnica), usando
    EXACTAMENTE el mismo dataset y los mismos helpers de formato
    (fmt_precio/fmt_valoracion/fmt_n_val/campo/valor_badge/
    rango_uso_html/...) que ya usa build_row() para la tabla de PC --
    ningun dato nuevo, ninguna duplicacion manual."""
    por_asin = {p["asin"]: p for p in productos}
    productos_ab = [por_asin[asin] for asin in DEMO_COMPARE_ASINS]

    selector_html = build_mobile_selector(productos)

    columnas = []
    for i, p in enumerate(productos_ab):
        slot = "a" if i == 0 else "b"
        columnas.append(f'''      <div class="mc-product" data-slot="{slot}">
        {build_mobile_vs_slot_inner(p)}
      </div>''')

    features_html = build_mobile_features(productos_ab)
    ficha_html = build_mobile_ficha(productos_ab)

    return f'''<div class="mobile-compare">
{selector_html}
  <div class="mc-vs-card">
{columnas[0]}
    <div class="mc-divider"></div>
    <div class="mc-vs">VS</div>
{columnas[1]}
  </div>
{features_html}
{ficha_html}
</div>'''


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
<title>PROTOTIPO v51 — Comparativa sillitas de coche</title>
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
/* Ajuste (18-ago-2026), SOLO movil: el precio de la tarjeta VS pasa a
   usar el mismo color de acento que la marca (var(--accent-deep), la
   misma variable que ya usa .mc-product-brand) -- antes usaba
   var(--ink) como el resto de texto neutro. Tamaño (16px), peso (700)
   y todo lo demas se mantienen exactamente igual. */
.mc-product-price{{font-size:16px; font-weight:700; color:var(--accent-deep);}}
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
/* Fase 2 (18-ago-2026): matriz CARACTERÍSTICA | SILLITA A | SILLITA B.
   Grid de 3 columnas -- cada fila de la matriz son 3 <div> hijos
   consecutivos (ver build_mobile_features() en el script), asi que el
   propio grid-auto-flow los agrupa en filas automaticamente. Misma
   tarjeta visual que .mc-vs-card (borde/radio/sombra), como
   "extension natural" pedida. Columna de etiqueta con ancho fijo justo
   (92px, suficiente para "Rango de uso"/"Orientación" en una o dos
   lineas cortas) y un tinte de fondo MUY sutil reutilizando el propio
   --bg de la pagina (no un color nuevo) para que se identifique de un
   vistazo sin añadir decoracion. */
.mc-features{{
  margin-top:20px; display:grid; grid-template-columns:92px 1fr 1fr;
  background:var(--card); border:1px solid var(--line); border-radius:14px;
  box-shadow:0 2px 8px rgba(0,0,0,.05); overflow:hidden;
}}
.mc-feat-label, .mc-feat-val{{
  padding:12px 8px; border-bottom:1px solid var(--line-row);
  display:flex; align-items:center; min-width:0;
}}
.mc-features > div:nth-last-child(-n+3){{border-bottom:none;}}
.mc-feat-label{{background:var(--bg); font-size:12px; font-weight:700; color:var(--ink);}}
.mc-feat-val{{
  justify-content:center; text-align:center; flex-direction:column; gap:2px;
  font-size:13px; color:var(--ink); font-weight:400;
}}
/* Rango de uso puede tener hasta 4 lineas -- en PC se recortan con
   ellipsis porque la columna es ancha (190px); aqui la columna es mas
   estrecha, asi que en vez de cortar el texto se permite salto de
   linea limpio (pedido explicito de esta fase). Selector de 2 clases
   -> mas especifico que ".rango-primary"/".rango-secondary" solas, asi
   que esto NUNCA afecta a la tabla de PC (td.col-rango sigue igual). */
.mc-feat-val .rango-primary, .mc-feat-val .rango-secondary{{
  white-space:normal; overflow:visible; text-overflow:clip; text-align:center;
}}
.mc-feat-val .rango-block{{display:flex; flex-direction:column; align-items:center;}}

/* Fase 2 -- Ficha técnica móvil (18-ago-2026): seccion independiente y
   colapsable debajo de la matriz principal, mismo lenguaje visual
   (misma tarjeta con borde/radio/sombra que .mc-vs-card/.mc-features;
   las filas reutilizan tal cual .mc-feat-label/.mc-feat-val, sin
   duplicar esas reglas). Empieza cerrada -- el boton es su propia
   tarjeta, separada visualmente de la matriz principal (margin-top),
   y el panel aparece justo debajo al abrirse. */
.mc-ficha{{margin-top:16px;}}
.mc-ficha-toggle{{
  width:100%; display:flex; align-items:center; justify-content:space-between; gap:10px;
  background:var(--card); border:1px solid var(--line); border-radius:14px;
  box-shadow:0 2px 8px rgba(0,0,0,.05); padding:14px 16px; cursor:pointer;
  font-family:'Inter',sans-serif; font-size:13px; font-weight:700; color:var(--ink);
  text-transform:uppercase; letter-spacing:.03em;
}}
.mc-ficha-toggle:hover{{color:var(--accent-deep);}}
.mc-ficha-toggle-icon{{font-size:12px; color:var(--accent-deep); transition:transform .15s;}}
.mc-ficha-toggle[aria-expanded="true"] .mc-ficha-toggle-icon{{transform:rotate(180deg);}}
.mc-ficha-panel{{
  margin-top:10px; display:grid; grid-template-columns:92px 1fr 1fr;
  background:var(--card); border:1px solid var(--line); border-radius:14px;
  box-shadow:0 2px 8px rgba(0,0,0,.05); overflow:hidden;
}}
.mc-ficha-panel[hidden]{{display:none;}}
.mc-ficha-panel > div:nth-last-child(-n+3){{border-bottom:none;}}

/* Selector "Comparar 2 sillitas" (18-ago-2026) -- mismo lenguaje
   visual que el resto (tarjeta con borde/radio/sombra, naranja de
   marca via var(--accent)/var(--accent-deep), sin colores nuevos).
   Fallback de imagen (.mc-thumb-ph) reutiliza el mismo patron que ya
   usa la tabla de PC (recuadro con iniciales), solo escalado a cada
   contexto (140px en la tarjeta VS, 56px en el chip/los resultados). */
.mc-thumb-ph{{
  display:flex; align-items:center; justify-content:center;
  background:linear-gradient(135deg,#F4F2EE,#E9E6DF); border:1px solid var(--line);
  border-radius:9px; font-family:'JetBrains Mono',monospace; font-weight:700;
  color:var(--ink-soft); font-size:28px;
}}
.mc-summary-img.mc-thumb-ph, .mc-result-thumb.mc-thumb-ph{{font-size:14px;}}

.mc-selector{{
  background:var(--card); border:1px solid var(--line); border-radius:14px;
  box-shadow:0 2px 8px rgba(0,0,0,.05); padding:18px 16px;
}}
.mc-selector-head{{display:flex; align-items:center; gap:12px; margin-bottom:14px;}}
.mc-selector-icon{{
  flex-shrink:0; width:36px; height:36px; border-radius:50%; display:flex;
  align-items:center; justify-content:center; font-size:15px;
  background:color-mix(in srgb, var(--accent) 18%, var(--card)); color:var(--accent-deep);
}}
.mc-selector-title{{display:block; font-size:15px; font-weight:700; color:var(--ink);}}
.mc-selector-sub{{display:block; font-size:12.5px; color:var(--ink-soft); margin-top:2px;}}
.mc-selector-topsearch, .mc-selector-search{{
  width:100%; box-sizing:border-box; padding:11px 14px; border:1px solid var(--line);
  border-radius:10px; background:var(--bg); font-family:'Inter',sans-serif; font-size:13.5px;
  color:var(--ink); margin-bottom:16px;
}}
.mc-selector-topsearch::placeholder, .mc-selector-search::placeholder{{color:var(--ink-soft);}}
.mc-selector-topsearch:focus, .mc-selector-search:focus{{outline:none; border-color:var(--accent);}}
.mc-slot-group{{margin-bottom:12px;}}
.mc-slot-label{{display:block; font-size:12px; font-weight:700; color:var(--ink); margin-bottom:6px;}}
.mc-slot-empty{{
  width:100%; display:flex; align-items:center; gap:10px; padding:12px 14px;
  background:color-mix(in srgb, var(--accent) 6%, var(--card));
  border:1.5px dashed var(--accent); border-radius:12px; cursor:pointer;
  font-family:'Inter',sans-serif; font-size:13.5px; font-weight:600; color:var(--accent-deep);
  text-align:left;
}}
.mc-slot-plus{{
  flex-shrink:0; width:24px; height:24px; border-radius:50%; display:flex;
  align-items:center; justify-content:center; font-size:15px; line-height:1;
  background:color-mix(in srgb, var(--accent) 20%, var(--card)); color:var(--accent-deep);
}}
.mc-slot-arrow{{margin-left:auto; color:var(--accent-deep);}}
.mc-slot-filled{{
  display:flex; align-items:center; gap:10px; padding:10px 12px;
  border:1px solid var(--line); border-radius:12px; background:var(--card);
}}
.mc-summary-img{{width:48px; height:48px; flex-shrink:0; border-radius:9px; object-fit:contain;}}
.mc-summary-info{{display:flex; flex-direction:column; gap:2px; min-width:0;}}
.mc-summary-brand{{font-size:11px; font-weight:700; color:var(--accent-deep); text-transform:uppercase; letter-spacing:.03em;}}
.mc-summary-model{{font-size:13.5px; font-weight:600; color:var(--ink);}}
.mc-slot-remove{{
  margin-left:auto; flex-shrink:0; width:26px; height:26px; border-radius:50%; border:0;
  background:var(--bg); color:var(--ink-soft); font-size:12px; cursor:pointer;
}}
.mc-slot-remove:hover{{background:var(--line); color:var(--ink);}}
.mc-compare-btn{{
  width:100%; margin-top:4px; padding:14px; border:0; border-radius:12px;
  background:var(--accent-deep); color:#fff; font-family:'Inter',sans-serif;
  font-size:13.5px; font-weight:700; text-transform:uppercase; letter-spacing:.04em;
  cursor:pointer; transition:background .15s;
}}
.mc-compare-btn:hover{{background:#B5471F;}}
.mc-compare-btn:disabled{{background:var(--line); color:var(--ink-soft); cursor:not-allowed;}}

/* Panel de busqueda -- hoja inferior (bottom sheet), patron movil
   estandar: overlay + tarjeta anclada abajo con lista con scroll
   propio, para no arrastrar scroll horizontal ni usar una tabla. */
.mc-selector-panel{{
  position:fixed; inset:0; z-index:60; background:rgba(28,28,30,.45);
  display:flex; align-items:flex-end; justify-content:center;
}}
.mc-selector-panel[hidden]{{display:none;}}
.mc-selector-panel-inner{{
  width:100%; max-width:520px; max-height:82vh; background:var(--card);
  border-radius:20px 20px 0 0; box-shadow:0 -8px 24px rgba(0,0,0,.18);
  display:flex; flex-direction:column; overflow:hidden;
}}
.mc-selector-panel-head{{
  display:flex; align-items:center; justify-content:space-between;
  padding:16px 16px 0; font-size:14.5px; font-weight:700; color:var(--ink);
}}
.mc-selector-panel-close{{
  width:28px; height:28px; border-radius:50%; border:0; background:var(--bg);
  color:var(--ink-soft); font-size:13px; cursor:pointer;
}}
.mc-selector-panel-close:hover{{background:var(--line); color:var(--ink);}}
.mc-selector-panel .mc-selector-search{{margin:14px 16px 8px; width:calc(100% - 32px);}}
/* Filtro por edad (18-ago-2026) -- mismo lenguaje visual que el
   buscador (misma caja: borde/radio/fondo/tipografia), reutilizando
   .mc-slot-label para el texto "Filtrar por edad" (la misma etiqueta
   que ya usan "Sillita 1"/"Sillita 2"). Solo dentro del panel: se le
   da el mismo margen/ancho con inset de 16px que ya usa el buscador
   del panel (.mc-selector-panel .mc-selector-search), para que quede
   alineado con el resto del contenido. */
.mc-selector-age{{
  width:100%; box-sizing:border-box; padding:11px 14px; border:1px solid var(--line);
  border-radius:10px; background:var(--bg); font-family:'Inter',sans-serif; font-size:13.5px;
  color:var(--ink);
}}
.mc-selector-age:focus{{outline:none; border-color:var(--accent);}}
.mc-selector-panel .mc-slot-label{{margin:0 16px 6px; width:calc(100% - 32px);}}
.mc-selector-panel .mc-selector-age{{margin:0 16px 14px; width:calc(100% - 32px);}}
.mc-selector-results{{overflow-y:auto; padding:0 16px 16px; flex:1;}}
.mc-result-card{{
  width:100%; display:flex; align-items:center; gap:12px; padding:12px 10px;
  border:0; border-bottom:1px solid var(--line-row); background:none; cursor:pointer;
  text-align:left; font-family:'Inter',sans-serif;
}}
.mc-result-card:last-child{{border-bottom:none;}}
.mc-result-card:hover{{background:#FBF6F1;}}
.mc-result-thumb{{width:56px; height:56px; flex-shrink:0; border-radius:9px; object-fit:contain;}}
.mc-result-body{{display:flex; flex-direction:column; gap:3px; min-width:0; flex:1;}}
.mc-result-head{{display:flex; flex-direction:column;}}
.mc-result-brand{{font-size:11px; font-weight:700; color:var(--accent-deep); text-transform:uppercase; letter-spacing:.03em;}}
.mc-result-model{{font-size:13px; font-weight:600; color:var(--ink);}}
.mc-result-rango .rango-block{{display:flex; flex-wrap:wrap; gap:0 6px;}}
.mc-result-rango .rango-primary, .mc-result-rango .rango-secondary{{
  display:inline; white-space:nowrap; font-size:11.5px;
}}
.mc-result-rango .rango-primary::after, .mc-result-rango .rango-secondary::after{{content:'·'; margin-left:6px; color:var(--ink-soft);}}
.mc-result-rango .rango-primary:last-child::after, .mc-result-rango .rango-secondary:last-child::after{{content:'';}}
.mc-result-rating{{font-size:12px; font-weight:700; color:var(--ink);}}
.mc-result-reviews{{font-size:11px; font-weight:400; color:var(--ink-soft);}}
.mc-result-foot{{display:flex; align-items:center; gap:10px; margin-top:2px;}}
.mc-result-price{{font-size:13px; font-weight:700; color:var(--ink);}}
.mc-result-isofix{{font-size:11px; color:var(--ink-soft);}}
.mc-result-isofix .txt-plain{{display:inline; font-size:11px; font-weight:600; color:var(--ink);}}

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

<div class="proto-banner">⚠ Prototipo v51 — <b>no es la web real</b> — misma fuente que v4-v50: tools/output/auditoria_30_candidatos.json (sin cambios de dato en esta versión)</div>
<p class="proto-note">
  Corrección (18-ago-2026): con un filtro de edad activo, usar el <b>buscador general</b> (el de fuera de los slots) para ver todos los productos dejaba el filtro de edad "pegado". Ahora ese buscador siempre limpia el filtro de edad al usarse — dentro del panel, el buscador y el filtro de edad siguen combinándose entre sí igual que antes. Redimensiona a &lt;768px para probarlo.
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

<p class="foot-note">Prototipo generado por tools/build_comparativa_prototipo_v51.py a partir de tools/output/auditoria_30_candidatos.json — no modifica ningún archivo de producción ni la web real.</p>

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

// ---------------------------------------------------------------------
// Fase 2 -- Ficha técnica móvil (18-ago-2026): toggle simple, sin
// relacion con el sistema de la ficha tecnica de PC (.btn-toggle) --
// IDs/clases propios, cero interferencia con esa logica.
// ---------------------------------------------------------------------
(function setupMobileFicha() {{
  const btn = document.getElementById('mc-ficha-toggle');
  const panel = document.getElementById('mc-ficha-panel');
  if (!btn || !panel) return;
  btn.addEventListener('click', () => {{
    const abierta = !panel.hasAttribute('hidden');
    if (abierta) {{
      panel.setAttribute('hidden', '');
      btn.setAttribute('aria-expanded', 'false');
    }} else {{
      panel.removeAttribute('hidden');
      btn.setAttribute('aria-expanded', 'true');
    }}
  }});
}})();

// ---------------------------------------------------------------------
// Selector "Comparar 2 sillitas" (18-ago-2026). MOBILE_PRODUCTS (30
// productos, con todo su HTML ya renderizado por Python) viene
// definido en el <script> de build_mobile_selector(), justo antes de
// este bloque. Este codigo NUNCA calcula ni reinterpreta un dato --
// solo decide que 2 ASIN estan elegidos y coloca sus fragmentos ya
// hechos en el DOM (data-slot="a"/"b" en .mc-product, data-feat/
// data-ficha en las celdas de la matriz/ficha).
// ---------------------------------------------------------------------
(function setupMobileSelector() {{
  if (typeof MOBILE_PRODUCTS === 'undefined') return;
  const byAsin = {{}};
  MOBILE_PRODUCTS.forEach(p => {{ byAsin[p.asin] = p; }});
  // Estado inicial = los mismos 2 productos que ya vienen renderizados
  // en servidor -- la pagina se ve identica a antes hasta que el
  // usuario elija otra cosa.
  let selected = [DEMO_ASIN_A, DEMO_ASIN_B];
  let pickingSlot = null;
  // Correccion (18-ago-2026): producto elegido desde el BUSCADOR
  // GENERAL cuando las 2 sillitas ya estaban ocupadas -- en ese caso
  // no se aplica todavia (no sabemos que slot sustituir), se guarda
  // aqui hasta que el usuario confirme el slot en renderSlotChoice().
  let pendingAsin = null;
  // Filtro por edad (18-ago-2026): '' = sin filtro, '0'..'10' = edad
  // exacta en años, '10plus' = 10 años o mas. Vive junto al resto del
  // estado del panel (se resetea al abrir/cerrar, igual que la busqueda
  // de texto) y se combina con ella en renderResults() -- son filtros
  // acumulativos sobre el MISMO listado, no un segundo buscador.
  let ageFilter = '';

  const els = {{
    slotA: document.getElementById('mc-slot-a'),
    slotB: document.getElementById('mc-slot-b'),
    compareBtn: document.getElementById('mc-compare-btn'),
    topSearch: document.getElementById('mc-selector-topsearch'),
    panel: document.getElementById('mc-selector-panel'),
    panelResults: document.getElementById('mc-selector-results'),
    panelSearch: document.getElementById('mc-selector-search'),
    panelClose: document.getElementById('mc-selector-close'),
    ageSelect: document.getElementById('mc-selector-age'),
  }};
  if (!els.slotA || !els.slotB || !els.compareBtn || !els.panel) return;

  // Compatibilidad de un producto con la edad elegida en el filtro --
  // reutiliza edadMinMeses/edadMaxMeses, que en Python vienen de
  // parse_edad_rango_meses() (la MISMA logica que ya usa la tabla de PC
  // para ordenar por Edad, ver build_mobile_product_payload()). Sin
  // rango de edad reconocible, el producto queda excluido cuando hay
  // filtro activo -- nunca se afirma una compatibilidad que no consta
  // en el dato real.
  function passesAgeFilter(p) {{
    if (!ageFilter) return true;
    if (p.edadMinMeses === null || p.edadMaxMeses === null) return false;
    if (ageFilter === '10plus') return p.edadMaxMeses >= 120;
    const edadMeses = parseInt(ageFilter, 10) * 12;
    return p.edadMinMeses <= edadMeses && edadMeses <= p.edadMaxMeses;
  }}

  function slotIndex(slotKey) {{ return slotKey === 'a' ? 0 : 1; }}

  function renderSlot(slotKey) {{
    const el = slotKey === 'a' ? els.slotA : els.slotB;
    const asin = selected[slotIndex(slotKey)];
    if (!asin) {{
      const texto = slotKey === 'a' ? 'Selecciona la primera sillita' : 'Selecciona la segunda sillita';
      el.innerHTML = `<button type="button" class="mc-slot-empty" data-pick="${{slotKey}}"><span class="mc-slot-plus" aria-hidden="true">+</span><span>${{texto}}</span><span class="mc-slot-arrow" aria-hidden="true">›</span></button>`;
      return;
    }}
    const p = byAsin[asin];
    // Correccion (18-ago-2026): el area de la sillita ya elegida ahora
    // lleva data-activate -- tocarla declara ese slot como "activo",
    // igual que tocar un slot vacio, para que el usuario pueda decidir
    // que sillita cambiar en vez de que se sustituya una al azar.
    el.innerHTML = `<div class="mc-slot-filled" data-activate="${{slotKey}}">${{p.summaryHtml}}<button type="button" class="mc-slot-remove" data-remove="${{slotKey}}" aria-label="Quitar sillita">✕</button></div>`;
  }}

  function updateCompareBtn() {{
    els.compareBtn.disabled = !(selected[0] && selected[1]);
  }}

  function renderCompare() {{
    if (!selected[0] || !selected[1]) return;
    const productos = {{ a: byAsin[selected[0]], b: byAsin[selected[1]] }};
    document.querySelectorAll('.mc-product[data-slot]').forEach(el => {{
      el.innerHTML = productos[el.dataset.slot].vsSlotHtml;
    }});
    document.querySelectorAll('[data-feat]').forEach(el => {{
      el.innerHTML = productos[el.dataset.slot].featureValues[el.dataset.feat];
    }});
    document.querySelectorAll('[data-ficha]').forEach(el => {{
      el.innerHTML = productos[el.dataset.slot].fichaValues[el.dataset.ficha];
    }});
  }}

  function renderResults(query) {{
    const q = query.trim().toLowerCase();
    // Con slot predeterminado (tocando Sillita 1/2, o resuelto solo
    // porque solo hay 1 hueco vacio) se excluye SOLO la otra sillita.
    // En modo "general" con las 2 llenas (pickingSlot === null) todavia
    // no sabemos que slot se va a sustituir, asi que se excluyen las 2
    // ya elegidas (elegir cualquiera de las 2 otra vez no tendria
    // sentido).
    let excluidos;
    if (pickingSlot === 'a') excluidos = [selected[1]];
    else if (pickingSlot === 'b') excluidos = [selected[0]];
    else excluidos = [selected[0], selected[1]];
    // Buscador + filtro de edad son ACUMULATIVOS -- ambas condiciones
    // deben cumplirse sobre el mismo listado, no son dos listados
    // separados.
    const lista = MOBILE_PRODUCTS.filter(p => {{
      if (excluidos.includes(p.asin)) return false;
      if (!passesAgeFilter(p)) return false;
      if (!q) return true;
      return (p.marca + ' ' + p.modelo).toLowerCase().includes(q);
    }});
    if (lista.length === 0) {{
      const mensaje = ageFilter
        ? 'No hemos encontrado sillitas para esta edad.'
        : 'No hemos encontrado ninguna sillita.';
      els.panelResults.innerHTML = `<p style="padding:24px 4px;color:var(--ink-soft);font-size:13px;text-align:center;">${{mensaje}}</p>`;
      return;
    }}
    els.panelResults.innerHTML = lista.map(p =>
      `<button type="button" class="mc-result-card" data-asin="${{p.asin}}">${{p.resultCardHtml}}</button>`
    ).join('');
  }}

  // Correccion (18-ago-2026): paso intermedio SOLO para el buscador
  // general cuando las 2 sillitas ya estaban ocupadas -- tras elegir un
  // producto nuevo, se pregunta que slot sustituir en vez de aplicarlo
  // directamente. Reutiliza la misma tarjeta .mc-result-card (ninguna
  // clase CSS nueva) con el summaryHtml ya renderizado de cada slot
  // actual, precedido de una etiqueta de texto con estilos en linea
  // (mismo patron ya usado en el mensaje "No hemos encontrado ninguna
  // sillita.", reutilizando los tokens de color existentes).
  function renderSlotChoice(asin) {{
    const actualA = byAsin[selected[0]];
    const actualB = byAsin[selected[1]];
    const etiqueta = (n) => `<span style="font-size:11px;font-weight:700;color:var(--ink-soft);text-transform:uppercase;letter-spacing:.03em;margin-right:8px;">Sillita ${{n}}</span>`;
    els.panelResults.innerHTML = `
      <p style="padding:4px 4px 14px;color:var(--ink);font-size:13.5px;font-weight:700;">¿Qué sillita quieres sustituir?</p>
      <button type="button" class="mc-result-card" data-choice-slot="a">${{etiqueta('1')}}${{actualA.summaryHtml}}</button>
      <button type="button" class="mc-result-card" data-choice-slot="b">${{etiqueta('2')}}${{actualB.summaryHtml}}</button>
    `;
  }}

  function applyChoice(slotKey, asin) {{
    selected[slotIndex(slotKey)] = asin;
    renderSlot(slotKey);
    updateCompareBtn();
    closePanel();
    if (els.topSearch) els.topSearch.value = '';
  }}

  // Correccion (18-ago-2026): "Buscar por marca o modelo" y "Filtrar
  // por edad" deben quedar SIEMPRE disponibles e independientes, sin
  // que el panel "recuerde" un modo. Antes habia DOS sitios distintos
  // que abrian el panel (openPanel(), usado al tocar un slot, y la
  // rama de apertura dentro de handleTopSearch(), usada por el
  // buscador general) y solo openPanel() reseteaba el filtro de edad
  // -- la rama de handleTopSearch() abria el panel sin tocar
  // ageFilter/el <select>, asi que un filtro de edad activo en una
  // apertura anterior podia seguir aplicado la siguiente vez que se
  // abria el panel desde el buscador general. resetPanelState() centra
  // en UN unico sitio el reseteo de los 2 filtros (texto + edad) mas
  // pendingAsin, y ahora la usan las 2 rutas de apertura por igual, asi
  // que el panel siempre empieza limpio venga por donde venga.
  function resetPanelState(slotKey) {{
    pickingSlot = slotKey;
    pendingAsin = null;
    ageFilter = '';
    if (els.ageSelect) els.ageSelect.value = '';
    els.panelSearch.value = '';
  }}

  function openPanel(slotKey) {{
    resetPanelState(slotKey);
    renderResults('');
    els.panel.removeAttribute('hidden');
    // Correccion (18-ago-2026): se quita el .focus() programatico que
    // había aquí. En movil, forzar el foco (y por tanto el teclado
    // virtual) justo al abrir el panel puede dejar el campo en un
    // estado de "foco fantasma" en algunos navegadores -- se ve con el
    // borde activo (naranja) pero deja de aceptar pulsaciones reales
    // hasta recargar, sobre todo despues de interactuar con el
    // <select> de edad (que abre su propio selector nativo del
    // sistema). Sin este .focus() automatico, el usuario simplemente
    // toca el campo el mismo (un gesto real), lo cual siempre funciona
    // de forma fiable -- y de paso evita que el teclado tape el panel
    // nada mas abrirlo, algo que tampoco es deseable en movil.
  }}

  function closePanel() {{
    els.panel.setAttribute('hidden', '');
    resetPanelState(null);
  }}

  els.panelSearch.addEventListener('input', () => renderResults(els.panelSearch.value));
  // Filtro por edad (18-ago-2026): se combina con el texto del
  // buscador ya escrito -- no reinicia la busqueda, solo añade la
  // condicion de edad sobre el mismo listado (ver renderResults()).
  if (els.ageSelect) {{
    els.ageSelect.addEventListener('change', () => {{
      ageFilter = els.ageSelect.value;
      renderResults(els.panelSearch.value);
    }});
  }}
  els.panelClose.addEventListener('click', closePanel);
  els.panel.addEventListener('click', (e) => {{ if (e.target === els.panel) closePanel(); }});
  document.addEventListener('keydown', (e) => {{
    if (e.key === 'Escape' && !els.panel.hasAttribute('hidden')) closePanel();
  }});

  // Correccion (18-ago-2026): el buscador GENERAL ("Buscar por marca o
  // modelo" de fuera de los slots) ahora SIEMPRE funciona, tenga la
  // cantidad de sillitas que tenga elegidas -- ya no se bloquea con las
  // 2 llenas. Con 0 o 1 elegida, el slot destino sigue siendo
  // inequivoco y se resuelve solo (pickingSlot queda en 'a'/'b',
  // exactamente igual que antes). Con las 2 llenas, se abre en modo
  // "general" (pickingSlot = null): se puede buscar y elegir un
  // producto nuevo con total normalidad, pero la sustitucion queda
  // pendiente de que el usuario diga que slot quiere cambiar (ver
  // renderSlotChoice() mas abajo) -- nunca se sustituye Sillita 1 ni
  // Sillita 2 automaticamente en este caso.
  //
  // El buscador de cada slot (tocar Sillita 1 / Sillita 2, vacia o
  // llena) sigue exactamente igual que antes: openPanel(slotKey) fija
  // pickingSlot de antemano, asi que esa busqueda modifica siempre y
  // solo ese slot, sin paso de confirmacion.
  if (els.topSearch) {{
    const handleTopSearch = () => {{
      if (els.panel.hasAttribute('hidden')) {{
        let slotKey;
        if (!selected[0]) {{
          slotKey = 'a';
        }} else if (!selected[1]) {{
          slotKey = 'b';
        }} else {{
          slotKey = null;
        }}
        // Misma funcion de reseteo que openPanel() -- el filtro de edad
        // y el texto del buscador del panel siempre empiezan limpios,
        // sin importar por donde se abrio. No se llama a
        // els.panelSearch.focus() aqui (a diferencia de openPanel())
        // para no robarle el foco al campo donde el usuario esta
        // escribiendo ahora mismo (el buscador general).
        resetPanelState(slotKey);
        els.panel.removeAttribute('hidden');
      }} else {{
        // Correccion (18-ago-2026): el buscador GENERAL (el de fuera de
        // los slots) es la via rapida para "quiero ver todos los
        // productos que coincidan con este texto" -- si el panel ya
        // estaba abierto (p.ej. porque antes se uso "Filtrar por edad"
        // dentro del panel) y el usuario vuelve a escribir aqui, este
        // buscador general limpia el filtro de edad en vez de
        // arrastrarlo, para que no se quede "pegado" un filtro que el
        // usuario ya no esta usando. El buscador y el filtro de edad
        // DENTRO del panel (el campo "Buscar por marca o modelo" del
        // propio panel + el <select> "Filtrar por edad") siguen siendo
        // acumulativos entre si, sin cambios -- esto solo afecta al
        // campo de fuera de los slots.
        ageFilter = '';
        if (els.ageSelect) els.ageSelect.value = '';
      }}
      els.panelSearch.value = els.topSearch.value;
      renderResults(els.topSearch.value);
    }};
    els.topSearch.addEventListener('focus', handleTopSearch);
    els.topSearch.addEventListener('input', handleTopSearch);
  }}

  document.addEventListener('click', (e) => {{
    const pickBtn = e.target.closest('[data-pick]');
    if (pickBtn) {{ openPanel(pickBtn.dataset.pick); return; }}

    const removeBtn = e.target.closest('[data-remove]');
    if (removeBtn) {{
      const slotKey = removeBtn.dataset.remove;
      selected[slotIndex(slotKey)] = null;
      renderSlot(slotKey);
      updateCompareBtn();
      return;
    }}

    // Tocar la tarjeta de una sillita YA elegida la activa para
    // cambiarla (sin afectar a la otra) -- mismo mecanismo que tocar
    // un slot vacio, solo que aqui el slot ya tenia producto.
    const activateEl = e.target.closest('[data-activate]');
    if (activateEl) {{ openPanel(activateEl.dataset.activate); return; }}

    // Confirmacion de slot (solo aparece tras elegir un producto desde
    // el buscador general con las 2 sillitas ya ocupadas).
    const choiceBtn = e.target.closest('[data-choice-slot]');
    if (choiceBtn && pendingAsin) {{ applyChoice(choiceBtn.dataset.choiceSlot, pendingAsin); return; }}

    const resultCard = e.target.closest('.mc-result-card[data-asin]');
    if (resultCard && !els.panel.hasAttribute('hidden')) {{
      const asin = resultCard.dataset.asin;
      if (pickingSlot === 'a' || pickingSlot === 'b') {{
        applyChoice(pickingSlot, asin);
      }} else {{
        pendingAsin = asin;
        renderSlotChoice(asin);
      }}
      return;
    }}
  }});

  els.compareBtn.addEventListener('click', () => {{
    if (!selected[0] || !selected[1]) return;
    renderCompare();
    const target = document.querySelector('.mc-vs-card');
    if (target) target.scrollIntoView({{ behavior: 'smooth', block: 'start' }});
  }});

  renderSlot('a');
  renderSlot('b');
  updateCompareBtn();
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
  console.log(`[prototipo v51] filas de producto: ${{rows}} | paneles de ficha: ${{panels}} | botones toggle: ${{toggles}} | botones Ver en Amazon (fila): ${{amazonRowBtns}} | cabeceras ordenables: ${{sortableHeaders}} | items en menus de cabecera: ${{totalMenuItems}} | campos ficha (min 6x30): ${{fichaCampos}} | botones cerrar ficha: ${{fichaCloseBtns}} | bloques de particularidad sueltos (deben ser 0): ${{fichaBloquesSueltos}} | restos del selector "Ordenar por" (debe ser 0): ${{sortSelectRestante}}`);
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
