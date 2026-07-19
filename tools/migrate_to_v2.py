#!/usr/bin/env python3
"""
Migra todos los productos de .product-card a .product-card-v2 en categorías de 3 años.
Transforma la estructura HTML manteniendo exactamente el mismo contenido.
"""

import re
import glob
from pathlib import Path

# Lista de archivos de 3 años a procesar (todos excepto juegos-de-mesa que ya está hecho)
FILES_TO_MIGRATE = [
    "bicicletas-y-patinetes-3-anos.html",
    "coches-3-anos.html",
    "cocinitas-3-anos.html",
    "construcciones-3-anos.html",
    "disfraces-3-anos.html",
    "figuras-y-animales-3-anos.html",
    "libros-3-anos.html",
    "manualidades-3-anos.html",
    "puzzles-3-anos.html",
    "juguetes-montessori-3-anos.html",
    "coches-teledirigidos-3-anos.html",
]

SVG_FAMILIES = '''<svg viewBox="0 0 100 100" fill="none" stroke="currentColor" stroke-width="4" stroke-linecap="round" stroke-linejoin="round"><circle cx="28" cy="34" r="12"/><path d="M14,82 C14,60 18,52 28,52 C38,52 42,60 42,82"/><circle cx="72" cy="32" r="13"/><path d="M57,84 C57,60 61,52 72,52 C83,52 87,60 87,84"/><circle cx="50" cy="54" r="9"/><path d="M39,86 C39,72 42,66 50,66 C58,66 61,72 61,86"/><path d="M50,26 C50,20 43,17 41,22 C39,27 45,31 50,36 C55,31 61,27 59,22 C57,17 50,20 50,26 Z"/></svg>'''

def transform_product(product_html):
    """Transforma un producto de .product-card a .product-card-v2"""

    # Extraer atributos del article
    asin_match = re.search(r'id="([^"]+)"', product_html)
    asin = asin_match.group(1) if asin_match else ""
    data_url_match = re.search(r'data-url="([^"]+)"', product_html)
    data_url = data_url_match.group(1) if data_url_match else ""

    # Extraer imagen
    img_match = re.search(r'<img class="product-card-img" src="([^"]+)" alt="([^"]+)"[^>]*>', product_html)
    img_src = img_match.group(1) if img_match else ""
    img_alt = img_match.group(2) if img_match else ""

    # Extraer título
    name_match = re.search(r'<h3 class="product-card-name">([^<]+)<\/h3>', product_html)
    title = name_match.group(1) if name_match else ""

    # Extraer descripción
    desc_match = re.search(r'<p class="product-card-desc">([^<]+)<\/p>', product_html)
    description = desc_match.group(1) if desc_match else ""

    # Extraer beneficios (items del "¿Por qué nos gusta?")
    benefits = []
    benefits_section = re.search(r'<div class="product-card-why">.*?<ul>(.*?)<\/ul>\s*<\/div>', product_html, re.DOTALL)
    if benefits_section:
        for item in re.finditer(r'<li>✔\s*([^<]+)<\/li>', benefits_section.group(1)):
            benefits.append(item.group(1).strip())

    # Extraer reseñas de familias
    reviews_match = re.search(r'<div class="product-card-reviews">.*?<p>([^<]+)<\/p>\s*<\/div>', product_html, re.DOTALL)
    reviews_text = reviews_match.group(1).strip() if reviews_match else ""

    # URL de Amazon (del botón)
    url_match = re.search(r'<a class="cta"[^>]*href="([^"]+)"', product_html)
    amazon_url = url_match.group(1) if url_match else data_url

    # Construir nuevo HTML
    new_html = f'''<article class="product-card-v2" id="{asin}" data-asin="{asin}" data-url="{amazon_url}">
    <div class="pc2-top">
      <div class="pc2-media">
        <img src="{img_src}" alt="{img_alt}" width="600" height="600" loading="lazy">
      </div>
      <div class="pc2-info">
        <span class="pc2-age">👶 3 años</span>
        <h3 class="pc2-name">{title}</h3>
        <div class="pc2-desc-card">
          <p>{description}</p>
        </div>
      </div>
    </div>
    <div class="pc2-why">
      <div class="pc2-why-head"><span class="pc2-badge">⭐</span><h4>¿Por qué nos gusta?</h4></div>
      <ul class="pc2-why-list">'''

    for benefit in benefits:
        new_html += f'\n        <li><span class="pc2-why-check">✔</span><span>{benefit}</span></li>'

    new_html += f'''
      </ul>
    </div>
    <div class="pc2-reviews">
      <div class="pc2-reviews-left">
        <div class="pc2-reviews-head"><span class="pc2-badge">💬</span><h4>Lo que más destacan las familias</h4></div>
        <p>{reviews_text}</p>
      </div>
      <div class="pc2-reviews-illu" aria-hidden="true">{SVG_FAMILIES}</div>
    </div>
    <div class="pc2-cta"><a class="cta" href="{amazon_url}" target="_blank" rel="noopener">Ver en Amazon</a></div>
  </article>'''

    return new_html

def migrate_file(filepath):
    """Migra todos los productos en un archivo"""

    print(f"Procesando {filepath}...")

    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Reemplazar <section class="products"> por <section class="products-v2">
    content = content.replace('<section class="products wrap">', '<section class="products-v2 wrap">')

    # Encontrar todos los productos y reemplazarlos
    def replace_product(match):
        product_html = match.group(0)
        # Extraer el contenido entre PRODUCT START y PRODUCT END
        product_content = re.search(r'<!-- PRODUCT START[^>]*>(.+?)<!-- PRODUCT END[^>]*-->', product_html, re.DOTALL)
        if product_content:
            transformed = transform_product(product_content.group(1))
            # Preservar los comentarios de delimitación
            asin = re.search(r'asin="([^"]+)"', product_html).group(1)
            return f'\n  <!-- PRODUCT START asin="{asin}" -->\n  {transformed}\n  <!-- PRODUCT END asin="{asin}" -->\n'
        return product_html

    # Patrón para encontrar productos completos
    pattern = r'<!-- PRODUCT START[^>]*>.*?<!-- PRODUCT END[^>]*-->'
    content = re.sub(pattern, replace_product, content, flags=re.DOTALL)

    # Guardar el archivo modificado
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"[OK] {filepath} migrado exitosamente")

# Ejecutar migración
if __name__ == "__main__":
    base_path = Path(__file__).parent.parent

    for filename in FILES_TO_MIGRATE:
        filepath = base_path / filename
        if filepath.exists():
            migrate_file(str(filepath))
        else:
            print(f"[WARN] No encontrado: {filepath}")

    print("\n[OK] Migracion completada!")
