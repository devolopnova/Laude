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

REPLACEMENTS = [
    (
        """  body.scp-page .sc-ficha-specs-title{
    font-family:'JetBrains Mono',monospace;font-size:11.5px;font-weight:700;
    color:var(--ink);text-transform:uppercase;letter-spacing:.06em;margin-bottom:16px;
  }""",
        """  body.scp-page .sc-ficha-specs-title{
    font-family:'Inter',sans-serif;font-size:11.5px;font-weight:700;
    color:var(--ink);text-transform:uppercase;letter-spacing:.06em;margin-bottom:16px;
  }""",
    ),
    (
        """  body.scp-page .sc-ficha-opiniones-head{
    font-family:'JetBrains Mono',monospace;font-size:11.5px;font-weight:700;
    color:var(--ink);text-transform:uppercase;letter-spacing:.06em;margin-bottom:10px;
  }""",
        """  body.scp-page .sc-ficha-opiniones-head{
    font-family:'Inter',sans-serif;font-size:11.5px;font-weight:700;
    color:var(--ink);text-transform:uppercase;letter-spacing:.06em;margin-bottom:10px;
  }""",
    ),
]

changed = []
for name in FILES:
    p = ROOT / name
    text = p.read_text(encoding="utf-8")
    ok = True
    for old, new in REPLACEMENTS:
        count = text.count(old)
        if count != 1:
            print(f"SKIP {name}: found {count} occurrences of one block (expected 1)")
            ok = False
            break
        text = text.replace(old, new)
    if ok:
        p.write_text(text, encoding="utf-8")
        changed.append(name)

print(f"Cambiados {len(changed)}/{len(FILES)}")
