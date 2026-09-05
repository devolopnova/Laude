#!/usr/bin/env python3
"""Script temporal. En movil (<=560px) devuelve el texto pequeno de las
paginas de sillitas al gris anterior #6B6B70: en pantalla pequena el
var(--ink) + weight 500 se percibia demasiado pesado.

Solo afecta al cuerpo de texto (parrafos, listas, FAQ, disclaimer), NO a
las fichas de producto ni a los titulares.

Nota de especificidad: para .scp-lead hace falta el selector largo
(body.scp-page .scp-section > p.scp-lead), porque la regla base
.scp-section > p.scp-lead empata en especificidad y va DESPUES en el
archivo, asi que ganaria.
"""
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

ANCHOR = "    body.scp-page .sc-ficha-attr:first-child{border-top:none;}\n  }"

RULE = """    body.scp-page .sc-ficha-attr:first-child{border-top:none;}
    /* Texto pequeno mas ligero en movil: en pantalla pequena el
       var(--ink) resultaba demasiado pesado. */
    body.scp-page .scp-section > p.scp-lead,
    body.scp-page .scp-lead,
    body.scp-page .scp-faq p,
    body.scp-page .scp-links li,
    body.scp-page .scp-checklist li,
    body.scp-page .scp-disclaimer{color:#6B6B70;}
  }"""

done, skipped = [], []
for name in FILES:
    p = pathlib.Path(name + ".html")
    t = p.read_text(encoding="utf-8")
    if "#6B6B70;}" in t:
        skipped.append(name + " (ya aplicado)")
        continue
    if ANCHOR not in t:
        skipped.append(name + " (ANCLA NO ENCONTRADA)")
        continue
    p.write_text(t.replace(ANCHOR, RULE, 1), encoding="utf-8")
    done.append(name)

out = ["APLICADO (%d):" % len(done)] + ["  " + d for d in done]
out += ["", "OMITIDO (%d):" % len(skipped)] + ["  " + s for s in skipped]
pathlib.Path("tools/output/_tmp_mobile.txt").write_text("\n".join(out), encoding="utf-8")
print("aplicado:", len(done), "| omitido:", len(skipped))
