"""Procesa las 7 fotos de cabecera de "Vida en familia" (originales ya
descargadas de Pexels en images/cabecera/vida-en-familia/*.jpg) a WebP,
recortadas para su uso en cada pagina. Mismo patron que
tools/process_hero_photos.py (Planes en casa): horizontales -> banner
1400x580, verticales -> lateral 700x900.

Uso: python tools/process_hero_photos_vida_en_familia.py
"""
import pathlib
from PIL import Image

SRC = pathlib.Path(__file__).resolve().parent.parent / "images/cabecera/vida-en-familia"

HORIZONTAL = {
    "comprar-mejor.jpg": ("comprar-mejor-hero.webp", 0.42),
    "lectura-y-cultura-infantil.jpg": ("lectura-y-cultura-infantil-hero.webp", 0.42),
    "pantallas-y-ocio.jpg": ("pantallas-y-ocio-hero.webp", 0.12),
}
HORIZ_SIZE = (1400, 580)

VERTICAL = {
    "organizacion-y-hogar.jpg": ("organizacion-y-hogar-hero.webp", 0.4),
    "cumpleanos-y-celebraciones.jpg": ("cumpleanos-y-celebraciones-hero.webp", 0.55),
    "consumo-responsable.jpg": ("consumo-responsable-hero.webp", 0.62),
}
VERT_SIZE = (700, 900)

# viajes-y-vacaciones.jpg queda fuera de VERTICAL a proposito: el sujeto
# (nina + maleta) ocupa solo el tercio inferior de una foto con mucho
# espacio blanco arriba, y como su ratio (0.667) esta demasiado cerca del
# ratio objetivo (0.778), el recorte por focus_y no tiene margen suficiente
# para eliminar ese hueco - se necesita ademas un zoom (recortar tambien en
# vertical mas alla del ancho completo). Se resolvio con un recorte manual
# fijo (ver commit): box = (807, 2920, 3140, 5920) sobre la imagen original
# de 3947x5920, tomando los 3000px inferiores centrados en horizontal.


def crop_to_ratio(im: Image.Image, target_w: int, target_h: int, focus_y: float) -> Image.Image:
    target_ratio = target_w / target_h
    w, h = im.size
    src_ratio = w / h
    if src_ratio > target_ratio:
        new_w = int(h * target_ratio)
        x0 = (w - new_w) // 2
        box = (x0, 0, x0 + new_w, h)
    else:
        new_h = int(w / target_ratio)
        max_y0 = h - new_h
        y0 = int(max_y0 * focus_y)
        y0 = max(0, min(y0, max_y0))
        box = (0, y0, w, y0 + new_h)
    cropped = im.crop(box)
    return cropped.resize((target_w, target_h), Image.LANCZOS)


def main():
    for fname, (out_name, focus_y) in {**HORIZONTAL, **VERTICAL}.items():
        src_path = SRC / fname
        im = Image.open(src_path).convert("RGB")
        size = HORIZ_SIZE if fname in HORIZONTAL else VERT_SIZE
        out = crop_to_ratio(im, *size, focus_y)
        out_path = SRC / out_name
        out.save(out_path, "WEBP", quality=82, method=6)
        print(f"{fname} -> {out_name} ({out.size[0]}x{out.size[1]}, {out_path.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
