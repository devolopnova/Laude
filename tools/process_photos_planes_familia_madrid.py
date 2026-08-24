"""Procesa las 15 fotos de "Planes en familia - Madrid" (originales en
images/planes-familia/madrid/*.jpg, descargadas de Pexels) a WebP,
redimensionadas SIN recorte fisico, preservando la proporcion natural de
cada fotografia, para la tarjeta vertical .pfb-card de
planes-en-familia-madrid.html.

Mismo patron ya usado en Barcelona/Tarragona/Valencia/Lleida/Girona: solo
redimensiona proporcionalmente hasta que el lado corto mida SHORT_SIDE px,
sin recortar nada; el recorte real para encajar en la tarjeta lo hace el
navegador via object-fit:cover + object-position (ajustado por imagen en
el HTML cuando hace falta, ya no en este script).

Uso: python tools/process_photos_planes_familia_madrid.py
"""
import pathlib
from PIL import Image

SRC = pathlib.Path(__file__).resolve().parent.parent / "images/planes-familia/madrid"
SHORT_SIDE = 1000

FILES = [
    "madrid-rio.jpg",
    "parque-atracciones.jpg",
    "faunia.jpg",
    "micropolix.jpg",
    "retiro.jpg",
    "zoo-aquarium.jpg",
    "raton-perez.jpg",
    "parque-warner.jpg",
    "bosque-encantado.jpg",
    "museo-ilusiones.jpg",
    "casa-de-campo.jpg",
    "museo-cera.jpg",
    "museo-ferrocarril.jpg",
    "tour-bernabeu.jpg",
    "museo-naval.jpg",
]


def resize_preserving_aspect(im: Image.Image, short_side: int) -> Image.Image:
    w, h = im.size
    if w <= h:
        new_w = short_side
        new_h = round(h * short_side / w)
    else:
        new_h = short_side
        new_w = round(w * short_side / h)
    return im.resize((new_w, new_h), Image.LANCZOS)


def main():
    for fname in FILES:
        src_path = SRC / fname
        im = Image.open(src_path).convert("RGB")
        out = resize_preserving_aspect(im, SHORT_SIDE)
        out_name = fname.rsplit(".", 1)[0] + ".webp"
        out_path = SRC / out_name
        out.save(out_path, "WEBP", quality=82, method=6)
        print(f"{fname} -> {out_name} ({out.size[0]}x{out.size[1]}, {out_path.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
