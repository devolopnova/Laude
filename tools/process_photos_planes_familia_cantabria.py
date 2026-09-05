"""Procesa las 15 fotos de "Planes en familia - Cantabria" (originales en
images/planes-familia/cantabria/*.jpg, descargadas de Pexels/Pixabay) a
WebP, redimensionadas SIN recorte fisico, preservando la proporcion
natural de cada fotografia, para la tarjeta .pfb-card de
planes-en-familia-cantabria.html.

Mismo patron exacto que tools/process_photos_planes_familia_castellon.py
(SHORT_SIDE=1000, calidad 82, metodo 6).

**Actualizacion 05/09/2026**: a peticion del usuario, se homogeneizaron
13 de las 15 fotos a exactamente 1500x1000 (mismo tamano que
cosmocaixa.webp de Barcelona), con recorte centrado en el sujeto
principal de cada foto quando hizo falta reencuadrar desde un original
retrato o de otra proporcion (capricho-gaudi, museo-altamira,
parque-cabarceno solo necesitaron un recorte minimo; centro-botin,
ecomuseo-fluviarium, jardines-pereda, museo-maritimo-cantabrico,
palacio-magdalena y teleferico-fuente-de venian en formato retrato y se
recortaron centrando el sujeto). **forestal-park-santander y estacion-esqui-alto-campoo** se dejaron
primero en formato retrato por el mismo motivo que ecomuseo-minero-samuno
en Asturias (sujeto pegado a un borde real de la foto, incompatible con
sobrevivir al ~51% central que deja visible object-fit:cover en
.pfb-photo -- ver [[feedback_planes_familia_pfb_photo_cover_crop]]), pero
el usuario, avisado del trade-off, pidio explicitamente forzarlas tambien
a 1500x1000 el mismo dia. Resultado: las 15 fotos de Cantabria estan en
1500x1000 exactos. forestal-park-santander recorto center-crop vertical
941x627 (top=575, con sesgo hacia abajo para priorizar el puente
colgante sobre la copa de arboles) + resize -- verificado visualmente que
el puente sobrevive bien, sin mas ajustes.

estacion-esqui-alto-campoo tuvo una historia larga el mismo dia: (1)
recorte generico 1600x1067 (top=256) -- el usuario confirmo con una
captura de pantalla real de la tarjeta que el telesilla NO se veia en
absoluto (solo cielo vacio), mas agresivo de lo estimado; (2) recorte
muy cerrado sobre el asiento (box 1132,424,1600,736) -- demasiado zoom,
"se ve conmucho zoom"; (3-4) dos vueltas mas alejando el zoom
progresivamente (box 850,300,1600,800 y luego 700,250,1600,850) -- en la
ultima el usuario pidio "que se vea la silla mas entera", pero alejar el
zoom sobre ESTE original (1600x2133) empuja la silla cada vez mas hacia
el borde derecho real de la foto (no hay mas contenido despues de
x=1600), reintroduciendo el riesgo de que la tarjeta real la vuelva a
cortar. **Solucion definitiva**: el usuario aporto una foto NUEVA y
mejor compuesta directamente (guardada en su Escritorio como eq.png,
original conservado en _originals/estacion-esqui-alto-campoo-original.png,
1448x1086) -- telesilla con 4 esquiadores, centrado horizontalmente con
margen real a ambos lados (a diferencia del original de Pexels, donde el
telesilla estaba pegado al borde). Recorte trivial: center-crop vertical
1448x965 (top=60) + resize a 1500x1000, sin necesidad de zoom agresivo
porque la composicion ya viene centrada. Leccion para el futuro: si tras
2-3 intentos de recrop una foto generica sigue sin encajar bien en el
hueco seguro del ~51% central, es mas eficiente pedir/usar una foto con
mejor composicion (sujeto centrado de origen) que seguir iterando sobre
un recorte imposible.

Origen de cada foto (Pexels salvo indicacion contraria; Pixabay para
parque-cabarceno... no, ver detalle por archivo mas abajo):
- parque-cabarceno.jpg: Unsplash, foto literal de una familia de
  elefantes caminando por un sendero en Cabarceno.
- palacio-magdalena.jpg: Unsplash, foto literal de la fachada del
  Palacio de la Magdalena en Santander.
- teleferico-fuente-de.jpg: Pexels, foto GENERICA de un teleferico rojo
  sobre una montana verde/rocosa (no se encontro foto literal del
  teleferico de Fuente De).
- forestal-park-santander: sustituida el 05/09/2026 por una foto LITERAL
  real del circuito de arbolismo (torres de madera, puente de red y
  pasarelas colgantes entre arboles), aportada directamente por el
  usuario (guardada en su Escritorio como sant.png, original conservado
  en _originals/forestal-park-santander-original.png, 941x1672, formato
  retrato). Ya no es la generica de puente colgante de cuerda/madera
  (Pexels) descrita antes. Procesada en formato retrato (center-crop
  vertical 941x1412 + resize a 1000x1501, mismo patron que
  casa-del-lobo/senda-del-oso de Asturias) en vez de forzar un tamano
  paisaje tipo Teverga: la composicion tiene elementos importantes en
  ambos bordes laterales (torre+puente de red a la izquierda, plataforma
  a la derecha), asi que un recorte paisaje los habria cortado -- ver
  [[feedback_planes_familia_pfb_photo_cover_crop]] en memoria.
- museo-maritimo-cantabrico.jpg: Pexels, foto GENERICA de un acuario con
  peces (no se encontro foto literal del Museo Maritimo del Cantabrico).
- cueva-el-soplao.jpg: Pexels, foto GENERICA de un interior de cueva con
  formaciones rocosas iluminadas (no se encontro foto literal de El
  Soplao).
- museo-altamira.jpg: Pixabay, foto literal del bisonte polícromo de
  las pinturas rupestres de Altamira.
- laberinto-villapresente.jpg: Pexels, foto GENERICA de un laberinto de
  seto visto de cerca (no se encontro foto literal del Laberinto de
  Villapresente).
- ecomuseo-fluviarium.jpg: Pexels, foto GENERICA de una nutria de rio
  nadando en un arroyo de bosque (no se encontro foto literal del
  Fluviarium de Lierganes).
- capricho-gaudi.jpg: Pexels, foto literal de El Capricho de Gaudi en
  Comillas.
- centro-botin.jpg: Pexels, foto literal del Centro Botin en Santander.
- zoo-santillana.jpg: Pexels, foto GENERICA de un orangutan (especie
  emblematica del zoo, no se encontro foto literal del Zoologico de
  Santillana del Mar).
- jardines-pereda.jpg: Pexels, foto GENERICA de un arbol maduro en un
  cesped junto a un puerto deportivo (no se encontro foto literal de
  los Jardines de Pereda).
- reserva-saja-besaya.jpg: Pexels, foto GENERICA de montanas boscosas
  verdes (no se encontro foto literal de la Reserva del Saja-Besaya).
- estacion-esqui-alto-campoo.jpg: Pexels, foto GENERICA de un telesilla
  sobre una pista de esqui nevada (no se encontro foto literal de Alto
  Campoo).

Uso: python tools/process_photos_planes_familia_cantabria.py
"""
import pathlib
from PIL import Image

SRC = pathlib.Path(__file__).resolve().parent.parent / "images/planes-familia/cantabria"
SHORT_SIDE = 1000

FILES = [
    "parque-cabarceno.jpg",
    "palacio-magdalena.jpg",
    "teleferico-fuente-de.jpg",
    "forestal-park-santander.jpg",
    "museo-maritimo-cantabrico.jpg",
    "cueva-el-soplao.jpg",
    "museo-altamira.jpg",
    "laberinto-villapresente.jpg",
    "ecomuseo-fluviarium.jpg",
    "capricho-gaudi.jpg",
    "centro-botin.jpg",
    "zoo-santillana.jpg",
    "jardines-pereda.jpg",
    "reserva-saja-besaya.jpg",
    "estacion-esqui-alto-campoo.jpg",
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
