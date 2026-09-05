#!/usr/bin/env python3
"""
Script temporal, NO parte del pipeline permanente del proyecto.
Recolecta miniaturas de las imagenes de galeria de Amazon para los ASIN
indicados y genera un contact-sheet (PIL) por producto, para revision
visual rapida antes de elegir la imagen final (regla permanente de
CLAUDE.md: unica foto limpia, sin collage, sin personas, sin texto).
No descarga ni sustituye nada en images/sillas-coche/ todavia.
"""
import importlib.util
import json
import os
import re
import sys
import time
from urllib.request import Request, urlopen

sys.path.insert(0, os.path.dirname(__file__))
spec = importlib.util.spec_from_file_location("amazon_sillas_coche", os.path.join(os.path.dirname(__file__), "amazon_sillas_coche.py"))
asc = importlib.util.module_from_spec(spec)
spec.loader.exec_module(asc)

from playwright.sync_api import sync_playwright
from playwright_stealth import Stealth
from PIL import Image, ImageDraw, ImageFont

OUT_DIR = "tools/output/img_review"
os.makedirs(OUT_DIR, exist_ok=True)

ASINS = sys.argv[1:]

def extract_gallery_urls(html: str):
    hires = re.findall(r'"hiRes":"(https://[^"]+?\.(?:jpg|png))"', html)
    large = re.findall(r'"large":"(https://[^"]+?\.(?:jpg|png))"', html)
    urls = []
    seen = set()
    for u in hires + large:
        u2 = u.replace("\\/", "/")
        if u2 not in seen:
            seen.add(u2)
            urls.append(u2)
    return urls


def download(url: str, dest: str) -> bool:
    try:
        req = Request(url, headers={"User-Agent": asc.USER_AGENT})
        with urlopen(req, timeout=20) as r:
            data = r.read()
        with open(dest, "wb") as f:
            f.write(data)
        return True
    except Exception as e:
        print(f"    fallo descarga {url}: {e}")
        return False


def build_contact_sheet(asin: str, thumb_paths):
    cell = 220
    cols = 4
    rows = (len(thumb_paths) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * cell, rows * cell), (240, 240, 240))
    draw = ImageDraw.Draw(sheet)
    for i, p in enumerate(thumb_paths):
        try:
            im = Image.open(p).convert("RGB")
            im.thumbnail((cell - 20, cell - 40))
            x = (i % cols) * cell + (cell - im.width) // 2
            y = (i // cols) * cell + 10
            sheet.paste(im, (x, y))
            draw.rectangle([( i % cols)*cell, (i//cols)*cell, (i%cols)*cell+cell-1, (i//cols)*cell+cell-1], outline=(180,180,180))
            draw.text(((i % cols) * cell + 8, (i // cols) * cell + cell - 24), f"#{i}", fill=(0,0,0))
        except Exception as e:
            print(f"    fallo miniatura {p}: {e}")
    out_path = os.path.join(OUT_DIR, f"{asin}_sheet.png")
    sheet.save(out_path)
    return out_path


def main():
    asc.ensure_playwright_installed()
    asc.ensure_playwright_stealth_installed()
    manifest = {}
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(user_agent=asc.USER_AGENT, viewport={"width": 1280, "height": 900}, locale="es-ES")
        Stealth().apply_stealth_sync(context)
        page = context.new_page()
        try:
            asc.warmup_session(page)
        except Exception as e:
            print("warmup fallo (continuo igual):", e)

        for asin in ASINS:
            print(f"=== {asin} ===")
            url = f"https://www.amazon.es/dp/{asin}"
            try:
                page.goto(url, wait_until="domcontentloaded", timeout=45000)
                page.wait_for_timeout(1500)
            except Exception as e:
                print(f"  fallo navegando: {e}")
                manifest[asin] = {"error": str(e)}
                continue
            html = page.content()
            urls = extract_gallery_urls(html)
            if not urls:
                print("  sin galeria detectada")
                manifest[asin] = {"urls": [], "sheet": None}
                continue
            urls = urls[:12]
            asin_dir = os.path.join(OUT_DIR, asin)
            os.makedirs(asin_dir, exist_ok=True)
            thumb_paths = []
            for i, u in enumerate(urls):
                dest = os.path.join(asin_dir, f"{i}.jpg")
                if download(u, dest):
                    thumb_paths.append(dest)
            if thumb_paths:
                sheet_path = build_contact_sheet(asin, thumb_paths)
                print(f"  {len(thumb_paths)} imagenes -> {sheet_path}")
            else:
                sheet_path = None
                print("  ninguna imagen descargada")
            manifest[asin] = {"urls": urls, "sheet": sheet_path}
            time.sleep(1.2)

        browser.close()

    with open(os.path.join(OUT_DIR, "_manifest.json"), "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)
    print("Manifest guardado en", os.path.join(OUT_DIR, "_manifest.json"))


if __name__ == "__main__":
    main()
