"""Aplica un plan.json de "Planes en familia" al sitio público.

Único script autorizado a publicar lugares de esa sección — ver
.claude/skills/planes-familia/SKILL.md. "crear plan" / "revisar plan" /
"actualizar plan" son de solo lectura respecto al sitio; este script es
el equivalente al comando "aplicar plan [PROVINCIA]" del skill.

Uso:
    python tools/apply_plan_familia.py <provincia-slug>
    python tools/apply_plan_familia.py <provincia-slug> --dry-run

<provincia-slug> debe coincidir con el nombre de carpeta en
tools/output/planes-familia/<provincia-slug>/plan.json (el mismo
province_slug que ya usa el skill).

--dry-run: hace todo el trabajo (carga, valida, renderiza HTML de la
página de provincia y de los bloques de tarjeta de los hubs) pero NUNCA
toca un archivo real del sitio (ni guia-regalos-juguetes.html, ni
planes-en-familia*.html, ni sitemap.xml). El resultado se escribe en
tools/output/planes-familia/<provincia-slug>/preview/ para poder
revisarlo, y se imprime un resumen de qué archivos reales se crearían o
modificarían si se ejecutara sin --dry-run. Pensado para poder probar el
generador sin publicar nada.

Reglas duras (no negociables, ver conversación de diseño del 2026-08-19):
- plan.json es la única fuente de verdad; los campos (name, description,
  official_url, address) se vuelcan literales, nunca se reescriben aquí
  (la redacción editorial ya ocurrió en la Fase A.7 del skill).
- Solo se publican lugares con status == "primary" (rank 1-15). Los
  "backup" nunca se leen para generar HTML público — es un error fatal
  si en algún momento hay más de 15 "primary" o si un "backup" se
  cuela en el render.
- Nunca imágenes en esta primera versión (plan.json no tiene ese campo).
- Los enlaces a official_url son enlaces externos normales
  (target="_blank" rel="noopener"): nunca reutilizan la lógica de
  afiliado de Amazon (?tag=..., rel="sponsored").
- Idempotente: volver a ejecutar el mismo plan no duplica tarjetas ni
  contenido — las páginas de hub se actualizan por marcador
  (CCAA-CARD / PROVINCE-CARD), la página de provincia se regenera
  entera (es 100% generada por script, nunca editada a mano).
- Nunca hace commit ni push.
"""
import argparse
import datetime
import json
import pathlib
import re
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
PLANES_DIR = ROOT / "tools" / "output" / "planes-familia"
DOMAIN = "https://www.lauderem.com"
GA4_ID = "G-88T9H9C650"
ADSENSE_CLIENT = "ca-pub-9559559964863356"

HOME_FILE = "guia-regalos-juguetes.html"
ROOT_HUB_FILE = "planes-en-familia.html"
NAVBAR_FILE = ROOT / HOME_FILE

# ----------------------------------------------------------------------
# Relación fija provincia -> comunidad autónoma. Dato del mundo real que
# nunca cambia, por eso vive aquí (no en plan.json: no tiene sentido que
# el skill de investigación guarde una geografía que es siempre la
# misma). Claves = province_slug tal como lo normaliza el skill
# (minúsculas, sin acentos/ñ, espacios -> guiones).
# ----------------------------------------------------------------------
CCAA_NAMES = {
    "andalucia": "Andalucía",
    "aragon": "Aragón",
    "asturias": "Principado de Asturias",
    "baleares": "Illes Balears",
    "canarias": "Canarias",
    "cantabria": "Cantabria",
    "castilla-la-mancha": "Castilla-La Mancha",
    "castilla-y-leon": "Castilla y León",
    "cataluna": "Cataluña",
    "comunidad-valenciana": "Comunidad Valenciana",
    "extremadura": "Extremadura",
    "galicia": "Galicia",
    "la-rioja": "La Rioja",
    "madrid": "Comunidad de Madrid",
    "murcia": "Región de Murcia",
    "navarra": "Comunidad Foral de Navarra",
    "pais-vasco": "País Vasco",
    "ceuta": "Ceuta",
    "melilla": "Melilla",
}

PROVINCIA_TO_CCAA_SLUG = {
    # Andalucía
    "almeria": "andalucia", "cadiz": "andalucia", "cordoba": "andalucia",
    "granada": "andalucia", "huelva": "andalucia", "jaen": "andalucia",
    "malaga": "andalucia", "sevilla": "andalucia",
    # Aragón
    "huesca": "aragon", "teruel": "aragon", "zaragoza": "aragon",
    # Asturias
    "asturias": "asturias",
    # Baleares
    "baleares": "baleares", "illes-balears": "baleares",
    # Canarias
    "las-palmas": "canarias", "santa-cruz-de-tenerife": "canarias",
    # Cantabria
    "cantabria": "cantabria",
    # Castilla-La Mancha
    "albacete": "castilla-la-mancha", "ciudad-real": "castilla-la-mancha",
    "cuenca": "castilla-la-mancha", "guadalajara": "castilla-la-mancha",
    "toledo": "castilla-la-mancha",
    # Castilla y León
    "avila": "castilla-y-leon", "burgos": "castilla-y-leon",
    "leon": "castilla-y-leon", "palencia": "castilla-y-leon",
    "salamanca": "castilla-y-leon", "segovia": "castilla-y-leon",
    "soria": "castilla-y-leon", "valladolid": "castilla-y-leon",
    "zamora": "castilla-y-leon",
    # Cataluña
    "barcelona": "cataluna", "girona": "cataluna", "lleida": "cataluna",
    "tarragona": "cataluna",
    # Comunidad Valenciana
    "alicante": "comunidad-valenciana", "castellon": "comunidad-valenciana",
    "valencia": "comunidad-valenciana",
    # Extremadura
    "badajoz": "extremadura", "caceres": "extremadura",
    # Galicia
    "a-coruna": "galicia", "lugo": "galicia", "ourense": "galicia",
    "pontevedra": "galicia",
    # La Rioja
    "la-rioja": "la-rioja",
    # Madrid
    "madrid": "madrid",
    # Murcia
    "murcia": "murcia",
    # Navarra
    "navarra": "navarra",
    # País Vasco
    "alava": "pais-vasco", "gipuzkoa": "pais-vasco", "bizkaia": "pais-vasco",
    # Ciudades autónomas
    "ceuta": "ceuta", "melilla": "melilla",
}

MAX_PRIMARY = 15
MAX_DESCRIPTION_LEN = 160


def truncate_description(text: str, max_len: int = MAX_DESCRIPTION_LEN) -> str:
    """Garantiza como máximo max_len caracteres, evitando cortar una
    palabra a mitad cuando sea posible: si el corte cae dentro de una
    palabra, retrocede hasta el último espacio anterior. Si no hay ningún
    espacio dentro del límite (una única palabra larguísima, caso
    extremo), corta tal cual en max_len -- preferible a no respetar el
    límite. Nunca añade "..." ni reescribe el texto: solo recorta."""
    if len(text) <= max_len:
        return text
    cut = text[:max_len]
    last_space = cut.rfind(" ")
    if last_space > 0:
        cut = cut[:last_space]
    return cut.rstrip(" ,.;:-")


class ApplyError(Exception):
    """Error que debe detener la aplicación del plan con un mensaje claro."""


# ----------------------------------------------------------------------
# Carga y validación del plan
# ----------------------------------------------------------------------

def load_plan(provincia_slug: str, enforce_status: bool = True) -> dict:
    """enforce_status=False se usa únicamente desde --dry-run: permite
    previsualizar el render (p.ej. para revisar un cambio de diseño de
    tarjeta) aunque el plan ya esté "applied" o todavía no esté
    "reviewed", sin tocar plan.json ni publicar nada. La ruta real de
    publicación (sin --dry-run) siempre llama con enforce_status=True."""
    path = PLANES_DIR / provincia_slug / "plan.json"
    if not path.exists():
        raise ApplyError(
            f"No existe {path}. Ejecuta primero 'crear plan {provincia_slug}'."
        )
    plan = json.loads(path.read_text(encoding="utf-8"))

    if enforce_status and plan.get("plan_status") != "reviewed":
        raise ApplyError(
            f"plan_status es '{plan.get('plan_status')}', debe ser 'reviewed'. "
            "Ejecuta 'revisar plan' y confirma el plan antes de aplicarlo."
        )
    if enforce_status and plan.get("validation", {}).get("status") != "ok":
        raise ApplyError(
            "validation.status no es 'ok'. Hay errores bloqueantes pendientes: "
            "revisa el plan antes de aplicar."
        )

    primaries = [p for p in plan["places"] if p["status"] == "primary"]
    backups_leaked = [p for p in plan["places"] if p["status"] not in ("primary", "backup")]
    if backups_leaked:
        raise ApplyError(
            f"plan.json tiene lugares con status inválido: {[p['name'] for p in backups_leaked]}"
        )
    if not primaries:
        raise ApplyError("El plan no tiene ningún lugar 'primary'. Nada que publicar.")
    if len(primaries) > MAX_PRIMARY:
        raise ApplyError(
            f"El plan tiene {len(primaries)} lugares 'primary' (máximo {MAX_PRIMARY}). "
            "Revisa plan.json antes de aplicar — esto no debería poder pasar."
        )

    primaries.sort(key=lambda p: p["rank"])
    return plan, primaries


def resolve_ccaa(provincia_slug: str) -> tuple[str, str]:
    """Devuelve (ccaa_slug, ccaa_name) o lanza ApplyError si la provincia
    no está en la tabla — nunca se adivina la CCAA."""
    ccaa_slug = PROVINCIA_TO_CCAA_SLUG.get(provincia_slug)
    if ccaa_slug is None:
        raise ApplyError(
            f"'{provincia_slug}' no está en PROVINCIA_TO_CCAA_SLUG "
            f"(tools/apply_plan_familia.py). Añade la relación provincia -> "
            f"CCAA manualmente antes de aplicar este plan — nunca se adivina."
        )
    return ccaa_slug, CCAA_NAMES[ccaa_slug]


# ----------------------------------------------------------------------
# Render de la tarjeta de lugar (ver tools/place_card_template.html)
# ----------------------------------------------------------------------

def render_place_card(place: dict) -> str:
    """Tarjeta horizontal editorial de 2 zonas: numeración a la izquierda
    (ancho fijo) + una única columna a la derecha con nombre, descripción,
    dirección y enlace apilados (uno debajo del otro, sin subcolumnas ni
    líneas divisorias). Ver tools/place_card_template.html. Sin imagen ni
    icono temático todavía (fase posterior, pendiente de aprobación del
    diseño)."""
    rank = place["rank"]
    rank_2d = f"{rank:02d}"
    name = place["name"]
    desc = place["description"]

    location_html = ""
    if place.get("address"):
        location_html = (
            f'\n    <span class="pf-place-loc">'
            f'<i class="ti ti-map-pin" aria-hidden="true"></i>'
            f'<span>{place["address"]}</span></span>'
        )

    action_html = ""
    if place.get("official_url"):
        action_html = (
            f'\n    <a class="pf-place-cta" href="{place["official_url"]}" '
            f'target="_blank" rel="noopener">Visitar web oficial '
            f'<i class="ti ti-external-link" aria-hidden="true"></i></a>'
        )

    return (
        f'<!-- PLACE START rank="{rank}" -->\n'
        f'<article class="pf-place-row" data-rank="{rank}">\n'
        f'  <div class="pf-place-rank" aria-hidden="true">{rank_2d}</div>\n'
        f'  <div class="pf-place-content">\n'
        f'    <h3 class="pf-place-name">{name}</h3>\n'
        f'    <p class="pf-place-desc">{desc}</p>'
        f'{location_html}'
        f'{action_html}\n'
        f'  </div>\n'
        f'</article>\n'
        f'<!-- PLACE END rank="{rank}" -->'
    )


# ----------------------------------------------------------------------
# Cabecera compartida (GA4 + AdSense + fonts + tabler icons + site.css)
# ----------------------------------------------------------------------

def render_head(title: str, description: str, canonical_path: str, breadcrumb_items: list[tuple[str, str]]) -> str:
    breadcrumb_json = json.dumps(
        {
            "@context": "https://schema.org",
            "@type": "BreadcrumbList",
            "itemListElement": [
                {"@type": "ListItem", "position": i + 1, "name": name, "item": item}
                for i, (name, item) in enumerate(breadcrumb_items)
            ],
        },
        ensure_ascii=False,
    )
    return f"""<script type="text/javascript" charset="UTF-8" src="//cdn.cookie-script.com/s/067dce5e5b2c3eeb8cc1f8f51d3c14a8.js"></script>
<script async src="https://www.googletagmanager.com/gtag/js?id={GA4_ID}"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){{dataLayer.push(arguments);}}
  gtag('js', new Date());

  gtag('config', '{GA4_ID}');
</script>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
<link rel="canonical" href="{DOMAIN}/{canonical_path}">
<meta name="description" content="{description}">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Fredoka:wght@500;600;700&family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@500;600&display=swap" rel="stylesheet">
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@tabler/icons-webfont@3.31.0/dist/tabler-icons.min.css">
<link rel="stylesheet" href="css/site.css">
<script type="application/ld+json">
{breadcrumb_json}
</script>
<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client={ADSENSE_CLIENT}"
     crossorigin="anonymous"></script>"""


def render_header_nav() -> str:
    return """<header>
  <nav class="wrap">
    <div class="logo"><img src="images/cabecera/logohero/lauderem-logo-hero.svg" alt="Lauderem" width="130" height="32" loading="lazy" decoding="async"></div>
    <a class="back" href="/">← Volver a la guía</a>
  </nav>
</header>"""


# ----------------------------------------------------------------------
# Página de provincia (100% generada por script, se regenera entera en
# cada aplicación — no hace falta parchear por marcador dentro de ella).
# ----------------------------------------------------------------------

def render_province_page(plan: dict, primaries: list[dict], ccaa_slug: str, ccaa_name: str) -> str:
    provincia_slug = plan["province_slug"]
    provincia_name = plan["province"]
    ccaa_file = f"planes-en-familia-{ccaa_slug}.html"
    canonical_path = f"planes-en-familia-{provincia_slug}.html"

    title = f"Planes en familia en {provincia_name} | Lauderem"
    description = truncate_description(
        f"Museos, parques y planes para hacer en familia en {provincia_name}, "
        f"seleccionados y verificados por Lauderem."
    )

    head = render_head(
        title, description, canonical_path,
        [
            ("Guía de Regalos", HOME_FILE),
            ("Planes en familia", ROOT_HUB_FILE),
            (ccaa_name, ccaa_file),
            (provincia_name, canonical_path),
        ],
    )

    cards = "\n\n".join(render_place_card(p) for p in primaries)

    body = f"""<header>
  <nav class="wrap">
    <div class="logo"><img src="images/cabecera/logohero/lauderem-logo-hero.svg" alt="Lauderem" width="130" height="32" loading="lazy" decoding="async"></div>
    <a class="back" href="/">← Volver a la guía</a>
  </nav>
</header>

<section class="cat-hero-2 wrap">
  <div class="pf-crumb">
    <a class="pf-crumb-link" href="{ROOT_HUB_FILE}">Planes en familia</a>&nbsp;·&nbsp;<a class="pf-crumb-link" href="{ccaa_file}">{ccaa_name}</a>
  </div>
  <h1>Planes en familia en {provincia_name}</h1>
  <p class="cat-hero-2-subtitle">Lugares para visitar y planes para hacer en familia en {provincia_name}.</p>
</section>

<section class="wrap">
  <div class="pf-place-list">

{cards}

  </div>
</section>"""

    return f"""<!DOCTYPE html>
<html lang="es">
<head>
{head}
</head>
<body>

{body}

</body>
</html>
"""


# ----------------------------------------------------------------------
# Utilidades de marcador (idempotencia en páginas de hub)
# ----------------------------------------------------------------------

def upsert_marker_block(html_text: str, start_marker: str, end_marker: str, new_block: str) -> tuple[str, bool]:
    """Sustituye el bloque entre start_marker y end_marker (incluidos) por
    new_block si el marcador ya existe; si no existe, devuelve (html_text,
    False) para que el llamador decida dónde insertarlo la primera vez."""
    pattern = re.compile(
        re.escape(start_marker) + r".*?" + re.escape(end_marker), re.DOTALL
    )
    if pattern.search(html_text):
        return pattern.sub(lambda _m: new_block, html_text, count=1), True
    return html_text, False


def insert_into_grid(html_text: str, grid_start: str, grid_end: str, new_block: str) -> str:
    """Inserta new_block justo antes de grid_end (dentro del contenedor
    delimitado por grid_start/grid_end)."""
    idx = html_text.find(grid_end)
    if idx == -1:
        raise ApplyError(f"No se encontró el marcador '{grid_end}' — el archivo puede estar corrupto.")
    return html_text[:idx] + new_block + "\n\n" + html_text[idx:]


# ----------------------------------------------------------------------
# Hub de CCAA (planes-en-familia-<ccaa>.html)
# ----------------------------------------------------------------------

def render_province_card(provincia_slug: str, provincia_name: str, num_places: int) -> str:
    return (
        f'<!-- PROVINCE-CARD slug="{provincia_slug}" -->\n'
        f'<a class="pf-hub-card" href="planes-en-familia-{provincia_slug}.html" data-province="{provincia_slug}">\n'
        f'  <span class="pf-hub-card-icon"><i class="ti ti-map-pin" aria-hidden="true"></i></span>\n'
        f'  <span class="pf-hub-card-body">\n'
        f'    <span class="pf-hub-card-title">{provincia_name}</span>\n'
        f'    <span class="pf-hub-card-desc">{num_places} planes familiares en {provincia_name}.</span>\n'
        f'  </span>\n'
        f'  <span class="pf-hub-card-arrow"><i class="ti ti-arrow-right" aria-hidden="true"></i></span>\n'
        f'</a>\n'
        f'<!-- /PROVINCE-CARD slug="{provincia_slug}" -->'
    )


def render_new_ccaa_hub(ccaa_slug: str, ccaa_name: str, province_card: str) -> str:
    canonical_path = f"planes-en-familia-{ccaa_slug}.html"
    title = f"Planes en familia en {ccaa_name} | Lauderem"
    description = truncate_description(
        f"Elige una provincia de {ccaa_name} para ver sus planes y lugares "
        f"seleccionados para hacer en familia."
    )
    head = render_head(
        title, description, canonical_path,
        [
            ("Guía de Regalos", HOME_FILE),
            ("Planes en familia", ROOT_HUB_FILE),
            (ccaa_name, canonical_path),
        ],
    )
    body = f"""{render_header_nav()}

<section class="cat-hero-2 wrap">
  <div class="pf-crumb">
    <a class="pf-crumb-link" href="{ROOT_HUB_FILE}">Planes en familia</a>
  </div>
  <h1>Planes en familia en {ccaa_name}</h1>
  <p class="cat-hero-2-subtitle">Elige una provincia para ver sus planes familiares.</p>
</section>

<section class="wrap">
  <div class="pf-hub-grid">
  <!-- PROVINCE-GRID START -->

{province_card}

  <!-- PROVINCE-GRID END -->
  </div>
</section>"""
    return f"""<!DOCTYPE html>
<html lang="es">
<head>
{head}
</head>
<body>

{body}

</body>
</html>
"""


def ensure_ccaa_hub(ccaa_slug: str, ccaa_name: str, provincia_slug: str, provincia_name: str, num_places: int) -> tuple[str, str, bool]:
    """Devuelve (ruta_relativa, contenido_final, ya_existia)."""
    filename = f"planes-en-familia-{ccaa_slug}.html"
    path = ROOT / filename
    card = render_province_card(provincia_slug, provincia_name, num_places)

    if not path.exists():
        return filename, render_new_ccaa_hub(ccaa_slug, ccaa_name, card), False

    html_text = path.read_text(encoding="utf-8")
    start = f'<!-- PROVINCE-CARD slug="{provincia_slug}" -->'
    end = f'<!-- /PROVINCE-CARD slug="{provincia_slug}" -->'
    new_html, replaced = upsert_marker_block(html_text, start, end, card)
    if not replaced:
        new_html = insert_into_grid(html_text, "<!-- PROVINCE-GRID START -->", "<!-- PROVINCE-GRID END -->", card)
    return filename, new_html, True


# ----------------------------------------------------------------------
# Hub raíz (planes-en-familia.html)
# ----------------------------------------------------------------------

def render_ccaa_card(ccaa_slug: str, ccaa_name: str, num_provinces: int) -> str:
    provincia_word = "provincia" if num_provinces == 1 else "provincias"
    return (
        f'<!-- CCAA-CARD slug="{ccaa_slug}" -->\n'
        f'<a class="pf-hub-card" href="planes-en-familia-{ccaa_slug}.html" data-ccaa="{ccaa_slug}">\n'
        f'  <span class="pf-hub-card-icon"><i class="ti ti-map" aria-hidden="true"></i></span>\n'
        f'  <span class="pf-hub-card-body">\n'
        f'    <span class="pf-hub-card-title">{ccaa_name}</span>\n'
        f'    <span class="pf-hub-card-desc">{num_provinces} {provincia_word} con planes familiares.</span>\n'
        f'  </span>\n'
        f'  <span class="pf-hub-card-arrow"><i class="ti ti-arrow-right" aria-hidden="true"></i></span>\n'
        f'</a>\n'
        f'<!-- /CCAA-CARD slug="{ccaa_slug}" -->'
    )


def render_new_root_hub(ccaa_card: str) -> str:
    canonical_path = ROOT_HUB_FILE
    title = "Planes en familia: lugares y planes por provincia | Lauderem"
    description = truncate_description(
        "Museos, parques y planes para hacer en familia fuera de casa, "
        "organizados por comunidad autónoma y provincia."
    )
    head = render_head(
        title, description, canonical_path,
        [
            ("Guía de Regalos", HOME_FILE),
            ("Planes en familia", canonical_path),
        ],
    )
    body = f"""{render_header_nav()}

<section class="cat-hero-2 wrap">
  <h1>Planes en familia</h1>
  <p class="cat-hero-2-subtitle">Lugares y planes para hacer en familia fuera de casa, organizados por provincia.</p>
  <p class="cat-hero-2-body">Museos, parques, teatros y planes verificados para disfrutar en familia, elegidos con un proceso de investigación e verificación editorial. Elige una comunidad autónoma para empezar.</p>
</section>

<section class="wrap">
  <div class="pf-hub-grid">
  <!-- CCAA-GRID START -->

{ccaa_card}

  <!-- CCAA-GRID END -->
  </div>
</section>"""
    return f"""<!DOCTYPE html>
<html lang="es">
<head>
{head}
</head>
<body>

{body}

</body>
</html>
"""


def ensure_root_hub(ccaa_slug: str, ccaa_name: str, num_provinces: int) -> tuple[str, str, bool]:
    path = ROOT / ROOT_HUB_FILE
    card = render_ccaa_card(ccaa_slug, ccaa_name, num_provinces)

    if not path.exists():
        return ROOT_HUB_FILE, render_new_root_hub(card), False

    html_text = path.read_text(encoding="utf-8")
    start = f'<!-- CCAA-CARD slug="{ccaa_slug}" -->'
    end = f'<!-- /CCAA-CARD slug="{ccaa_slug}" -->'
    new_html, replaced = upsert_marker_block(html_text, start, end, card)
    if not replaced:
        new_html = insert_into_grid(html_text, "<!-- CCAA-GRID START -->", "<!-- CCAA-GRID END -->", card)
    return ROOT_HUB_FILE, new_html, True


# ----------------------------------------------------------------------
# Navbar (guia-regalos-juguetes.html) — nav-chip "Planes en familia"
# ----------------------------------------------------------------------

NAVCHIP_START = "<!-- NAV-CHIP planes-en-familia -->"
NAVCHIP_END = "<!-- /NAV-CHIP planes-en-familia -->"

NAVCHIP_BLOCK = f"""{NAVCHIP_START}
      <a class="nav-chip" href="{ROOT_HUB_FILE}">
        <i class="ti ti-map" aria-hidden="true"></i><span>Planes en familia</span>
      </a>
      {NAVCHIP_END}"""

PLANES_EN_CASA_CHIP_END = """<i class="ti ti-sofa" aria-hidden="true"></i><span>Planes en casa</span>
      </a>"""


def ensure_navchip() -> tuple[str, bool]:
    """Devuelve (contenido_final_del_navbar, ya_estaba_presente)."""
    html_text = NAVBAR_FILE.read_text(encoding="utf-8")
    if NAVCHIP_START in html_text or f'href="{ROOT_HUB_FILE}"' in html_text:
        return html_text, True
    if PLANES_EN_CASA_CHIP_END not in html_text:
        raise ApplyError(
            "No se encontró el nav-chip de 'Planes en casa' en "
            f"{HOME_FILE} para insertar el nuevo justo después — la navbar "
            "puede haber cambiado de formato. Revisa manualmente."
        )
    new_html = html_text.replace(
        PLANES_EN_CASA_CHIP_END,
        PLANES_EN_CASA_CHIP_END + "\n      " + NAVCHIP_BLOCK,
        1,
    )
    return new_html, False


# ----------------------------------------------------------------------
# Validación básica de HTML (checklist de CLAUDE.md)
# ----------------------------------------------------------------------

def validate_html_basic(name: str, html_text: str) -> None:
    if html_text.count("<head>") != 1 or html_text.count("</head>") != 1:
        raise ApplyError(f"{name}: <head> no aparece exactamente una vez.")
    if html_text.count("<html") != 1 or html_text.count("</html>") != 1:
        raise ApplyError(f"{name}: <html> no aparece exactamente una vez.")
    place_starts = re.findall(r'<!-- PLACE START rank="(\d+)" -->', html_text)
    if len(place_starts) != len(set(place_starts)):
        raise ApplyError(f"{name}: hay bloques PLACE START duplicados.")
    if len(place_starts) > MAX_PRIMARY:
        raise ApplyError(f"{name}: se están publicando {len(place_starts)} lugares (máximo {MAX_PRIMARY}).")


# ----------------------------------------------------------------------
# Regeneración de sitemap.xml
# ----------------------------------------------------------------------

def regenerate_sitemap(dry_run: bool) -> None:
    if dry_run:
        print("  [dry-run] no se ejecuta tools/generate_sitemap.py")
        return
    subprocess.run([sys.executable, str(ROOT / "tools" / "generate_sitemap.py")], check=True, cwd=ROOT)


# ----------------------------------------------------------------------
# main
# ----------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("provincia_slug", help="province_slug tal como aparece en tools/output/planes-familia/<slug>/plan.json")
    parser.add_argument("--dry-run", action="store_true", help="No toca ningún archivo real; escribe una previsualización en tools/output/planes-familia/<slug>/preview/")
    args = parser.parse_args()

    try:
        plan, primaries = load_plan(args.provincia_slug, enforce_status=not args.dry_run)
        ccaa_slug, ccaa_name = resolve_ccaa(args.provincia_slug)
    except ApplyError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1

    provincia_slug = plan["province_slug"]
    provincia_name = plan["province"]

    province_html = render_province_page(plan, primaries, ccaa_slug, ccaa_name)
    validate_html_basic(f"planes-en-familia-{provincia_slug}.html", province_html)

    ccaa_filename, ccaa_html, ccaa_existed = ensure_ccaa_hub(
        ccaa_slug, ccaa_name, provincia_slug, provincia_name, len(primaries)
    )
    validate_html_basic(ccaa_filename, ccaa_html)

    # num_provinces del hub raíz: si el hub de CCAA ya existía, cuenta sus
    # PROVINCE-CARD tras la actualización; si es nuevo, es 1.
    num_provinces = len(re.findall(r'<!-- PROVINCE-CARD slug="', ccaa_html)) or 1

    root_filename, root_html, root_existed = ensure_root_hub(ccaa_slug, ccaa_name, num_provinces)
    validate_html_basic(root_filename, root_html)

    navchip_html, navchip_existed = ensure_navchip()

    print(f"Plan: {provincia_name} ({provincia_slug}) -> {ccaa_name} ({ccaa_slug})")
    print(f"Lugares primary a publicar: {len(primaries)}")
    print()
    print("Archivos que se " + ("previsualizarían" if args.dry_run else "escribirían") + ":")
    print(f"  planes-en-familia-{provincia_slug}.html  (nuevo)")
    print(f"  {ccaa_filename}  ({'actualizado' if ccaa_existed else 'nuevo'})")
    print(f"  {root_filename}  ({'actualizado' if root_existed else 'nuevo'})")
    print(f"  {HOME_FILE}  ({'sin cambios, ya tenía el chip' if navchip_existed else 'nav-chip Planes en familia añadido'})")
    print(f"  sitemap.xml  ({'sin cambios' if args.dry_run else 'regenerado'})")

    if args.dry_run:
        preview_dir = PLANES_DIR / provincia_slug / "preview"
        preview_dir.mkdir(parents=True, exist_ok=True)
        (preview_dir / f"planes-en-familia-{provincia_slug}.html").write_text(province_html, encoding="utf-8")
        (preview_dir / ccaa_filename).write_text(ccaa_html, encoding="utf-8")
        (preview_dir / root_filename).write_text(root_html, encoding="utf-8")
        (preview_dir / HOME_FILE).write_text(navchip_html, encoding="utf-8")
        print()
        print(f"[dry-run] Nada real modificado. Previsualización escrita en {preview_dir}")
        return 0

    (ROOT / f"planes-en-familia-{provincia_slug}.html").write_text(province_html, encoding="utf-8")
    (ROOT / ccaa_filename).write_text(ccaa_html, encoding="utf-8")
    (ROOT / root_filename).write_text(root_html, encoding="utf-8")
    NAVBAR_FILE.write_text(navchip_html, encoding="utf-8")

    regenerate_sitemap(dry_run=False)

    # plan.applied.json debe ser un snapshot fiel del plan YA aplicado, no
    # del plan justo antes de aplicarlo -- por eso plan_status se marca
    # "applied" ANTES de escribir el snapshot, y el mismo dict (ya con
    # "applied") es el que se vuelca también en plan.json.
    plan["plan_status"] = "applied"
    applied_path = PLANES_DIR / provincia_slug / "plan.applied.json"
    applied_path.write_text(json.dumps(plan, ensure_ascii=False, indent=2), encoding="utf-8")
    plan_path = PLANES_DIR / provincia_slug / "plan.json"
    plan_path.write_text(json.dumps(plan, ensure_ascii=False, indent=2), encoding="utf-8")

    print()
    print(f"Aplicado. plan_status -> 'applied'. Snapshot guardado en {applied_path}")
    print("No se ha hecho commit ni push.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
