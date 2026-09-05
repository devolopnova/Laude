#!/usr/bin/env python3
"""Script temporal, NO forma parte del pipeline permanente.

Aplica el lenguaje visual CERRADO de la landing de sillitas de coche
(ver memoria project_sillas_coche_tarjeta_diseno_definitivo) al resto de
articulos de la seccion:

  1. <link> de fuentes: + Playfair Display, JetBrains Mono hasta 700
  2. <body class="scp-page">
  3. Bloque CSS scoped (fondo marfil, H1/H2 serif, ficha en 3 bloques)
  4. Reestructura cada .sc-ficha de 1 caja a 3 bloques + boton centrado
  5. Corrige conflictos de especificidad ya conocidos (.scp-lead, .scp-faq)

NO toca datos, precios, ASIN, enlaces ni caracteristicas. El unico cambio
de texto es en las opiniones: se elimina el emoji y la primera letra pasa
a mayuscula al dejar de ser continuacion de la frase (autorizado por el
usuario el 27-ago-2026).

Uso:  python tools/_apply_sillas_design.py
"""
import pathlib
import re
import sys

FILES = """sillas-coche-isofix silla-coche-grupo-0-recien-nacido
sillas-coche-grupo-1-2-3 alzadores-elevadores-coche sillas-coche-cybex
sillas-coche-maxi-cosi sillas-coche-britax-romer sillas-coche-chicco
sillas-coche-nania sillas-coche-jovikids sillas-coche-kinderkraft
sillas-coche-babyauto sillas-coche-lionelo sillas-coche-kikkaboo
sillas-coche-graco otras-marcas-sillas-coche
normativa-dgt-i-size-sillas-coche silla-coche-a-contramarcha
silla-coche-giratoria-360 alquiler-sillas-coche-segunda-mano""".split()

FONT_OLD = ("family=Fredoka:wght@500;600;700&family=Inter:wght@400;500;600"
            "&family=JetBrains+Mono:wght@500;600&display=swap")
FONT_NEW = ("family=Fredoka:wght@500;600;700&family=Inter:wght@400;500;600"
            "&family=JetBrains+Mono:wght@500;600;700"
            "&family=Playfair+Display:wght@600;700&display=swap")

CSS_BLOCK = """  /* LENGUAJE VISUAL SILLITAS DE COCHE (cerrado 27-ago-2026).
     Identico al de sillitas-de-coche.html. Scope body.scp-page: no toca
     css/site.css, asi que el resto del sitio queda intacto. */
  body.scp-page{--bg:#F2ECDE;}
  body.scp-page h1,
  body.scp-page .scp-section h2{
    font-family:'Playfair Display',serif;font-weight:700;letter-spacing:normal;
  }
  body.scp-page .scp-lead,
  body.scp-page .scp-faq p,
  body.scp-page .scp-links li,
  body.scp-page .scp-checklist li,
  body.scp-page .scp-disclaimer{
    color:var(--ink);font-weight:500;
  }

  /* Ficha de producto en TRES bloques + boton centrado */
  body.scp-page .sc-ficha{
    display:flex;flex-direction:column;align-items:center;gap:20px;
    background:none;border:none;box-shadow:none;border-radius:0;padding:0;
    margin-bottom:44px;
  }
  body.scp-page .sc-ficha:last-child{border:none;margin-bottom:0;}

  body.scp-page .sc-ficha-product{
    display:flex;align-items:stretch;gap:28px;width:100%;
    background:#FFFFFF;border:1px solid var(--line);border-radius:14px;
    padding:24px;box-shadow:0 1px 8px rgba(28,28,30,.04);
  }
  body.scp-page .sc-ficha-product .sc-ficha-img{
    width:240px;min-width:240px;height:auto;align-self:stretch;
    object-fit:contain;border-radius:10px;
  }
  body.scp-page .sc-ficha-body{justify-content:center;}
  body.scp-page .sc-ficha-brand{letter-spacing:.08em;}
  body.scp-page .sc-ficha-name{
    font-family:'Playfair Display',serif;font-weight:700;font-size:24px;margin-top:4px;
  }
  body.scp-page .sc-ficha-meta{align-items:baseline;}
  body.scp-page .sc-ficha-price{font-size:26px;color:var(--accent);}
  body.scp-page .sc-ficha-rating{font-size:13px;}

  body.scp-page .sc-ficha-specs{
    width:100%;background:#ECE1CB;border:1px solid var(--line);border-radius:14px;
    padding:24px 28px;box-shadow:0 1px 8px rgba(28,28,30,.04);
  }
  body.scp-page .sc-ficha-specs-title{
    font-family:'JetBrains Mono',monospace;font-size:11.5px;font-weight:700;
    color:var(--ink);text-transform:uppercase;letter-spacing:.06em;margin-bottom:16px;
  }
  body.scp-page .sc-ficha-attrs{
    background:none;border:none;border-radius:0;padding:0;column-gap:32px;row-gap:0;
  }
  /* Separador arriba y no abajo: funciona con cualquier numero de
     atributos, par o impar (10 fichas de la seccion tienen 7 o 9). */
  body.scp-page .sc-ficha-attr{
    display:flex;justify-content:space-between;align-items:baseline;gap:16px;
    padding:11px 0;border-top:1px solid #D9CBAC;border-bottom:none;
  }
  body.scp-page .sc-ficha-attr:nth-child(-n+2){border-top:none;}
  body.scp-page .sc-ficha-attr-label{white-space:nowrap;color:var(--ink);}
  body.scp-page .sc-ficha-attr-value{text-align:right;}

  body.scp-page .sc-ficha-opiniones{
    width:100%;background:#ECE1CB;border:1px solid var(--line);border-radius:14px;
    padding:22px 28px;box-shadow:0 1px 8px rgba(28,28,30,.04);
  }
  body.scp-page .sc-ficha-opiniones-head{
    font-family:'JetBrains Mono',monospace;font-size:11.5px;font-weight:700;
    color:var(--ink);text-transform:uppercase;letter-spacing:.06em;margin-bottom:10px;
  }
  body.scp-page .sc-ficha-opiniones-text{color:var(--ink);font-size:15px;line-height:1.7;}

  body.scp-page .sc-ficha > .cta{align-self:center;}

  @media (max-width:560px){
    body.scp-page .sc-ficha-product{flex-direction:column;padding:20px;gap:18px;}
    body.scp-page .sc-ficha-product .sc-ficha-img{width:100%;min-width:0;height:200px;}
    body.scp-page .sc-ficha-specs,
    body.scp-page .sc-ficha-opiniones{padding:20px;}
    body.scp-page .sc-ficha-name{font-size:21px;}
    body.scp-page .sc-ficha-price{font-size:23px;}
    body.scp-page .sc-ficha-attr:nth-child(-n+2){border-top:1px solid #D9CBAC;}
    body.scp-page .sc-ficha-attr:first-child{border-top:none;}
  }
"""

FICHA_RE = re.compile(
    r'<div class="sc-ficha">\s*'
    r'(?P<img><img class="sc-ficha-img"[^>]*>)\s*'
    r'<div class="sc-ficha-body">\s*'
    r'(?P<head><div>\s*<span class="sc-ficha-brand">.*?</div>)\s*'
    r'(?P<desc><p class="sc-ficha-desc">.*?</p>)\s*'
    r'(?P<meta><div class="sc-ficha-meta">.*?</div>)\s*'
    r'(?P<attrs><div class="sc-ficha-attrs">.*?</div>)\s*'
    r'(?P<opi><p class="sc-ficha-opiniones">.*?</p>\s*)?'
    r'(?P<cta><a class="cta"[^>]*>.*?</a>)\s*'
    r'</div>\s*</div>',
    re.S,
)

OPI_RE = re.compile(
    r'<p class="sc-ficha-opiniones"><strong>[^<]*Lo que destacan las familias:</strong>\s*(.*?)</p>',
    re.S,
)


def reindent(block, spaces):
    """Reindenta un bloque multilinea al nivel dado."""
    lines = [ln.strip() for ln in block.strip().split("\n")]
    return ("\n" + " " * spaces).join(lines)


def build_ficha(m):
    img = m.group("img").strip()
    head = reindent(m.group("head"), 10)
    desc = m.group("desc").strip()
    meta = reindent(m.group("meta"), 10)
    attrs = reindent(m.group("attrs"), 10)
    cta = m.group("cta").strip()

    parts = []
    parts.append('<div class="sc-ficha">')
    parts.append('      <div class="sc-ficha-product">')
    parts.append('        ' + img)
    parts.append('        <div class="sc-ficha-body">')
    parts.append('          ' + head)
    parts.append('          ' + desc)
    parts.append('          ' + meta)
    parts.append('        </div>')
    parts.append('      </div>')
    parts.append('      <div class="sc-ficha-specs">')
    parts.append('        <p class="sc-ficha-specs-title">Características principales</p>')
    parts.append('        ' + attrs)
    parts.append('      </div>')

    if m.group("opi"):
        om = OPI_RE.search(m.group("opi"))
        if not om:
            raise SystemExit("ERROR: bloque de opiniones con formato inesperado:\n"
                             + m.group("opi")[:200])
        texto = " ".join(om.group(1).split())
        texto = texto[0].upper() + texto[1:]
        parts.append('      <div class="sc-ficha-opiniones">')
        parts.append('        <p class="sc-ficha-opiniones-head">Lo que destacan las familias</p>')
        parts.append('        <p class="sc-ficha-opiniones-text">' + texto + '</p>')
        parts.append('      </div>')

    parts.append('      ' + cta)
    parts.append('    </div>')
    return "\n".join(parts)


def main():
    report = []
    for name in FILES:
        path = pathlib.Path(name + ".html")
        t = path.read_text(encoding="utf-8")
        orig = t

        # 1. fuentes
        if FONT_OLD in t:
            t = t.replace(FONT_OLD, FONT_NEW)
        elif "Playfair+Display" not in t:
            raise SystemExit("ERROR: link de fuentes inesperado en " + name)

        # 2. body scope
        if '<body class="scp-page">' not in t:
            if "<body>" not in t:
                raise SystemExit("ERROR: <body> no encontrado en " + name)
            t = t.replace("<body>", '<body class="scp-page">', 1)

        # 3. CSS: insertar bloque justo tras <style>
        if "body.scp-page" not in t:
            t = t.replace("<style>\n", "<style>\n" + CSS_BLOCK, 1)

        # 5. conflictos de especificidad conocidos
        t = t.replace(
            '.scp-section > p.scp-lead{color:var(--ink-soft);',
            '.scp-section > p.scp-lead{color:var(--ink);')
        t = t.replace('.scp-faq{margin-top:16px;}', '.scp-faq{margin-top:48px;}')

        # 4. reestructurar fichas
        n = len(FICHA_RE.findall(t))
        t = FICHA_RE.sub(build_ficha, t)

        if t != orig:
            path.write_text(t, encoding="utf-8")
        report.append("%-40s fichas reestructuradas: %d" % (name, n))

    pathlib.Path("tools/output/_tmp_apply_report.txt").write_text(
        "\n".join(report), encoding="utf-8")
    print("OK")


if __name__ == "__main__":
    main()
