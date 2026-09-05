"""Descarga la imagen principal de una lista de ASIN a partir de un JSON
de busqueda del extractor, reutilizando sus funciones (misma descarga,
misma conversion a WebP 600x600 sin deformar).

Uso:
    python tools/_fetch_marca_images.py <json_busqueda> <ASIN> [ASIN ...]

Las fotos quedan como images/sillas-coche/<ASIN>.webp, que es la
convencion que espera el generador del comparador. HAY QUE REVISARLAS a
mano contra la regla de imagenes de CLAUDE.md (silla sola, sin ninos,
sin caja, sin textos promocionales) antes de darlas por buenas.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import amazon_sillas_coche as ex
from playwright.sync_api import sync_playwright


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)
    fuente = Path(sys.argv[1])
    asins = sys.argv[2:]

    datos = json.loads(fuente.read_text(encoding="utf-8"))
    por_asin = {p["asin"]: p for p in datos["productos"]}

    with sync_playwright() as pw:
        navegador = pw.chromium.launch(headless=True)
        contexto = navegador.new_context(
            user_agent=ex.USER_AGENT, locale="es-ES", viewport={"width": 1366, "height": 900}
        )
        pagina = contexto.new_page()
        ex.warmup_session(pagina)

        for asin in asins:
            producto = por_asin.get(asin)
            if not producto:
                print(f"[WARN] {asin}: no esta en {fuente.name}")
                continue
            try:
                pagina.goto(producto["url"], wait_until="domcontentloaded", timeout=60000)
                pagina.wait_for_timeout(1800)
                url_img = ex.get_main_image_url(pagina)
                if not url_img:
                    print(f"[WARN] {asin}: sin imagen localizable")
                    continue
                ruta = ex.download_and_process_image(url_img, asin, None)
                print(f"[OK] {asin} -> {ruta}")
            except Exception as e:
                print(f"[WARN] {asin}: {e}")

        navegador.close()


if __name__ == "__main__":
    main()
