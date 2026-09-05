# -*- coding: utf-8 -*-
"""Procesa las 15 fotos de "Planes en familia - A Coruna" (originales en
images/planes-familia/a-coruna/*.jpg) a WebP, redimensionadas SIN recorte
fisico, preservando la proporcion natural de cada fotografia, para la
tarjeta .pfb-card de planes-en-familia-a-coruna.html.

Mismo patron exacto que tools/process_photos_planes_familia_lugo.py y
tools/process_photos_planes_familia_cantabria.py (SHORT_SIDE=1000,
calidad 82, metodo 6).

Origen de cada foto (regla del proyecto: solo Pexels/Unsplash/Pixabay
navegando su web oficial). LITERAL = foto del lugar real; GENERICA =
fallback tematicamente representativo al no existir foto literal:
- aquarium-finisterrae.png: APORTADA POR EL USUARIO (tiburon nadando en un
  tanque de acuario). Sustituye a la generica de Pexels que se uso en la
  primera version (nino explorando un tunel subacuatico), retirada al
  cambiarla. Unica foto del lote que no viene de Pexels/Pixabay: la dio el
  usuario directamente, asi que no le aplica la regla de bancos de imagen.
- casa-de-las-ciencias.png: APORTADA POR EL USUARIO (interior de un museo
  de ciencia con planetario mecanico, bola de plasma, pendulo de Newton y
  modulos interactivos). Sustituye a la generica de Pexels que se uso en la
  primera version (exterior de un planetario con cupula geodesica),
  retirada al cambiarla. No viene de Pexels/Pixabay: la dio el usuario
  directamente, asi que no le aplica la regla de bancos de imagen.
- domus.jpg: Pexels, GENERICA (una adulta y un nino jugando en un museo).
- monte-de-san-pedro.jpg: Pixabay, LITERAL (Monte de San Pedro, A Coruna).
- muncyt.jpg: Pexels, GENERICA (manos sujetando una bola de plasma
  iluminada, imagen clasica de museo de ciencia).
- casa-grande-de-xanceda.jpg: Pexels, GENERICA (vacas pastando en una
  colina verde).
- torre-de-hercules.jpg: Pixabay, LITERAL (Torre de Hercules, A Coruna).
- corax-fauna.jpg: Pexels, GENERICA (lobo gris en un santuario natural).
- termaria.jpg: Pexels, GENERICA (un adulto y un nino en una piscina).
- parque-de-eiris.jpg: Pexels, GENERICA (ninos jugando en una torre de
  juegos moderna).
- fervenza-do-ezaro.jpg: Pixabay, LITERAL (cascada del Ezaro, Galicia).
- aquapark-cerceda.jpg: Pexels, GENERICA (parque acuatico con toboganes
  de colores).
- fragas-do-eume.jpg: Pexels, GENERICA (arroyo forestal entre rocas
  cubiertas de musgo).
- naturmaz.jpg: Pexels, GENERICA (una adulta y un nino haciendo kayak).
- castillo-de-san-anton.jpg: Pexels, GENERICA (fortaleza costera historica
  con vista al mar).

Uso: python tools/process_photos_planes_familia_a_coruna.py
"""
import pathlib
from PIL import Image

SRC = pathlib.Path(__file__).resolve().parent.parent / "images/planes-familia/a-coruna"
SHORT_SIDE = 1000

FILES = [
    "aquarium-finisterrae.png",
    "casa-de-las-ciencias.png",
    "domus.jpg",
    "monte-de-san-pedro.jpg",
    "muncyt.jpg",
    "casa-grande-de-xanceda.jpg",
    "torre-de-hercules.jpg",
    "corax-fauna.jpg",
    "termaria.jpg",
    "parque-de-eiris.jpg",
    "fervenza-do-ezaro.jpg",
    "aquapark-cerceda.jpg",
    "fragas-do-eume.jpg",
    "naturmaz.jpg",
    "castillo-de-san-anton.jpg",
]


# Excepcion al "sin recorte fisico": la tarjeta .pfb-card recorta la foto con
# object-fit:cover a una caja de proporcion ~3:4, asi que de una foto mas
# alargada en vertical se descarta una franja que no se llega a ver nunca (en
# las mas verticales, mas de un tercio del archivo). Toda foto por debajo de
# 3:4 se recorta a esa proporcion en origen: el encuadre visible en la
# tarjeta no cambia, pero queda controlado aqui en vez de depender del
# navegador, y el archivo pesa menos. Las fotos que ya son 3:4 o mas anchas
# (incluidas todas las horizontales) no se tocan.
MIN_RATIO = 3 / 4

# focus_y por foto para el recorte anterior: 0 = conserva la parte alta,
# 1 = la baja, 0.5 = centro (valor por defecto si no aparece aqui). Solo hace
# falta cuando el motivo no esta centrado verticalmente en el original.
FOCUS_Y = {
    # El tiburon esta en el tercio superior: se tira del fondo de arena para
    # que quede centrado en la tarjeta.
    "aquarium-finisterrae.png": 0.2,
}


def crop_to_ratio(im: Image.Image, tw: int, th: int, focus_y: float = 0.5) -> Image.Image:
    w, h = im.size
    target = tw / th
    if w / h > target:
        new_w = round(h * target)
        left = (w - new_w) // 2
        im = im.crop((left, 0, left + new_w, h))
    else:
        new_h = round(w / target)
        top = int((h - new_h) * focus_y)
        top = max(0, min(top, h - new_h))
        im = im.crop((0, top, w, top + new_h))
    return im.resize((tw, th), Image.LANCZOS)


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
        im = Image.open(SRC / fname).convert("RGB")
        w, h = im.size
        if w / h < MIN_RATIO:
            out = crop_to_ratio(im, SHORT_SIDE, round(SHORT_SIDE / MIN_RATIO),
                                focus_y=FOCUS_Y.get(fname, 0.5))
        else:
            out = resize_preserving_aspect(im, SHORT_SIDE)
        out_name = fname.rsplit(".", 1)[0] + ".webp"
        out_path = SRC / out_name
        out.save(out_path, "WEBP", quality=82, method=6)
        print("%-32s -> %-32s %dx%d  %d bytes"
              % (fname, out_name, out.size[0], out.size[1], out_path.stat().st_size))


if __name__ == "__main__":
    main()
