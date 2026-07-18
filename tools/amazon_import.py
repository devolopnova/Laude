#!/usr/bin/env python3
"""
amazon_import.py

Descarga la imagen principal de un producto de Amazon a partir de su URL y
extrae materia prima (titulo, bullets, muestra de resenas) para que el
contenido final de la ficha se redacte por separado, nunca copiando texto
de Amazon literalmente.

Uso:
    python amazon_import.py <URL_DE_AMAZON> [--target archivo.html] [--no-image]
    python amazon_import.py --square-only images/producto.webp

    --target ARCHIVO   Comprueba si el producto (por ASIN o URL) ya esta
                        insertado en ese HTML antes de hacer nada. Si ya
                        existe, no descarga ni escrapea: devuelve
                        {"ya_existe": true, ...}.
    --no-image         No descarga la imagen (se asume que ya existe en el
                        proyecto). Solo devuelve titulo/bullets/resenas
                        frescos. Pensado para regenerar el contenido de un
                        producto ya importado sin tocar su imagen.
    --square-only RUTA No accede a Amazon: reencuadra una imagen local ya
                        descargada a un cuadrado 600x600 (WebP, sin deformar).

Salida (JSON en stdout, para que otras herramientas puedan consumirlo):
    {
      "asin": "B08WKCD19K",
      "titulo": "Fisher Price Koala Hora de Dormir",
      "bullets": ["...", "..."],
      "reviews_muestra": ["...", "..."],
      "valoracion": 4.8,
      "num_valoraciones": 62500,
      "imagen": "images/fisher-price-koala-hora-de-dormir.webp",
      "slug": "fisher-price-koala-hora-de-dormir",
      "url": "https://www.amazon.es/...",
      "ya_existe": false
    }

    "valoracion" y "num_valoraciones" alimentan el componente reutilizable
    "⭐ Favoritos de los papás" (ver CLAUDE.md). Pueden venir a null si
    Amazon no expone la valoracion en esa pagina de producto.
"""

import argparse
import importlib.util
import json
import os
import re
import subprocess
import sys
import unicodedata
import urllib.request
from typing import List, Optional, Tuple


def ensure_pillow_installed() -> None:
    """Instala el paquete 'Pillow' (PIL) si no esta disponible."""
    if importlib.util.find_spec("PIL") is None:
        subprocess.run([sys.executable, "-m", "pip", "install", "Pillow"], check=True)


def ensure_playwright_installed() -> None:
    """Instala el paquete 'playwright' y el navegador Chromium si faltan."""
    if importlib.util.find_spec("playwright") is None:
        subprocess.run([sys.executable, "-m", "pip", "install", "playwright"], check=True)
    # 'playwright install chromium' no vuelve a descargar si ya esta presente.
    subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"], check=True)


# Pillow es ligero y lo necesitan tanto el flujo normal como --square-only,
# asi que se asegura siempre. Playwright (con su navegador) solo se instala
# de forma perezosa, cuando realmente hace falta acceder a Amazon.
ensure_pillow_installed()
from PIL import Image  # noqa: E402  (import tras auto-instalacion)


# Cabecera de navegador "normal" para reducir la probabilidad de bloqueo por Amazon.
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)

# Selectores candidatos para la imagen principal del producto.
# Amazon cambia el marcado con frecuencia: si deja de funcionar, añade
# aquí el selector nuevo (usa el inspector del navegador para encontrarlo).
IMAGE_SELECTORS = [
    "#landingImage",
    "#imgTagWrapperId img",
    "#main-image-container img",
    "#imageBlock img",
    "img#main-image",
]


def extract_asin(url: str) -> Optional[str]:
    """Extrae el ASIN (10 caracteres alfanumericos) de patrones habituales de URL de Amazon."""
    match = re.search(r"/(?:dp|gp/product|gp/aw/d)/([A-Z0-9]{10})", url)
    if match:
        return match.group(1)
    match = re.search(r"[?&]asin=([A-Z0-9]{10})", url, re.IGNORECASE)
    if match:
        return match.group(1).upper()
    return None


def get_main_image_url(page) -> Optional[str]:
    """Recorre IMAGE_SELECTORS y devuelve la URL de la primera imagen encontrada."""
    for selector in IMAGE_SELECTORS:
        element = page.query_selector(selector)
        if not element:
            continue
        # data-old-hires suele apuntar a la version de mayor resolucion.
        src = element.get_attribute("data-old-hires") or element.get_attribute("src")
        if src:
            return src
    return None


def get_product_title(page) -> Optional[str]:
    """Devuelve el titulo del producto (selector estandar de Amazon), o None si no se encuentra."""
    element = page.query_selector("#productTitle")
    if element:
        text = element.inner_text().strip()
        if text:
            return text
    return None


def extract_bullets(page, limit: int = 10) -> List[str]:
    """
    Extrae los bullet points de caracteristicas del producto.
    Es solo materia prima para redactar contenido original despues:
    nunca debe copiarse literalmente en la ficha final.
    """
    bullets: List[str] = []
    for element in page.query_selector_all("#feature-bullets li span.a-list-item"):
        text = element.inner_text().strip()
        if text and text not in bullets:
            bullets.append(text)
        if len(bullets) >= limit:
            break
    return bullets


def extract_reviews_sample(page, limit: int = 8, max_chars: int = 300) -> List[str]:
    """
    Extrae una muestra de texto de resenas de clientes (si Amazon las muestra
    en la propia pagina de producto). Es solo materia prima para el resumen
    "Lo que mas destacan las familias": nunca se copia literalmente.
    """
    reviews: List[str] = []
    for element in page.query_selector_all('[data-hook="review-body"] span'):
        text = element.inner_text().strip()
        if text:
            reviews.append(text[:max_chars])
        if len(reviews) >= limit:
            break
    return reviews


def get_rating(page) -> Optional[float]:
    """
    Extrae la valoracion media (0-5) del selector estandar de Amazon
    (texto oculto para lectores de pantalla, tipo "4,8 de 5 estrellas").
    Usa text_content() en vez de inner_text() porque el texto esta oculto
    visualmente y inner_text() no lo devolveria.
    """
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
    """Extrae el numero de valoraciones/calificaciones del producto (p.ej. 62.500)."""
    element = page.query_selector("#acrCustomerReviewText")
    if not element:
        return None
    text = (element.text_content() or "").strip()
    match = re.search(r"([\d.,]+)", text)
    if not match:
        return None
    digits = re.sub(r"[^\d]", "", match.group(1))
    return int(digits) if digits else None


def slugify(title: str, max_length: int = 70) -> str:
    """
    Convierte un titulo en un nombre de archivo SEO:
    minusculas, sin acentos, espacios/simbolos -> guiones, truncado a ~max_length.
    """
    # Descompone acentos/diacriticos (NFKD) y descarta los caracteres combinados.
    ascii_text = unicodedata.normalize("NFKD", title).encode("ascii", "ignore").decode("ascii")
    lowered = ascii_text.lower()
    # Cualquier caracter que no sea letra/numero se trata como separador de palabras.
    cleaned = re.sub(r"[^a-z0-9]+", " ", lowered)
    slug = re.sub(r"\s+", "-", cleaned.strip())
    if len(slug) > max_length:
        # Corta en el ultimo guion dentro del limite para no partir una palabra.
        slug = slug[:max_length].rsplit("-", 1)[0]
    return slug or "producto"


def get_unique_path(directory: str, filename: str) -> str:
    """Si 'filename' ya existe en 'directory', añade -2, -3, ... hasta encontrar uno libre."""
    base, ext = os.path.splitext(filename)
    candidate = os.path.join(directory, filename)
    counter = 2
    while os.path.exists(candidate):
        candidate = os.path.join(directory, f"{base}-{counter}{ext}")
        counter += 1
    return candidate


def guess_extension(image_url: str) -> str:
    """Deduce la extension del archivo a partir de la URL de la imagen (por defecto jpg)."""
    match = re.search(r"\.(jpg|jpeg|png|webp)(?:[?#]|$)", image_url, re.IGNORECASE)
    return match.group(1).lower() if match else "jpg"


def download_image(image_url: str, dest_path: str) -> None:
    """Descarga el binario de la imagen y lo escribe en dest_path."""
    request = urllib.request.Request(image_url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=30) as response:
        data = response.read()
    with open(dest_path, "wb") as f:
        f.write(data)


def convert_to_webp(source_path: str, quality: int = 85) -> Optional[str]:
    """
    Convierte source_path a WebP (calidad 85) en la misma carpeta.
    Devuelve la ruta del .webp generado, o None si la conversion falla.
    """
    webp_path = os.path.splitext(source_path)[0] + ".webp"
    try:
        with Image.open(source_path) as img:
            # WebP no admite el modo P (paleta); RGBA se conserva para transparencia.
            if img.mode not in ("RGB", "RGBA"):
                img = img.convert("RGBA" if "A" in img.mode else "RGB")
            img.save(webp_path, "WEBP", quality=quality)
        return webp_path
    except Exception:
        return None


def pad_to_square(image_path: str, size: int = 600, background: Tuple[int, int, int] = (255, 255, 255)) -> str:
    """
    Encuadra image_path en un lienzo cuadrado de size x size sin recortar ni
    deformar el producto: lo escala manteniendo la proporcion original y
    rellena los margenes sobrantes con 'background' (letterbox). Guarda
    siempre como WebP; si el archivo de entrada no era .webp, el original
    se elimina tras la conversion. Devuelve la ruta final.
    """
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


def check_duplicate(target_file: str, asin: Optional[str], url: str) -> bool:
    """Comprueba si el producto (por ASIN o URL exacta) ya esta insertado en target_file."""
    if not target_file or not os.path.exists(target_file):
        return False
    with open(target_file, "r", encoding="utf-8") as f:
        content = f.read()
    if asin and (
        f'data-asin="{asin}"' in content
        or re.search(rf"/{re.escape(asin)}(?:[/?\"'\s]|$)", content)
    ):
        return True
    if url in content:
        return True
    return False


def scrape_product(url: str):
    """Abre la URL con Playwright y devuelve (image_url, title, bullets, reviews, rating, review_count)."""
    ensure_playwright_installed()
    from playwright.sync_api import sync_playwright  # noqa: E402  (import tras auto-instalacion)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(user_agent=USER_AGENT, locale="es-ES")
        page = context.new_page()
        try:
            page.goto(url, wait_until="networkidle", timeout=60000)
            image_url = get_main_image_url(page)
            title = get_product_title(page)
            bullets = extract_bullets(page)
            reviews = extract_reviews_sample(page)
            rating = get_rating(page)
            review_count = get_review_count(page)
        finally:
            browser.close()

    return image_url, title, bullets, reviews, rating, review_count


def main() -> None:
    # Fuerza UTF-8 en stdout: en consola Windows el valor por defecto (cp1252)
    # corrompe titulos con acentos en el JSON de salida.
    sys.stdout.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(description="Importa un producto de Amazon o reencuadra una imagen existente.")
    parser.add_argument("url", nargs="?", help="URL del producto en Amazon")
    parser.add_argument("--target", help="Ruta del HTML destino: si el producto ya esta insertado ahi, no hace nada")
    parser.add_argument(
        "--no-image", action="store_true",
        help="No descarga la imagen; solo devuelve titulo/bullets/resenas frescos (para regenerar contenido)",
    )
    parser.add_argument(
        "--square-only", metavar="RUTA_IMAGEN",
        help="No accede a Amazon: solo reencuadra una imagen local existente a un cuadrado 600x600",
    )
    args = parser.parse_args()

    if args.square_only:
        if not os.path.exists(args.square_only):
            print(f"ERROR: no existe el archivo {args.square_only}", file=sys.stderr)
            sys.exit(2)
        final_path = pad_to_square(args.square_only)
        print(json.dumps({"imagen": final_path.replace(os.sep, "/")}, ensure_ascii=False, indent=2))
        return

    if not args.url:
        parser.error("se requiere una URL de Amazon (o usa --square-only <ruta_imagen>)")

    url = args.url
    asin = extract_asin(url)

    if args.target and check_duplicate(args.target, asin, url):
        print(json.dumps(
            {
                "ya_existe": True,
                "asin": asin,
                "url": url,
                "mensaje": "Este producto ya esta insertado en el archivo destino.",
            },
            ensure_ascii=False, indent=2,
        ))
        return

    images_dir = "images"
    os.makedirs(images_dir, exist_ok=True)

    image_url, title, bullets, reviews, rating, review_count = scrape_product(url)

    slug = slugify(title) if title else None
    final_path: Optional[str] = None

    if not args.no_image:
        if not image_url:
            print("ERROR: no se pudo localizar la imagen principal del producto.", file=sys.stderr)
            sys.exit(2)

        extension = guess_extension(image_url)
        filename = f"{asin}.{extension}" if asin else f"temp_{os.getpid()}.{extension}"
        dest_path = os.path.join(images_dir, filename)

        download_image(image_url, dest_path)

        # Convierte la descarga a WebP y, solo si la conversion tuvo exito,
        # elimina el archivo original para no dejar duplicados en "images".
        webp_path = convert_to_webp(dest_path)
        if webp_path and webp_path != dest_path:
            os.remove(dest_path)
            final_path = webp_path
        else:
            final_path = webp_path or dest_path

        # Si se obtuvo el titulo, renombra el WebP final a un nombre SEO,
        # evitando sobrescribir archivos existentes (-2, -3, ...).
        if slug:
            seo_path = get_unique_path(images_dir, f"{slug}.webp")
            os.rename(final_path, seo_path)
            final_path = seo_path

        # Encuadra a cuadrado 600x600 sin recortar ni deformar el producto.
        final_path = pad_to_square(final_path)

    # Salida final: informacion del producto en JSON (unica salida en stdout)
    # para que otras herramientas puedan integrarla facilmente.
    product_info = {
        "asin": asin,
        "titulo": title,
        "bullets": bullets,
        "reviews_muestra": reviews,
        "valoracion": rating,
        "num_valoraciones": review_count,
        "imagen": final_path.replace(os.sep, "/") if final_path else None,
        "slug": slug,
        "url": url,
        "ya_existe": False,
    }
    print(json.dumps(product_info, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
