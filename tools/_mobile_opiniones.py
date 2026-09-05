#!/usr/bin/env python3
"""Anade el texto de 'Lo que destacan las familias' al override de movil,
para que use el mismo gris #6B6B70 que el resto del texto pequeno."""
import pathlib

FILES = """sillitas-de-coche sillas-coche-isofix
silla-coche-grupo-0-recien-nacido sillas-coche-grupo-1-2-3
alzadores-elevadores-coche sillas-coche-cybex sillas-coche-maxi-cosi
sillas-coche-britax-romer sillas-coche-chicco sillas-coche-nania
sillas-coche-jovikids sillas-coche-kinderkraft sillas-coche-babyauto
sillas-coche-lionelo sillas-coche-kikkaboo sillas-coche-graco
otras-marcas-sillas-coche normativa-dgt-i-size-sillas-coche
silla-coche-a-contramarcha silla-coche-giratoria-360
alquiler-sillas-coche-segunda-mano""".split()

OLD = "    body.scp-page .scp-disclaimer{color:#6B6B70;}"
NEW = ("    body.scp-page .scp-disclaimer,\n"
       "    body.scp-page .sc-ficha-opiniones-text{color:#6B6B70;}")

done, skipped = [], []
for name in FILES:
    p = pathlib.Path(name + ".html")
    t = p.read_text(encoding="utf-8")
    if "sc-ficha-opiniones-text{color:#6B6B70" in t:
        skipped.append(name + " (ya aplicado)")
        continue
    if OLD not in t:
        skipped.append(name + " (ANCLA NO ENCONTRADA)")
        continue
    p.write_text(t.replace(OLD, NEW, 1), encoding="utf-8")
    done.append(name)

out = ["APLICADO (%d)" % len(done), "OMITIDO (%d):" % len(skipped)]
out += ["  " + s for s in skipped]
pathlib.Path("tools/output/_tmp_mobile_op.txt").write_text(
    "\n".join(out), encoding="utf-8")
print("aplicado:", len(done), "| omitido:", len(skipped))
