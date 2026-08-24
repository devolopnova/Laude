import json

with open('tools/output/planes-familia/lleida/plan.json', encoding='utf-8') as f:
    plan = json.load(f)

primary = sorted([p for p in plan['places'] if p['status'] == 'primary'], key=lambda x: x['rank'])
assert len(primary) == 15

blocks = []
for p in primary:
    rank = p['rank']
    rank_str = f"{rank:02d}"
    addr = p['address'] or ''
    block = (
        f'<!-- PLACE START rank="{rank}" -->\n'
        f'<article class="pf-place-row" data-rank="{rank}">\n'
        f'  <div class="pf-place-rank" aria-hidden="true">{rank_str}</div>\n'
        f'  <div class="pf-place-content">\n'
        f'    <h3 class="pf-place-name">{p["name"]}</h3>\n'
        f'    <p class="pf-place-desc">{p["description"]}</p>\n'
        f'    <span class="pf-place-loc"><i class="ti ti-map-pin" aria-hidden="true"></i><span>{addr}</span></span>\n'
        f'    <a class="pf-place-cta" href="{p["official_url"]}" target="_blank" rel="noopener">Visitar web oficial <i class="ti ti-external-link" aria-hidden="true"></i></a>\n'
        f'  </div>\n'
        f'</article>\n'
        f'<!-- PLACE END rank="{rank}" -->'
    )
    blocks.append(block)

places_html = "\n\n".join(blocks)

breadcrumb_json = (
    '{"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": '
    '[{"@type": "ListItem", "position": 1, "name": "Guía de Regalos", "item": "guia-regalos-juguetes.html"}, '
    '{"@type": "ListItem", "position": 2, "name": "Planes en familia", "item": "planes-en-familia.html"}, '
    '{"@type": "ListItem", "position": 3, "name": "Cataluña", "item": "planes-en-familia-cataluna.html"}, '
    '{"@type": "ListItem", "position": 4, "name": "Lleida", "item": "planes-en-familia-lleida.html"}]}'
)

template = """<!DOCTYPE html>
<html lang="es">
<head>
<script type="text/javascript" charset="UTF-8" src="//cdn.cookie-script.com/s/067dce5e5b2c3eeb8cc1f8f51d3c14a8.js"></script>
<script async src="https://www.googletagmanager.com/gtag/js?id=G-88T9H9C650"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  gtag('js', new Date());

  gtag('config', 'G-88T9H9C650');
</script>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Planes en familia en Lleida | Lauderem</title>
<link rel="canonical" href="https://www.lauderem.com/planes-en-familia-lleida.html">
<meta name="description" content="Museos, parques y planes para hacer en familia en Lleida, seleccionados y verificados por Lauderem.">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Fredoka:wght@500;600;700&family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@500;600&display=swap" rel="stylesheet">
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@tabler/icons-webfont@3.31.0/dist/tabler-icons.min.css">
<link rel="stylesheet" href="css/site.css">
<script type="application/ld+json">
__BREADCRUMB__
</script>
<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-9559559964863356"
     crossorigin="anonymous"></script>
</head>
<body>

<header>
  <nav class="wrap">
    <div class="logo"><img src="images/cabecera/logohero/lauderem-logo-hero.svg" alt="Lauderem" width="130" height="32" loading="lazy" decoding="async"></div>
    <a class="back" href="/">← Volver a la guía</a>
  </nav>
</header>

<section class="cat-hero-2 wrap">
  <div class="pf-crumb">
    <a class="pf-crumb-link" href="planes-en-familia.html">Planes en familia</a>&nbsp;·&nbsp;<a class="pf-crumb-link" href="planes-en-familia-cataluna.html">Cataluña</a>
  </div>
  <h1>Planes en familia en Lleida</h1>
  <p class="cat-hero-2-subtitle">Lugares para visitar y planes para hacer en familia en Lleida.</p>
</section>

<section class="wrap">
  <div class="pf-place-list">

__PLACES__

  </div>
</section>

<footer class="wrap">
  <p>Planes en familia es la sección de Lauderem con lugares y planes para hacer en familia fuera de casa, organizados por provincia.</p>
</footer>

</body>
</html>
"""

template = template.replace("__BREADCRUMB__", breadcrumb_json).replace("__PLACES__", places_html)

with open('planes-en-familia-lleida.html', 'w', encoding='utf-8') as f:
    f.write(template)

print("written, length:", len(template))
