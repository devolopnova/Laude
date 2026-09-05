import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent

# (filename, target h2 text to insert BEFORE)
TARGETS = [
    ("alquiler-sillas-coche-segunda-mano.html", "Preguntas frecuentes"),
    ("alzadores-elevadores-coche.html", "Mejores alzadores y elevadores"),
    ("normativa-dgt-i-size-sillas-coche.html", "Sillas homologadas i-Size recomendadas"),
    ("otras-marcas-sillas-coche.html", "Modelos destacados"),
    ("silla-coche-a-contramarcha.html", "Mejores sillas a contramarcha"),
    ("silla-coche-giratoria-360.html", "Mejores sillas giratorias 360º"),
    ("silla-coche-grupo-0-recien-nacido.html", "Mejores sillas de coche Grupo 0+"),
    ("sillas-coche-babyauto.html", "Modelo BabyAuto destacado"),
    ("sillas-coche-britax-romer.html", "Modelos Britax Römer por etapa"),
    ("sillas-coche-chicco.html", "Modelos Chicco por etapa"),
    ("sillas-coche-cybex.html", "Modelos Cybex por etapa"),
    ("sillas-coche-graco.html", "Modelos Graco por etapa"),
    ("sillas-coche-grupo-1-2-3.html", "Mejores sillas evolutivas y elevadores"),
    ("sillas-coche-isofix.html", "Mejores sillas de coche con Isofix"),
    ("sillas-coche-jovikids.html", "Modelo Jovikids destacado"),
    ("sillas-coche-kikkaboo.html", "Modelos KikkaBoo por etapa"),
    ("sillas-coche-kinderkraft.html", "Modelos Kinderkraft por etapa"),
    ("sillas-coche-lionelo.html", "Modelos Lionelo por etapa"),
    ("sillas-coche-maxi-cosi.html", "Modelos Maxi-Cosi por etapa"),
    ("sillas-coche-nania.html", "Modelos Nania por etapa"),
]

CSS_BLOCK = """
  /* Bloque destacado "Comparador de marcas" (ver sillitas-de-coche.html).
     Verde salvia pastel, coherente con el resto de la paleta de la
     seccion. Colocado encima del H2 de fichas de producto (o encima de
     Preguntas frecuentes si la pagina no tiene fichas). */
  .scp-marcas-highlight{
    display:flex;align-items:center;justify-content:space-between;gap:32px;
    background:#EAF1E7;border:1px solid #C9DDBF;border-radius:16px;
    padding:32px 36px;margin:32px 0;
  }
  .scp-marcas-highlight-text h3{font-size:19px;margin:0 0 8px;}
  .scp-marcas-highlight-text p{color:var(--ink-soft);font-size:14.5px;line-height:1.6;max-width:520px;margin:0;}
  .scp-marcas-highlight-cta{flex-shrink:0;font-size:14px;padding:14px 24px;}
  @media (max-width:640px){
    .scp-marcas-highlight{flex-direction:column;align-items:flex-start;padding:24px;gap:20px;}
    .scp-marcas-highlight-cta{width:100%;text-align:center;}
  }
"""

HTML_BLOCK = """    <div class="scp-marcas-highlight">
      <div class="scp-marcas-highlight-text">
        <h3>¿Qué marca de sillita de coche elegir?</h3>
        <p>Compara las principales marcas de sillitas de coche y descubre sus diferencias antes de elegir la que mejor se adapte a tu familia.</p>
      </div>
      <a class="cta scp-marcas-highlight-cta" href="comparador-sillas-coche.html">Comparar marcas →</a>
    </div>
"""

changed = []
for name, h2_text in TARGETS:
    p = ROOT / name
    text = p.read_text(encoding="utf-8")

    if "scp-marcas-highlight" in text:
        print(f"SKIP {name}: ya tiene el bloque")
        continue

    old_h2 = f"    <h2>{h2_text}</h2>"
    count = text.count(old_h2)
    if count != 1:
        print(f"SKIP {name}: {count} occurrences of h2 {h2_text!r}")
        continue

    # Insert CSS before </style>
    if "</style>" not in text:
        print(f"SKIP {name}: no </style> found")
        continue
    text = text.replace("</style>", CSS_BLOCK + "</style>", 1)

    # Insert HTML block before target h2
    new_h2 = HTML_BLOCK + old_h2
    text = text.replace(old_h2, new_h2, 1)

    p.write_text(text, encoding="utf-8")
    changed.append(name)

print(f"\nCambiados {len(changed)}/{len(TARGETS)}")
for c in changed:
    print(" -", c)
