"""La imagen principal del Titan S i-Size (B0CZ12Q54X) es una
composicion con 3 vistas de la silla, y la regla de imagenes de
CLAUDE.md exige una foto limpia de UNA sola silla. Este script lista las
imagenes alternativas de la galeria del propio anuncio para poder elegir
una que si cumpla (no descarga nada todavia: primero hay que mirarlas).
"""
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import amazon_sillas_coche as ex
from playwright.sync_api import sync_playwright

ASIN = "B0CZ12Q54X"
FUENTE = Path(__file__).resolve().parent / "output/_tmp_maxicosi_busqueda.json"
SALIDA = Path(__file__).resolve().parent / "output/_tmp_titan_s_galeria.json"


def main():
    datos = json.loads(FUENTE.read_text(encoding="utf-8"))
    producto = next(p for p in datos["productos"] if p["asin"] == ASIN)

    with sync_playwright() as pw:
        navegador = pw.chromium.launch(headless=True)
        contexto = navegador.new_context(
            user_agent=ex.USER_AGENT, locale="es-ES", viewport={"width": 1366, "height": 900}
        )
        pagina = contexto.new_page()
        ex.warmup_session(pagina)
        pagina.goto(producto["url"], wait_until="domcontentloaded", timeout=60000)
        pagina.wait_for_timeout(2500)

        # Las miniaturas de la galeria llevan una url de baja resolucion;
        # la de alta se obtiene quitando el sufijo de tamano (_SX38_SY50_
        # etc.) que Amazon mete en el nombre del archivo.
        urls = []
        for el in pagina.query_selector_all("#altImages li img, #imageBlock img"):
            src = el.get_attribute("src") or ""
            if not src or "sprite" in src or "play-button" in src:
                continue
            alta = re.sub(r"\._[^.]+_\.", ".", src)
            if alta not in urls:
                urls.append(alta)

        # Tambien el JSON incrustado del visor, que trae las variantes
        # grandes ya listadas.
        html = pagina.content()
        for m in re.findall(r'"hiRes":"(https://[^"]+?)"', html):
            u = m.replace("\\/", "/")
            if u not in urls:
                urls.append(u)

        navegador.close()

    SALIDA.write_text(json.dumps(urls, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{len(urls)} imagenes encontradas")
    for i, u in enumerate(urls):
        print(i, u)


if __name__ == "__main__":
    main()
