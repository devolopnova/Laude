"""Procesa las 15 fotos de "Planes en familia - Castellon" (originales en
images/planes-familia/castellon/*.jpg, descargadas de Pexels/Pixabay) a
WebP, redimensionadas SIN recorte fisico, preservando la proporcion
natural de cada fotografia, para la tarjeta .pfb-card de
planes-en-familia-castellon.html.

Mismo patron exacto que tools/process_photos_planes_familia_barcelona.py
(SHORT_SIDE=1000, calidad 82, metodo 6) aplicado a las provincias
siguientes (Tarragona, Valencia, Lleida, Girona) y ahora Castellon.

Uso: python tools/process_photos_planes_familia_castellon.py
"""
import pathlib
from PIL import Image

SRC = pathlib.Path(__file__).resolve().parent.parent / "images/planes-familia/castellon"
SHORT_SIDE = 1000

FILES = [
    "planetari-castello.jpg",
    "parc-miner-maestrat.jpg",
    "parc-del-trenet.jpg",
    "coves-sant-josep.jpg",
    "fuente-de-los-banos.jpg",
    "via-verde-del-mar.jpg",
    "castillo-papa-luna.jpg",
    "desert-de-les-palmes.jpg",
    "jardin-encantado.jpg",
    "islas-columbretes.jpg",
    "museo-del-naipe.jpg",
    "saltapins-morella.jpg",
    "jardin-del-papagayo.jpg",
    "serra-despada.jpg",
    "morella.jpg",
]

# miau-fanzara.jpg queda fuera de esta lista desde el 23/08/2026: MIAU se
# intercambio por Saltapins (Morella) en plan.json (backup <-> primary,
# ver selection_notes) porque no se encontro foto adecuada para su ficha.
# El archivo miau-fanzara.jpg/webp se deja en disco sin borrar (ya no se
# usa en planes-en-familia-castellon.html).


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
