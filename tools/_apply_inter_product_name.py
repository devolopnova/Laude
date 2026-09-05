import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent

FILES = [
    "alquiler-sillas-coche-segunda-mano.html",
    "alzadores-elevadores-coche.html",
    "normativa-dgt-i-size-sillas-coche.html",
    "otras-marcas-sillas-coche.html",
    "silla-coche-a-contramarcha.html",
    "silla-coche-giratoria-360.html",
    "silla-coche-grupo-0-recien-nacido.html",
    "sillas-coche-babyauto.html",
    "sillas-coche-britax-romer.html",
    "sillas-coche-chicco.html",
    "sillas-coche-cybex.html",
    "sillas-coche-graco.html",
    "sillas-coche-grupo-1-2-3.html",
    "sillas-coche-isofix.html",
    "sillas-coche-jovikids.html",
    "sillas-coche-kikkaboo.html",
    "sillas-coche-kinderkraft.html",
    "sillas-coche-lionelo.html",
    "sillas-coche-maxi-cosi.html",
    "sillas-coche-nania.html",
]

OLD = """  body.scp-page .sc-ficha-name{
    font-family:'Playfair Display',serif;font-weight:700;font-size:24px;margin-top:4px;
  }"""

NEW = """  body.scp-page .sc-ficha-name{
    font-size:24px;margin-top:4px;
  }"""

changed = []
for name in FILES:
    p = ROOT / name
    text = p.read_text(encoding="utf-8")
    count = text.count(OLD)
    if count != 1:
        print(f"SKIP {name}: found {count} occurrences (expected 1)")
        continue
    text = text.replace(OLD, NEW)
    p.write_text(text, encoding="utf-8")
    changed.append(name)

print(f"Cambiados {len(changed)}/{len(FILES)}")
