#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Migra las fichas de producto de las 10 paginas de 0-6 meses (a0) de la
plantilla antigua .product-card a la plantilla actual .product-card-v2,
conservando integramente el contenido (imagen, nombre, descripcion,
beneficios y resenas ya redactados) - no se reescribe ningun texto."""

import re
from pathlib import Path

ROOT = Path(__file__).parent.parent

FILES = [
    'peluches.html', 'mordedores.html', 'gimnasio-de-actividades.html',
    'juguete-espiral-cochecito.html', 'regalos-personalizados.html',
    'canastillas-de-regalo.html', 'sonajeros.html', 'libros-de-tela.html',
    'cesta-organizadora.html', 'primera-puesta.html',
]

AGE_LABEL = '👶 0-6 meses'

SVG_ILLU = ('<svg viewBox="0 0 100 100" fill="none" stroke="currentColor" stroke-width="4" '
            'stroke-linecap="round" stroke-linejoin="round"><circle cx="28" cy="34" r="12"/>'
            '<path d="M14,82 C14,60 18,52 28,52 C38,52 42,60 42,82"/><circle cx="72" cy="32" r="13"/>'
            '<path d="M57,84 C57,60 61,52 72,52 C83,52 87,60 87,84"/><circle cx="50" cy="54" r="9"/>'
            '<path d="M39,86 C39,72 42,66 50,66 C58,66 61,72 61,86"/>'
            '<path d="M50,26 C50,20 43,17 41,22 C39,27 45,31 50,36 C55,31 61,27 59,22 C57,17 50,20 50,26 Z"/></svg>')

OLD_PRODUCT_RE = re.compile(
    r'<!-- PRODUCT START asin="(?P<asin>[A-Z0-9]+)" -->\s*'
    r'<article class="product-card" id="[A-Z0-9]+" data-asin="[A-Z0-9]+" data-url="(?P<url>[^"]*)">\s*'
    r'<img class="product-card-img" src="(?P<img>[^"]*)" alt="(?P<alt>[^"]*)"[^>]*>\s*'
    r'<h3 class="product-card-name">(?P<name>.*?)</h3>\s*'
    r'<p class="product-card-desc">(?P<desc>.*?)</p>\s*'
    r'<div class="product-card-why">\s*<h4>.*?</h4>\s*<ul>\s*(?P<why>.*?)</ul>\s*</div>\s*'
    r'<div class="product-card-reviews">\s*<h4>.*?</h4>\s*<p>(?P<review>.*?)</p>\s*</div>\s*'
    r'<a class="cta" href="[^"]*" target="_blank" rel="noopener">Ver en Amazon</a>\s*'
    r'</article>\s*'
    r'<!-- PRODUCT END asin="(?P=asin)" -->',
    re.DOTALL
)

WHY_LI_RE = re.compile(r'<li>✔\s*(.*?)</li>')

def build_article(asin, url, img, alt, name, desc, why_items, review):
    why_html = '\n'.join(
        f'        <li><span class="pc2-why-check">✔</span><span>{item}</span></li>'
        for item in why_items
    )
    return f'''<!-- PRODUCT START asin="{asin}" -->
  <article class="product-card-v2" id="{asin}" data-asin="{asin}" data-url="{url}">
    <div class="pc2-top">
      <div class="pc2-media">
        <img src="{img}" alt="{alt}" width="600" height="600" loading="lazy">
      </div>
      <div class="pc2-info">
        <span class="pc2-age">{AGE_LABEL}</span>
        <h3 class="pc2-name">{name}</h3>
        <div class="pc2-desc-card">
          <p>{desc}</p>
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
        <p>{review}</p>
      </div>
      <div class="pc2-reviews-illu" aria-hidden="true">{SVG_ILLU}</div>
    </div>
    <div class="pc2-cta"><a class="cta" href="{url}" target="_blank" rel="noopener">Ver en Amazon</a></div>
  </article>
  <!-- PRODUCT END asin="{asin}" -->'''

def migrate_file(fname):
    fpath = ROOT / fname
    html = fpath.read_text(encoding='utf-8')

    if 'product-card-v2' in html:
        print(f'  ⏭️  {fname}: ya migrado')
        return

    count = 0
    def replacer(m):
        nonlocal count
        why_items = [w.strip() for w in WHY_LI_RE.findall(m.group('why'))]
        count += 1
        return build_article(
            m.group('asin'), m.group('url'), m.group('img'), m.group('alt'),
            m.group('name').strip(), m.group('desc').strip(), why_items, m.group('review').strip()
        )

    new_html = OLD_PRODUCT_RE.sub(replacer, html)

    # Actualizar el wrapper de la seccion de productos al nuevo formato v2
    new_html = new_html.replace('<section class="products wrap">', '<section class="products-v2 wrap">', 1)

    if count == 0:
        print(f'  ❌ {fname}: no se encontraron productos en formato antiguo')
        return

    fpath.write_text(new_html, encoding='utf-8')
    print(f'  ✅ {fname}: {count} productos migrados')

def main():
    for fname in FILES:
        migrate_file(fname)

if __name__ == '__main__':
    main()
