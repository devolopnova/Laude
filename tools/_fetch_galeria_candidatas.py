"""Descarga candidatas de la galeria de Amazon de uno o varios ASIN, para
poder mirarlas y elegir una que cumpla la regla de imagen de CLAUDE.md
(silla sola, foto limpia, sin textos ni composiciones de varias vistas).

No toca images/sillas-coche/: deja las candidatas en
tools/output/_candidatas/<ASIN>/cand_NN.webp para revisarlas primero.

Uso:
    python tools/_fetch_galeria_candidatas.py <json_busqueda> <ASIN> [ASIN ...]
"""
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import amazon_sillas_coche as ex
from playwright.sync_api import sync_playwright

DESTINO = Path(__file__).resolve().parent / "output/_candidatas"


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
                pagina.wait_for_timeout(2500)
                html = pagina.content()
                urls = []
                for m in re.findall(r'"hiRes":"(https://[^"]+?)"', html):
                    u = m.replace("\\/", "/")
                    if u not in urls:
                        urls.append(u)
                carpeta = DESTINO / asin
                carpeta.mkdir(parents=True, exist_ok=True)
                for i, u in enumerate(urls[:8]):
                    jpg = carpeta / f"cand_{i:02d}.jpg"
                    ex.download_image(u, str(jpg))
                    ex.convert_to_webp(str(jpg))
                    jpg.unlink(missing_ok=True)
                (carpeta / "urls.json").write_text(
                    json.dumps(urls, ensure_ascii=False, indent=1), encoding="utf-8"
                )
                print(f"[OK] {asin}: {min(len(urls), 8)} candidatas en {carpeta}")
            except Exception as e:
                print(f"[WARN] {asin}: {e}")

        navegador.close()


if __name__ == "__main__":
    main()
