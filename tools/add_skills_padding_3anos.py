#!/usr/bin/env python3
"""
Aumenta el padding-top de la tarjeta .skills-card en mobile solo para 3 años.
"""

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

    # Si ya tiene el style tag, no agregar
    if '.skills-card{padding-top:32px;}' in content:
        print(f"[SKIP] {filename} ya tiene skills padding")
        return

    # Buscar si ya hay un style tag con .pc2-cta (del anterior script)
    # Si existe, insertamos antes de ese cierre </style>
    if '.pc2-cta{padding-top:2px' in content:
        # Ya existe un style tag, insertamos el CSS dentro
        old_style_end = '@media (max-width:560px){\n  .pc2-top{gap:10px;padding:12px;}\n  .pc2-why,.pc2-reviews{padding:12px 12px;}\n  .pc2-reviews{gap:12px;}\n  .pc2-reviews-illu{width:70px;height:70px;}\n  .product-card-v2{gap:14px;padding:18px 0;}\n  .pc2-cta{padding-top:2px;padding-bottom:0;}\n  .cta{padding:7px 14px;font-size:11px;}\n}'

        new_style = '@media (max-width:560px){\n  .pc2-top{gap:10px;padding:12px;}\n  .pc2-why,.pc2-reviews{padding:12px 12px;}\n  .pc2-reviews{gap:12px;}\n  .pc2-reviews-illu{width:70px;height:70px;}\n  .product-card-v2{gap:14px;padding:18px 0;}\n  .pc2-cta{padding-top:2px;padding-bottom:0;}\n  .cta{padding:7px 14px;font-size:11px;}\n  .skills-card{padding-top:32px;}\n}'

        if old_style_end in content:
            content = content.replace(old_style_end, new_style)
            print(f"[OK] {filename} skills padding agregado al style existente")
        else:
            print(f"[WARN] {filename} no se pudo encontrar el style tag completo")
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
            add_skills_padding(str(filepath))
        else:
            print(f"[WARN] No encontrado: {filename}")

    print("\n[OK] Skills padding agregado solo a categorias de 3 anos!")
