"""Procesa las 5 fotos de cabecera de "Planes en casa" (originales ya
descargadas de Pexels en images/cabecera/planes-en-casa/*.jpg) a WebP,
recortadas para su uso en cada hub.

- Horizontales (juegos, crear-y-construir, cocinar-juntos): recorte a
  ratio ancho, pensado para cabecera a ancho completo del bloque
  .cat-hero-2 (max-width 1080px). Salida 1400x580 (ratio ~2.41:1).
- Verticales (manualidades, experimentos): recorte a ratio retrato,
  pensado para cabecera con la foto en un lateral. Salida 700x900
  (ratio ~0.78:1).

focus_y controla qué parte de la imagen se conserva al recortar
verticalmente (0 = arriba, 1 = abajo), ajustado a mano por foto según
donde esté el contenido relevante.

Uso: python tools/process_hero_photos.py
"""
import pathlib
from PIL import Image

SRC = pathlib.Path(__file__).resolve().parent.parent / "images/cabecera/planes-en-casa"

HORIZONTAL = {
    "juegos.jpg": ("juegos-hero.webp", 0.5),
    "crear-y-construir.jpg": ("crear-y-construir-hero.webp", 0.42),
    "cocinar-juntos.jpg": ("cocinar-juntos-hero.webp", 0.5),
}
HORIZ_SIZE = (1400, 580)

VERTICAL = {
    "manualidades.jpg": ("manualidades-hero.webp", 0.5),
    "experimentos.jpg": ("experimentos-hero.webp", 0.38),
}
VERT_SIZE = (700, 900)


def crop_to_ratio(im: Image.Image, target_w: int, target_h: int, focus_y: float) -> Image.Image:
    target_ratio = target_w / target_h
    w, h = im.size
    src_ratio = w / h
    if src_ratio > target_ratio:
        # imagen mas ancha que el objetivo: recortar por los lados, centrado
        new_w = int(h * target_ratio)
        x0 = (w - new_w) // 2
        box = (x0, 0, x0 + new_w, h)
    else:
        # imagen mas alta que el objetivo: recortar arriba/abajo segun focus_y
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
        if fname in HORIZONTAL:
            out = crop_to_ratio(im, *HORIZ_SIZE, focus_y)
        else:
            out = crop_to_ratio(im, *VERT_SIZE, focus_y)
        out_path = SRC / out_name
        out.save(out_path, "WEBP", quality=82, method=6)
        print(f"{fname} -> {out_name} ({out.size[0]}x{out.size[1]}, {out_path.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
