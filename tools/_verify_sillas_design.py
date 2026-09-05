#!/usr/bin/env python3
"""Script temporal. Compara cada articulo de sillitas contra su copia de
seguridad para confirmar que el rediseno NO altero datos: mismos ASIN,
mismos enlaces de Amazon, mismos atributos, mismos precios/valoraciones,
y mismo texto de opiniones (salvo la mayuscula inicial autorizada).
"""
import pathlib
import re
import sys

BK = pathlib.Path(
    "C:/Users/COBOLM~1.2/AppData/Local/Temp/claude/C--guia-regalos/"
    "2a1f1f77-72cf-4a23-9a20-6c969562b303/scratchpad/backup_sillas")

FILES = """sillas-coche-isofix silla-coche-grupo-0-recien-nacido
sillas-coche-grupo-1-2-3 alzadores-elevadores-coche sillas-coche-cybex
sillas-coche-maxi-cosi sillas-coche-britax-romer sillas-coche-chicco
sillas-coche-nania sillas-coche-jovikids sillas-coche-kinderkraft
sillas-coche-babyauto sillas-coche-lionelo sillas-coche-kikkaboo
sillas-coche-graco otras-marcas-sillas-coche
normativa-dgt-i-size-sillas-coche silla-coche-a-contramarcha
silla-coche-giratoria-360 alquiler-sillas-coche-segunda-mano""".split()

ATTR_RE = re.compile(
    r'<span class="sc-ficha-attr"><span class="sc-ficha-attr-label">(.*?)</span>'
    r'<span class="sc-ficha-attr-value">(.*?)</span></span>')
LINK_RE = re.compile(r'href="(https://www\.amazon\.es/dp/[^"]+)"')
PRICE_RE = re.compile(r'<span class="sc-ficha-price">(.*?)</span>')
RATING_RE = re.compile(r'<span class="sc-ficha-rating">(.*?)</span>')
NAME_RE = re.compile(r'<h3 class="sc-ficha-name">(.*?)</h3>')
DESC_RE = re.compile(r'<p class="sc-ficha-desc">(.*?)</p>', re.S)
IMG_RE = re.compile(r'src="(images/sillas-coche/[^"]+)"')

OPI_OLD = re.compile(
    r'<p class="sc-ficha-opiniones"><strong>[^<]*familias:</strong>\s*(.*?)</p>', re.S)
OPI_NEW = re.compile(
    r'<p class="sc-ficha-opiniones-text">(.*?)</p>', re.S)

problems = []
stats = {"attrs": 0, "links": 0, "opis": 0}

for name in FILES:
    new = pathlib.Path(name + ".html").read_text(encoding="utf-8")
    old = (BK / (name + ".html")).read_text(encoding="utf-8")

    for label, rx in (("atributos", ATTR_RE), ("enlaces", LINK_RE),
                      ("precios", PRICE_RE), ("valoraciones", RATING_RE),
                      ("nombres", NAME_RE), ("imagenes", IMG_RE)):
        a, b = rx.findall(old), rx.findall(new)
        if a != b:
            problems.append("%s: %s DIFIEREN (%d -> %d)" % (name, label, len(a), len(b)))

    da = [" ".join(x.split()) for x in DESC_RE.findall(old)]
    db = [" ".join(x.split()) for x in DESC_RE.findall(new)]
    if da != db:
        problems.append("%s: descripciones DIFIEREN" % name)

    oa = [" ".join(x.split()) for x in OPI_OLD.findall(old)]
    ob = [" ".join(x.split()) for x in OPI_NEW.findall(new)]
    if len(oa) != len(ob):
        problems.append("%s: nº de opiniones %d -> %d" % (name, len(oa), len(ob)))
    else:
        for x, y in zip(oa, ob):
            if y != x[0].upper() + x[1:]:
                problems.append("%s: texto de opinion alterado:\n  ANTES: %s\n  AHORA: %s"
                                % (name, x[:90], y[:90]))

    stats["attrs"] += len(ATTR_RE.findall(new))
    stats["links"] += len(LINK_RE.findall(new))
    stats["opis"] += len(ob)

    for tag, n in (("<head>", 1), ("</head>", 1), ("</body>", 1), ("<h1>", 1)):
        if new.count(tag) != n:
            problems.append("%s: %s aparece %d veces" % (name, tag, new.count(tag)))
    if new.count("<body") != 1 or '<body class="scp-page">' not in new:
        problems.append("%s: <body class=scp-page> incorrecto" % name)
    for bad in ("\U0001F4AC", "ti-quote"):
        if bad in new:
            problems.append("%s: quedan restos de icono/emoji" % name)

    n_prod = new.count('class="sc-ficha-product"')
    n_specs = new.count('class="sc-ficha-specs"')
    n_ficha = new.count('class="sc-ficha"')
    if not (n_prod == n_specs == n_ficha):
        problems.append("%s: bloques descuadrados ficha=%d prod=%d specs=%d"
                        % (name, n_ficha, n_prod, n_specs))

out = ["TOTALES: %d atributos, %d enlaces Amazon, %d bloques de opiniones"
       % (stats["attrs"], stats["links"], stats["opis"]), ""]
out.append("PROBLEMAS: " + (str(len(problems)) if problems else "NINGUNO"))
out += problems
pathlib.Path("tools/output/_tmp_verify_design.txt").write_text(
    "\n".join(out), encoding="utf-8")
print("problemas:", len(problems))
