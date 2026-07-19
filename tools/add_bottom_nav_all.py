#!/usr/bin/env python3
"""
Agrega el bloque de navegacion inferior a TODAS las categorias de todas las edades.
"""

import glob
import re
from pathlib import Path

def extract_age_link_data(content):
    """Extrae la edad anterior y siguiente del contenido HTML"""
    prev_link = None
    next_link = None

    # Buscar categoria anterior/siguiente en .cat-pager
    cat_pager_match = re.search(
        r'<nav class="cat-pager wrap">(.*?)</nav>',
        content,
        re.DOTALL
    )
    if cat_pager_match:
        pager_content = cat_pager_match.group(1)

        prev_match = re.search(
            r'<a class="cat-pager-link prev" href="([^"]+)">',
            pager_content
        )
        if prev_match:
            prev_link = prev_match.group(1)

        next_match = re.search(
            r'<a class="cat-pager-link next" href="([^"]+)">',
            pager_content
        )
        if next_match:
            next_link = next_match.group(1)

    # Buscar edad anterior/siguiente en .age-pager
    age_pager_match = re.search(
        r'<nav class="age-pager wrap">(.*?)</nav>',
        content,
        re.DOTALL
    )
    prev_age_link = None
    next_age_link = None
    if age_pager_match:
        age_pager_content = age_pager_match.group(1)

        prev_age_match = re.search(
            r'<a class="cat-pager-link prev" href="([^"]+)">',
            age_pager_content
        )
        if prev_age_match:
            prev_age_link = prev_age_match.group(1)

        next_age_match = re.search(
            r'<a class="cat-pager-link next" href="([^"]+)">',
            age_pager_content
        )
        if next_age_match:
            next_age_link = next_age_match.group(1)

    return {
        'prev_cat': prev_link,
        'next_cat': next_link,
        'prev_age': prev_age_link,
        'next_age': next_age_link
    }

def get_age_link_for_file(filename):
    """Retorna el enlace a la edad anterior/siguiente basado en el nombre del archivo"""
    # Mapeo de edades a sus enlaces en la landing
    age_map = {
        '0-6-meses': 'guia-regalos-juguetes.html#a0',
        '6-12-meses': 'guia-regalos-juguetes.html#a1',
        '1-ano': 'guia-regalos-juguetes.html#a2',
        '2-anos': 'guia-regalos-juguetes.html#a2',  # 1-3 años
        '3-anos': 'guia-regalos-juguetes.html#a2',  # 1-3 años
        '4-anos': 'guia-regalos-juguetes.html#a5',  # 4-7 años
        '5-anos': 'guia-regalos-juguetes.html#a5',  # 4-7 años
        '6-anos': 'guia-regalos-juguetes.html#a5',  # 4-7 años
        '7-anos': 'guia-regalos-juguetes.html#a5',  # 4-7 años
        '8-anos': 'guia-regalos-juguetes.html#a9',  # 8-9 años
        '9-anos': 'guia-regalos-juguetes.html#a9',  # 8-9 años
        '10-anos': 'guia-regalos-juguetes.html#a11', # 10 años
    }

    for age_key, link in age_map.items():
        if age_key in filename:
            return link
    return 'guia-regalos-juguetes.html'

def generate_bottom_nav_html(prev_cat, next_cat, prev_age_link, next_age_link):
    """Genera el HTML del bloque de navegacion inferior"""

    # Usar enlaces de categoría si existen, sino usar edad
    prev_link = prev_cat if prev_cat else (prev_age_link if prev_age_link else 'guia-regalos-juguetes.html')
    next_link = next_cat if next_cat else (next_age_link if next_age_link else 'guia-regalos-juguetes.html')

    html = f"""<div class="bottom-nav wrap">
  <section class="bottom-nav-section">
    <h3 class="bottom-nav-title">⊞ NAVEGAR ENTRE CATEGORÍAS</h3>
    <div class="bottom-nav-grid">
      <a class="bottom-nav-card bottom-nav-prev" href="{prev_link}">
        <span class="bottom-nav-icon">←</span>
        <span class="bottom-nav-label">Categoría anterior</span>
      </a>
      <a class="bottom-nav-card bottom-nav-center" href="guia-regalos-juguetes.html">
        <span class="bottom-nav-icon">⊞</span>
        <span class="bottom-nav-title-main">Todas las categorías</span>
      </a>
      <a class="bottom-nav-card bottom-nav-next" href="{next_link}">
        <span class="bottom-nav-label">Siguiente categoría</span>
        <span class="bottom-nav-icon">→</span>
      </a>
    </div>
  </section>

  <section class="bottom-nav-section">
    <h3 class="bottom-nav-title">🔍 EXPLORAR MÁS</h3>
    <div class="bottom-nav-explore">
      <a class="bottom-nav-explore-card" href="guia-regalos-juguetes.html#a0">
        <strong class="bottom-nav-explore-name">Ver regalos para<br>0–6 meses</strong>
        <span class="bottom-nav-explore-desc">Ideas para la etapa anterior</span>
      </a>
      <a class="bottom-nav-explore-card" href="guia-regalos-juguetes.html#a1">
        <strong class="bottom-nav-explore-name">Ver regalos para<br>2 años</strong>
        <span class="bottom-nav-explore-desc">Ideas para la siguiente etapa</span>
      </a>
      <a class="bottom-nav-explore-card" href="guia-montessori.html">
        <strong class="bottom-nav-explore-name">Descubre la<br>Guía Montessori</strong>
        <span class="bottom-nav-explore-desc">Juguetes por edades basados en el método Montessori</span>
      </a>
    </div>
    <p class="bottom-nav-note">ℹ Los enlaces llevan directamente a la ficha del producto en Amazon.es.</p>
  </section>
</div>
"""
    return html

def add_bottom_nav(filepath):
    """Agrega el bloque de navegacion a un archivo"""
    filename = Path(filepath).name
    print(f"Procesando {filename}...")

    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Si ya tiene el bloque, no agregar
    if 'class="bottom-nav wrap"' in content:
        print(f"[SKIP] {filename} ya tiene bottom-nav")
        return

    # Extraer datos de navegacion
    nav_data = extract_age_link_data(content)
    age_link = get_age_link_for_file(filename)

    # Generar HTML del bloque
    bottom_nav_html = generate_bottom_nav_html(
        nav_data['prev_cat'],
        nav_data['next_cat'],
        nav_data['prev_age'],
        nav_data['next_age']
    )

    # Buscar donde insertar (antes del footer)
    if '<footer class="wrap">' in content:
        content = content.replace(
            '<footer class="wrap">',
            bottom_nav_html + '\n<footer class="wrap">'
        )

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)

        print(f"[OK] {filename} bottom-nav agregado")
    else:
        print(f"[ERROR] {filename} no tiene footer")

if __name__ == "__main__":
    base_path = Path(__file__).parent.parent

    import os
    os.chdir(base_path)

    # Encontrar todos los archivos de categorias
    all_files = sorted(glob.glob("*.html"))

    category_files = [
        f for f in all_files
        if ("meses" in f or "ano" in f) and
           "guia-regalos" not in f and
           "favorito" not in f and
           "montessori" not in f
    ]

    print(f"Encontrados {len(category_files)} archivos para procesar\n")

    for filename in category_files:
        filepath = base_path / filename
        if filepath.exists():
            add_bottom_nav(str(filepath))
        else:
            print(f"[WARN] No encontrado: {filename}")

    print(f"\n[OK] Bottom-nav agregado a todas las categorias!")
