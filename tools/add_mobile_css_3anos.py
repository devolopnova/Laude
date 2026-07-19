#!/usr/bin/env python3
"""
Agrega CSS móvil compacto solo a las categorías de 3 años.
Inserta un <style> tag en el <head> con overrides específicos.
"""

import glob
from pathlib import Path

MOBILE_CSS = """
<style>
@media (max-width:560px){
  .pc2-top{gap:10px;padding:12px;}
  .pc2-why,.pc2-reviews{padding:12px 12px;}
  .pc2-reviews{gap:12px;}
  .pc2-reviews-illu{width:70px;height:70px;}
  .product-card-v2{gap:14px;padding:18px 0;}
  .pc2-cta{padding-top:2px;padding-bottom:0;}
  .cta{padding:7px 14px;font-size:11px;}
}
</style>
"""

def add_mobile_css(filepath):
    """Agrega CSS móvil al head de un archivo de 3 años"""

    filename = Path(filepath).name
    print(f"Procesando {filename}...")

    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Si ya tiene el style tag, no agregar
    if '@media (max-width:560px){' in content and '.pc2-cta{padding-top:2px' in content:
        print(f"[SKIP] {filename} ya tiene CSS móvil")
        return

    # Buscar el cierre de </head> e insertar el style antes
    if '</head>' in content:
        content = content.replace('</head>', MOBILE_CSS + '</head>')

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)

        print(f"[OK] {filename} CSS móvil agregado")
    else:
        print(f"[ERROR] {filename} no tiene </head>")

# Archivos de 3 años
FILES_3ANOS = [
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
    "juegos-de-mesa-3-anos.html",
]

if __name__ == "__main__":
    base_path = Path(__file__).parent.parent

    import os
    os.chdir(base_path)

    for filename in FILES_3ANOS:
        filepath = base_path / filename
        if filepath.exists():
            add_mobile_css(str(filepath))
        else:
            print(f"[WARN] No encontrado: {filename}")

    print("\n[OK] CSS móvil agregado solo a categorías de 3 años!")
