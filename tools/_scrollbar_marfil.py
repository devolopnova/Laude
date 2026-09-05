#!/usr/bin/env python3
"""La tabla comparativa (.sc-compare) tiene overflow-x:auto, y su barra de
scroll se pintaba con el estilo por defecto del navegador (blanco), que
desentona con el fondo marfil. La adapta a la paleta de la seccion."""
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

ANCHOR = "  body.scp-page .sc-ficha > .cta{align-self:center;}"

RULE = """  body.scp-page .sc-ficha > .cta{align-self:center;}

  /* Barra de scroll de la tabla comparativa en tonos marfil: por
     defecto el navegador la pinta blanca y destaca sobre el fondo. */
  body.scp-page .sc-compare{
    scrollbar-width:thin;scrollbar-color:#C6B694 #E8DFC9;
  }
  body.scp-page .sc-compare::-webkit-scrollbar{height:10px;}
  body.scp-page .sc-compare::-webkit-scrollbar-track{
    background:#E8DFC9;border-radius:6px;
  }
  body.scp-page .sc-compare::-webkit-scrollbar-thumb{
    background:#C6B694;border-radius:6px;
  }
  body.scp-page .sc-compare::-webkit-scrollbar-thumb:hover{background:#B5A47F;}"""

done, skipped = [], []
for name in FILES:
    p = pathlib.Path(name + ".html")
    t = p.read_text(encoding="utf-8")
    if "::-webkit-scrollbar" in t:
        skipped.append(name + " (ya aplicado)")
        continue
    if ANCHOR not in t:
        skipped.append(name + " (ANCLA NO ENCONTRADA)")
        continue
    p.write_text(t.replace(ANCHOR, RULE, 1), encoding="utf-8")
    done.append(name)

out = ["APLICADO (%d)" % len(done), "OMITIDO (%d):" % len(skipped)]
out += ["  " + s for s in skipped]
pathlib.Path("tools/output/_tmp_scroll.txt").write_text(
    "\n".join(out), encoding="utf-8")
print("aplicado:", len(done), "| omitido:", len(skipped))
