#!/usr/bin/env python3
"""
Aumenta el padding-top de la tarjeta .skills-card en mobile para TODAS las categorías.
"""

import glob
from pathlib import Path

SKILLS_PADDING_CSS = """
<style>
@media (max-width:560px){
  .skills-card{padding-top:32px;}
}
</style>
"""

def add_skills_padding(filepath):
    """Agrega padding-top aumentado a .skills-card en mobile"""

    filename = Path(filepath).name
    print(f"Procesando {filename}...")

    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Si ya tiene el CSS de skills, no agregar
    if '.skills-card{padding-top:32px;}' in content:
        print(f"[SKIP] {filename} ya tiene skills padding")
        return

    # Buscar si ya hay un style tag con .pc2-cta (3 años con mobile CSS)
    if '.pc2-cta{padding-top:2px' in content:
        # Ya existe un style tag de 3 años, insertamos el CSS dentro
        old_pattern = '  .cta{padding:7px 14px;font-size:11px;}\n}'
        new_pattern = '  .cta{padding:7px 14px;font-size:11px;}\n  .skills-card{padding-top:32px;}\n}'

        if old_pattern in content:
            content = content.replace(old_pattern, new_pattern)
            print(f"[OK] {filename} skills padding agregado al style existente")
        else:
            print(f"[WARN] {filename} no se pudo encontrar el pattern completo")
            return

    else:
        # No existe style tag anterior, insertamos uno nuevo
        if '</head>' in content:
            content = content.replace('</head>', SKILLS_PADDING_CSS + '</head>')
            print(f"[OK] {filename} skills padding agregado")
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
            add_skills_padding(str(filepath))
        else:
            print(f"[WARN] No encontrado: {filename}")

    print(f"\n[OK] Skills padding agregado a todas las categorias!")
