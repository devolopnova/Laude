"""Descarga la imagen principal de los 8 Maxi-Cosi seleccionados,
reutilizando las funciones del extractor (misma descarga, misma
conversion a WebP 600x600 sin deformar) -- no duplica esa logica.

La busqueda se lanzo con --no-images, asi que solo faltaban las fotos;
el resto de datos (caracteristicas, clasificacion, opiniones) ya esta en
tools/output/_tmp_maxicosi_busqueda.json.

Las fotos quedan como images/sillas-coche/<ASIN>.webp, que es la
convencion que espera el generador del comparador. HAY QUE REVISARLAS a
mano contra la regla de imagenes de CLAUDE.md (silla sola, sin ninos,
sin caja, sin banners) antes de darlas por buenas.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import amazon_sillas_coche as ex
from playwright.sync_api import sync_playwright

SELECCION = [
    "B07RP2XR8J",  # Kore i-Size
    "B0CKZC1WZG",  # RodiFix M i-Size
    "B09LVM4ZF5",  # CabrioFix i-Size
    "B0CHYBHS31",  # Nomad Plus
    "B0CZ12Q54X",  # Titan S i-Size
    "B09BDJ6G8B",  # Pebble 360
    "B0BXY35J5N",  # Mica Pro Eco i-Size
    "B0DJBR1TYR",  # Mica 360 S
]

FUENTE = Path(__file__).resolve().parent / "output/_tmp_maxicosi_busqueda.json"
SALIDA = Path(__file__).resolve().parent / "output/_tmp_maxicosi_imagenes.json"


def main():
    datos = json.loads(FUENTE.read_text(encoding="utf-8"))
    por_asin = {p["asin"]: p for p in datos["productos"]}
    resultado = {}

    with sync_playwright() as pw:
        navegador = pw.chromium.launch(headless=True)
        contexto = navegador.new_context(
            user_agent=ex.USER_AGENT, locale="es-ES", viewport={"width": 1366, "height": 900}
        )
        pagina = contexto.new_page()
        ex.warmup_session(pagina)

        for asin in SELECCION:
            producto = por_asin[asin]
            try:
                pagina.goto(producto["url"], wait_until="domcontentloaded", timeout=60000)
                pagina.wait_for_timeout(1800)
                url_img = ex.get_main_image_url(pagina)
                if not url_img:
                    print(f"[WARN] {asin}: sin imagen localizable")
                    resultado[asin] = None
                    continue
                ruta = ex.download_and_process_image(url_img, asin, None)
                resultado[asin] = ruta
                print(f"[OK] {asin} -> {ruta}")
            except Exception as e:
                print(f"[WARN] {asin}: {e}")
                resultado[asin] = None

        navegador.close()

    SALIDA.write_text(json.dumps(resultado, ensure_ascii=False, indent=1), encoding="utf-8")
    print("\nGuardado en", SALIDA)


if __name__ == "__main__":
    main()
