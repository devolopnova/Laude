"""Descarga a una carpeta temporal varias candidatas de la galeria del
Titan S para poder mirarlas y elegir la que cumpla la regla de imagen
(silla sola, foto limpia). No toca images/sillas-coche/ todavia.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import amazon_sillas_coche as ex

GALERIA = Path(__file__).resolve().parent / "output/_tmp_titan_s_galeria.json"
DESTINO = Path(__file__).resolve().parent / "output/_titan_s_candidatas"


def main():
    urls = json.loads(GALERIA.read_text(encoding="utf-8"))
    grandes = [u for u in urls if "_AC_SL1500_" in u]
    DESTINO.mkdir(parents=True, exist_ok=True)
    for i, u in enumerate(grandes[:10]):
        destino = DESTINO / f"cand_{i:02d}.jpg"
        try:
            ex.download_image(u, str(destino))
            ex.convert_to_webp(str(destino))
            print(f"[OK] {i} -> {destino.with_suffix('.webp').name}")
        except Exception as e:
            print(f"[WARN] {i}: {e}")


if __name__ == "__main__":
    main()
