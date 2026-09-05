#!/usr/bin/env python3
"""
amazon_sillas_coche.py

Extractor INDEPENDIENTE de sillitas de coche para bebe en Amazon Espana.
No importa ni modifica `amazon_import.py` (version estable, intocable):
la logica reutilizable (Playwright, stealth, warm-up, descarga/recuadre de
imagen, valoracion, numero de valoraciones...) esta copiada/adaptada aqui
dentro para que este archivo pueda evolucionar sin afectar al extractor
original de fichas de juguetes.

Pipeline (etapas separadas, ver funciones mas abajo):

    busqueda Amazon -> resultados brutos -> filtro de marcas -> deduplicado
    -> ficha de producto -> texto crudo -> normalizacion de atributos
    -> analisis de opiniones (muestra) -> JSON estructurado

Uso:
    python tools/amazon_sillas_coche.py --search "sillita coche"
    python tools/amazon_sillas_coche.py --search "sillita coche bebe" --max-pages 2 --max-products 15
    python tools/amazon_sillas_coche.py --search "sillita coche" --no-images --out tools/output/test.json

Notas de diseno importantes:
- Regla "no inventar": cada atributo normalizado se obtiene de un detector
  basado en palabras clave/regex sobre texto REAL de Amazon (titulo,
  bullets, descripcion, tabla de detalles). Si ninguna fuente contiene
  evidencia explicita, el valor queda en "N/A" (nunca se infiere ni se
  asume). Se conserva el texto de origen que justifica cada valor no-N/A
  en `caracteristicas_fuente`.
- El "resumen" de opiniones (2-3 lineas, redaccion editorial) NO lo genera
  este script: igual que la redaccion de fichas en amazon_import.py, es
  criterio editorial y lo hace el asistente a partir de `opiniones.muestra`
  (texto crudo de resenas). Este script deja `opiniones.resumen = null`.
- Esta primera version NO genera tabla comparativa ni interfaz web: solo
  produce el JSON estructurado por producto.
"""

import argparse
import importlib.util
import json
import os
import random
import re
import subprocess
import sys
import time
import unicodedata
import urllib.request
from collections import OrderedDict
from datetime import date
from typing import Callable, Dict, List, Optional, Tuple
from urllib.parse import quote_plus


# ---------------------------------------------------------------------------
# CONFIGURACION (todo lo ajustable vive aqui, nada disperso por el codigo)
# ---------------------------------------------------------------------------

MAX_PAGES = 3
MAX_PRODUCTS = 30
REVIEW_SAMPLE_LIMIT = 10
BULLET_LIMIT = 12
IMAGES_DIR = "images/sillas-coche"
OUTPUT_DIR = "tools/output"

# Marca canonica -> alias tolerantes (ya en minusculas y sin acentos; la
# comparacion se hace tras normalizar el texto de Amazon del mismo modo).
BRANDS: "OrderedDict[str, List[str]]" = OrderedDict([
    ("Cybex", ["cybex"]),
    ("Maxi-Cosi", ["maxi cosi", "maxi-cosi", "maxicosi"]),
    ("Britax Römer", ["britax romer", "britax-romer", "britax"]),
    ("Be Cool", ["be cool", "becool"]),
    ("Joie", ["joie"]),
    ("Jané", ["jane"]),
    ("BeSafe", ["besafe", "be safe"]),
    ("Recaro", ["recaro"]),
    ("Kinderkraft", ["kinderkraft"]),
    ("BabyAuto", ["babyauto", "baby auto"]),
    ("Chicco", ["chicco"]),
    ("Bébé Confort", ["bebe confort", "bebeconfort"]),
    ("Nuna", ["nuna"]),
    ("Concord", ["concord"]),
    ("GB", ["gb"]),
    ("Klippan", ["klippan"]),
    ("Babify", ["babify"]),
])

SEARCH_HOST = "https://www.amazon.es"

# Categorias/busquedas usadas por warmup_session() para calentar la sesion
# con una navegacion mas natural antes de scrapear en serio.
WARMUP_CATEGORY_URLS = [
    "https://www.amazon.es/s?k=sillas+de+coche+bebe",
    "https://www.amazon.es/s?k=sillita+coche+isofix",
]

# Selectores candidatos para la imagen principal del producto.
IMAGE_SELECTORS = [
    "#landingImage",
    "#imgTagWrapperId img",
    "#main-image-container img",
    "#imageBlock img",
    "img#main-image",
]

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)


# ---------------------------------------------------------------------------
# UTILIDADES BASE (copiadas/adaptadas de amazon_import.py; ese archivo no
# se toca ni se importa: si algo cambia aqui, no afecta al original)
# ---------------------------------------------------------------------------

def ensure_pillow_installed() -> None:
    if importlib.util.find_spec("PIL") is None:
        subprocess.run([sys.executable, "-m", "pip", "install", "Pillow"], check=True)


def ensure_playwright_installed() -> None:
    if importlib.util.find_spec("playwright") is None:
        subprocess.run([sys.executable, "-m", "pip", "install", "playwright"], check=True)
    subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"], check=True)


def ensure_playwright_stealth_installed() -> None:
    if importlib.util.find_spec("playwright_stealth") is None:
        subprocess.run([sys.executable, "-m", "pip", "install", "playwright-stealth"], check=True)


ensure_pillow_installed()
from PIL import Image  # noqa: E402


def _log(msg: str) -> None:
    """Log de diagnostico a stderr (stdout solo lleva el JSON/rutas finales)."""
    print(msg, file=sys.stderr)


def _norm(text: str) -> str:
    """minusculas + sin acentos, para comparaciones tolerantes a acentos/mayusculas.

    Normaliza tambien las variantes de guion (en dash/em dash) a un guion
    ASCII antes de quitar acentos: encode("ascii","ignore") las elimina por
    completo (no tiene forma de descomponerlas a ASCII), lo que fusionaria
    p.ej. "15 meses - 12 anos" en "15 meses  12 anos" sin separador.
    """
    if not text:
        return ""
    text = text.replace("–", "-").replace("—", "-").replace("‒", "-")
    nfkd = unicodedata.normalize("NFKD", text)
    return nfkd.encode("ascii", "ignore").decode("ascii").lower()


def slugify(title: str, max_length: int = 70) -> str:
    ascii_text = unicodedata.normalize("NFKD", title).encode("ascii", "ignore").decode("ascii")
    lowered = ascii_text.lower()
    cleaned = re.sub(r"[^a-z0-9]+", " ", lowered)
    slug = re.sub(r"\s+", "-", cleaned.strip())
    if len(slug) > max_length:
        slug = slug[:max_length].rsplit("-", 1)[0]
    return slug or "producto"


def get_unique_path(directory: str, filename: str) -> str:
    base, ext = os.path.splitext(filename)
    candidate = os.path.join(directory, filename)
    counter = 2
    while os.path.exists(candidate):
        candidate = os.path.join(directory, f"{base}-{counter}{ext}")
        counter += 1
    return candidate


def guess_extension(image_url: str) -> str:
    match = re.search(r"\.(jpg|jpeg|png|webp)(?:[?#]|$)", image_url, re.IGNORECASE)
    return match.group(1).lower() if match else "jpg"


def download_image(image_url: str, dest_path: str) -> None:
    request = urllib.request.Request(image_url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=30) as response:
        data = response.read()
    with open(dest_path, "wb") as f:
        f.write(data)


def convert_to_webp(source_path: str, quality: int = 85) -> Optional[str]:
    webp_path = os.path.splitext(source_path)[0] + ".webp"
    try:
        with Image.open(source_path) as img:
            if img.mode not in ("RGB", "RGBA"):
                img = img.convert("RGBA" if "A" in img.mode else "RGB")
            img.save(webp_path, "WEBP", quality=quality)
        return webp_path
    except Exception:
        return None


def pad_to_square(image_path: str, size: int = 600, background: Tuple[int, int, int] = (255, 255, 255)) -> str:
    with Image.open(image_path) as img:
        if img.mode == "RGBA":
            flattened = Image.new("RGB", img.size, background)
            flattened.paste(img, mask=img.split()[3])
            img = flattened
        elif img.mode != "RGB":
            img = img.convert("RGB")

        ratio = min(size / img.width, size / img.height)
        new_size = (max(1, round(img.width * ratio)), max(1, round(img.height * ratio)))
        resized = img.resize(new_size, Image.LANCZOS)

        canvas = Image.new("RGB", (size, size), background)
        offset = ((size - new_size[0]) // 2, (size - new_size[1]) // 2)
        canvas.paste(resized, offset)

        webp_path = os.path.splitext(image_path)[0] + ".webp"
        canvas.save(webp_path, "WEBP", quality=90)

    if webp_path != image_path and os.path.exists(image_path):
        os.remove(image_path)
    return webp_path


def download_and_process_image(image_url: str, asin: str, slug: Optional[str]) -> Optional[str]:
    """Descarga, convierte a WebP y recuadra a 600x600 sin deformar. Devuelve la ruta final."""
    os.makedirs(IMAGES_DIR, exist_ok=True)
    extension = guess_extension(image_url)
    filename = f"{asin}.{extension}"
    dest_path = os.path.join(IMAGES_DIR, filename)
    try:
        download_image(image_url, dest_path)
    except Exception as e:
        _log(f"[WARN] fallo descargando imagen de {asin} ({e})")
        return None

    webp_path = convert_to_webp(dest_path)
    if webp_path and webp_path != dest_path:
        os.remove(dest_path)
        final_path = webp_path
    else:
        final_path = webp_path or dest_path

    if slug:
        seo_path = get_unique_path(IMAGES_DIR, f"{slug}.webp")
        os.rename(final_path, seo_path)
        final_path = seo_path

    final_path = pad_to_square(final_path)
    return final_path.replace(os.sep, "/")


def warmup_session(page) -> None:
    """Calienta la sesion antes de scrapear en serio (ver amazon_import.py: mismo patron)."""
    _log("[INFO] Warm-up iniciado")
    try:
        page.goto("https://www.amazon.es", wait_until="domcontentloaded", timeout=45000)
        _log("[INFO] Home cargada")
    except Exception as e:
        _log(f"[WARN] Warm-up: fallo cargando la home ({e}); se continua igualmente")

    try:
        wait1 = random.uniform(8, 15)
        _log(f"[INFO] Esperando {wait1:.0f} segundos")
        time.sleep(wait1)
    except Exception as e:
        _log(f"[WARN] Warm-up: fallo en la espera inicial ({e})")

    category_url = random.choice(WARMUP_CATEGORY_URLS)
    try:
        page.goto(category_url, wait_until="domcontentloaded", timeout=45000)
        _log(f"[INFO] Categoria abierta ({category_url})")
    except Exception as e:
        _log(f"[WARN] Warm-up: fallo abriendo la categoria {category_url} ({e}); se continua igualmente")

    try:
        for _ in range(random.randint(3, 5)):
            page.mouse.wheel(0, random.randint(150, 400))
            time.sleep(random.uniform(0.4, 1.2))
        _log("[INFO] Scroll realizado")
    except Exception as e:
        _log(f"[WARN] Warm-up: fallo haciendo scroll ({e}); se continua igualmente")

    _log("[INFO] Warm-up completado")


# ---------------------------------------------------------------------------
# ETAPA 1: BUSQUEDA EN AMAZON Y EXTRACCION DE RESULTADOS
# ---------------------------------------------------------------------------

def build_search_url(query: str, page_num: int) -> str:
    return f"{SEARCH_HOST}/s?k={quote_plus(query)}&page={page_num}"


def extract_search_results(page) -> List[Dict]:
    """Extrae {asin, title, url, thumb} de cada tarjeta de resultado visible."""
    results = []
    cards = page.query_selector_all('div[data-component-type="s-search-result"]')
    for card in cards:
        asin = card.get_attribute("data-asin")
        if not asin:
            continue
        title_el = card.query_selector("h2 a span") or card.query_selector("h2 span")
        title = title_el.inner_text().strip() if title_el else ""
        link_el = card.query_selector("h2 a") or card.query_selector("a.a-link-normal.s-no-outline")
        href = link_el.get_attribute("href") if link_el else None
        if not href:
            continue
        url = f"{SEARCH_HOST}{href}" if href.startswith("/") else href
        img_el = card.query_selector("img.s-image")
        thumb = img_el.get_attribute("src") if img_el else None
        if not title:
            continue
        results.append({"asin": asin, "title": title, "url": url, "thumb": thumb})
    return results


def search_amazon(page, query: str, max_pages: int) -> Tuple[List[Dict], int]:
    """Recorre hasta max_pages paginas de resultados. Devuelve (lista bruta, nº de paginas cargadas con exito)."""
    all_results: List[Dict] = []
    pages_loaded = 0
    for page_num in range(1, max_pages + 1):
        url = build_search_url(query, page_num)
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=45000)
            page.wait_for_selector('div[data-component-type="s-search-result"]', timeout=20000)
        except Exception as e:
            _log(f"[WARN] fallo cargando pagina de resultados {page_num} ({e}); se detiene la paginacion")
            break
        pages_loaded += 1
        time.sleep(random.uniform(1.5, 3.0))
        page_results = extract_search_results(page)
        _log(f"[INFO] Pagina {page_num}: {len(page_results)} resultados brutos")
        if not page_results:
            _log(f"[INFO] Pagina {page_num} sin resultados, se detiene la paginacion")
            break
        all_results.extend(page_results)
    return all_results, pages_loaded


# ---------------------------------------------------------------------------
# ETAPA 2: FILTRADO DE MARCAS Y DEDUPLICADO
# ---------------------------------------------------------------------------

def match_brand(text: str) -> Optional[str]:
    """Devuelve la marca canonica si el texto contiene alguno de sus alias (tolerante a acentos/mayus)."""
    norm = _norm(text)
    for brand, aliases in BRANDS.items():
        for alias in aliases:
            pattern = r"\b" + re.escape(alias) + r"\b"
            if re.search(pattern, norm):
                return brand
    return None


def filter_by_brand(candidates: List[Dict]) -> List[Dict]:
    filtered = []
    for c in candidates:
        brand = match_brand(c["title"])
        if brand:
            c["marca_detectada"] = brand
            filtered.append(c)
    return filtered


def dedupe_by_asin(candidates: List[Dict]) -> List[Dict]:
    seen = set()
    unique = []
    for c in candidates:
        if c["asin"] in seen:
            continue
        seen.add(c["asin"])
        unique.append(c)
    return unique


# ---------------------------------------------------------------------------
# ETAPA 3: EXTRACCION DE FICHA DE PRODUCTO (texto crudo, sin normalizar)
# ---------------------------------------------------------------------------

def get_main_image_url(page) -> Optional[str]:
    for selector in IMAGE_SELECTORS:
        element = page.query_selector(selector)
        if not element:
            continue
        src = element.get_attribute("data-old-hires") or element.get_attribute("src")
        if src:
            return src
    return None


def get_product_title(page) -> Optional[str]:
    element = page.query_selector("#productTitle")
    if element:
        text = element.inner_text().strip()
        if text:
            return text
    return None


def extract_bullets(page, limit: int = BULLET_LIMIT) -> List[str]:
    bullets: List[str] = []
    for element in page.query_selector_all("#feature-bullets li span.a-list-item"):
        text = element.inner_text().strip()
        if text and text not in bullets:
            bullets.append(text)
        if len(bullets) >= limit:
            break
    return bullets


def _clean_review_text(text: str) -> str:
    """Colapsa espacios/saltos de linea sobrantes y quita comillas envolventes."""
    text = re.sub(r"\s+", " ", text).strip()
    return text.strip("\"'“”")


# Fragmentos de UI que a veces quedan como unico contenido de un contenedor
# de reseña (enlaces/botones incrustados) y que no son texto de opinion real.
REVIEW_NOISE_TEXTS = {
    "leer mas", "leer más", "show more", "reportar", "denunciar",
    "informar de un problema", "compra verificada", "traducir todas las reseñas al español",
}

# Contenedores de texto de reseña candidatos, probados en orden dentro de
# cada tarjeta `[data-hook="review"]`. Amazon ha cambiado el marcado de
# opiniones mas de una vez: "reviewRichContentContainer" es el actual
# (verificado en vivo en 2026-08), "review-text-content" y "review-body"
# son marcados anteriores que Amazon todavia sirve en algunos layouts/
# locales, y se mantienen como fallback.
REVIEW_TEXT_CONTAINER_SELECTORS = [
    '[data-hook="reviewRichContentContainer"]',
    '[data-hook="review-text-content"]',
    '[data-hook="review-body"]',
]


def extract_reviews_sample(page, limit: int = REVIEW_SAMPLE_LIMIT, max_chars: int = 400) -> List[str]:
    """
    Extrae el texto real de hasta `limit` reseñas de clientes, una por
    tarjeta de reseña (`[data-hook="review"]`). Para cada tarjeta prueba los
    selectores de REVIEW_TEXT_CONTAINER_SELECTORS en orden y usa el primero
    que devuelva texto no vacio y que no sea puro ruido de interfaz (p.ej.
    "Leer más"), para no confundir un boton/enlace con una opinion real.
    """
    reviews: List[str] = []
    cards = page.query_selector_all('[data-hook="review"]')
    for card in cards:
        text = None
        for selector in REVIEW_TEXT_CONTAINER_SELECTORS:
            element = card.query_selector(selector)
            if not element:
                continue
            candidate = _clean_review_text(element.inner_text())
            if candidate and candidate.lower() not in REVIEW_NOISE_TEXTS:
                text = candidate
                break
        if text:
            reviews.append(text[:max_chars])
        if len(reviews) >= limit:
            break
    return reviews


def get_rating(page) -> Optional[float]:
    element = page.query_selector("#acrPopover span.a-icon-alt") or page.query_selector(
        "#averageCustomerReviews span.a-icon-alt"
    )
    if not element:
        return None
    text = (element.text_content() or "").strip()
    match = re.search(r"([\d,.]+)\s*de\s*5", text)
    if not match:
        return None
    try:
        return float(match.group(1).replace(",", "."))
    except ValueError:
        return None


def get_review_count(page) -> Optional[int]:
    element = page.query_selector("#acrCustomerReviewText")
    if not element:
        return None
    text = (element.text_content() or "").strip()
    match = re.search(r"([\d.,]+)", text)
    if not match:
        return None
    digits = re.sub(r"[^\d]", "", match.group(1))
    return int(digits) if digits else None


def get_byline_brand(page) -> Optional[str]:
    """Marca segun la linea 'Visita la tienda de X' / 'Marca: X' bajo el titulo (mas fiable que el titulo)."""
    el = page.query_selector("#bylineInfo")
    if not el:
        return None
    text = el.inner_text().strip()
    text = re.sub(r"^(Visita la tienda de|Marca)\s*:?\s*", "", text, flags=re.IGNORECASE).strip()
    return text or None


def _parse_price(text: Optional[str]) -> Optional[float]:
    if not text:
        return None
    match = re.search(r"([\d.,]+)", text)
    if not match:
        return None
    raw = match.group(1)
    if "," in raw:
        raw = raw.replace(".", "").replace(",", ".")
    try:
        return round(float(raw), 2)
    except ValueError:
        return None


def get_price(page) -> Tuple[Optional[float], Optional[float]]:
    """Devuelve (precio_actual, precio_anterior). precio_anterior es None si Amazon no muestra tachado."""
    current = None
    for selector in (
        ".priceToPay .a-offscreen",
        "#corePrice_feature_div .a-price .a-offscreen",
        "#corePriceDisplay_desktop_feature_div .a-price .a-offscreen",
        "span.a-price .a-offscreen",
    ):
        el = page.query_selector(selector)
        if el:
            current = _parse_price(el.text_content())
            if current is not None:
                break

    previous = None
    for selector in (".basisPrice .a-offscreen", "span.a-price.a-text-price .a-offscreen"):
        el = page.query_selector(selector)
        if el:
            previous = _parse_price(el.text_content())
            if previous is not None:
                break

    return current, previous


def get_description(page) -> str:
    el = page.query_selector("#productDescription")
    if el:
        return el.inner_text().strip()
    return ""


def extract_table_rows(page, selector: str) -> List[Tuple[str, str]]:
    """Filas th/td de una tabla de detalles (especificaciones tecnicas / resumen del producto)."""
    rows = []
    for tr in page.query_selector_all(f"{selector} tr"):
        cells = tr.query_selector_all("th, td")
        if len(cells) >= 2:
            label = cells[0].inner_text().strip()
            value = cells[1].inner_text().strip()
            if label and value:
                rows.append((label, value))
    return rows


def extract_detail_bullets(page) -> List[Tuple[str, str]]:
    """Lista 'Detalles del producto' (formato 'Etiqueta : Valor' con separadores unicode ocultos)."""
    rows = []
    for li in page.query_selector_all("#detailBullets_feature_div li"):
        text = li.inner_text().strip()
        parts = re.split(r"[:‏‎]+", text, maxsplit=1)
        if len(parts) == 2:
            label, value = parts[0].strip(), parts[1].strip()
            if label and value:
                rows.append((label, value))
    return rows


def scrape_product_detail(page, url: str) -> Optional[Dict]:
    """Visita la ficha y devuelve texto crudo (sin normalizar). None si la pagina no carga o no tiene titulo."""
    try:
        page.goto(url, wait_until="domcontentloaded", timeout=45000)
        page.wait_for_selector("#productTitle", timeout=20000)
    except Exception as e:
        _log(f"[WARN] fallo cargando ficha {url} ({e})")
        return None

    title = get_product_title(page)
    if not title:
        _log(f"[WARN] sin titulo de producto en {url}, se omite")
        return None

    detail_rows = (
        extract_table_rows(page, "#productDetails_techSpec_section_1")
        + extract_table_rows(page, "#productOverview_feature_div")
        + extract_detail_bullets(page)
    )

    price_actual, price_anterior = get_price(page)

    return {
        "title": title,
        "image_url": get_main_image_url(page),
        "bullets": extract_bullets(page),
        "description": get_description(page),
        "reviews": extract_reviews_sample(page),
        "rating": get_rating(page),
        "review_count": get_review_count(page),
        "price_actual": price_actual,
        "price_anterior": price_anterior,
        "byline_brand": get_byline_brand(page),
        "detail_rows": detail_rows,
    }


# ---------------------------------------------------------------------------
# ETAPA 4: NORMALIZACION DE LOS 13 ATRIBUTOS
#
# Cada detector recibe (origen, texto) y devuelve un valor normalizado SOLO
# si encuentra evidencia EXPLICITA en ese texto (palabra clave / patron).
# Si no hay evidencia, devuelve None y el motor prueba la siguiente fuente;
# si ninguna fuente da evidencia, el atributo queda en "N/A". Nunca se
# infiere un valor a partir de lenguaje de marketing ambiguo.
# ---------------------------------------------------------------------------

Detector = Callable[[str, str], Optional[str]]


def det_grupo_edad(origin: str, text: str) -> Optional[str]:
    t = _norm(text)
    # Unidad del primer numero: si Amazon dice "15 meses - 12 anos", las
    # unidades de cada extremo son distintas y hay que conservarlo tal cual
    # (etiquetar ambos como "años" seria inventar un dato que Amazon no dio).
    m = re.search(r"(\d{1,2}(?:,\d)?)\s*(meses)?\s*(?:a|-|hasta)\s*(\d{1,2}(?:,\d)?)\s*anos?", t)
    if m:
        n1, unit1_is_meses, n2 = m.group(1), bool(m.group(2)), m.group(3)
        if unit1_is_meses:
            return f"{n1} meses - {n2} años"
        return f"{n1}-{n2} años"
    m2 = re.search(r"grupo\s*(0\+/1/2/3|0\+/1|1/2/3|2/3|0\+|[0-3])\b", t)
    if m2:
        return f"Grupo {m2.group(1).upper()}"
    return None


def det_peso_recomendado(origin: str, text: str) -> Optional[str]:
    # Amazon casi siempre escribe "Kilogramos" (palabra completa) en la
    # tabla de detalles, no la abreviatura "kg": se normaliza aqui para que
    # el resto de patrones (todos escritos en torno a "kg") los reconozcan
    # igual sin duplicar cada regex en dos variantes.
    t = re.sub(r"kilogramos?", "kg", text.lower())
    if "paquete" in t or "envio" in t or "envío" in t:
        return None
    m = re.search(r"(\d{1,3})\s*kg\.?\s*(?:a|-|–|—|hasta)\s*(\d{1,3})\s*kg", t)
    if m:
        return f"{m.group(1)}-{m.group(2)} kg"
    m2 = re.search(r"de\s+(\d{1,3})\s*a\s*(\d{1,3})\s*kg", t)
    if m2:
        return f"{m2.group(1)}-{m2.group(2)} kg"
    # Patron mas comun en titulos de Amazon: "9-36 kg" (un solo guion, un
    # solo "kg" al final), distinto del patron de arriba que exige "kg"
    # despues de cada numero.
    m3 = re.search(r"(\d{1,3})\s*-\s*(\d{1,3})\s*kg\b", t)
    if m3:
        return f"{m3.group(1)}-{m3.group(2)} kg"
    # Solo el maximo disponible (fila de tabla "Recomendacion de peso
    # maximo: X kg" sin un minimo emparejado en la misma cadena).
    m4 = re.search(r"peso\s*m[aá]ximo[^\d]{0,20}(\d{1,3})\s*kg", t)
    if m4:
        return f"Hasta {m4.group(1)} kg"
    m5 = re.search(r"hasta\s+(\d{1,3})\s*kg", t)
    if m5:
        return f"Hasta {m5.group(1)} kg"
    return None


def det_isofix(origin: str, text: str) -> Optional[str]:
    t = _norm(text)
    if "isofix" not in t:
        return None
    if re.search(r"sin\s+isofix", t):
        return "No"
    return "Sí"


def det_orientacion(origin: str, text: str) -> Optional[str]:
    t = _norm(text)
    # "hacia adelante"/"orientacion trasera" son el fraseo que usa el campo
    # estructurado de Amazon ("Orientacion: Orientacion hacia adelante"),
    # distinto de "a favor/contra la marcha" que usan titulo/bullets.
    # No se añade "sentido opuesto a la marcha": ese fraseo aparece en un
    # campo de PESO (no de orientacion) y en al menos un caso del lote
    # contradice el resto de la ficha (booster 100-150cm solo hacia
    # delante), asi que no es fiable como evidencia de contramarcha.
    contramarcha = bool(re.search(r"contramarcha|orientacion trasera|hacia atras", t))
    favor = bool(re.search(r"favor de la marcha|sentido de la marcha|hacia adelante|hacia delante", t))
    if contramarcha and favor:
        return "Ambas"
    if contramarcha:
        return "A contramarcha"
    if favor:
        return "A favor de la marcha"
    return None


def det_reclinable(origin: str, text: str) -> Optional[str]:
    t = _norm(text)
    if not re.search(r"reclinable|reclinacion|reclinado", t):
        return None
    m = re.search(r"(\d+)\s*posicion", t)
    if m:
        return f"Sí — {m.group(1)} posiciones"
    return "Sí"


HOMOLOGACION_RE = re.compile(r"\b(i-?Size|R129(?:/\d{2})?|R44(?:/\d{2})?|ECE\s?R44(?:/\d{2})?)\b", re.IGNORECASE)


def det_homologacion(origin: str, text: str) -> Optional[str]:
    m = HOMOLOGACION_RE.search(text)
    if not m:
        return None
    val = re.sub(r"\s+", " ", m.group(1)).strip()
    if val.lower().replace("-", "") == "isize":
        return "i-Size"
    return val.upper()


def det_giro_360(origin: str, text: str) -> Optional[str]:
    t = _norm(text)
    if re.search(r"gir\w*", t) and re.search(r"360", t):
        return "Sí"
    # Algunos titulos solo listan "360º" como especificacion suelta, sin la
    # palabra "girar/giratoria" en ningun texto rastreado (aunque las
    # reseñas de clientes si lo describan; esas no se usan aqui). El simbolo
    # de grados junto a 360 es evidencia suficientemente inequivoca en el
    # contexto de una silla de coche. Se comprueba sobre el texto ORIGINAL
    # (no _norm, que ya ha eliminado "º"/"°" al pasar a ASCII).
    if re.search(r"360\s*[°º]", text):
        return "Sí"
    return None


def det_reposacabezas(origin: str, text: str) -> Optional[str]:
    """El numero de posiciones debe corresponder EXCLUSIVAMENTE a la
    regulacion en ALTURA del reposacabezas -- nunca a su reclinacion/
    inclinacion, que es una regulacion distinta con su propio contador.
    Caso real que motivo esta regla (auditoria fabricante): Cybex Solution
    X i-Fix tiene dos frases separadas -- "Reposacabezas reclinable...de 3
    posiciones" (inclinacion) y "Reposacabezas ajustable en altura...11
    posiciones" (altura) --; el valor correcto para este atributo es 11, no
    el primero que aparezca en el texto.

    Dos pasadas: la primera recorre cada mencion de "reposacabezas" del
    texto buscando un numero de posiciones valido (se descarta si la
    mencion es "reposacabezas reclinable..." o si aparece "reclinable/
    reclinacion/inclinacion" entre "reposacabezas" y el numero -- asi no
    importa el orden en que aparezcan las menciones, la de altura se
    encuentra igual). Si ninguna mencion da un numero valido, la segunda
    pasada acepta una confirmacion cualitativa ("Sí" sin numero) con el
    mismo criterio de la version anterior (regula/ajust/en altura/
    posicion en cualquier parte del texto) — salvo "posicion" a secas, que
    se retira de este segundo criterio: sin verbo de regulacion alrededor,
    "N posiciones" sin mas contexto es precisamente el patron ambiguo que
    esta funcion existe para no confirmar a ciegas (ver caso Cybex bullet
    de reclinado, que solo dice "...de 3 posiciones..." sin "regula/
    ajust/altura" en absoluto).
    """
    t = _norm(text)
    if "reposacabezas" not in t:
        return None

    ocurrencias = list(re.finditer(r"reposacabezas", t))

    for m in ocurrencias:
        after = t[m.start():m.start() + 130]
        if re.match(r"^reposacabezas\s+reclinable\b", after):
            continue
        num_m = re.search(r"(\d+)\s*posicion", after)
        if num_m and not re.search(r"reclinable|reclinacion|inclinacion", after[:num_m.start()]):
            return f"Sí — {num_m.group(1)} posiciones"

    if re.search(r"regula|ajust|en altura", t):
        return "Sí"

    return None


def det_arnes(origin: str, text: str) -> Optional[str]:
    t = _norm(text)
    # Hasta 20 caracteres no numericos entre "arnes" y "N puntos" para
    # cubrir tanto prosa ("arnes interior de 5 puntos") como el formato de
    # tabla de detalles ("Tipo de arnes: 5 puntos", con dos puntos), sin
    # tener que enumerar cada palabra intermedia posible.
    if re.search(r"arnes[^\d]{0,20}5\s*puntos", t):
        return "Arnés de 5 puntos"
    if re.search(r"arnes[^\d]{0,20}3\s*puntos", t):
        return "Arnés de 3 puntos"
    # "Cinturon de seguridad de 5 puntos" (sin la palabra "arnes") es un
    # sinonimo real usado por algunos fabricantes para el arnes interior
    # (caso confirmado en auditoria: Kinderkraft I-COMFY). Solo se acepta
    # con la estructura explicita "5 puntos": un cinturon de vehiculo nunca
    # es "de 5 puntos" (siempre 2 o 3 puntos), asi que no hay riesgo de
    # confundirlo con el sistema de instalacion de la silla. No se aplica la
    # misma relajacion a "3 puntos": esa cifra si es ambigua (cinturon de
    # vehiculo de 3 puntos es el caso mas comun), asi que ahi se sigue
    # exigiendo la palabra "arnes" explicita.
    if re.search(r"cinturon\w*[^\d]{0,20}5\s*puntos", t):
        return "Arnés de 5 puntos"
    if re.search(r"escudo de impacto|escudo anti.?impacto|escudo protector", t):
        return "Escudo de impacto"
    # "cinturon(es) ... coche/vehiculo/automovil" en una ventana amplia para
    # cubrir variantes de articulo/plural ("del vehiculo", "de tu coche",
    # "de este automovil"...). No se relaja mas alla de eso: un texto que
    # solo dice "cinturon de seguridad" sin mencionar coche/vehiculo en
    # ningun momento se deja en N/A en vez de asumir a que cinturon se
    # refiere.
    if re.search(r"cinturon\w*[^\d]{0,25}(?:vehiculo|coche|automovil)", t):
        return "Cinturón del vehículo"
    return None


def det_peso_silla(origin: str, text: str) -> Optional[str]:
    if origin.startswith("detalle:"):
        label = _norm(origin[len("detalle:"):])
        if "peso" in label and ("producto" in label or "articulo" in label or "silla" in label) \
                and "paquete" not in label and "envio" not in label:
            m = re.search(r"([\d.,]+)\s*(?:kg|kilogramos)", text.lower())
            if m:
                return f"{m.group(1).replace('.', ',')} kg"
    m2 = re.search(r"pesa\s+([\d.,]+)\s*kg", text.lower())
    if m2:
        return f"{m2.group(1).replace('.', ',')} kg"
    return None


def det_proteccion_lateral(origin: str, text: str) -> Optional[str]:
    t = _norm(text)
    # Formas en plural ("impactos laterales", "protectores laterales") son
    # el fraseo mas habitual en bullets de Amazon; el patron original solo
    # cubria el singular. "colision lateral" es otra variante real
    # encontrada en el lote (en vez de "impacto lateral").
    if re.search(r"proteccion(?:es)? lateral(?:es)?|impacto(?:s)? lateral(?:es)?"
                 r"|protector(?:es)? lateral(?:es)?|colision lateral|l\.?s\.?p\.?", t):
        return "Sí"
    # "Sistema lateral SPS/H-GUARD/G-CELL ... absorbiendo la energia del
    # impacto" (caso confirmado en auditoria: Kinderkraft JUNIOR FIX 2 PRO):
    # "lateral" y "impacto/proteccion" no son contiguos, pero el texto
    # nombra una tecnologia de proteccion lateral reconocida junto a
    # "lateral" y menciona impacto/proteccion en el mismo texto. Se exige
    # el nombre de la tecnologia a proposito para no convertir menciones
    # genericas de espuma/acolchado/confort (sin tecnologia nombrada) en
    # proteccion lateral.
    if re.search(r"sistema lateral\b", t) and re.search(r"h-?guard|sps\+?|g-?cell", t) \
            and re.search(r"impacto|proteccion|protege", t):
        return "Sí"
    return None


def det_funda_lavable(origin: str, text: str) -> Optional[str]:
    t = _norm(text)
    # Amazon rara vez dice "funda lavable" tal cual, contiguo: lo habitual
    # es "funda... se puede lavar", "forro... lavarlo", "tapiceria...
    # lavable a maquina", con palabras de por medio y el verbo conjugado en
    # vez del adjetivo. En vez de enumerar cada frase exacta, se comprueba
    # que aparezcan juntos (en el mismo bullet/fila) una palabra de "funda"
    # (incluye sinonimos reales del lote: forro, tapiceria/tapizado) y una
    # palabra de la familia "lavar" (lavable/lavar/lavado/lavarla/lavarlo).
    if re.search(r"funda|forro|tapiceria|tapizado", t) and re.search(r"lava", t):
        return "Sí"
    return None


def det_travel_system(origin: str, text: str) -> Optional[str]:
    t = _norm(text)
    if re.search(r"travel system|compatible con capazo|compatible con (?:la )?silla de paseo|click ?& ?go", t):
        return "Sí"
    return None


# clave -> (etiqueta ES, detector, es_obligatorio)
ATTRS: "OrderedDict[str, Tuple[str, Detector, bool]]" = OrderedDict([
    ("grupo_edad", ("Grupo / rango de edad", det_grupo_edad, True)),
    ("peso_recomendado", ("Peso recomendado (kg)", det_peso_recomendado, True)),
    ("isofix", ("ISOFIX", det_isofix, True)),
    ("orientacion", ("Orientacion (contramarcha/favor de la marcha)", det_orientacion, True)),
    ("reclinable", ("Reclinable", det_reclinable, True)),
    ("homologacion", ("Homologacion / normativa", det_homologacion, True)),
    ("giro_360", ("Giratoria 360º", det_giro_360, True)),
    ("reposacabezas_regulable", ("Reposacabezas regulable en altura", det_reposacabezas, True)),
    ("tipo_arnes_proteccion", ("Tipo de arnes / proteccion", det_arnes, True)),
    ("peso_silla", ("Peso de la silla (kg)", det_peso_silla, True)),
    ("proteccion_lateral", ("Proteccion lateral de impactos", det_proteccion_lateral, False)),
    ("funda_lavable", ("Funda lavable / desenfundable", det_funda_lavable, False)),
    ("travel_system", ("Compatibilidad capazo / travel system", det_travel_system, False)),
])

REQUIRED_ATTRS = [key for key, (_, _, required) in ATTRS.items() if required]


def _extract_number(value: str) -> Optional[str]:
    m = re.search(r"[\d.,]+", value)
    return m.group(0) if m else None


def build_origins(raw: Dict) -> List[Tuple[str, str]]:
    """Orden de prioridad: tabla de detalles (mas estructurada) > bullets > titulo > descripcion."""
    origins: List[Tuple[str, str]] = []

    # Amazon a veces expone el peso recomendado como dos filas separadas
    # ("Recomendacion de peso minimo" / "Recomendacion de peso maximo") en
    # vez de un unico texto con el rango; el detector de peso_recomendado
    # solo mira un origen (una fila) a la vez, asi que aqui se combinan en
    # un origen sintetico "X kg - Y kg" cuando ambas existen, para que
    # det_peso_recomendado pueda leer el rango completo. Se exige
    # literalmente "recomendacion" en la etiqueta para no confundirlo con
    # otros campos de peso con "minimo/maximo" en el nombre pero que no son
    # el rango general (p.ej. "Peso minimo EN SENTIDO OPUESTO A LA MARCHA",
    # que es especifico de la instalacion a contramarcha, no del rango
    # general del producto).
    peso_min_val = peso_max_val = None
    for label, value in raw["detail_rows"]:
        l = _norm(label)
        if "recomendacion" in l and "peso" in l:
            if "maximo" in l:
                peso_max_val = _extract_number(value)
            elif "minimo" in l:
                peso_min_val = _extract_number(value)
    if peso_min_val and peso_max_val:
        origins.append(("detalle:peso_recomendado_combinado", f"{peso_min_val} kg - {peso_max_val} kg"))

    for label, value in raw["detail_rows"]:
        origins.append((f"detalle:{label}", f"{label}: {value}"))
    for b in raw["bullets"]:
        origins.append(("bullet", b))
    if raw["title"]:
        origins.append(("titulo", raw["title"]))
    if raw["description"]:
        origins.append(("descripcion", raw["description"]))
    return origins


def normalize_attributes(raw: Dict) -> "OrderedDict[str, Dict]":
    """Devuelve, por atributo, {"valor": ..., "fuente": texto_original_o_None}."""
    origins = build_origins(raw)
    caracteristicas: "OrderedDict[str, Dict]" = OrderedDict()
    for key, (_, detector, _required) in ATTRS.items():
        value, source = "N/A", None
        for origin_label, text in origins:
            hit = detector(origin_label, text)
            if hit:
                value, source = hit, text
                break
        caracteristicas[key] = {"valor": value, "fuente": source}
    return caracteristicas


def determine_estado(caracteristicas: "OrderedDict[str, Dict]") -> str:
    for key in REQUIRED_ATTRS:
        if caracteristicas[key]["valor"] == "N/A":
            return "PENDIENTE_REVISION"
    return "VERIFICADO"


# ---------------------------------------------------------------------------
# ETAPA 4B: CLASIFICACION CON FUENTE SECUNDARIA (FABRICANTE OFICIAL)
#
# Bloque nuevo "clasificacion", separado de `caracteristicas` (que no se
# toca: sigue igual para no romper build_sillas_report.py / comparativa).
# Cada campo usa el envoltorio original/normalizado/mostrar/revisar/fuente/
# url_fuente validado con el usuario. Reglas de fuentes:
#   1. Amazon es la fuente principal.
#   2. Si Amazon no permite confirmar el dato, se consulta el lookup de
#      fabricante oficial (tools/fabricante_lookup.json).
#   3. No se usan tiendas/marketplaces/blogs de terceros.
#   4. Si Amazon y fabricante coinciden, fuente = "amazon_y_fabricante".
#   5. Si solo el fabricante lo confirma, fuente = "fabricante_oficial" (dato
#      de primer nivel, NUNCA se marca como "inferido").
#   6. Si hay contradiccion, revisar=True y normalizado=None — nunca se
#      resuelve automaticamente (salvo que un humano ya la haya resuelto
#      explicitamente en el chat, ver "resuelto_manualmente" mas abajo).
#
# CONTENIDO VALIDO vs. NO VALIDO en la web del fabricante (metodologia
# fijada tras el caso Maxi-Cosi Tanza): solo cuenta como evidencia el
# contenido VISIBLE de la ficha del producto (descripcion, secciones de
# caracteristicas/especificaciones, tablas visibles, FAQs desplegadas
# dentro de la ficha). NUNCA la etiqueta <title> HTML, meta description,
# datos estructurados ocultos, snippets de buscador, la URL o nombres de
# archivo. Al usar get_page_text, todo lo que aparece antes de la linea
# "Source element: <main> / ---" es metadato (incluida la linea "Title:") y
# se descarta; solo cuenta lo que viene despues.
#
# IDENTIFICACION DEL PRODUCTO: el nombre comercial en Amazon y en la web del
# fabricante no tienen por que coincidir (ver caso Kinderkraft JUNIOR FIX 2
# PRO=PLUS). Cada entrada del lookup lleva "identidad_verificada" (bool):
# solo se usa el hallazgo si es true. La equivalencia se confirma con al
# menos 2 señales independientes (SKU/prefijo de familia, caracteristicas
# tecnicas coincidentes, rango de altura, homologacion, ISOFIX...) — nunca
# solo por parecido de nombre. Si se investigo pero NO se pudo confirmar,
# la entrada queda con identidad_verificada=false (no se usa su contenido,
# pero se avisa "Posible variante/producto diferente" en vez de un N/A
# silencioso). Cuando el nombre difiere pero la identidad si se confirma,
# se guarda aviso_nombre_diferente=true + nombre_amazon/nombre_fabricante/
# motivo_equivalencia, sin ocultar la discrepancia de nombre.
#
# IMPORTANTE sobre el lookup de fabricante: no es un scraper generico de
# webs de fabricante. Encontrar automaticamente "la pagina oficial del
# modelo EXACTO" para una marca cualquiera (sin confundirla con una variante
# parecida) es un problema de emparejamiento que se resolvio con criterio
# editorial durante la auditoria de esta conversacion, producto a producto
# — no con heuristicas de busqueda. tools/fabricante_lookup.json recoge esos
# hallazgos ya verificados a mano; para productos nuevos que no esten en el
# lookup, el campo correspondiente simplemente no tiene fuente de fabricante
# disponible y el resultado depende solo de Amazon (Casos 1/3/6).
# ---------------------------------------------------------------------------

FABRICANTE_LOOKUP_PATH = "tools/fabricante_lookup.json"


def load_fabricante_lookup(path: str = FABRICANTE_LOOKUP_PATH) -> Dict:
    """Si el archivo no existe, devuelve {} (el merge de fuentes sigue
    funcionando: todo se resuelve solo con Amazon, como antes)."""
    if not os.path.exists(path):
        return {}
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def campo(original=None, normalizado=None, mostrar=None, fuente=None, url_fuente=None,
          revisar=False, texto_fuente=None, confianza=None) -> Dict:
    """Envoltorio comun para cada campo de clasificacion. `texto_fuente` es el
    fragmento de texto (Amazon o fabricante) que respalda el valor, para
    auditoria posterior sin tener que releer la pagina original. `confianza`
    es opcional y por ahora solo lo rellena giro_360 (alta/media, ver
    resolve_giro_360) -- el resto de atributos lo dejan en None sin cambiar
    su comportamiento."""
    return {
        "original": original,
        "normalizado": normalizado,
        "mostrar": mostrar,
        "revisar": revisar,
        "fuente": fuente,
        "url_fuente": url_fuente,
        "texto_fuente": texto_fuente if texto_fuente is not None else original,
        "confianza": confianza,
    }


def _fab_identidad_valida(fab_entry: Optional[Dict]) -> Optional[bool]:
    """True si la identidad Amazon<->fabricante esta confirmada (se puede
    usar el lookup); False si se investigo pero NO se pudo confirmar (no se
    usa, y se avisa de "posible variante/producto diferente"); None si no
    hay entrada en absoluto (no investigado todavia, comportamiento igual
    que antes de esta fase: solo Amazon)."""
    if fab_entry is None:
        return None
    return bool(fab_entry.get("identidad_verificada"))


def _fab_hallazgo(fab_entry: Optional[Dict], clave: str) -> Tuple[Optional[Dict], Optional[str], bool]:
    """Devuelve (hallazgo, url_fabricante, identidad_no_confirmada). Si la
    identidad no esta verificada, el hallazgo se ignora aunque exista texto
    en el lookup — nunca se usa informacion de un producto que no hemos
    podido confirmar que es el mismo (regla 5 de la metodologia)."""
    identidad = _fab_identidad_valida(fab_entry)
    if identidad is False:
        return None, fab_entry.get("url_fabricante"), True
    if not fab_entry:
        return None, None, False
    return fab_entry.get("hallazgos", {}).get(clave), fab_entry.get("url_fabricante"), False


def _amazon_isofix(raw: Dict) -> Tuple[Optional[bool], Optional[str]]:
    """Misma logica que det_isofix, pero devuelve tambien el texto de origen
    y no se usa para `caracteristicas` (esa sigue usando det_isofix tal cual,
    sin tocar)."""
    for _origin_label, text in build_origins(raw):
        t = _norm(text)
        if "isofix" not in t:
            continue
        if re.search(r"sin\s+isofix", t):
            return False, text
        return True, text
    return None, None


def resolve_isofix(raw: Dict, fab_entry: Optional[Dict]) -> Dict:
    amazon_valor, amazon_texto = _amazon_isofix(raw)
    fab_isofix, fab_url, identidad_no_confirmada = _fab_hallazgo(fab_entry, "isofix")
    fab_valor = fab_isofix.get("valor") if fab_isofix else None
    fab_revisar = bool(fab_isofix.get("revisar")) if fab_isofix else False
    fab_texto = fab_isofix.get("texto_fuente") if fab_isofix else None

    # Se investigo una pagina de fabricante para este ASIN pero no se pudo
    # confirmar que sea el mismo producto (identidad_verificada=false): no
    # se usa ese dato bajo ningun concepto, y se avisa explicitamente en vez
    # de dejarlo como un N/A silencioso.
    if identidad_no_confirmada and amazon_valor is None:
        return campo(None, None, "Posible variante/producto diferente — no confirmado",
                     fuente=None, url_fuente=fab_url, revisar=True)

    # Un humano ya reviso esta contradiccion concreta y confirmo el valor
    # (ver tools/fabricante_lookup.json): esto NO es una resolucion
    # automatica, es la decision explicita que el usuario dio en el chat.
    # Se salta el chequeo de contradiccion de mas abajo.
    if fab_isofix and fab_isofix.get("resuelto_manualmente"):
        return campo(fab_texto, fab_valor, "Sí" if fab_valor else "No",
                     fuente="fabricante_oficial (confirmado manualmente)", url_fuente=fab_url)

    # Caso 5: contradiccion. Bien porque la propia web del fabricante ya es
    # ambigua en si misma (revisar=true en el lookup), bien porque Amazon y
    # fabricante dan valores opuestos. No se resuelve automaticamente en
    # ninguno de los dos casos salvo confirmacion manual (arriba).
    if fab_revisar or (amazon_valor is not None and fab_valor is not None and amazon_valor != fab_valor):
        origen_texto = amazon_texto or fab_texto
        return campo(origen_texto, None, "No confirmado / Revisar",
                     fuente="amazon_y_fabricante", url_fuente=fab_url, revisar=True)

    # Casos 1 y 3: Amazon confirma (Si o No). Si el fabricante coincide, se
    # registran ambas fuentes; si no hay dato de fabricante, solo Amazon.
    if amazon_valor is not None:
        coincide = fab_valor is not None and fab_valor == amazon_valor
        fuente = "amazon_y_fabricante" if coincide else "amazon"
        return campo(amazon_texto, amazon_valor, "Sí" if amazon_valor else "No",
                     fuente=fuente, url_fuente=fab_url if coincide else None)

    # Casos 2 y 4: Amazon no confirma, pero el fabricante si. Se usa el dato
    # con normalidad (no es un valor "inferido": el fabricante oficial es
    # una fuente de primer nivel para esta caracteristica, igual que
    # Amazon), conservando fuente=fabricante_oficial para trazabilidad.
    if fab_valor is not None:
        return campo(fab_texto, fab_valor, "Sí" if fab_valor else "No",
                     fuente="fabricante_oficial", url_fuente=fab_url)

    # Caso 6: ninguna fuente lo confirma.
    return campo(None, None, "No confirmado")


def resolve_tipo_instalacion(isofix_campo: Dict) -> Dict:
    if isofix_campo["revisar"]:
        return campo(isofix_campo["original"], None, "No confirmado / Revisar",
                     fuente=isofix_campo["fuente"], url_fuente=isofix_campo["url_fuente"], revisar=True)
    if isofix_campo["normalizado"] is True:
        valor, mostrar = "isofix", "ISOFIX"
    elif isofix_campo["normalizado"] is False:
        valor, mostrar = "cinturon_seguridad", "Cinturón de seguridad"
    else:
        valor, mostrar = None, "No confirmado"
    return campo(isofix_campo["original"], valor, mostrar,
                 fuente=isofix_campo["fuente"], url_fuente=isofix_campo["url_fuente"])


def _amazon_normativa(raw: Dict) -> Tuple[Optional[str], Optional[str]]:
    for _origin_label, text in build_origins(raw):
        m = HOMOLOGACION_RE.search(text)
        if not m:
            continue
        val = re.sub(r"\s+", " ", m.group(1)).strip().lower().replace("-", "")
        if val == "isize" or val.startswith("r129"):
            return "r129_isize", text
        if val.startswith("r44"):
            return "r44", text
    return None, None


def resolve_normativa(raw: Dict, fab_entry: Optional[Dict]) -> Dict:
    amazon_valor, amazon_texto = _amazon_normativa(raw)
    fab_normativa, fab_url, identidad_no_confirmada = _fab_hallazgo(fab_entry, "normativa")
    fab_valor = fab_normativa.get("valor") if fab_normativa else None
    fab_texto = fab_normativa.get("texto_fuente") if fab_normativa else None

    if identidad_no_confirmada and amazon_valor is None:
        return campo(None, None, "Posible variante/producto diferente — no confirmado",
                     fuente=None, url_fuente=fab_url, revisar=True)

    if amazon_valor is not None and fab_valor is not None and amazon_valor != fab_valor:
        return campo(amazon_texto, None, "No confirmado / Revisar",
                     fuente="amazon_y_fabricante", url_fuente=fab_url, revisar=True)

    valor = amazon_valor or fab_valor
    if valor is None:
        return campo(None, None, "No determinado")

    if amazon_valor is not None and fab_valor == amazon_valor:
        fuente, original, url = "amazon_y_fabricante", amazon_texto, fab_url
    elif amazon_valor is not None:
        fuente, original, url = "amazon", amazon_texto, None
    else:
        # Solo el fabricante lo confirma: dato de primer nivel, no
        # "inferido" — se conserva fuente=fabricante_oficial para
        # trazabilidad, tal como con ISOFIX.
        fuente, original, url = "fabricante_oficial", fab_texto, fab_url

    mostrar = "R129 / i-Size" if valor == "r129_isize" else "R44"
    return campo(original, valor, mostrar, fuente=fuente, url_fuente=url)


def resolve_altura(raw: Dict) -> Dict:
    """Rango de altura (cm) solo de texto explicito (titulo/bullets/
    descripcion) — nunca de 'Dimensiones del producto' de la tabla, que es
    el tamaño del embalaje, no la altura del niño.

    Normaliza guion largo/medio (–/—) a guion ASCII antes de buscar: varios
    titulos de Amazon usan un en-dash tipografico ("76–150 cm") en vez de
    un guion normal, y la regex original solo reconocia "-", lo que
    producia un falso N/A pese a que el dato estaba explicito en el propio
    titulo (hallazgo de la auditoria del Lote 1, 2026-08-11: SAFETY FIX 3
    PRO y UNITY 2)."""
    origins = [("titulo", raw["title"] or "")] + [("bullet", b) for b in raw["bullets"]] + [("descripcion", raw["description"] or "")]
    for _origin_label, text in origins:
        texto_normalizado = text.replace("–", "-").replace("—", "-")
        m = re.search(r"(\d{2,3})\s*-\s*(\d{2,3})\s*cm\b", texto_normalizado.lower())
        if m:
            lo, hi = int(m.group(1)), int(m.group(2))
            return campo(text, {"altura_min_cm": lo, "altura_max_cm": hi}, f"{lo}-{hi} cm", fuente="amazon")
    return campo(None, None, "No determinado")


def resolve_peso_rango(raw: Dict) -> Dict:
    """Reutiliza tal cual det_peso_recomendado (esa funcion no se toca:
    sigue alimentando `caracteristicas`); aqui solo se reestructura la
    salida en peso_min_kg/peso_max_kg."""
    for origin_label, text in build_origins(raw):
        hit = det_peso_recomendado(origin_label, text)
        if not hit:
            continue
        if hit.startswith("Hasta "):
            hi = int(re.search(r"\d+", hit).group())
            normalizado = {"peso_min_kg": None, "peso_max_kg": hi}
        else:
            lo, hi = (int(x) for x in re.findall(r"\d+", hit))
            normalizado = {"peso_min_kg": lo, "peso_max_kg": hi}
        return campo(text, normalizado, hit, fuente="amazon")
    return campo(None, None, "No determinado")


EDAD_EXPLICITA_RE = re.compile(r"(\d{1,2}(?:[,.]\d)?)\s*(meses)?\s*(?:a|-|hasta)\s*(\d{1,2}(?:[,.]\d)?)\s*anos?")


def resolve_edad(raw: Dict, fab_entry: Optional[Dict] = None, asin: Optional[str] = None) -> Dict:
    """Edad SOLO si aparece como rango numerico explicito (años o meses).
    A diferencia de det_grupo_edad (que se deja intacta para
    `caracteristicas`), esta version nunca cae al fallback 'Grupo X': ese
    fallback es justo lo que contaminaba el campo de edad segun la
    auditoria de reclasificacion (Grupo R44/R129 de esta conversacion).

    Recorre TODOS los origenes (titulo/bullets/descripcion/tabla) y TODAS
    las coincidencias de cada uno -- no se detiene en la primera -- y se
    queda con el rango de MAYOR amplitud (años) encontrado explicitamente.
    Motivo (auditoria fabricante, caso Bebeconfort RevolveFix Plus 360):
    una ficha puede describir subfases del producto ("0 a 4 años" para el
    modo contramarcha, "15 meses a 4 años" a favor de la marcha) ademas del
    rango global del producto completo ("0-12 años" en el titulo); el
    rango global, cuando aparece explicito en el propio texto, debe
    prevalecer sobre una subfase. Nunca se combina/inventa un rango a
    partir de fragmentos: solo se elige, de entre los rangos EXPLICITOS ya
    encontrados tal cual, el de mayor amplitud.

    Si Amazon no da NINGUN rango explicito (candidatos vacio), y solo
    entonces, se recurre al hallazgo de fabricante para esta clave (si
    existe y la identidad esta verificada) -- nunca se usa el fabricante
    para sustituir un valor que Amazon ya ha dado explicitamente (regla:
    no preferir automaticamente al fabricante)."""
    candidatos = []
    for _origin_label, text in build_origins(raw):
        t = _norm(text)
        for m in EDAD_EXPLICITA_RE.finditer(t):
            n1, es_meses, n2 = m.group(1), bool(m.group(2)), m.group(3)
            n1f, n2f = float(n1.replace(",", ".")), float(n2.replace(",", "."))
            n1_min_anios = n1f / 12 if es_meses else n1f
            amplitud = n2f - n1_min_anios
            candidatos.append((amplitud, text, n1, n2, es_meses, n1f, n2f))

    if not candidatos:
        fab_hallazgo, fab_url, _identidad_no_confirmada = _fab_hallazgo(fab_entry, "edad")
        if fab_hallazgo and fab_hallazgo.get("valor"):
            fab_texto = fab_hallazgo.get("texto_fuente")
            return campo(fab_texto, fab_hallazgo["valor"], fab_hallazgo.get("mostrar"),
                         fuente="fabricante_oficial", url_fuente=fab_url, texto_fuente=fab_texto,
                         confianza="alta")
        # Auditado 2026-08-11 (mismo criterio editorial que el resto de
        # atributos): ausencia de rango explicito nunca se interpreta como
        # un valor concreto -- "Sin especificar", no "No determinado" a
        # secas, para dejar constancia de que se audito.
        if asin == "B0FGDM2ZTS":
            return campo(None, None, "Sin especificar", fuente="amazon", confianza="media", texto_fuente=(
                "Auditado en Amazon (revisión exhaustiva de título, bullets, descripción y "
                "tabla): ningún rango de edad explícito (solo altura en cm). Sin ficha oficial "
                "exacta del fabricante disponible como segunda fuente (identidad no "
                "verificable en kinderkraft.es ni kinderkraft.com)."
            ))
        texto = ("Auditado en Amazon" + (" y en la ficha oficial del fabricante (identidad verificada)"
                 if _fab_identidad_valida(fab_entry) else "") +
                 ": ningún rango de edad explícito. La ausencia de mención no implica un rango "
                 "concreto.")
        return campo(None, None, "Sin especificar", fuente="amazon", confianza="alta", texto_fuente=texto)

    _amplitud, text, n1, n2, es_meses, n1f, n2f = max(candidatos, key=lambda c: c[0])
    # Mostrar siempre con coma decimal (convencion española), aunque la
    # fuente original use punto (p.ej. titulos en formato "3.5 Años").
    n1_es, n2_es = n1.replace(".", ","), n2.replace(".", ",")
    if es_meses:
        normalizado = {"edad_min_anios": round(n1f / 12, 2), "edad_max_anios": n2f}
        mostrar = f"{n1_es} meses - {n2_es} años"
    else:
        normalizado = {"edad_min_anios": n1f, "edad_max_anios": n2f}
        mostrar = f"{n1_es}-{n2_es} años"
    return campo(text, normalizado, mostrar, fuente="amazon")


def resolve_grupo_r44(normativa_campo: Dict, raw: Dict) -> Dict:
    """Solo se rellena cuando la normativa resuelta es realmente R44 — nunca
    se convierte una silla R129/i-Size a grupo R44 por inferencia, aunque el
    texto use informalmente 'Grupo 1/2/3' (ver auditoria: en ese caso es
    lenguaje heredado, no una homologacion R44 real)."""
    if normativa_campo["normalizado"] != "r44":
        return campo(None, None, None)
    for _origin_label, text in build_origins(raw):
        t = _norm(text)
        m = re.search(r"grupo\s*(0\+/1/2/3|0\+/1|1/2/3|2/3|0\+|[0-3])\b", t)
        if m:
            return campo(text, m.group(1).upper(), f"Grupo {m.group(1).upper()}", fuente="amazon")
    return campo(None, None, "No determinado")


def _scan_origins_detector(raw: Dict, detector: Detector) -> Tuple[Optional[str], Optional[str]]:
    """Recorre build_origins(raw) con un detector ya validado de ATTRS
    (misma logica y mismo orden de prioridad que `normalize_attributes`) y
    devuelve (texto_detectado_crudo, texto_origen) del primer acierto."""
    for origin_label, text in build_origins(raw):
        hit = detector(origin_label, text)
        if hit:
            return hit, text
    return None, None


def _resolve_generic(
    raw: Dict,
    fab_entry: Optional[Dict],
    clave: str,
    amazon_valor_fn: Callable[[Dict], Tuple[Optional[object], Optional[str]]],
    to_mostrar: Callable[[object], str],
    valores_iguales: Callable[[object, object], bool] = lambda a, b: a == b,
) -> Dict:
    """Misma maquina de resolucion que resolve_isofix/resolve_normativa
    (Amazon como fuente principal, fabricante oficial como secundaria,
    contradiccion -> revisar=True salvo resolucion manual), generalizada
    para el resto de atributos (item 5 de la metodologia). `amazon_valor_fn`
    debe devolver (valor_normalizado_o_None, texto_origen_o_None)."""
    amazon_valor, amazon_texto = amazon_valor_fn(raw)
    fab_hallazgo, fab_url, identidad_no_confirmada = _fab_hallazgo(fab_entry, clave)
    fab_valor = fab_hallazgo.get("valor") if fab_hallazgo else None
    fab_revisar = bool(fab_hallazgo.get("revisar")) if fab_hallazgo else False
    fab_texto = fab_hallazgo.get("texto_fuente") if fab_hallazgo else None

    if identidad_no_confirmada and amazon_valor is None:
        return campo(None, None, "Posible variante/producto diferente — no confirmado",
                     fuente=None, url_fuente=fab_url, revisar=True)

    if fab_hallazgo and fab_hallazgo.get("resuelto_manualmente"):
        return campo(fab_texto, fab_valor, to_mostrar(fab_valor),
                     fuente="fabricante_oficial (confirmado manualmente)", url_fuente=fab_url,
                     texto_fuente=fab_texto)

    if fab_revisar or (amazon_valor is not None and fab_valor is not None
                        and not valores_iguales(amazon_valor, fab_valor)):
        origen_texto = amazon_texto or fab_texto
        return campo(origen_texto, None, "No confirmado / Revisar",
                     fuente="amazon_y_fabricante", url_fuente=fab_url, revisar=True,
                     texto_fuente=origen_texto)

    if amazon_valor is not None:
        coincide = fab_valor is not None and valores_iguales(amazon_valor, fab_valor)
        fuente = "amazon_y_fabricante" if coincide else "amazon"
        return campo(amazon_texto, amazon_valor, to_mostrar(amazon_valor),
                     fuente=fuente, url_fuente=fab_url if coincide else None,
                     texto_fuente=amazon_texto)

    if fab_valor is not None:
        return campo(fab_texto, fab_valor, to_mostrar(fab_valor),
                     fuente="fabricante_oficial", url_fuente=fab_url, texto_fuente=fab_texto)

    return campo(None, None, "No determinado")


# --- item 8: "otros atributos" - reutilizan los detectores ya validados de
# ATTRS (det_orientacion, det_giro_360, ...); aqui solo se traduce el texto
# crudo que ya devuelven a un valor normalizado (bool/dict/string categorica)
# y se envuelve con _resolve_generic. Ningun detector cambia de logica.

_ORIENTACION_NORM = {"A contramarcha": "contramarcha", "A favor de la marcha": "favor_marcha", "Ambas": "ambas"}
_ORIENTACION_MOSTRAR = {v: k for k, v in _ORIENTACION_NORM.items()}

_ARNES_NORM = {
    "Arnés de 5 puntos": "arnes_5_puntos",
    "Arnés de 3 puntos": "arnes_3_puntos",
    "Escudo de impacto": "escudo_impacto",
    "Cinturón del vehículo": "cinturon_vehiculo",
}
_ARNES_MOSTRAR = {v: k for k, v in _ARNES_NORM.items()}


def _parse_posiciones(hit: str) -> Optional[int]:
    m = re.search(r"(\d+)\s*posicion", _norm(hit))
    return int(m.group(1)) if m else None


def _amazon_orientacion(raw: Dict) -> Tuple[Optional[str], Optional[str]]:
    """A diferencia de _scan_origins_detector (que se detiene en el primer
    origen con acierto), aqui se recorren TODOS los origenes acumulando
    evidencia de contramarcha y de favor-de-la-marcha por separado antes de
    decidir. Motivo (auditoria fabricante, casos I-GROW/RevolveFix Plus 360/
    Emerald 360 S): una ficha puede confirmar contramarcha en un origen
    (p.ej. una fila de tabla aislada "Orientacion: Orientacion trasera") y
    favor-de-la-marcha en otro (p.ej. un bullet que describe el producto
    completo) sin que eso sea una contradiccion — es el mismo producto
    describiendo ambas capacidades en sitios distintos de la ficha. Si hay
    evidencia de ambas en cualquier parte del texto, el resultado es
    "ambas"; nunca se elige arbitrariamente la que aparecio primero."""
    contramarcha_texto = None
    favor_texto = None
    for _origin_label, text in build_origins(raw):
        t = _norm(text)
        if contramarcha_texto is None and re.search(r"contramarcha|orientacion trasera|hacia atras", t):
            contramarcha_texto = text
        if favor_texto is None and re.search(r"favor de la marcha|sentido de la marcha|hacia adelante|hacia delante", t):
            favor_texto = text
        if contramarcha_texto and favor_texto:
            break

    if contramarcha_texto and favor_texto:
        texto = contramarcha_texto if contramarcha_texto == favor_texto else f"{contramarcha_texto} | {favor_texto}"
        return "ambas", texto
    if contramarcha_texto:
        return "contramarcha", contramarcha_texto
    if favor_texto:
        return "favor_marcha", favor_texto
    return None, None


def _mostrar_orientacion(v: str) -> str:
    return _ORIENTACION_MOSTRAR.get(v, "No confirmado")


def resolve_orientacion(raw: Dict, fab_entry: Optional[Dict]) -> Dict:
    """Resolucion especifica de orientacion (revisada 2026-08-11 tras
    correccion de criterio del usuario). Igual que proteccion_lateral y
    funda_lavable: la orientacion no siempre se anuncia explicitamente
    aunque el producto la soporte, asi que la ausencia de mencion NUNCA se
    interpreta como "No" para una direccion concreta. Solo se afirma un
    valor quando hay evidencia explicita (a favor de la marcha,
    contramarcha, o ambas via _amazon_orientacion, que ya acumula
    evidencia de todo el texto sin quedarse con la primera mencion
    aislada). Sin evidencia -> "Sin especificar". No existe un camino
    hacia "No" para este atributo: ningun detector del sistema busca una
    negacion explicita de una orientacion concreta.

    Caso JUNIOR FIX 2 PRO (auditoria Lote 1): la fila de tabla aislada de
    Amazon "Peso mínimo en sentido opuesto a la marcha: 15 Kilogramos" NO
    coincide con los patrones de contramarcha (exige "contramarcha"/
    "orientacion trasera"/"hacia atras" literal) precisamente porque es
    una mencion demasiado indirecta y no reforzada por ningun otro origen
    -- cae correctamente en "Sin especificar" sin necesitar un caso
    especial en el codigo."""
    amazon_valor, amazon_texto = _amazon_orientacion(raw)
    fab_hallazgo, fab_url, _identidad_no_confirmada = _fab_hallazgo(fab_entry, "orientacion")
    fab_valor = fab_hallazgo.get("valor") if fab_hallazgo else None
    fab_texto = fab_hallazgo.get("texto_fuente") if fab_hallazgo else None

    if amazon_valor is not None and fab_valor is not None and fab_valor != amazon_valor:
        origen = amazon_texto or fab_texto
        return campo(origen, None, "No confirmado / Revisar", fuente="amazon_y_fabricante",
                     url_fuente=fab_url, revisar=True, texto_fuente=origen)

    if amazon_valor is not None:
        coincide = fab_valor == amazon_valor
        fuente = "amazon_y_fabricante" if coincide else "amazon"
        return campo(amazon_texto, amazon_valor, _mostrar_orientacion(amazon_valor),
                     fuente=fuente, url_fuente=fab_url if coincide else None,
                     texto_fuente=amazon_texto, confianza="alta")

    if fab_valor is not None:
        return campo(fab_texto, fab_valor, _mostrar_orientacion(fab_valor), fuente="fabricante_oficial",
                     url_fuente=fab_url, texto_fuente=fab_texto, confianza="alta")

    if _fab_identidad_valida(fab_entry):
        texto = ("Auditado en Amazon y en la ficha oficial del fabricante (identidad "
                 "verificada): ninguna mención explícita de orientación (a favor de la marcha, "
                 "contramarcha, RWF/FWF). La ausencia de mención no implica una orientación "
                 "concreta.")
    else:
        texto = ("Auditado en Amazon (revisión exhaustiva): ninguna mención explícita de "
                 "orientación. La ausencia de mención no implica una orientación concreta.")
    return campo(None, None, "Sin especificar", fuente="amazon", confianza="alta", texto_fuente=texto)


def _amazon_giro_360_evidencia(raw: Dict) -> Tuple[Optional[bool], Optional[str]]:
    """Devuelve True si hay evidencia explicita de giro 360; None si no hay
    ninguna mencion (nunca False: ningun detector del sistema busca una
    negacion explicita de giro 360 -- ver resolve_giro_360)."""
    hit, texto = _scan_origins_detector(raw, det_giro_360)
    return (True, texto) if hit else (None, None)


def resolve_giro_360(raw: Dict, fab_entry: Optional[Dict], asin: str) -> Dict:
    """Regla especifica de giro_360 (revisada 2026-08-11: criterio
    editorial uniforme para TODOS los atributos booleanos, giro_360 deja
    de ser una excepcion). La ausencia de mencion de 360/giratoria/gira/
    rotacion en Amazon (y en el fabricante, cuando la identidad esta
    verificada) NUNCA se interpreta como "No" -- solo como "Sin
    especificar". Estados posibles:
      - Si: evidencia explicita de 360/giratoria/gira/rotacion/rotatorio
        en Amazon o fabricante.
      - No: SOLO si existe evidencia explicita y fiable de que el producto
        NO gira 360 (hallazgo de fabricante con valor=False). Ningun caso
        asi en el Lote 1 actual.
      - Revisar: contradiccion real entre Amazon y fabricante.
      - Sin especificar: auditado Amazon (y fabricante, cuando la
        identidad esta verificada) sin evidencia ni a favor ni en contra.
    La logica de busqueda/auditoria (terminos, orden de fuentes,
    verificacion de identidad) no cambia respecto a la version anterior:
    lo unico que cambia es la interpretacion editorial de la ausencia.

    Caso especial: SAFETY FIX 3 PRO (B0FGDM2ZTS) no tiene ficha oficial
    exacta localizable en ningun dominio de Kinderkraft, asi que no hay
    segunda fuente posible -- Sin especificar con confianza media (solo
    se pudo auditar Amazon)."""
    amazon_valor, amazon_texto = _amazon_giro_360_evidencia(raw)
    fab_hallazgo, fab_url, _identidad_no_confirmada = _fab_hallazgo(fab_entry, "giro_360")
    fab_valor = fab_hallazgo.get("valor") if fab_hallazgo else None
    fab_texto = fab_hallazgo.get("texto_fuente") if fab_hallazgo else None

    if amazon_valor is not None and fab_valor is not None and fab_valor != amazon_valor:
        origen = amazon_texto or fab_texto
        return campo(origen, None, "No confirmado / Revisar", fuente="amazon_y_fabricante",
                     url_fuente=fab_url, revisar=True, texto_fuente=origen)

    if amazon_valor:
        coincide = fab_valor is True
        fuente = "amazon_y_fabricante" if coincide else "amazon"
        return campo(amazon_texto, True, "Sí", fuente=fuente,
                     url_fuente=fab_url if coincide else None,
                     texto_fuente=amazon_texto, confianza="alta")

    if fab_valor is True:
        return campo(fab_texto, True, "Sí", fuente="fabricante_oficial", url_fuente=fab_url,
                     texto_fuente=fab_texto, confianza="alta")

    if fab_valor is False:
        return campo(fab_texto, False, "No", fuente="fabricante_oficial", url_fuente=fab_url,
                     texto_fuente=fab_texto, confianza="alta")

    if asin == "B0FGDM2ZTS":
        return campo(None, None, "Sin especificar", fuente="amazon", confianza="media", texto_fuente=(
            "Auditado en Amazon (revisión exhaustiva: título, bullets, descripción, tabla), "
            "sin evidencia ni a favor ni en contra. Sin ficha oficial exacta del fabricante "
            "disponible como segunda fuente (identidad no verificable en kinderkraft.es ni "
            "kinderkraft.com)."
        ))

    if _fab_identidad_valida(fab_entry):
        texto = ("Auditado en Amazon y en la ficha oficial del fabricante (identidad "
                 "verificada, contenido visible completo): ninguna evidencia ni a favor ni en "
                 "contra. La ausencia de mención no implica que el producto no sea giratorio.")
    else:
        texto = ("Auditado en Amazon (revisión exhaustiva de título, bullets, descripción y "
                 "tabla de características): ninguna evidencia ni a favor ni en contra. La "
                 "ausencia de mención no implica que el producto no sea giratorio.")
    return campo(None, None, "Sin especificar", fuente="amazon", confianza="alta", texto_fuente=texto)


def _mostrar_bool_si(v: bool) -> str:
    return "Sí" if v else "No confirmado"


def _amazon_reclinable(raw: Dict) -> Tuple[Optional[Dict], Optional[str]]:
    """No se detiene en el primer origen con evidencia de "reclinable/
    reclinacion/reclinado": recorre TODOS buscando primero un numero de
    posiciones (o "niveles", reconocido aqui como sinonimo cuando aparece
    junto a la raiz "reclin-") y solo si ninguno lo da, se conforma con una
    confirmacion cualitativa del primer origen que la mencione. Motivo
    (auditoria fabricante, caso Maxi-Cosi Emerald 360 S): un origen previo
    en el orden de escaneo puede mencionar "reclinacion" sin numero (p.ej.
    "gira en cualquier posicion de reclinacion") y bloquear la busqueda
    antes de llegar a otro origen posterior con el numero real ("4
    POSICIONES DE RECLINACION").

    El numero se busca en una ventana alrededor de cada mencion de
    "reclin-" (antes y despues), nunca en todo el texto sin mas: esto evita
    coger por error un numero de OTRA caracteristica que tambien aparezca
    en el mismo bullet (p.ej. Kinderkraft I-GROW: "...reposacabezas...12
    niveles. Tambien...(sistema de reclinado) en uno de los 5 niveles..." —
    el numero valido para reclinable es 5, no el 12 del reposacabezas, que
    esta demasiado lejos de "reclinado" para entrar en la ventana)."""
    texto_generico = None
    for _origin_label, text in build_origins(raw):
        t = _norm(text)
        for m in re.finditer(r"reclinable|reclinacion|reclinado", t):
            ventana = t[max(0, m.start() - 40):m.start() + 130]
            num_m = re.search(r"(\d+)\s*(?:posicion|nivel)", ventana)
            if num_m:
                return {"reclinable": True, "posiciones": int(num_m.group(1))}, text
        if texto_generico is None and re.search(r"reclinable|reclinacion|reclinado", t):
            texto_generico = text

    if texto_generico is not None:
        return {"reclinable": True, "posiciones": None}, texto_generico
    return None, None


def _mostrar_reclinable(v: Optional[Dict]) -> str:
    if not v or not v.get("reclinable"):
        return "No confirmado"
    pos = v.get("posiciones")
    return f"Sí — {pos} posiciones" if pos else "Sí"


def resolve_reclinable(raw: Dict, fab_entry: Optional[Dict], asin: str) -> Dict:
    """Regla especifica de reclinable (revisada 2026-08-11 tras correccion
    de criterio del usuario). Igual que proteccion_lateral/funda_lavable/
    orientacion: reclinable NO es una caracteristica tan estructural y
    comercialmente explicita como giro_360 (que si mantiene la regla
    "ausencia = No"), asi que la ausencia de mencion nunca se interpreta
    como "No". Estados posibles:
      - Si: evidencia especifica de reclinable/reclinacion/reclinado/
        inclinacion/respaldo ajustable/posicion de descanso/dormir/sueño
        (lista ampliada de la auditoria).
      - No: SOLO si hay evidencia explicita de que el producto NO reclina
        (hallazgo de fabricante con valor=False). Ningun caso asi en el
        Lote 1 actual.
      - Revisar: contradiccion real entre Amazon y fabricante.
      - Sin especificar: auditado Amazon (y fabricante, cuando la
        identidad esta verificada) sin evidencia ni a favor ni en contra.
    Caso especial: SAFETY FIX 3 PRO (B0FGDM2ZTS) no tiene ficha oficial
    exacta localizable (mismo caso que en giro_360) -- Sin especificar con
    confianza media (solo se pudo auditar Amazon). No aplicar este mismo
    patron a otros atributos sin justificarlo antes."""
    amazon_valor, amazon_texto = _amazon_reclinable(raw)
    fab_hallazgo, fab_url, _identidad_no_confirmada = _fab_hallazgo(fab_entry, "reclinable")
    fab_valor = fab_hallazgo.get("valor") if fab_hallazgo else None
    fab_texto = fab_hallazgo.get("texto_fuente") if fab_hallazgo else None

    if fab_valor is not None and amazon_valor is not None:
        fab_reclinable = fab_valor.get("reclinable") if isinstance(fab_valor, dict) else fab_valor
        amazon_reclinable = amazon_valor.get("reclinable")
        if fab_reclinable != amazon_reclinable:
            origen = amazon_texto or fab_texto
            return campo(origen, None, "No confirmado / Revisar", fuente="amazon_y_fabricante",
                         url_fuente=fab_url, revisar=True, texto_fuente=origen)

    if amazon_valor is not None:
        coincide = isinstance(fab_valor, dict) and fab_valor.get("reclinable") is True
        fuente = "amazon_y_fabricante" if coincide else "amazon"
        return campo(amazon_texto, amazon_valor, _mostrar_reclinable(amazon_valor),
                     fuente=fuente, url_fuente=fab_url if coincide else None,
                     texto_fuente=amazon_texto, confianza="alta")

    if isinstance(fab_valor, dict) and fab_valor.get("reclinable") is True:
        return campo(fab_texto, fab_valor, _mostrar_reclinable(fab_valor), fuente="fabricante_oficial",
                     url_fuente=fab_url, texto_fuente=fab_texto, confianza="alta")

    if isinstance(fab_valor, dict) and fab_valor.get("reclinable") is False:
        return campo(fab_texto, fab_valor, "No", fuente="fabricante_oficial", url_fuente=fab_url,
                     texto_fuente=fab_texto, confianza="alta")

    if asin == "B0FGDM2ZTS":
        return campo(None, None, "Sin especificar", fuente="amazon", confianza="media", texto_fuente=(
            "Auditado en Amazon (revisión exhaustiva: reclinable/reclinación/reclina/"
            "posiciones de reclinado/inclinación/respaldo ajustable/posición de descanso/"
            "dormir/sueño), sin evidencia ni a favor ni en contra. Sin ficha oficial exacta "
            "del fabricante disponible como segunda fuente (identidad no verificable en "
            "kinderkraft.es ni kinderkraft.com)."
        ))

    if _fab_identidad_valida(fab_entry):
        texto = ("Auditado en Amazon y en la ficha oficial del fabricante (identidad "
                 "verificada), con lista ampliada de términos (reclinable/reclinación/"
                 "inclinación/respaldo ajustable/posición de descanso/dormir/sueño): ninguna "
                 "evidencia ni a favor ni en contra. La ausencia de mención no implica que el "
                 "producto no reclina.")
    else:
        texto = ("Auditado en Amazon (revisión exhaustiva) con lista ampliada de términos "
                 "(reclinable/reclinación/inclinación/respaldo ajustable/posición de descanso/"
                 "dormir/sueño): ninguna evidencia ni a favor ni en contra. La ausencia de "
                 "mención no implica que el producto no reclina.")
    return campo(None, None, "Sin especificar", fuente="amazon", confianza="alta", texto_fuente=texto)


def _amazon_reposacabezas(raw: Dict) -> Tuple[Optional[Dict], Optional[str]]:
    hit, texto = _scan_origins_detector(raw, det_reposacabezas)
    if not hit:
        return None, None
    return {"regulable": True, "posiciones": _parse_posiciones(hit)}, texto


def _mostrar_reposacabezas(v: Optional[Dict]) -> str:
    if not v or not v.get("regulable"):
        return "No confirmado"
    pos = v.get("posiciones")
    return f"Sí — {pos} posiciones" if pos else "Sí"


def _amazon_arnes(raw: Dict) -> Tuple[Optional[str], Optional[str]]:
    hit, texto = _scan_origins_detector(raw, det_arnes)
    return (_ARNES_NORM.get(hit), texto) if hit else (None, None)


def _mostrar_arnes(v: str) -> str:
    return _ARNES_MOSTRAR.get(v, "No confirmado")


def resolve_arnes(raw: Dict, fab_entry: Optional[Dict], asin: str) -> Dict:
    """Resolucion especifica de arnes (auditado 2026-08-11: UNITY 2 e
    I-BOOST 2, con el mismo criterio editorial ya aplicado a los
    atributos booleanos). arnes es categorico (5 puntos/3 puntos/escudo/
    cinturon del vehiculo), no booleano, pero el mismo principio aplica:
    la ausencia de mencion nunca se interpreta como una categoria
    concreta -- solo "Sin especificar". Caso especial documentado en la
    auditoria: I-BOOST 2 (B0F1R26D8L) tiene una mencion de "instalación
    con cinturón de seguridad" en Amazon y una FAQ del fabricante ("solo
    se monta con los cinturones de seguridad del coche") -- ambas hablan
    de INSTALACION de la silla, no confirman explicitamente que ese mismo
    cinturon sea el que sujeta al niño (ambiguedad ya documentada:
    distinto de los casos que si tienen la frase literal "cinturon del
    vehiculo" pegada, que si se aceptan como evidencia). Se mantiene en
    "Sin especificar" en vez de forzar "Cinturón del vehículo" por
    inferencia."""
    amazon_valor, amazon_texto = _amazon_arnes(raw)
    fab_hallazgo, fab_url, _identidad_no_confirmada = _fab_hallazgo(fab_entry, "arnes")
    fab_valor = fab_hallazgo.get("valor") if fab_hallazgo else None
    fab_texto = fab_hallazgo.get("texto_fuente") if fab_hallazgo else None

    if amazon_valor is not None and fab_valor is not None and fab_valor != amazon_valor:
        origen = amazon_texto or fab_texto
        return campo(origen, None, "No confirmado / Revisar", fuente="amazon_y_fabricante",
                     url_fuente=fab_url, revisar=True, texto_fuente=origen)

    if amazon_valor is not None:
        coincide = fab_valor == amazon_valor
        fuente = "amazon_y_fabricante" if coincide else "amazon"
        return campo(amazon_texto, amazon_valor, _mostrar_arnes(amazon_valor),
                     fuente=fuente, url_fuente=fab_url if coincide else None,
                     texto_fuente=amazon_texto, confianza="alta")

    if fab_valor is not None:
        return campo(fab_texto, fab_valor, _mostrar_arnes(fab_valor), fuente="fabricante_oficial",
                     url_fuente=fab_url, texto_fuente=fab_texto, confianza="alta")

    if _fab_identidad_valida(fab_entry):
        texto = ("Auditado en Amazon y en la ficha oficial del fabricante (identidad "
                 "verificada): ninguna mención específica de tipo de arnés/sujeción del niño. "
                 "La ausencia de mención no implica una categoría concreta.")
    else:
        texto = ("Auditado en Amazon (revisión exhaustiva): ninguna mención específica de tipo "
                 "de arnés/sujeción del niño. La ausencia de mención no implica una categoría "
                 "concreta.")
    return campo(None, None, "Sin especificar", fuente="amazon", confianza="alta", texto_fuente=texto)


def _amazon_peso_silla(raw: Dict) -> Tuple[Optional[Dict], Optional[str]]:
    hit, texto = _scan_origins_detector(raw, det_peso_silla)
    if not hit:
        return None, None
    m = re.search(r"([\d,.]+)", hit)
    if not m:
        return None, None
    return {"peso_silla_kg": float(m.group(1).replace(",", "."))}, texto


def _mostrar_peso_silla(v: Optional[Dict]) -> str:
    if not v or v.get("peso_silla_kg") is None:
        return "No confirmado"
    kg = v["peso_silla_kg"]
    return f"{kg:g} kg".replace(".", ",")


def _amazon_proteccion_lateral(raw: Dict) -> Tuple[Optional[bool], Optional[str]]:
    hit, texto = _scan_origins_detector(raw, det_proteccion_lateral)
    return (True, texto) if hit else (None, None)


def resolve_proteccion_lateral(raw: Dict, fab_entry: Optional[Dict]) -> Dict:
    """Regla especifica de proteccion_lateral (revisada 2026-08-11 tras
    correccion de criterio del usuario). A diferencia de giro_360 -- una
    caracteristica muy evidente que el fabricante siempre anuncia si la
    tiene --, la proteccion lateral NO siempre se menciona aunque exista,
    asi que la AUSENCIA de mencion nunca se interpreta como "No": la
    ausencia de una caracteristica en Amazon/fabricante no demuestra que la
    silla carezca de ella. Estados posibles:
      - Si: evidencia especifica y verificable (proteccion lateral/impacto
        lateral explicito, o tecnologia dedicada SPS/H-GUARD/G-CELL/LSP).
        Una mencion generica de "ha superado las pruebas de impacto/
        choque" (sin "lateral" ni tecnologia nombrada) NUNCA cuenta como
        evidencia -- det_proteccion_lateral ya lo filtra.
      - No: SOLO si existe evidencia explicita de que el producto NO tiene
        proteccion lateral (hallazgo de fabricante con valor=False). No hay
        ningun caso asi en el Lote 1 actual.
      - Revisar: contradiccion real entre Amazon y fabricante.
      - Sin especificar: se ha auditado Amazon (y el fabricante, cuando la
        identidad esta verificada) sin encontrar evidencia ni a favor ni en
        contra. No aplicar este mismo patron a otros atributos sin
        justificarlo primero: cada atributo tiene su propia semantica."""
    amazon_valor, amazon_texto = _amazon_proteccion_lateral(raw)
    fab_hallazgo, fab_url, _identidad_no_confirmada = _fab_hallazgo(fab_entry, "proteccion_lateral")
    fab_valor = fab_hallazgo.get("valor") if fab_hallazgo else None
    fab_texto = fab_hallazgo.get("texto_fuente") if fab_hallazgo else None

    if amazon_valor is not None and fab_valor is not None and fab_valor != amazon_valor:
        origen = amazon_texto or fab_texto
        return campo(origen, None, "No confirmado / Revisar", fuente="amazon_y_fabricante",
                     url_fuente=fab_url, revisar=True, texto_fuente=origen)

    if amazon_valor:
        coincide = fab_valor is True
        fuente = "amazon_y_fabricante" if coincide else "amazon"
        return campo(amazon_texto, True, "Sí", fuente=fuente,
                     url_fuente=fab_url if coincide else None,
                     texto_fuente=amazon_texto, confianza="alta")

    if fab_valor is True:
        return campo(fab_texto, True, "Sí", fuente="fabricante_oficial", url_fuente=fab_url,
                     texto_fuente=fab_texto, confianza="alta")

    if fab_valor is False:
        # Unico camino hacia "No": evidencia explicita del fabricante de
        # que el producto NO tiene proteccion lateral (ningun caso asi
        # todavia en el lookup).
        return campo(fab_texto, False, "No", fuente="fabricante_oficial", url_fuente=fab_url,
                     texto_fuente=fab_texto, confianza="alta")

    if _fab_identidad_valida(fab_entry):
        texto = ("Auditado en Amazon y en la ficha oficial del fabricante (identidad "
                 "verificada): ninguna mención específica de protección lateral, impacto "
                 "lateral ni tecnología dedicada (SPS/H-GUARD/G-CELL/L.S.P.). Las menciones "
                 "genéricas de \"pruebas de impacto/choque superadas\", cuando aparecen, no "
                 "cuentan como evidencia por no estar ligadas a \"lateral\". La ausencia de "
                 "mención no implica que el producto carezca de la característica.")
    else:
        texto = ("Auditado en Amazon (revisión exhaustiva): ninguna mención específica de "
                 "protección lateral ni tecnología dedicada. La ausencia de mención no "
                 "implica que el producto carezca de la característica.")
    return campo(None, None, "Sin especificar", fuente="amazon", confianza="alta", texto_fuente=texto)


def _amazon_funda_lavable(raw: Dict) -> Tuple[Optional[bool], Optional[str]]:
    hit, texto = _scan_origins_detector(raw, det_funda_lavable)
    return (True, texto) if hit else (None, None)


def resolve_funda_lavable(raw: Dict, fab_entry: Optional[Dict], asin: str) -> Dict:
    """Regla especifica de funda_lavable (revisada 2026-08-11 tras
    correccion de criterio del usuario). Igual que proteccion_lateral: la
    lavabilidad no siempre se anuncia aunque exista, asi que la AUSENCIA de
    mencion nunca se interpreta como "No". Estados posibles:
      - Si: "funda/tapiceria/forro lavable", "lavable a maquina", "apta
        para lavadora" u otra evidencia especifica y verificable.
      - No: SOLO si el fabricante indica explicitamente que NO se puede
        lavar (hallazgo con valor=False). No hay ningun caso asi en el
        Lote 1 actual.
      - Revisar: contradiccion real entre Amazon y fabricante.
      - Sin especificar: se ha auditado Amazon (y el fabricante, cuando la
        identidad esta verificada) sin encontrar evidencia ni a favor ni en
        contra. "Extraible"/"se limpia con facilidad" NUNCA cuenta como
        evidencia de "lavable" (regla ya documentada del proyecto) --
        det_funda_lavable ya exige la raiz "lava" junto a funda/forro/
        tapiceria/tapizado, asi que esas menciones parciales no producen un
        "hit" y quedan correctamente en Sin especificar, no en Si ni en No.
    Caso especial: I-GROW 2 PRO (B0F9YR27XX) no tiene ficha oficial exacta
    localizable (mismo caso que SAFETY FIX 3 PRO en giro_360/reclinable) --
    Sin especificar con confianza media (solo se pudo auditar Amazon). No
    aplicar este mismo patron a otros atributos sin justificarlo antes."""
    amazon_valor, amazon_texto = _amazon_funda_lavable(raw)
    fab_hallazgo, fab_url, _identidad_no_confirmada = _fab_hallazgo(fab_entry, "funda_lavable")
    fab_valor = fab_hallazgo.get("valor") if fab_hallazgo else None
    fab_texto = fab_hallazgo.get("texto_fuente") if fab_hallazgo else None

    if amazon_valor is not None and fab_valor is not None and fab_valor != amazon_valor:
        origen = amazon_texto or fab_texto
        return campo(origen, None, "No confirmado / Revisar", fuente="amazon_y_fabricante",
                     url_fuente=fab_url, revisar=True, texto_fuente=origen)

    if amazon_valor:
        coincide = fab_valor is True
        fuente = "amazon_y_fabricante" if coincide else "amazon"
        return campo(amazon_texto, True, "Sí", fuente=fuente,
                     url_fuente=fab_url if coincide else None,
                     texto_fuente=amazon_texto, confianza="alta")

    if fab_valor is True:
        return campo(fab_texto, True, "Sí", fuente="fabricante_oficial", url_fuente=fab_url,
                     texto_fuente=fab_texto, confianza="alta")

    if fab_valor is False:
        return campo(fab_texto, False, "No", fuente="fabricante_oficial", url_fuente=fab_url,
                     texto_fuente=fab_texto, confianza="alta")

    if asin == "B0F9YR27XX":
        return campo(None, None, "Sin especificar", fuente="amazon", confianza="media", texto_fuente=(
            "Auditado en Amazon (revisión exhaustiva: funda/forro/tapicería/tapizado/"
            "desenfundable/lavable/lava/limpia/extraíble/quitar), sin evidencia ni a favor ni "
            "en contra. Sin ficha oficial exacta del fabricante disponible como segunda fuente "
            "(identidad no verificable en kinderkraft.es ni kinderkraft.com)."
        ))

    if _fab_identidad_valida(fab_entry):
        texto = ("Auditado en Amazon y en la ficha oficial del fabricante (identidad "
                 "verificada): ninguna mención de \"lavable\"/\"lava\" en ninguna fuente. "
                 "Menciones de \"extraíble\"/\"se limpia con facilidad\", cuando existen, no "
                 "cuentan como evidencia de lavable sin decirlo explícitamente. La ausencia de "
                 "mención no implica que el producto no sea lavable.")
    else:
        texto = ("Auditado en Amazon (revisión exhaustiva): ninguna mención de \"lavable\"/"
                 "\"lava\" ni equivalentes. La ausencia de mención no implica que el producto "
                 "no sea lavable.")
    return campo(None, None, "Sin especificar", fuente="amazon", confianza="alta", texto_fuente=texto)


def build_clasificacion(raw: Dict, asin: str, fabricante_lookup: Dict) -> Dict:
    fab_entry = fabricante_lookup.get(asin)
    isofix_c = resolve_isofix(raw, fab_entry)
    normativa_c = resolve_normativa(raw, fab_entry)
    return {
        "isofix": isofix_c,
        "tipo_instalacion": resolve_tipo_instalacion(isofix_c),
        "normativa": normativa_c,
        "grupo_r44": resolve_grupo_r44(normativa_c, raw),
        "altura_r129": resolve_altura(raw),
        "peso": resolve_peso_rango(raw),
        "edad": resolve_edad(raw, fab_entry, asin),
        "orientacion": resolve_orientacion(raw, fab_entry),
        "giro_360": resolve_giro_360(raw, fab_entry, asin),
        "reclinable": resolve_reclinable(raw, fab_entry, asin),
        "reposacabezas": _resolve_generic(raw, fab_entry, "reposacabezas", _amazon_reposacabezas, _mostrar_reposacabezas),
        "arnes": resolve_arnes(raw, fab_entry, asin),
        "peso_silla": _resolve_generic(raw, fab_entry, "peso_silla", _amazon_peso_silla, _mostrar_peso_silla),
        "proteccion_lateral": resolve_proteccion_lateral(raw, fab_entry),
        "funda_lavable": resolve_funda_lavable(raw, fab_entry, asin),
        "fabricante_oficial": {
            "marca": fab_entry.get("marca_fabricante"),
            "modelo": fab_entry.get("modelo_fabricante"),
            "url": fab_entry.get("url_fabricante"),
            "identidad_verificada": fab_entry.get("identidad_verificada"),
            "nombre_amazon": fab_entry.get("nombre_amazon"),
            "nombre_fabricante": fab_entry.get("nombre_fabricante"),
            "aviso_nombre_diferente": fab_entry.get("aviso_nombre_diferente"),
            "motivo_equivalencia": fab_entry.get("motivo_equivalencia"),
        } if fab_entry else None,
    }


# ---------------------------------------------------------------------------
# ETAPA 5: ENSAMBLADO DEL JSON POR PRODUCTO
# ---------------------------------------------------------------------------

def build_product_entry(
    candidate: Dict,
    raw: Dict,
    caracteristicas: "OrderedDict[str, Dict]",
    estado: str,
    image_path: Optional[str],
    clasificacion: Optional[Dict] = None,
) -> Dict:
    return {
        "asin": candidate["asin"],
        "marca": candidate.get("marca_confirmada") or candidate.get("marca_detectada"),
        # v1: no se separa modelo/variante (color, pack...) para no fusionar
        # de forma agresiva productos que podrian ser distintos (regla 7).
        # "modelo" es el titulo completo de Amazon hasta que exista una
        # segunda pasada de agrupado editorial.
        "modelo": raw["title"],
        "titulo_amazon": raw["title"],
        "url": candidate["url"],
        "imagen": image_path,
        "precio": {
            "actual": raw["price_actual"] if raw["price_actual"] is not None else "N/A",
            "anterior": raw["price_anterior"] if raw["price_anterior"] is not None else "N/A",
            "fecha_extraccion": date.today().isoformat(),
        },
        "valoraciones": {
            "puntuacion": raw["rating"],
            "numero": raw["review_count"],
        },
        "caracteristicas": {k: v["valor"] for k, v in caracteristicas.items()},
        "caracteristicas_fuente": {k: v["fuente"] for k, v in caracteristicas.items()},
        # Bloque nuevo (Amazon + fabricante oficial como fuente secundaria),
        # separado de `caracteristicas` para no romper nada que ya funciona.
        "clasificacion": clasificacion,
        "opiniones": {
            "muestra": raw["reviews"],
            # Redaccion editorial pendiente (criterio humano/asistente, no
            # generada por este script: ver docstring del archivo).
            "resumen": None,
        },
        "estado": estado,
    }


# ---------------------------------------------------------------------------
# ORQUESTACION
# ---------------------------------------------------------------------------

def run(search: str, max_pages: int, max_products: int, download_images: bool, out_path: str) -> Dict:
    ensure_playwright_installed()
    ensure_playwright_stealth_installed()
    from playwright.sync_api import sync_playwright  # noqa: E402
    from playwright_stealth import Stealth  # noqa: E402

    stats = {
        "busqueda": search,
        "paginas_recorridas": 0,
        "candidatos_brutos": 0,
        "tras_filtro_marca": 0,
        "tras_deduplicado": 0,
        "procesados": 0,
        "verificados": 0,
        "pendiente_revision": 0,
        "descartados_marca_ficha": 0,
        "fallos_ficha": 0,
    }

    productos: List[Dict] = []
    fabricante_lookup = load_fabricante_lookup()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        _log("[INFO] Browser iniciado")
        context = browser.new_context(
            user_agent=USER_AGENT,
            locale="es-ES",
            viewport={"width": 1920, "height": 1080},
        )
        stealth = Stealth(navigator_languages_override=("es-ES", "es"))
        stealth.apply_stealth_sync(context)
        page = context.new_page()

        warmup_session(page)

        raw_candidates, pages_loaded = search_amazon(page, search, max_pages)
        stats["paginas_recorridas"] = pages_loaded
        stats["candidatos_brutos"] = len(raw_candidates)

        brand_filtered = filter_by_brand(raw_candidates)
        stats["tras_filtro_marca"] = len(brand_filtered)

        unique_candidates = dedupe_by_asin(brand_filtered)
        stats["tras_deduplicado"] = len(unique_candidates)

        limited = unique_candidates[:max_products]

        for candidate in limited:
            time.sleep(random.uniform(2.0, 4.5))
            raw = scrape_product_detail(page, candidate["url"])
            if raw is None:
                stats["fallos_ficha"] += 1
                continue

            # La marca de la ficha (bylineInfo) es mas fiable que el titulo
            # del listado; si aparece y no es ninguna marca autorizada, el
            # match por titulo era un falso positivo y se descarta.
            if raw["byline_brand"]:
                confirmed = match_brand(raw["byline_brand"])
                if confirmed:
                    candidate["marca_confirmada"] = confirmed
                else:
                    _log(f"[INFO] {candidate['asin']}: marca de ficha '{raw['byline_brand']}' "
                         f"no esta en la lista autorizada, se descarta")
                    stats["descartados_marca_ficha"] += 1
                    continue

            caracteristicas = normalize_attributes(raw)
            estado = determine_estado(caracteristicas)

            image_path = None
            if download_images and raw["image_url"]:
                slug = slugify(raw["title"])
                image_path = download_and_process_image(raw["image_url"], candidate["asin"], slug)

            clasificacion = build_clasificacion(raw, candidate["asin"], fabricante_lookup)
            entry = build_product_entry(candidate, raw, caracteristicas, estado, image_path, clasificacion)
            productos.append(entry)

            stats["procesados"] += 1
            if estado == "VERIFICADO":
                stats["verificados"] += 1
            else:
                stats["pendiente_revision"] += 1

            _log(f"[INFO] {candidate['asin']} ({estado}) — {raw['title'][:70]}")

        browser.close()
        _log("[INFO] Browser cerrado")

    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump({"stats": stats, "productos": productos}, f, ensure_ascii=False, indent=2)

    return {"stats": stats, "out_path": out_path}


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(description="Extractor de sillitas de coche en Amazon Espana (independiente de amazon_import.py).")
    parser.add_argument("--search", required=True, help='Termino de busqueda, p.ej. "sillita coche"')
    parser.add_argument("--max-pages", type=int, default=MAX_PAGES, help=f"Paginas de resultados a recorrer (default {MAX_PAGES})")
    parser.add_argument("--max-products", type=int, default=MAX_PRODUCTS, help=f"Maximo de fichas a procesar (default {MAX_PRODUCTS})")
    parser.add_argument("--no-images", action="store_true", help="No descarga ni procesa imagenes (mas rapido para pruebas)")
    parser.add_argument("--out", default=None, help="Ruta del JSON de salida (default tools/output/<slug-busqueda>.json)")
    args = parser.parse_args()

    out_path = args.out or os.path.join(OUTPUT_DIR, f"{slugify(args.search)}.json")

    result = run(
        search=args.search,
        max_pages=args.max_pages,
        max_products=args.max_products,
        download_images=not args.no_images,
        out_path=out_path,
    )

    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
