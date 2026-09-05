"""Busca fotos limpias de producto en la web OFICIAL de Kinderkraft para
los modelos cuya imagen de Amazon es una composicion de varias vistas o
lleva textos promocionales (incumple la regla de imagen de CLAUDE.md,
que permite recurrir a la ficha del fabricante como alternativa).

Deja las candidatas en tools/output/_candidatas_oficial/<ASIN>/ para
revisarlas a ojo antes de usar ninguna.
"""
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import amazon_sillas_coche as ex
from playwright.sync_api import sync_playwright

DESTINO = Path(__file__).resolve().parent / "output/_candidatas_oficial"

# ASIN -> posibles URL de la ficha oficial (se prueba en orden hasta que
# una cargue). El patron /productos/<slug> es el que ya usaba la entrada
# de I-COMFY en tools/fabricante_lookup.json.
OBJETIVOS = {
    "B0DSL7WGB2": ["https://kinderkraft.es/productos/unity-2", "https://kinderkraft.es/productos/unity2"],
    "B0DP7TRLX6": ["https://kinderkraft.es/productos/fix2go", "https://kinderkraft.es/productos/fix-2-go"],
    "B0DNRCJ8MX": ["https://kinderkraft.es/productos/xrider-2", "https://kinderkraft.es/productos/xrider2"],
    "B0DNRBWB1Q": ["https://kinderkraft.es/productos/xpedition-3", "https://kinderkraft.es/productos/xpedition3"],
}


def main():
    with sync_playwright() as pw:
        navegador = pw.chromium.launch(headless=True)
        contexto = navegador.new_context(
            user_agent=ex.USER_AGENT, locale="es-ES", viewport={"width": 1366, "height": 900}
        )
        pagina = contexto.new_page()

        for asin, urls in OBJETIVOS.items():
            cargada = None
            for url in urls:
                try:
                    resp = pagina.goto(url, wait_until="domcontentloaded", timeout=45000)
                    if resp and resp.status < 400:
                        cargada = url
                        break
                except Exception:
                    continue
            if not cargada:
                print(f"[WARN] {asin}: no he podido abrir ninguna URL oficial")
                continue

            pagina.wait_for_timeout(2500)
            html = pagina.content()
            imgs = []
            for m in re.findall(r'https://[^"\'\s]+?\.(?:jpg|jpeg|png|webp)', html):
                if any(x in m.lower() for x in ("logo", "icon", "sprite", "banner", "flag")):
                    continue
                if m not in imgs:
                    imgs.append(m)

            carpeta = DESTINO / asin
            carpeta.mkdir(parents=True, exist_ok=True)
            guardadas = 0
            for u in imgs:
                if guardadas >= 8:
                    break
                try:
                    jpg = carpeta / f"of_{guardadas:02d}.jpg"
                    ex.download_image(u, str(jpg))
                    if jpg.stat().st_size < 15000:  # miniaturas/iconos
                        jpg.unlink(missing_ok=True)
                        continue
                    ex.convert_to_webp(str(jpg))
                    jpg.unlink(missing_ok=True)
                    guardadas += 1
                except Exception:
                    continue
            (carpeta / "fuente.json").write_text(
                json.dumps({"url": cargada, "imagenes": imgs[:20]}, ensure_ascii=False, indent=1),
                encoding="utf-8",
            )
            print(f"[OK] {asin}: {guardadas} candidatas de {cargada}")

        navegador.close()


if __name__ == "__main__":
    main()
