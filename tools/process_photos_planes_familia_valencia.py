"""Procesa las 15 fotos de "Planes en familia - Valencia" (originales en
images/planes-familia/valencia/*.jpg, descargadas de Pexels) a WebP,
redimensionadas SIN recorte fisico, preservando la proporcion natural de
cada fotografia, para la tarjeta vertical .pfb-card de
planes-en-familia-valencia.html.

Sustituye el pipeline antiguo (crop_to_ratio a 400x300 fijo en 4:3,
pensado para el diseno horizontal de 3 columnas ya retirado). Un raster
fijo tan pequeno, servido dentro del contenedor vertical actual (~316px x
385-490px), obligaba al navegador a ampliarlo un 30-45% y perdia
nitidez. La nueva logica solo redimensiona proporcionalmente hasta que el
lado corto mida SHORT_SIDE px, sin recortar nada; el recorte real para
encajar en la tarjeta lo hace el navegador via object-fit:cover +
object-position (ajustado por imagen en el HTML cuando hace falta, ya no
en este script).

Uso: python tools/process_photos_planes_familia_valencia.py
"""
import pathlib
from PIL import Image

SRC = pathlib.Path(__file__).resolve().parent.parent / "images/planes-familia/valencia"
SHORT_SIDE = 1000

FILES = [
    "museu-ciencies.jpg",
    "oceanografic.jpg",
    "bioparc-valencia.jpg",
    "parc-gulliver.jpg",
    "albufera.jpg",
    "malvarrosa.jpg",
    "museu-faller.jpg",
    "iluziona.jpg",
    "hemisferic.jpg",
    "jardines-turia.jpg",
    "liber.jpg",
    "hortensia-herrero.jpg",
    "ratoncito-perez.jpg",
    "bombas-gens.jpg",
    "centre-carme.jpg",
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
