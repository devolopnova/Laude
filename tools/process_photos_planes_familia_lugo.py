# -*- coding: utf-8 -*-
"""Procesa las fotos de "Planes en familia - Lugo".

1) Las 15 fotos de lugar (images/planes-familia/lugo/*.jpg) a WebP,
   redimensionadas SIN recorte fisico, preservando la proporcion natural,
   para la tarjeta .pfb-card de planes-en-familia-lugo.html. Mismo patron
   exacto que tools/process_photos_planes_familia_cantabria.py
   (SHORT_SIDE=1000, calidad 82, metodo 6).
2) La foto panoramica del hub de Galicia, recortada a 21:9 (1920x823),
   mismo formato que el resto de *-panoramica.webp de
   images/cabecera/planes-en-familia/.

Origen de cada foto (regla del proyecto: solo Pexels/Unsplash/Pixabay
navegando su web oficial). LITERAL = foto del lugar real; GENERICA =
fallback tematicamente representativo al no existir foto literal:
- marcelle-natureza.jpg: Pexels, GENERICA (familia de ciervos descansando
  en un entorno forestal).
- avifauna.jpg: Pexels, GENERICA (guacamayos coloridos posados al aire
  libre).
- mihl.jpg: Pexels, GENERICA (ninos junto a una exposicion en un museo
  moderno).
- museo-ferrocarril-galicia.jpg: Pexels, GENERICA (locomotora de vapor
  antigua expuesta bajo un toldo).
- roq-park.jpg: Pexels, GENERICA (padre e hijo en un parque de aventura y
  tirolinas entre arboles).
- laberinto-costa-marina.jpg: Pexels, GENERICA (laberinto de setos verdes
  en un jardin).
- muralla-romana-lugo.jpg: Pixabay, LITERAL (adarve de la muralla de Lugo
  con las torres de la catedral al fondo).
- praia-das-catedrais.jpg: Pexels, LITERAL (arcada de la playa de las
  Catedrales con la marea baja).
- aldea-das-formigas.png: APORTADA POR EL USUARIO (casa rural de piedra con
  cubierta vegetal en un entorno verde). Sustituye a la generica de Pexels
  que se uso en la primera version (sendero de parque con esculturas de
  hormigas gigantes), retirada al cambiarla. No viene de Pexels/Pixabay: la
  dio el usuario directamente, asi que no le aplica la regla de bancos de
  imagen.
- carballolandia.jpg: Pexels, GENERICA (columpio rustico colgando de un
  arbol).
- parque-rosalia-de-castro.jpg: Pexels, GENERICA (estanque de patos en un
  parque verde).
- parque-do-mino.jpg: Pexels, GENERICA (sendero de parque natural junto a
  un rio).
- fucino-do-porco.jpg: Pexels, GENERICA (pasarela de madera sobre un
  acantilado junto al mar).
- tirolina-das-minas.jpg: Pexels, GENERICA (persona descendiendo por una
  tirolina).
- piornedo.jpg: Pixabay, LITERAL (palloza de piedra con techo vegetal).
- galicia-panoramica-src.jpg: Pexels, LITERAL de la comunidad (costa
  rocosa de Galicia) -> images/cabecera/planes-en-familia/galicia-panoramica.webp

Uso: python tools/process_photos_planes_familia_lugo.py
"""
import pathlib
from PIL import Image

BASE = pathlib.Path(__file__).resolve().parent.parent
SRC = BASE / "images/planes-familia/lugo"
HERO = BASE / "images/cabecera/planes-en-familia"
SHORT_SIDE = 1000

FILES = [
    "marcelle-natureza.jpg",
    "avifauna.jpg",
    "mihl.jpg",
    "museo-ferrocarril-galicia.jpg",
    "roq-park.jpg",
    "laberinto-costa-marina.jpg",
    "muralla-romana-lugo.jpg",
    "praia-das-catedrais.jpg",
    "aldea-das-formigas.png",
    "carballolandia.jpg",
    "parque-rosalia-de-castro.jpg",
    "parque-do-mino.jpg",
    "fucino-do-porco.jpg",
    "tirolina-das-minas.jpg",
    "piornedo.jpg",
]

HERO_W, HERO_H = 1920, 823  # 21:9, mismo tamano que el resto de panoramicas

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
    # El asiento del columpio esta en el tercio inferior: se tira de la copa
    # del arbol para que no quede cortado ni pegado al borde de abajo.
    "carballolandia.jpg": 1.0,
}


def resize_preserving_aspect(im: Image.Image, short_side: int) -> Image.Image:
    w, h = im.size
    if w <= h:
        new_w = short_side
        new_h = round(h * short_side / w)
    else:
        new_h = short_side
        new_w = round(w * short_side / h)
    return im.resize((new_w, new_h), Image.LANCZOS)


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
        print("%-34s -> %-34s %dx%d  %d bytes"
              % (fname, out_name, out.size[0], out.size[1], out_path.stat().st_size))

    hero_src = HERO / "galicia-panoramica-src.jpg"
    im = Image.open(hero_src).convert("RGB")
    out = crop_to_ratio(im, HERO_W, HERO_H, focus_y=0.5)
    out_path = HERO / "galicia-panoramica.webp"
    out.save(out_path, "WEBP", quality=82, method=6)
    print("%-34s -> %-34s %dx%d  %d bytes"
          % (hero_src.name, out_path.name, HERO_W, HERO_H, out_path.stat().st_size))


if __name__ == "__main__":
    main()
