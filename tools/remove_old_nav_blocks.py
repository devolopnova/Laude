#!/usr/bin/env python3
"""
Elimina los bloques antiguos de navegacion (.cat-pager, .age-pager, .mont-chip)
que quedan duplicados ahora que tenemos el nuevo .bottom-nav
"""

import glob
import re
from pathlib import Path

def remove_old_nav_blocks(filepath):
    """Elimina los bloques antiguos de navegacion"""
    filename = Path(filepath).name
    print(f"Procesando {filename}...")

    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Contador de cambios
    changes = 0

    # Eliminar .cat-pager
    cat_pager_pattern = r'<nav class="cat-pager wrap">.*?</nav>\s*'
    if re.search(cat_pager_pattern, content, re.DOTALL):
        content = re.sub(cat_pager_pattern, '', content, flags=re.DOTALL)
        changes += 1
        print(f"  - Eliminado .cat-pager")

    # Eliminar .age-pager
    age_pager_pattern = r'<nav class="age-pager wrap">.*?</nav>\s*'
    if re.search(age_pager_pattern, content, re.DOTALL):
        content = re.sub(age_pager_pattern, '', content, flags=re.DOTALL)
        changes += 1
        print(f"  - Eliminado .age-pager")

    # Eliminar .mont-chip
    mont_chip_pattern = r'<p class="mont-chip wrap">.*?</p>\s*'
    if re.search(mont_chip_pattern, content, re.DOTALL):
        content = re.sub(mont_chip_pattern, '', content, flags=re.DOTALL)
        changes += 1
        print(f"  - Eliminado .mont-chip")

    if changes > 0:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"[OK] {filename} - {changes} bloque(s) eliminado(s)")
    else:
        print(f"[SKIP] {filename} - sin bloques antiguos")

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
            remove_old_nav_blocks(str(filepath))
        else:
            print(f"[WARN] No encontrado: {filename}")

    print(f"\n[OK] Bloques antiguos eliminados!")
