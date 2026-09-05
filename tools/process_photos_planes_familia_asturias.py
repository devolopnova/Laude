"""Procesa las 15 fotos de "Planes en familia - Asturias" (originales en
images/planes-familia/asturias/_originals/*.jpg|png, descargadas de
Pexels/Unsplash) a WebP, redimensionadas SIN recorte fisico, preservando
la proporcion natural de cada fotografia, para la tarjeta .pfb-card de
planes-en-familia-asturias.html.

Mismo patron exacto que tools/process_photos_planes_familia_castellon.py
(SHORT_SIDE=1000, calidad 82, metodo 6).

Asturias es una comunidad autonoma uniprovincial: existen dos paginas
separadas, planes-en-familia-asturias.html (pagina de provincia, con las
15 fichas de este script) y planes-en-familia-principado-de-asturias.html
(hub de CCAA con 1 sola tarjeta, enlazando a la de provincia) -- igual
patron que Madrid (planes-en-familia-madrid.html / -comunidad-madrid.html).

Origen de cada foto (12/15 son fallback tematico generico porque no se
encontro foto literal del lugar concreto en Pexels/Unsplash/Pixabay para
sitios locales/pequenos asturianos; ver informe entregado al usuario --
2 de esas 15 se sustituyeron despues por fotos literales aportadas
directamente por el usuario, ver bufones-de-pria y ecomuseo-minero-samuno
mas abajo):
- muja.jpg: fosil/craneo de dinosaurio sobre roca (Unsplash) - generico.
- acuario-de-gijon.jpg: peces en acuario con plantas (Pexels) - generico.
- senda-del-oso.jpg: dos osos pardos en el agua (Pexels) - generico.
- funicular-de-bulnes.jpg: teleferico ascendiendo montana verde (Unsplash)
  - generico.
- parque-prehistoria-teverga.jpg: petroglifo/grabado rupestre de ciervo en
  roca (Unsplash) - generico.
- ecomuseo-minero-samuno: sustituida el 05/09/2026 por una foto LITERAL
  real de una galeria minera con el tren naranja del ecomuseo, aportada
  directamente por el usuario (guardada en su Escritorio como mina.png,
  original conservado en _originals/ecomuseo-minero-samuno-original.png,
  941x1672, mismas dimensiones que bufon.png). Ya no es la generica de
  tren minero oxidado entre vegetacion (Unsplash) descrita antes.
  Historial de recortes el mismo dia: (1) retrato 1000x1501 -- el tren se
  veia completo, pero el usuario pidio homogeneizar tamanos con
  parque-prehistoria-teverga.webp/cosmocaixa.webp (paisaje 1500x1000);
  (2) se avisexplicitamente de que el tren esta compuesto a ~10px del
  borde derecho REAL de la foto original, y que .pfb-photo (contenedor
  mas alto que ancho, ratio ~0.77) con object-fit:cover solo deja ver el
  ~51% central del ancho de una imagen 1500x1000 -- geometricamente
  incompatible con mostrar el tren completo Y en paisaje a la vez; (3) el
  usuario, informado del trade-off, opto explicitamente por "recorta el
  tren" -- version FINAL: center-crop vertical 941x627 (centrado en la
  zona de la via/tren, y=487 a 1114) + resize a 1500x1000. El tren se ve
  en el lateral derecho del archivo pero su cabina se recorta mas al
  mostrarse dentro de la tarjeta real (aceptado a proposito). Ver
  [[feedback_planes_familia_pfb_photo_cover_crop]] en memoria para la
  explicacion completa de por que un sujeto pegado al borde no sobrevive
  al recorte panoramico de esta tarjeta.
- tito-bustillo.jpg: pintura rupestre de caballo sobre roca (Unsplash) -
  generico.
- bufones-de-pria: sustituida el 05/09/2026 por una foto LITERAL real del
  bufon en plena erupcion, aportada directamente por el usuario (guardada
  en su Escritorio como bufon.png, original conservado en
  _originals/bufones-de-pria-original.png, 941x1672, formato retrato muy
  alto/estrecho). Ya no es la generica de olas contra acantilado de
  basalto (Unsplash) descrita antes. Recortada el mismo dia: primer
  intento a ratio 0.667 (1000x1501, como casa-del-lobo/senda-del-oso) fue
  sustituido por indicacion expresa del usuario para usar como referencia
  el tamano de parque-prehistoria-teverga.webp (1500x1000, paisaje) en vez
  de las fotos retrato -- center-crop vertical (941x627 centrado) seguido
  de resize a 1500x1000 exactos. Ecomuseo-minero-samuno (ver mas abajo) se
  ajusto igual el mismo dia, mismo criterio de tamano de referencia.
- circuito-fernando-alonso.jpg: vista aerea de circuito de karting
  (Unsplash) - generico.
- museo-del-oro.jpg: manos con bateas lavando oro en un canal de agua
  (Pexels) - generico.
- casa-del-lobo.jpg: retrato de lobo en bosque (Pexels) - generico.
- los-caserinos.jpg: dos cabras blancas en granja verde (Pexels) -
  generico.
- camin-encantau.jpg: sendero de bosque verde (Pexels) - generico.
- jardin-botanico-gijon.jpg: camino de piedra entre helechos verdes
  (Unsplash) - generico.
- mumi.jpg: galeria de mina iluminada con vigas de madera (Unsplash) -
  generico.

Uso: python tools/process_photos_planes_familia_asturias.py
"""
import pathlib
from PIL import Image

SRC = pathlib.Path(__file__).resolve().parent.parent / "images/planes-familia/asturias"
ORIG = SRC / "_originals"
SHORT_SIDE = 1000

FILES = [
    "muja.jpg",
    "acuario-de-gijon.jpg",
    "senda-del-oso.jpg",
    "funicular-de-bulnes.jpg",
    "parque-prehistoria-teverga.jpg",
    "ecomuseo-minero-samuno.jpg",
    "tito-bustillo.jpg",
    "bufones-de-pria.jpg",
    "circuito-fernando-alonso.jpg",
    "museo-del-oro.jpg",
    "casa-del-lobo.jpg",
    "los-caserinos.jpg",
    "camin-encantau.png",
    "jardin-botanico-gijon.jpg",
    "mumi.jpg",
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
        src_path = ORIG / fname
        im = Image.open(src_path).convert("RGB")
        out = resize_preserving_aspect(im, SHORT_SIDE)
        out_name = fname.rsplit(".", 1)[0] + ".webp"
        out_path = SRC / out_name
        out.save(out_path, "WEBP", quality=82, method=6)
        print(f"{fname} -> {out_name} ({out.size[0]}x{out.size[1]}, {out_path.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
