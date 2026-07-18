"""Inserta fichas de producto en una pagina de categoria y verifica.

Uso:
    python tools/insert_products.py <target.html> <editorial.json>

- Lee `_imp.json` (generado por import_batch.py) para imagen y url por ASIN.
- Lee <editorial.json>, con este formato (lo unico que redacta el asistente):
    {
      "order": ["ASIN1", "ASIN2", ...],   # orden final (normalmente por nº valoraciones desc)
      "items": {
        "ASIN1": {"name": "...", "desc": "...",
                   "why": ["b1", "b2", "b3"], "reviews": "..."}
      }
    }
- Genera cada bloque con la estructura EXACTA de product_card_template.html
  (comentarios PRODUCT START/END, data-asin, data-url, mismas clases).
- Sustituye el placeholder `.empty` si existe; si no, inserta antes de
  cerrar la <section class="products">.
- Verifica sin navegador: nº de bloques START==END y que cada imagen exista
  en disco. Imprime un resumen corto.

Reduce tokens/pasos: el asistente solo escribe el JSON editorial; nada de
scaffolding repetido ni verificacion por navegador para cambios de texto.
"""
import json, os, sys, re, html

EMPTY = '  <p class="empty">Todavía no hay productos en esta categoría. Vuelve pronto.</p>'

def esc(s):
    return html.escape(s, quote=True)

def block(asin, it, img, url):
    why = "\n".join(f"        <li>✔ {esc(w)}</li>" for w in it["why"])
    return (
f'''  <!-- PRODUCT START asin="{asin}" -->
  <article class="product-card" id="{asin}" data-asin="{asin}" data-url="{url}">
    <img class="product-card-img" src="{img}" alt="{esc(it["name"])}" width="600" height="600" loading="lazy">
    <h3 class="product-card-name">{esc(it["name"])}</h3>
    <p class="product-card-desc">{esc(it["desc"])}</p>
    <div class="product-card-why">
      <h4>⭐ ¿Por qué nos gusta?</h4>
      <ul>
{why}
      </ul>
    </div>
    <div class="product-card-reviews">
      <h4>💬 Lo que más destacan las familias</h4>
      <p>{esc(it["reviews"])}</p>
    </div>
    <a class="cta" href="{url}" target="_blank" rel="noopener">Ver en Amazon</a>
  </article>
  <!-- PRODUCT END asin="{asin}" -->''')

def main():
    if len(sys.argv) != 3:
        print("uso: python tools/insert_products.py <target.html> <editorial.json>"); sys.exit(2)
    target, edpath = sys.argv[1], sys.argv[2]
    imp = json.load(open("_imp.json", encoding="utf-8"))
    ed = json.load(open(edpath, encoding="utf-8"))
    order, items = ed["order"], ed["items"]

    blocks, missing_img = [], []
    for asin in order:
        it = items[asin]
        d = imp.get(asin, {})
        img, url = d.get("imagen"), d.get("url")
        if not img or not url:
            print(f"ERROR: {asin} sin imagen/url en _imp.json"); sys.exit(1)
        if not os.path.isfile(img):
            missing_img.append(img)
        blocks.append(block(asin, it, img, url))
    joined = "\n\n".join(blocks)

    content = open(target, encoding="utf-8").read()
    if EMPTY in content:
        content = content.replace(EMPTY, joined)
    else:
        # inserta antes del cierre de la seccion de productos
        idx = content.find("</section>", content.find('class="products'))
        if idx == -1:
            print("ERROR: no encuentro </section> de productos"); sys.exit(1)
        prev = content[:idx].rstrip()
        content = prev + "\n\n" + joined + "\n" + content[idx:]
    open(target, "w", encoding="utf-8").write(content)

    starts = re.findall(r'PRODUCT START asin="(\w+)"', content)
    ends = re.findall(r'PRODUCT END asin="(\w+)"', content)
    ok = len(starts) == len(ends) and len(set(starts)) == len(starts)
    print(f"insertados {len(order)} | tarjetas totales {len(starts)} | "
          f"markers {'OK' if ok else 'DESCUADRADOS'} | "
          f"imgs {'OK' if not missing_img else 'FALTAN: '+str(missing_img)}")

if __name__ == "__main__":
    main()
