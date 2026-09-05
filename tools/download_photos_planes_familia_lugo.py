# -*- coding: utf-8 -*-
"""Descarga los originales de las fotos de "Planes en familia - Lugo".

Fuentes: Pexels (images.pexels.com) y Pixabay (cdn.pixabay.com), navegando
sus webs oficiales y usando el enlace CDN real, tal como exige la regla de
busqueda de imagenes del proyecto (nunca Google Imagenes, blogs ni webs de
turismo).

Uso: python tools/download_photos_planes_familia_lugo.py
"""
import pathlib
import urllib.request

BASE = pathlib.Path(__file__).resolve().parent.parent
DST = BASE / "images/planes-familia/lugo"
HERO = BASE / "images/cabecera/planes-en-familia"

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0 Safari/537.36")


def pexels(pid, w=1600):
    return ("https://images.pexels.com/photos/%d/pexels-photo-%d.jpeg"
            "?auto=compress&cs=tinysrgb&w=%d" % (pid, pid, w))


# (archivo destino, url, carpeta)
JOBS = [
    ("marcelle-natureza.jpg", pexels(37422588), DST),
    ("avifauna.jpg", pexels(38244770), DST),
    ("mihl.jpg", pexels(12471788), DST),
    ("museo-ferrocarril-galicia.jpg", pexels(37496823), DST),
    ("roq-park.jpg", pexels(32507024), DST),
    ("laberinto-costa-marina.jpg", pexels(31945033), DST),
    ("muralla-romana-lugo.jpg",
     "https://cdn.pixabay.com/photo/2019/12/07/14/10/city-wall-4679397_1280.jpg", DST),
    ("praia-das-catedrais.jpg", pexels(35614354), DST),
    ("aldea-das-formigas.jpg", pexels(36547610), DST),
    ("carballolandia.jpg", pexels(36597548), DST),
    ("parque-rosalia-de-castro.jpg", pexels(38496002), DST),
    ("parque-do-mino.jpg", pexels(31042223), DST),
    ("fucino-do-porco.jpg", pexels(19359818), DST),
    ("tirolina-das-minas.jpg", pexels(13663971), DST),
    ("piornedo.jpg",
     "https://cdn.pixabay.com/photo/2015/03/16/13/01/palloza-675964_1280.jpg", DST),
    ("galicia-panoramica-src.jpg", pexels(36537419, 2400), HERO),
]


def main():
    DST.mkdir(parents=True, exist_ok=True)
    HERO.mkdir(parents=True, exist_ok=True)
    for name, url, folder in JOBS:
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=60) as r:
            data = r.read()
        out = folder / name
        out.write_bytes(data)
        print("%-34s %8d bytes" % (name, len(data)))


if __name__ == "__main__":
    main()
