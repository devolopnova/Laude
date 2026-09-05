#!/usr/bin/env python3
"""Busca referencias de navegacion que quedaron SIN enlazar en la seccion
de sillitas: lineas de lista o parrafos que mencionan 'guia especifica',
'guia de marca' o 'guia completa' sin ningun <a href>."""
import pathlib
import re

FILES = sorted(set("""sillitas-de-coche sillas-coche-isofix
silla-coche-grupo-0-recien-nacido sillas-coche-grupo-1-2-3
alzadores-elevadores-coche sillas-coche-cybex sillas-coche-maxi-cosi
sillas-coche-britax-romer sillas-coche-chicco sillas-coche-nania
sillas-coche-jovikids sillas-coche-kinderkraft sillas-coche-babyauto
sillas-coche-lionelo sillas-coche-kikkaboo sillas-coche-graco
otras-marcas-sillas-coche normativa-dgt-i-size-sillas-coche
silla-coche-a-contramarcha silla-coche-giratoria-360
alquiler-sillas-coche-segunda-mano""".split()))

# Frases que en esta seccion SIEMPRE deberian llevar enlace
SIGNALS = ("guía específica", "guía de marca", "guía completa",
           "guía transversal", "pilar general", "comparador")

findings = []
for name in FILES:
    t = pathlib.Path(name + ".html").read_text(encoding="utf-8")
    for i, line in enumerate(t.split("\n"), 1):
        low = line.lower()
        if not any(s in low for s in SIGNALS):
            continue
        if "<style" in low or "/*" in low:
            continue
        # solo lineas de contenido (li o p)
        if not re.search(r'<li>|<p class="scp-lead">', line):
            continue
        if "<a href=" in line:
            continue
        findings.append("%s:%d\n    %s" % (name, i, line.strip()[:160]))

out = ["REFERENCIAS SIN ENLAZAR: %d" % len(findings), ""] + findings
pathlib.Path("tools/output/_tmp_unlinked.txt").write_text(
    "\n".join(out), encoding="utf-8")
print(len(findings), "sin enlazar")
