#!/usr/bin/env python3
"""
Aumenta el margin-bottom de la tarjeta .skills-card en mobile para TODAS las categorías.
Crea separación visual entre la tarjeta de skills y la siguiente.
"""

import glob
from pathlib import Path

SKILLS_MARGIN_CSS = """
<style>
@media (max-width:560px){
  .skills-card{margin-bottom:28px;}
}
</style>
"""

def add_skills_margin(filepath):
    """Agrega margin-bottom a .skills-card en mobile"""

    filename = Path(filepath).name
    print(f"Procesando {filename}...")

    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Si ya tiene el CSS de skills margin, no agregar
    if '.skills-card{margin-bottom:28px;}' in content:
        print(f"[SKIP] {filename} ya tiene skills margin")
        return

    # Buscar si ya hay un style tag con .skills-card{padding-top:32px;}
    if '.skills-card{padding-top:32px;}' in content:
        # Ya existe .skills-card, agregar el margin-bottom a la regla existente
        old_pattern = '  .skills-card{padding-top:32px;}\n}'
        new_pattern = '  .skills-card{padding-top:32px;margin-bottom:28px;}\n}'

        if old_pattern in content:
            content = content.replace(old_pattern, new_pattern)
            print(f"[OK] {filename} skills margin agregado")
        else:
            print(f"[WARN] {filename} no se pudo encontrar el pattern completo")
            return

    else:
        # No existe style tag con skills, insertamos uno nuevo
        if '</head>' in content:
            content = content.replace('</head>', SKILLS_MARGIN_CSS + '</head>')
            print(f"[OK] {filename} skills margin agregado (nuevo style tag)")
        else:
            print(f"[ERROR] {filename} no tiene </head>")
            return

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

if __name__ == "__main__":
    base_path = Path(__file__).parent.parent

    import os
    os.chdir(base_path)

    # Encontrar todos los archivos de categorías
    all_files = sorted(glob.glob("*.html"))

    category_files = [
        f for f in all_files
        if ("meses" in f or "ano" in f) and
           "guia-regalos" not in f and
           "favorito" not in f
    ]

    print(f"Encontrados {len(category_files)} archivos para procesar\n")

    for filename in category_files:
        filepath = base_path / filename
        if filepath.exists():
            add_skills_margin(str(filepath))
        else:
            print(f"[WARN] No encontrado: {filename}")

    print(f"\n[OK] Skills margin agregado a todas las categorias en mobile!")
