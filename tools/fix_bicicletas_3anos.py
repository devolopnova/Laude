#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Recupera el contenido perdido de bicicletas-y-patinetes-3-anos.html:
extrae los datos reales (imagen, nombre, descripcion, beneficios, resenas)
del commit inicial (estructura antigua .product-card) y reconstruye cada
bloque <article class="product-card-v2"> completo con esos datos."""

import re
from pathlib import Path

ROOT = Path(__file__).parent.parent
OLD_FILE = Path(r"C:\Users\COBOLM~1.2\AppData\Local\Temp\claude\C--guia-regalos\eba7f328-9358-4e27-a54e-fc7c4b223a41\scratchpad\bicicletas_original.html")
CURRENT_FILE = ROOT / "bicicletas-y-patinetes-3-anos.html"

old_html = OLD_FILE.read_text(encoding="utf-8")
current_html = CURRENT_FILE.read_text(encoding="utf-8")

OLD_PRODUCT_RE = re.compile(
    r'<!-- PRODUCT START asin="(?P<asin>[A-Z0-9]+)" -->.*?'
    r'<img class="product-card-img" src="(?P<img>[^"]*)" alt="(?P<alt>[^"]*)"[^>]*>\s*'
    r'<h3 class="product-card-name">(?P<name>.*?)</h3>\s*'
    r'<p class="product-card-desc">(?P<desc>.*?)</p>\s*'
    r'<div class="product-card-why">\s*<h4>.*?</h4>\s*<ul>\s*(?P<why>.*?)</ul>\s*</div>\s*'
    r'<div class="product-card-reviews">\s*<h4>.*?</h4>\s*<p>(?P<review>.*?)</p>\s*</div>\s*'
    r'<a class="cta" href="(?P<url>[^"]*)"',
    re.DOTALL
)

WHY_LI_RE = re.compile(r'<li>✔\s*(.*?)</li>')

products = {}
for m in OLD_PRODUCT_RE.finditer(old_html):
    asin = m.group('asin')
    why_items = [w.strip() for w in WHY_LI_RE.findall(m.group('why'))]
    products[asin] = {
        'img': m.group('img'),
        'alt': m.group('alt'),
        'name': m.group('name').strip(),
        'desc': m.group('desc').strip(),
        'why': why_items,
        'review': m.group('review').strip(),
        'url': m.group('url'),
    }

print(f"Productos extraídos del original: {len(products)}")

SVG_ILLU = ('<svg viewBox="0 0 100 100" fill="none" stroke="currentColor" stroke-width="4" '
            'stroke-linecap="round" stroke-linejoin="round"><circle cx="28" cy="34" r="12"/>'
            '<path d="M14,82 C14,60 18,52 28,52 C38,52 42,60 42,82"/><circle cx="72" cy="32" r="13"/>'
            '<path d="M57,84 C57,60 61,52 72,52 C83,52 87,60 87,84"/><circle cx="50" cy="54" r="9"/>'
            '<path d="M39,86 C39,72 42,66 50,66 C58,66 61,72 61,86"/>'
            '<path d="M50,26 C50,20 43,17 41,22 C39,27 45,31 50,36 C55,31 61,27 59,22 C57,17 50,20 50,26 Z"/></svg>')

def build_article(asin, p):
    why_html = '\n'.join(
        f'        <li><span class="pc2-why-check">✔</span><span>{item}</span></li>'
        for item in p['why']
    )
    return f'''  <!-- PRODUCT START asin="{asin}" -->
  <article class="product-card-v2" id="{asin}" data-asin="{asin}" data-url="{p['url']}">
    <div class="pc2-top">
      <div class="pc2-media">
        <img src="{p['img']}" alt="{p['alt']}" width="600" height="600" loading="lazy">
      </div>
      <div class="pc2-info">
        <span class="pc2-age">👶 3 años</span>
        <h3 class="pc2-name">{p['name']}</h3>
        <div class="pc2-desc-card">
          <p>{p['desc']}</p>
        </div>
      </div>
    </div>
    <div class="pc2-why">
      <div class="pc2-why-head"><span class="pc2-badge">⭐</span><h4>¿Por qué nos gusta?</h4></div>
      <ul class="pc2-why-list">
{why_html}
      </ul>
    </div>
    <div class="pc2-reviews">
      <div class="pc2-reviews-left">
        <div class="pc2-reviews-head"><span class="pc2-badge">💬</span><h4>Lo que más destacan las familias</h4></div>
        <p>{p['review']}</p>
      </div>
      <div class="pc2-reviews-illu" aria-hidden="true">{SVG_ILLU}</div>
    </div>
    <div class="pc2-cta"><a class="cta" href="{p['url']}" target="_blank" rel="noopener">Ver en Amazon</a></div>
  </article>
  <!-- PRODUCT END asin="{asin}" -->'''

# Reemplazar cada bloque <!-- PRODUCT START asin="X" --> ... <!-- PRODUCT END asin="X" -->
# completo (sin importar su estado actual, corrupto o no) por el reconstruido.
BLOCK_RE = re.compile(
    r'<!-- PRODUCT START asin="([A-Z0-9]+)" -->.*?<!-- PRODUCT END asin="\1" -->',
    re.DOTALL
)

count = 0
def replacer(m):
    global count
    asin = m.group(1)
    if asin not in products:
        print(f'  AVISO: {asin} no encontrado en el original, se deja tal cual')
        return m.group(0)
    count += 1
    return build_article(asin, products[asin])

new_html = BLOCK_RE.sub(replacer, current_html)
print(f"Bloques reconstruidos: {count}")

CURRENT_FILE.write_text(new_html, encoding="utf-8")
print("Guardado.")
