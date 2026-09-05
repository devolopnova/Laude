# -*- coding: utf-8 -*-
"""Descarga los originales de las fotos de "Planes en familia - A Coruna".

Fuentes: Pexels (images.pexels.com) y Pixabay (cdn.pixabay.com), navegando
sus webs oficiales y usando el enlace CDN real, tal como exige la regla de
busqueda de imagenes del proyecto (nunca Google Imagenes, blogs ni webs de
turismo).

Uso: python tools/download_photos_planes_familia_a_coruna.py
"""
import pathlib
import urllib.request

BASE = pathlib.Path(__file__).resolve().parent.parent
DST = BASE / "images/planes-familia/a-coruna"

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0 Safari/537.36")


def pexels(pid, w=1600):
    return ("https://images.pexels.com/photos/%d/pexels-photo-%d.jpeg"
            "?auto=compress&cs=tinysrgb&w=%d" % (pid, pid, w))


JOBS = [
    ("aquarium-finisterrae.jpg", pexels(36466275)),
    ("casa-de-las-ciencias.jpg", pexels(39246215)),
    ("domus.jpg", pexels(12471787)),
    ("monte-de-san-pedro.jpg",
     "https://cdn.pixabay.com/photo/2020/05/02/15/17/monte-san-pedro-5121819_1280.jpg"),
    ("muncyt.jpg", pexels(9141491)),
    ("casa-grande-de-xanceda.jpg", pexels(33037023)),
    ("torre-de-hercules.jpg",
     "https://cdn.pixabay.com/photo/2019/03/04/16/41/the-tower-of-hercules-4034593_1280.jpg"),
    ("corax-fauna.jpg", pexels(37346934)),
    ("termaria.jpg", pexels(5603212)),
    ("parque-de-eiris.jpg", pexels(34353411)),
    ("fervenza-do-ezaro.jpg",
     "https://cdn.pixabay.com/photo/2019/07/21/15/00/waterfall-4352913_1280.jpg"),
    ("aquapark-cerceda.jpg", pexels(31181782)),
    ("fragas-do-eume.jpg", pexels(36846068)),
    ("naturmaz.jpg", pexels(36663043)),
    ("castillo-de-san-anton.jpg", pexels(30042444)),
]


def main():
    DST.mkdir(parents=True, exist_ok=True)
    for name, url in JOBS:
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=60) as r:
            data = r.read()
        (DST / name).write_bytes(data)
        print("%-32s %8d bytes" % (name, len(data)))


if __name__ == "__main__":
    main()
