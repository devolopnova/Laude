#!/usr/bin/env python3
"""Verifica que la regla de movil (#6B6B70) realmente GANA la cascada en
cada archivo. Las media queries no suman especificidad, asi que el orden
en el archivo importa. Comprueba caso por caso quien gana."""
import pathlib
import re

FILES = """sillitas-de-coche sillas-coche-isofix
silla-coche-grupo-0-recien-nacido sillas-coche-grupo-1-2-3
alzadores-elevadores-coche sillas-coche-cybex sillas-coche-maxi-cosi
sillas-coche-britax-romer sillas-coche-chicco sillas-coche-nania
sillas-coche-jovikids sillas-coche-kinderkraft sillas-coche-babyauto
sillas-coche-lionelo sillas-coche-kikkaboo sillas-coche-graco
otras-marcas-sillas-coche normativa-dgt-i-size-sillas-coche
silla-coche-a-contramarcha silla-coche-giratoria-360
alquiler-sillas-coche-segunda-mano""".split()

problems = []
for name in FILES:
    t = pathlib.Path(name + ".html").read_text(encoding="utf-8")
    style = t.split("<style>")[1].split("</style>")[0]

    pos_mobile = style.find("#6B6B70;}")
    pos_dark = style.find("color:var(--ink);font-weight:500;")
    pos_base = style.find(".scp-section > p.scp-lead{color:var(--ink)")

    if pos_mobile < 0:
        problems.append(name + ": FALTA la regla de movil")
        continue
    if pos_dark < 0:
        problems.append(name + ": FALTA la regla de texto oscuro")
        continue

    # .scp-faq p / .scp-links li / .scp-disclaimer: mismos selectores en
    # ambas reglas -> empate de especificidad -> gana la posterior.
    if pos_mobile < pos_dark:
        problems.append(
            "%s: la regla de movil va ANTES de la oscura (pos %d < %d) -> "
            "FAQ/listas/disclaimer se quedarian oscuros en movil"
            % (name, pos_mobile, pos_dark))

    # .scp-lead: la regla base empata con 'body.scp-page .scp-lead', pero
    # el selector largo (0,3,2) la gana siempre, este donde este.
    if "body.scp-page .scp-section > p.scp-lead," not in style:
        problems.append(name + ": falta el selector largo para .scp-lead")

    if t.count("<head>") != 1 or t.count("</body>") != 1:
        problems.append(name + ": HTML descuadrado")

out = ["ARCHIVOS: %d" % len(FILES),
       "PROBLEMAS: " + (str(len(problems)) if problems else "NINGUNO")]
out += problems
pathlib.Path("tools/output/_tmp_verify_mobile.txt").write_text(
    "\n".join(out), encoding="utf-8")
print("problemas:", len(problems))
