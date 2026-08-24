# Guía de Regalos — importación de productos de Amazon

Este proyecto es una web estática de recomendaciones de juguetes para bebés,
organizada en páginas de categoría (`juguetes-sensoriales.html`,
`mordedores.html`, `peluches.html`, `sonajeros.html`, ...) enlazadas desde
`guia-regalos-juguetes.html`.

## Páginas por franja de edad

Cada franja de edad de la landing (0-6 meses, 6-12 meses, 1 año, ...) tiene
sus propias páginas de categoría, aunque el nombre de la categoría se
repita entre franjas (p.ej. "Mordedores" existe tanto en 0-6 como en 6-12
meses). Nunca se comparte una página de producto entre dos franjas de edad.

Convención de nombre de archivo: toda página de categoría de una franja
distinta a 0-6 meses lleva el rango de edad como sufijo en minúsculas:
`<categoria-slug>-<rango-edad>.html` (p.ej.
`andadores-y-primeros-pasos-6-12-meses.html`, `mordedores-6-12-meses.html`,
`mordedores-1-ano.html`). Se aplica siempre, coincida o no el nombre con
una categoría ya existente de otra franja — así queda inequívoco a qué
edad pertenece cada archivo con solo mirar su nombre, sin tener que
comprobar colisiones caso a caso. Las categorías de 0-6 meses no llevan
sufijo (son las originales, ya creadas sin él). El `<h1>` y el `eyebrow`
de cada página siguen indicando su franja de edad real (p.ej.
"6–12 meses"), igual que ya hacen las páginas de 0-6 meses.

## Arquitectura de la importación de productos

- `tools/amazon_import.py`: scraping (Playwright) y procesado de imagen
  (Pillow). Descarga la imagen principal, la convierte a WebP y la encuadra
  en un cuadrado 600x600 sin recortar ni deformar (fondo blanco). También
  extrae *materia prima* en crudo (título de Amazon, bullets de
  características, muestra de reseñas si Amazon las expone en la página) —
  nunca la redacción final.
- `tools/product_card_template.html`: plantilla de referencia con la
  estructura y el orden exacto de una ficha de producto. El diseño se
  cambia aquí y en `css/site.css`, nunca en el `.py`.
- `css/site.css`: estilos compartidos por todas las páginas de categoría.
- La redacción del contenido (título corto, descripción, beneficios,
  resumen de reseñas) la hace el asistente en el momento de insertar el
  producto, siguiendo las reglas de este documento — no la genera el script
  Python, porque requiere criterio editorial.

## Flujo al pegar una URL de Amazon

1. Ejecutar `python tools/amazon_import.py <URL> --target <archivo.html>`
   desde la raíz del proyecto. Esto comprueba primero si el producto (por
   ASIN o URL) ya está insertado en ese archivo; si `ya_existe` es `true`,
   informar al usuario y no continuar.
2. Si no existe, el script descarga la imagen, la convierte a WebP 600x600
   y devuelve JSON con `asin`, `titulo` (crudo de Amazon), `bullets`,
   `reviews_muestra`, `imagen`, `slug`, `url`.
3. Redactar el contenido siguiendo las reglas editoriales de abajo, a
   partir del título/bullets/reseñas crudos — nunca copiándolos.
4. Insertar el bloque en la página de categoría siguiendo exactamente
   `tools/product_card_template.html`, incluyendo los comentarios
   `<!-- PRODUCT START asin="..." -->` / `<!-- PRODUCT END asin="..." -->`,
   el atributo `data-asin` y el atributo `id="ASIN"` en el `<article>`
   (este último es el enlace interno que usa el componente
   "⭐ Favoritos de los papás", ver más abajo).

## Reglas editoriales

**Título** (`product-card-name`): nunca el título literal de Amazon.
Reescribir corto (3-8 palabras), natural, conservando marca + producto.
Eliminar edades, cantidades, "Sin BPA", "regalo", superlativos y demás
relleno de marketing.

En productos de la categoría **Peluches**, si el nombre corto resultante
empezaría por "Sonajero de peluche" (p.ej. porque el título de Amazon es
un "sonajero de peluche con forma de X"), invertir el orden a **"Peluche
sonajero"** en su lugar (p.ej. "Peluche sonajero León", "Peluche sonajero
Sophie la girafe"). Da más peso a que es un peluche antes que a que es un
sonajero, coherente con la categoría en la que vive la ficha. Esta regla
no aplica a nombres que ya empiezan de otra forma (p.ej. "Ganso sonajero
Sensimals Fisher-Price" se queda igual).

**Descripción** (`product-card-desc`): 2-3 líneas originales. Explica qué
es, para qué sirve y por qué puede ser una buena opción. Nunca copiar
frases de Amazon.

**⭐ ¿Por qué nos gusta?** (`product-card-why`): exactamente 3 beneficios
cortos, formato `✔ Beneficio.` en frase corta y concreta.

**💬 Lo que más destacan las familias** (`product-card-reviews`): resumen
original de 1-2 frases, con tono de recomendación de experto/guía de
padres — no una cita literal de una reseña. Si `reviews_muestra` viene
vacío (Amazon no siempre expone reseñas en la ficha de producto), redactar
igualmente un resumen plausible apoyado en los `bullets` y el tipo de
producto, sin inventar cifras ni afirmaciones verificables (nº de compras,
valoraciones, etc.).

**Tono general**: español natural, para padres, frases cortas, cercano y
profesional, sin exageraciones. Prohibido: "el mejor del mercado",
"increíble", "compra ya", "producto imprescindible" y expresiones
similares. Debe leerse como una guía de recomendaciones, no como un anuncio.

## Estructura de cada ficha (orden fijo)

Imagen → Nombre → Descripción → "⭐ ¿Por qué nos gusta?" (3 beneficios) →
"💬 Lo que más destacan las familias" → botón "Ver en Amazon".

## Reglas de diseño base

- Espaciado vertical de la ficha, de **24px exactos** entre bloques,
  con una excepción: imagen → nombre (24px) → **descripción (8px)** →
  "⭐ ¿Por qué nos gusta?" (24px) → "💬 Lo que más destacan las familias"
  (24px) → botón "Ver en Amazon" (24px). El nombre y la descripción
  llevan solo 8px porque forman parte del mismo bloque de información
  (el nombre "respira" un poco sin separarse demasiado de su
  descripción); el resto usa el espaciado base de la ficha.
  Implementado en `css/site.css` con una única variable
  `--card-gap: 24px` en `.product-card` (flex column + `gap`), y la
  única excepción (`.product-card-desc`) usa
  `margin-top: calc(8px - var(--card-gap))` en vez de un valor
  hardcodeado, para que siga dando 8px exactos aunque `--card-gap`
  cambie en el futuro.
- Si en el futuro se necesita un margen distinto entre dos bloques
  concretos, seguir este mismo patrón: nunca un `margin-top` fijo
  suelto, sino `calc(valor_deseado - var(--card-gap))`.
- Al añadir nuevas reglas de espaciado/diseño "permanentes" como esta,
  documentarlas aquí y aplicarlas siempre en `css/site.css` (nunca con
  estilos inline en el HTML de un producto individual), para que se
  hereden automáticamente en todas las fichas ya existentes y en las
  futuras importaciones/regeneraciones.

### Cabecera y hero de la landing

Solo aplica a `guia-regalos-juguetes.html`:

- **Cabecera oscura**: fondo tinta `#2C2C2A`, logo en blanco con "Regalos"
  en `--accent`, enlaces en gris claro y una píldora naranja `#D85A30`
  "Buscar regalo" (`.nav-cta`) que ancla a `#ageList`.
- **Hero centrado**: píldora `eyebrow` "Sin marcas, solo criterio" (fondo
  `#FAECE7`, texto `#993C1D`), titular a dos líneas sin punto final y
  lead corto. Debajo, el **selector de edades tipo flecha** (`.age-cards`,
  con `id="chart"` para que el enlace "Por edades" siga funcionando): 6
  segmentos chevron conectados (0-6m, 6-12m, 1-3, 4-7, 8-9, 10), cada uno
  con su tinte de familia de color (clases `.ac-coral/.ac-amber/.ac-yellow/
  .ac-green/.ac-blue/.ac-purple`, definidas en CSS, nunca inline) y una
  insignia circular blanca (`.age-badge`) con icono Tabler que sobresale
  por arriba. La forma chevron se hace con `clip-path` (el primero sin
  muesca izquierda, el último sin punta derecha). El segmento seleccionado
  lleva además `.is-selected`: chevron azul sólido y texto blanco (por
  defecto es 8-9). Cada uno ancla a la primera franja de su rango (`#a0`,
  `#a1`, `#a2`, `#a5`, `#a9`, `#a11`). Sustituyó al antiguo gráfico de
  barras (`.gc-*`), que ya no existe. En móvil los chevrons pierden la
  punta (`clip-path:none`) y pasan a una cuadrícula de 3 columnas de
  tarjetas redondeadas, con la insignia igualmente encima.

### Franjas de edad de la landing (insignia + tarjetas de categoría)

Solo aplica a `guia-regalos-juguetes.html` (sus estilos viven en el
`<style>` propio de la landing, no en `css/site.css`):

- **Insignia de edad**: el número de cada franja va en un círculo de 58px
  con fondo tintado y anillo de 3px del color de la franja (`--accent`,
  fijado por fila desde el array `bands`). Del círculo baja una línea
  vertical fina (2px) que recorre toda la franja y termina en un punto de
  8px. Los tintes se derivan con `color-mix` del color de la franja —
  nunca colores hardcodeados por edad. En móvil la línea y el punto se
  ocultan y el círculo se alinea en fila con el contenido.
- **Tarjetas de categoría (chips)**: dos columnas de ancho fijo e idéntico
  (260px, dimensionado para la categoría más larga en una línea), sin
  punto decorativo y sin flecha `↗`. Cada tarjeta muestra un icono
  minimalista + nombre. Los iconos son la webfont **Tabler Icons**
  (enlazada por CDN en el `<head>` de la landing) y se resuelven por
  palabra clave en la función `chipIcon()` del `<script>`; el icono va
  siempre en el mismo azul (variable `--chip-icon`, `#378ADD`), nunca en
  el color de la franja ni en gris — uniforme en toda la landing. El texto
  de la tarjeta usa la fuente Inter. Al crear una categoría nueva,
  comprobar que
  `chipIcon()` la cubre — si no, añadir la palabra clave (el comodín es
  `ti-gift`).

## Checklist obligatorio al crear una página HTML nueva

Cada vez que se crea una página `.html` nueva en la raíz del proyecto
(nueva categoría, nueva franja de edad, nueva guía...), Claude debe
completar esta checklist antes de darla por terminada, sin que el
usuario tenga que pedirlo:

1. **Google Analytics 4**: insertar el snippet de gtag.js en el `<head>`,
   justo después de la etiqueta de apertura `<head>` (mismo sitio que en
   el resto de páginas). ID de medición: `G-88T9H9C650`. No existe
   sistema de plantilla compartida para el `<head>`, así que se inserta
   página a página — se puede reutilizar la lógica de
   `tools/install_ga4.py` (detecta duplicados por ID antes de insertar).
2. **Google AdSense**: si la página va a mostrar anuncios (caso general:
   todas las páginas de categoría/producto), añadir también en el
   `<head>` el mismo script que ya llevan el resto de páginas:
   `<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-9559559964863356" crossorigin="anonymous"></script>`.
   Páginas puramente institucionales/legales sin intención de monetizar
   pueden omitirlo si así se decide explícitamente, pero por defecto se
   añade igual que en el resto del sitio.
3. **Enlaces de afiliado de Amazon**: todo enlace `href` a un producto de
   Amazon (botón "Ver en Amazon" de cada ficha) debe llevar el parámetro
   `?tag=laude09-21` (o `&tag=laude09-21` si la URL ya tiene query
   string). Verificar con
   `grep -o 'amazon\.[a-z.]*/[^"]*"' <archivo>.html` que ningún enlace de
   producto se quedó sin el tag.
4. **`sitemap.xml`**: regenerar tras crear la página con
   `python tools/generate_sitemap.py` (lee todos los `.html` de la raíz,
   asigna prioridad según el tipo de página — home 1.0, guías 0.9,
   categorías 0.8, legales 0.2 — y usa la fecha de modificación real del
   archivo como `lastmod`). Si la página nueva no encaja en ninguna
   categoría existente del script (por ejemplo una guía nueva tipo
   `guia-montessori.html`), actualizar antes los sets `GUIDES`/`LEGAL`
   del script para que la clasifique bien, en vez de editar `sitemap.xml`
   a mano.
5. **`robots.txt`**: no requiere cambios salvo que la página nueva deba
   quedar excluida de la indexación (páginas de prueba/preview tipo
   `footer-preview.html`); en ese caso añadir una regla `Disallow:` en
   vez de tocar el resto del archivo.
6. **`<title>`, meta description y canonical**: toda página nueva lleva
   los tres en el `<head>`:
   - `<title>` descriptivo y único (patrón ya usado: `Categoría · Franja
     de edad` o similar).
   - `<meta name="description" content="...">` de ~150-160 caracteres,
     redactado siguiendo el mismo tono que el resto del contenido
     editorial (ver reglas editoriales más abajo), nunca copiado de otra
     página.
   - `<link rel="canonical" href="https://www.lauderem.com/<archivo>.html">`
     (o `https://www.lauderem.com/` si la página nueva fuera a sustituir
     la home, caso que no debería darse — ver `vercel.json`).
7. **Enlace interno**: la página nueva debe quedar enlazada desde al
   menos otra página real del sitio (típicamente desde
   `guia-regalos-juguetes.html` y/o desde la página de su franja de edad
   o guía relacionada). Verificar con
   `grep -rl "href=\"<archivo>.html\"" *.html` que aparece al menos una
   vez fuera de sí misma.
8. **Validación básica de HTML**: comprobar que la página no tiene
   `<head>`/`</head>` ni `<html>`/`</html>` duplicados ni mal cerrados, y
   que no hay bloques repetidos (p. ej. un mismo `<!-- PRODUCT START
   asin="..." -->` insertado dos veces). Un chequeo rápido:
   `python -c "import pathlib; t=pathlib.Path('<archivo>.html').read_text(encoding='utf-8'); print(t.count('<head>'), t.count('</head>'))"`
   debe devolver `1 1`.

## Preparado para el futuro: actualizar productos

No existe todavía un comando de "actualizar producto", pero el sistema
está preparado para añadirlo:

- Cada ficha lleva `data-asin="..."` e `id="ASIN"` ocultos y está
  delimitada por `<!-- PRODUCT START asin="..." -->` /
  `<!-- PRODUCT END asin="..." -->`, así que un bloque completo se puede
  localizar y sustituir por ASIN sin depender del resto del formato del
  HTML, y también se puede enlazar directamente desde otra página con
  `<categoria>.html#ASIN`.
- La URL de Amazon original queda siempre en el `href` del botón "Ver en
  Amazon", que sirve de fuente para releer el producto.
- `tools/amazon_import.py <URL> --no-image` releé título/bullets/reseñas
  frescos sin volver a descargar la imagen — es la pieza que usará la
  futura función "Actualizar todos los productos de X.html" para
  regenerar el contenido manteniendo las imágenes ya descargadas.

## Componente reutilizable: "⭐ Favoritos de los papás"

Bloque ligero de recomendación rápida — no es una ficha de producto ni
compite visualmente con ellas. Vive tanto en `css/site.css` (para poder
usarse en cualquier página de categoría) como replicado con las mismas
clases en el `<style>` propio de `guia-regalos-juguetes.html` (la landing
tiene su propia hoja de estilos, separada de `css/site.css`; si el
componente cambia, actualizar los dos sitios).

**Estructura** (ver `tools/favorite_item_template.html` como referencia):
```html
<div class="favorites">
  <h4 class="favorites-title">⭐ Favoritos de los papás</h4>
  <div class="favorites-list">
    <a class="favorite-item" href="<categoria>.html#<ASIN>">
      <img class="favorite-thumb" src="..." alt="..." width="56" height="56" loading="lazy">
      <span class="favorite-info">
        <span class="favorite-name">Nombre corto del producto</span>
        <span class="favorite-rating">⭐ 4,8 · 62.590 valoraciones en Amazon</span>
      </span>
      <span class="favorite-arrow" aria-hidden="true">›</span>
    </a>
    <!-- máximo 5 filas -->
  </div>
</div>
```

Cada `favorite-item` es una **tarjeta con marco** (no una fila suelta):
fondo blanco, borde `1px solid #EAEAEA`, `border-radius:8px`, sombra muy
suave (`box-shadow:0 1px 2px rgba(0,0,0,.06)`) y `padding:16px` vertical y
horizontal. Termina con una flecha `›` en color `--accent` (naranja),
pegada al borde derecho de la tarjeta vía `margin-left:auto` en
`.favorite-arrow`. El contenido interior (imagen, título, valoración) y
sus estilos de tipografía/color no cambian por llevar marco.

Sin subtítulo bajo el título y sin ningún texto/consejo después de la
última tarjeta: el bloque termina justo después del último `favorite-item`.
Cuando una franja de edad tiene `favorites`, no se muestra el `tip-line`
(💡 consejo) que normalmente sigue a los chips de categoría — solo se
muestra ese consejo en las franjas que todavía no tienen favoritos.

**Reglas del componente:**
- Cuatro separaciones fijas alrededor del bloque, iguales en todas las
  franjas de edad:
  1. **24px** entre la última categoría de la sección anterior y el
     título "⭐ Favoritos de los papás". Se fija con `.favorites{margin-top:24px}`
     y, como `.favorites` es siempre el hermano inmediato de `.chips` en
     `guia-regalos-juguetes.html`, ese margen colapsa (CSS) con el
     `margin-bottom` de `.chips`: ambos están fijados a 24px a propósito,
     para que el resultado colapsado sea 24px exactos en vez de que uno de
     los dos "gane" con un valor mayor.
  2. **28px** entre el título y la primera tarjeta (`margin-top:28px` fijo
     en `.favorites-list`, independiente de `--favorites-gap`), un poco
     más suelto que el ritmo entre tarjetas para que el título respire.
  3. **16px exactos** entre tarjetas (cada una con su propio marco), fijados
     con la variable `--favorites-gap: 16px` en `.favorites-list`
     (`gap` para las tarjetas).
  4. **32px** entre la última tarjeta de Favoritos y el título de la
     siguiente franja de edad. Se logra repartiendo el padding vertical de
     `.age-row` de forma asimétrica: `padding-top:26px` (space entre la
     línea divisoria y el título de esa misma franja, sin cambios) y
     `padding-bottom:5px` (en vez de los 26px que tenía antes), de modo
     que 5px + 1px de `border-top` + 26px del `padding-top` de la
     siguiente fila sumen los 32px exactos.
  Ninguno de estos cuatro valores es inline ni hardcodeado en una página
  suelta. Si se necesita cambiar cualquiera, editar `css/site.css` y su
  copia idéntica en el `<style>` de `guia-regalos-juguetes.html` a la vez
  (`.age-row` solo existe en la landing, no en `css/site.css`).
- Máximo **5 productos**. Nunca más.
- Cada fila muestra únicamente miniatura (56×56, `object-fit:contain`),
  nombre en negrita, una línea de valoración y la flecha `›` a la derecha.
  Nunca descripción, beneficios, precio ni botón "Ver en Amazon" — su
  función es la recomendación de un vistazo, no sustituir a la ficha.
- El enlace de cada fila puede ser **interno o externo**, según si el
  producto tiene ya una ficha real en alguna categoría:
  - Si existe una ficha (`<article class="product-card">` con ese
    `id="ASIN"` en alguna página de categoría), el objeto lleva `page`
    (el archivo de esa categoría) y el enlace es interno,
    `<categoria>.html#ASIN`, para que el navegador haga scroll directo a
    la ficha.
  - Si el producto **no** tiene ficha propia todavía, el objeto lleva
    `url` (la URL de Amazon del producto, la misma que usaría el botón
    "Ver en Amazon" si tuviera ficha) y el enlace abre esa URL en una
    pestaña nueva (`target="_blank" rel="noopener"`) en vez de hacer
    scroll interno. Un objeto de favoritos lleva `page` **o** `url`,
    nunca los dos.
  - La lógica de renderizado (en el `<script>` de
    `guia-regalos-juguetes.html`) decide cuál usar comprobando si el
    objeto tiene `page`: `href = p.page ? \`${p.page}#${p.asin}\` : p.url`.
- `valoracion` y `num_valoraciones` deben ser datos reales obtenidos con
  `tools/amazon_import.py` (campos `valoracion` y `num_valoraciones` en su
  JSON de salida) — nunca inventar o redondear estas cifras. Esto aplica
  igual a productos con ficha propia y a los que enlazan directo a
  Amazon: siempre hay que ejecutar `amazon_import.py` para conseguir
  imagen, valoración y nº de valoraciones reales antes de añadirlos a
  Favoritos, aunque no se cree una ficha completa para ellos.
- Formato de la línea de valoración: `⭐ {valoración con coma decimal} · {nº
  de valoraciones con separador de miles} valoraciones en Amazon`.

**Datos de origen:** el bloque `favorites` de cada franja de edad en
`guia-regalos-juguetes.html` (array `bands`) es una lista de objetos
`{asin, name, img, rating, reviews, page}` (ficha propia) o
`{asin, name, img, rating, reviews, url}` (sin ficha propia, enlace
directo a Amazon). Si una franja de edad no tiene `favorites` definido,
el bloque simplemente no se renderiza (no hace falta rellenarlo con datos
de relleno).

## Componente reutilizable: "Producto recomendado"

Mención editorial mínima de un producto dentro del cuerpo de un artículo
(guías tipo `puzzle-3d.html` y sus hijos, u otro contenido editorial) — no
es una ficha de producto ni un bloque de favoritos: es el texto
"Recomendación:" seguido de una tarjeta compacta con miniatura, pensada
como etiqueta editorial que forma parte del contenido, no como CTA de
compra grande.

**Disparador:** este componente se inserta **únicamente** cuando el propio
texto de origen (Word, mensaje del usuario, etc.) trae explícitamente un
bloque con este formato:

```
[PRODUCTO RECOMENDADO]
Nombre: Ravensburger Puzzle 3D Castillo de Neuschwanstein
URL: https://...
[/PRODUCTO RECOMENDADO]
```

Nunca se inserta de oficio ni se sugiere por iniciativa propia — solo
cuando aparece ese marcador exacto.

**Flujo automático al encontrar el marcador** (sin pedir confirmación,
igual que el resto de cambios del proyecto — ver memoria
`workflow_amazon_import`):
1. Ejecutar `python tools/amazon_import.py <URL>` desde la raíz del
   proyecto **únicamente para conseguir la imagen principal** del
   producto (se descarga en `images/`, WebP, igual que para cualquier
   otra importación). No se genera ficha de producto, no se redacta
   descripción y no se extraen/usan reseñas — el resto del JSON que
   devuelve el script (`titulo`, `bullets`, `reviews_muestra`,
   `valoracion`, `num_valoraciones`) se ignora por completo para este
   componente.
2. Sustituir el bloque `[PRODUCTO RECOMENDADO]...[/PRODUCTO RECOMENDADO]`
   por el componente con imagen (variante "tarjeta", ver
   `tools/recommended_product_template.html`), sin modificar el resto del
   artículo.
3. **Si la descarga de imagen falla** (error del script, producto sin
   imagen accesible, etc.), no bloquear la inserción: usar en su lugar la
   variante sin imagen (la píldora simple, ver más abajo) para que el
   componente se muestre siempre aunque no haya imagen.

**Nombre de la tarjeta (`{{NOMBRE}}`):** nunca el nombre literal que trae
el marcador ni el título de Amazon — se reescribe corto y editorial,
siguiendo estas reglas:
- 2-3 palabras como norma general; si con 2 el producto queda
  perfectamente identificado, no añadir una tercera.
- Si el nombre original es muy largo, quedarse solo con las palabras más
  representativas.
- Eliminar palabras comerciales o de relleno: "Puzzle", "3D", "Maqueta",
  "Metálico", "Premium", "Edición", "Coleccionista", "Compatible", "Kit",
  "Modelo", nombre de marca, etc., salvo que sean imprescindibles para
  identificar el producto (p.ej. mantener la marca en "Porsche 911" o
  "Mini Cooper", donde el modelo por sí solo sería ambiguo).
- Nunca cortar palabras ni usar puntos suspensivos ("...").
- Debe leerse como un título editorial, no como el título de Amazon.
- Objetivo estético: la tarjeta `.reco-card` tiene ancho fijo (460px,
  igual en todas, ver `css/site.css`) dimensionado para el nombre más
  largo permitido por esta regla — mantener el nombre dentro de 2-3
  palabras es lo que garantiza que quepa siempre en una sola línea, sin
  necesidad de truncarlo ni de ensanchar la tarjeta.
  Ejemplos: "Big Ben Londres Puzzle 3D Metálico" → "Big Ben" · "Puzzle 3D
  Castillo de Hogwarts Express Edición Coleccionista" → "Castillo
  Hogwarts" · "Puzzle 3D Puente de la Torre de Londres con Luz LED" →
  "Puente Londres" · "Puzzle 3D Torre Eiffel Metal Earth" → "Torre
  Eiffel".
- Excepción: si en la misma página hay dos tarjetas del mismo producto en
  variantes distintas (p.ej. con y sin luz LED), mantener el matiz que
  las distingue (p.ej. "Big Ben" / "Big Ben Led") aunque añada una
  palabra — sin él ambas tarjetas quedarían con el nombre idéntico.

**Estructura de salida — variante con imagen (por defecto):**
```html
<div class="reco-product reco-product--card">
  <strong>Recomendación:</strong>
  <div class="reco-card">
    <img class="reco-card-img" src="{{IMAGEN}}" alt="{{NOMBRE}}" width="80" height="80" loading="lazy">
    <span class="reco-card-body">
      <span class="reco-card-name">{{NOMBRE}}</span>
      <span class="reco-card-sep" aria-hidden="true"></span>
      <a class="reco-card-link" href="{{URL}}" target="_blank" rel="nofollow sponsored noopener">Ver en Amazon →</a>
    </span>
  </div>
</div>
```

**Estructura de salida — variante sin imagen (fallback si falla la
descarga):**
```html
<div class="reco-product">
  <strong>Recomendación:</strong>
  <span class="reco-pill">
    <a class="reco-product-name" href="{{URL}}" target="_blank" rel="nofollow sponsored noopener">{{NOMBRE}}</a>
    <span class="reco-pill-dot" aria-hidden="true">·</span>
    <a class="reco-product-link" href="{{URL}}" target="_blank" rel="nofollow sponsored noopener">Ver en Amazon →</a>
  </span>
</div>
```

Ambas son un `<div>`, no un `<p>`, a propósito: varias páginas de artículo
(p.ej. las guías `puzzles-3d-*.html`) tienen reglas propias de tipo
`p + p` para el espaciado entre párrafos, más específicas en CSS que
`.reco-product` por sí solo. Al no ser `<p>`, esas reglas nunca lo
alcanzan y el margen fijo de abajo se respeta siempre, en cualquier
página donde se inserte.

**Reglas de diseño** (clases `.reco-product*`/`.reco-pill*`/`.reco-card*`
en `css/site.css`):
- `margin-top: 16px`, `margin-bottom: 36px`, fijos en `.reco-product`
  (ambas variantes).
- "Recomendación:" en negrita (`<strong>`), fuera de la tarjeta/píldora.
- **Variante con imagen** (`.reco-card`) — diseño definitivo, fijado el
  06/08/2026 tras varias iteraciones, no volver a rediseñarlo salvo
  petición explícita: tarjeta horizontal, fondo `var(--card)`, borde
  `1px solid var(--accent)`, `border-radius: 12px`. Ancho fijo e
  idéntico en todas las tarjetas (`width: 460px`, con `max-width: 100%`
  para no desbordar en móvil) — ese ancho es el mínimo necesario para
  que quepa el nombre más largo permitido por la regla editorial (2-3
  palabras) sin dejar hueco de sobra en las tarjetas con nombre corto;
  si en el futuro hace falta un nombre más largo que ya no quepa,
  ampliar este valor en vez de romper la regla de "misma anchura para
  todas". Padding `2px 14px` (vertical mínimo a propósito: con la
  miniatura fija en 80×80 no se puede bajar de ~82-86px de alto sin
  recortar la imagen, así que el padding vertical se dejó casi a cero
  para acercarse lo más posible a una tarjeta compacta). Miniatura
  `.reco-card-img` de **80×80** fijo (no reducir sin que el usuario lo
  pida explícitamente — ya se intentó bajar a 52×52 y a 44×44 en
  iteraciones previas y el usuario pidió mantenerla en 80×80), gap de
  16px respecto al nombre, `object-fit: contain`, esquinas redondeadas
  (`border-radius: 9px`). `.reco-card-body` es un **grid** de columnas
  `1fr auto auto` (nombre / separador / enlace), no flex: el nombre
  (`font-weight: 700`, `17px`, color `var(--ink)`) va **centrado**
  (`justify-self: center`) dentro de la columna `1fr`, que ocupa todo el
  espacio libre entre la imagen y el separador — como esa columna mide
  siempre lo mismo (ancho de tarjeta fijo, resto de columnas de ancho
  fijo), el separador y "Ver en Amazon →" quedan siempre en la misma
  posición horizontal en todas las tarjetas, sea cual sea la longitud
  del nombre. Separador (`.reco-card-sep`, 1px × 22px, color
  `var(--line)`) y enlace con `column-gap: 10px` entre sí. "Ver en
  Amazon →" en `var(--accent)`, negrita, `14.5px` fijo (no hereda el
  tamaño del artículo, para que la tarjeta se vea igual en cualquier
  página), sin subrayado (subrayado al hover). En escritorio (≥768px)
  todo va en una sola línea siempre (sin `flex-wrap`, sin truncar) — el
  nombre del producto se redacta corto a propósito (ver reglas
  editoriales más arriba) para que quepa sin necesidad de partir la
  tarjeta en dos líneas.
  **Móvil (`<768px`):** la distribución de una sola línea deja de usarse
  (no cabría sin reducir la fuente ni truncar) y `.reco-card-body` pasa
  de grid a columna vertical (`flex-direction: column`, `gap: 4px`,
  alineado a la izquierda): nombre arriba, "Ver en Amazon →" justo
  debajo, ambos con el mismo tamaño de fuente que en escritorio. El
  separador (`.reco-card-sep`) se oculta (`display: none`). La imagen
  sigue a la izquierda en 80×80 sin cambios, y como el bloque de texto
  apilado mide menos que la miniatura, la altura de la tarjeta no varía
  respecto a escritorio.
- **Variante sin imagen** (`.reco-pill`, fallback): fondo blanco, borde
  `1px solid var(--accent)`, esquinas `border-radius: 9999px`, ~32-33px
  de alto, `padding: 7px 16px`, sin sombra ni icono. `font-size: 13px`
  fijo — más pequeño que el cuerpo del artículo a propósito, para que
  tenga menos protagonismo. Dentro: nombre sin subrayado (mismo color de
  texto que el resto, sin usar `--accent`), un punto `·` centrado como
  separador (`var(--ink-soft)`), y "Ver en Amazon →" en `var(--accent)` y
  negrita.
- Hover (ambas variantes): borde ligeramente más oscuro
  (`color-mix(in srgb, var(--accent) 70%, #000)`) y fondo con un tinte
  muy suave del color de marca (`color-mix(in srgb, var(--accent) 6%,
  var(--card))`), transición de 0.2s. Sin animaciones llamativas.
- Responsive: si el contenido no cabe en una línea, el texto salta de
  línea dentro de la propia tarjeta/píldora (`flex-wrap`) — nunca se
  convierte en un botón grande ni se parte en elementos separados.
- Ambos enlaces llevan `target="_blank" rel="nofollow sponsored noopener"`
  (enlace de afiliado saliente: `nofollow sponsored`, no solo `noopener`
  como en los enlaces internos de Favoritos).

## Sección editorial "Planes en casa" (arquitectura, en desarrollo)

Sección editorial de ocio y actividades para hacer en casa con niños —
promesa: "Ideas para jugar, crear y disfrutar en casa con los niños."
Responde a la necesidad "tengo a los niños en casa, ¿qué podemos hacer?".
No es una sección de crianza, psicología ni desarrollo infantil: nunca
afirmar lo que un niño "debería" conseguir a determinada edad.

**Regla general de toda la sección**: todas las actividades de "Planes en
casa" deben realizarse bajo la supervisión de un adulto responsable, con
materiales adecuados a la edad. Esta nota (ver texto exacto aprobado en
`manualidades-faciles.html`, bloque `.pec-act-callout`) debe aparecer de
forma visible antes de las actividades en cada página de subtipo — no es
opcional, es una directriz fija para toda la sección, no solo para
Manualidades.

**Estado actual:**
- Chip de navegación "Planes en casa" en la navbar de
  `guia-regalos-juguetes.html` (entre "Vida en familia" y "Guía
  Montessori"), enlaza a `planes-en-casa.html`.
- Landing `planes-en-casa.html` creada siguiendo el mismo patrón técnico
  que `vida-en-familia.html` (mismo `<head>`, mismo header simple con
  "← Volver a la guía", mismo `.cat-hero-2` para el hero). Contiene hero +
  intro + 5 tarjetas de área (`.pec-card`, sin enlace todavía — no hay
  páginas de destino aún; no tocar esta landing salvo petición explícita).
- **`manualidades-faciles.html` (primer subtipo, CON CONTENIDO REAL Y
  APROBADO)**: 8 actividades completas (título, edad, tiempo, dificultad,
  materiales, pasos, variante y nota de supervisión), estructura de
  tarjeta `.pec-act-card` en `.pec-act-grid` (2 columnas escritorio, 1
  columna móvil). Breadcrumb funcional "Planes en casa · Manualidades"
  (pill `.cat-hero-2-chip` enlazando a `planes-en-casa.html` — no existe
  todavía una página hub de "Manualidades" separada, así que ese enlace
  es la única ruta real disponible). Indexable (sin `noindex`), en
  sitemap. El párrafo de introducción del hero (`.cat-hero-2-body
  .pec-act-placeholder`) sigue siendo un placeholder pendiente — no se
  proporcionó texto editorial para él en esta fase. **Página huérfana a
  propósito**: no está enlazada desde `planes-en-casa.html` ni desde
  ninguna otra página, porque las instrucciones de esta fase prohibían
  tocar la landing; enlazarla desde la tarjeta "Manualidades" de la
  landing queda pendiente para cuando el usuario lo pida.
- **`dibujo-y-pintura.html` (segundo subtipo, CON CONTENIDO REAL Y
  APROBADO)**: mismo patrón exacto que `manualidades-faciles.html` (8
  actividades, mismo `.pec-act-*`, misma nota de supervisión). A
  diferencia de la primera página, aquí NO se muestra ningún placeholder
  visible para la introducción del hero — al no haber texto editorial
  aprobado todavía, el bloque simplemente se omite (queda un comentario
  HTML indicando dónde insertarlo) en vez de mostrar corchetes en
  producción. Este es el patrón preferido a partir de ahora para
  introducciones pendientes en páginas de "Planes en casa" —
  `manualidades-faciles.html` se dejó con su placeholder visible
  original sin tocar, por no formar parte del encargo que introdujo esta
  preferencia. También huérfana a propósito (sin enlace desde la
  landing), indexable y en sitemap.
- **`manualidades-con-papel.html` (tercer subtipo, CON CONTENIDO REAL Y
  APROBADO, 3+)**: mismo patrón exacto que las dos anteriores (8
  actividades, `.pec-act-*`, callout de supervisión, sin placeholder
  visible de intro). Huérfana a propósito, indexable, en sitemap.
- **`manualidades-con-carton.html` (4+)**, **`manualidades-con-materiales-reciclados.html`
  (4+)**, **`recortar-y-pegar.html` (4+)** y **`manualidades-con-varios-pasos.html`
  (5+)** — todas CON CONTENIDO REAL Y APROBADO, mismo patrón exacto (8
  actividades, `.pec-act-*`, callout de supervisión, sin placeholder
  visible de intro).
- **`manualidades.html` (HUB de Manualidades, creado)**: página
  intermedia entre `planes-en-casa.html` y las subáreas, con H1
  "Manualidades para hacer en casa con niños", intro editorial real (ya
  no placeholder), grid `.pec-hub-*` de 8 tarjetas (2 columnas
  escritorio / 1 móvil) y el mismo `.pec-act-callout` al final de la
  página. De las 8 tarjetas, **7 son enlaces reales** (fáciles, dibujo y
  pintura, papel, cartón, materiales reciclados, recortar y pegar,
  varios pasos) y solo queda **1 pendiente sin enlace** (Manualidades
  creativas avanzadas,
  7+, `.pec-hub-card--pending`, opacidad reducida, sin flecha, div en
  vez de `<a>`, sin etiqueta "PRÓXIMAMENTE" — no existe ese patrón en el
  proyecto). La tarjeta "Manualidades" de `planes-en-casa.html` ahora
  enlaza a este hub (única modificación autorizada en esa landing; se
  añadió también un pequeño hover a esa tarjeta vía `a.pec-card:hover`,
  sin tocar las otras 4 tarjetas que siguen siendo `<div>`).
- **`manualidades-de-creacion-y-diseno.html` (6+)** y
  **`manualidades-creativas-avanzadas.html` (7+)**: completan el bloque,
  mismo patrón `.pec-act-*` con contenido real. La subárea de 6 años no
  estaba en la lista original de 8 subtipos del hub — se añadió sobre la
  marcha como escalón intermedio entre "varios pasos" (5+) y "avanzadas"
  (7+); el hub tiene **9 tarjetas**, todas con enlace real, 0
  pendientes. El texto bajo "Explora las manualidades" dice "Nueve
  formas de crear en casa..." (corregido de "Ocho" al añadir la 9ª
  tarjeta).
- **BLOQUE MANUALIDADES COMPLETO Y CONSISTENTE (cierre de correcciones)**:
  las 9 subáreas tienen página propia con contenido real y aprobado,
  todas enlazadas desde el hub `manualidades.html`: fáciles (2+), dibujo
  y pintura (2+), con papel (edad actualizada, ver nota más abajo), con
  cartón (4+), con materiales reciclados (4+), recortar y pegar (edad
  actualizada, ver nota más abajo), con varios pasos (5+), de
  creación y diseño (6+), creativas avanzadas (7+). **Todas las 9
  páginas, incluidas las 4 más antiguas (fáciles, dibujo y pintura,
  papel, cartón), tienen ya su breadcrumb "Planes en casa · Manualidades"
  apuntando al hub real `manualidades.html`** — la inconsistencia
  original (esas 4 apuntaban a `planes-en-casa.html` por haberse creado
  antes de que el hub existiera) quedó corregida.
  La descripción de la tarjeta "Manualidades de creación y diseño" en el
  hub se reescribió para igualar el tono/extensión de las otras 8
  ("Proyectos para imaginar, diseñar y decidir cómo será el resultado
  final de cada manualidad.") — ya no queda pendiente de revisión.
- **ESTADO ACTUAL (19/08, tras varios ajustes puntuales)**: el hub tiene
  ahora **10 tarjetas** (texto "Diez formas de crear en casa...", ya no
  "Nueve") — se añadió **Construcciones con plastilina (5+)**, movida
  desde el área "Crear y construir" antes de eliminarla por completo
  (ver bloque "Crear y construir — ÁREA ELIMINADA" más abajo). Además,
  dos edades se corrigieron a petición del usuario: **Manualidades con
  papel pasó de 3+ a 4+** y **Recortar y pegar pasó de 4+ a 5+**
  (actualizado en `<title>`, meta description, H1, subtítulo, las 8
  fichas de actividad de cada página y su tarjeta en el hub).
- **`experimentos-faciles.html` (primera subárea de Experimentos, 3+,
  CON CONTENIDO REAL Y APROBADO)**: mismo patrón exacto `.pec-act-*` que
  Manualidades (8 actividades, callout de supervisión, sin placeholder
  visible de intro). Experimentos todavía no tiene hub propio (no existe
  `experimentos.html`), así que el breadcrumb "Planes en casa ·
  Experimentos" enlaza a `planes-en-casa.html`, igual que hacían las
  primeras páginas de Manualidades antes de que su hub existiera — se
  actualizará a un hub real si/cuando se cree, igual que se hizo con
  Manualidades. Criterio de seguridad más estricto que Manualidades:
  nada de fuego, electricidad, productos químicos, objetos cortantes ni
  piezas pequeñas ingeribles. Huérfana a propósito (sin enlace desde la
  landing todavía), indexable, en sitemap. **Actualización 19/08**: la
  actividad "¿Qué objetos atrae el imán?" se eliminó a petición del
  usuario — la página tiene ahora **7 actividades**, no 8 (meta
  description actualizada de "8 experimentos" a "7 experimentos").
- **`experimentos-con-colores.html` (segunda subárea de Experimentos, 4+,
  CON CONTENIDO REAL Y APROBADO)**: mismo patrón exacto. Un campo Tiempo
  usa "Varias horas" en vez de un rango en minutos (actividad "Flores
  que cambian de color") — se dejó tal cual, sin normalizar el formato.
  Mismo criterio de seguridad conservador y mismo breadcrumb provisional
  a `planes-en-casa.html` (Experimentos sigue sin hub propio).
- **`agua-y-liquidos.html` (tercera subárea de Experimentos, 4+, CON
  CONTENIDO REAL Y APROBADO)**: mismo patrón exacto, mismo criterio de
  seguridad, mismo breadcrumb provisional.
- **`naturaleza-y-plantas.html` (cuarta subárea de Experimentos, 4+, CON
  CONTENIDO REAL Y APROBADO)**: mismo patrón exacto. Varios campos
  Tiempo usan formato compuesto ("10 minutos + observación durante
  varios días", "10 minutos al día durante varios días") en vez de un
  rango simple en minutos — se dejaron tal cual, sin normalizar.
  Criterio de seguridad añade restricción específica de esta subárea:
  nunca plantas desconocidas ni potencialmente tóxicas, y nunca llevarse
  hojas/semillas/algodón a la boca.
- **`reacciones-y-transformaciones.html` (quinta subárea de Experimentos,
  5+, CON CONTENIDO REAL Y APROBADO)**: mismo patrón exacto. Restricción
  de seguridad propia y explícita: ningún cuchillo ni actividad de
  cortar fruta/alimentos — el niño nunca manipula objetos cortantes. La
  actividad 6 se sustituyó en el propio encargo (el usuario reenvió el
  prompt cambiando "La manzana que cambia de color" con cuchillo por "El
  papel que se encoge", sin cuchillo) antes de que se diera por cerrada
  esta página; la versión final no contiene manzana ni cuchillo. La
  subárea "Imanes y movimiento" que existía en una lista intermedia fue
  eliminada por el usuario y no debe volver a crearse.
- **`luz-sombras-y-electricidad.html` (sexta subárea de Experimentos, 5+,
  CON CONTENIDO REAL Y APROBADO)**: mismo patrón exacto. Pese al nombre
  de la subárea, esta primera página es solo luz y sombras con
  linterna — el criterio de seguridad prohíbe explícitamente
  electricidad real (enchufes, circuitos, pilas, cables) y también
  fuego/velas/láseres; verificado que ninguno de esos términos aparece
  en el archivo. Nota fija en las 8 actividades: nunca dirigir la
  linterna directamente a los ojos.
- **`pequenos-cientificos.html` (séptima y última subárea de
  Experimentos, 6+, CON CONTENIDO REAL Y APROBADO)**: mismo patrón
  exacto. Cierra el bloque Experimentos (7/7 subáreas). Nota histórica:
  una actividad de "paracaídas de papel" fue eliminada del contenido
  antes de esta entrega — verificado que no aparece en el archivo final,
  y no debe volver a añadirse.
- **BLOQUE EXPERIMENTOS COMPLETO (7/7 subáreas con contenido real)**:
  fáciles (3+), con colores (4+), agua y líquidos (4+), naturaleza y
  plantas (4+), reacciones y transformaciones (5+), luz/sombras/
  electricidad (5+), pequeños científicos (6+). Todas huérfanas a
  propósito (breadcrumb a `planes-en-casa.html`, sin hub propio —
  Experimentos no tiene página hub, a diferencia de Manualidades).
- Las otras 2 áreas de Planes en casa (Crear y construir, Cocinar
  juntos) siguen sin ninguna página ni arquitectura detallada más allá
  de la lista de subtipos de la fase 3.

### Juegos — arquitectura y progreso

Subtipos confirmados por el usuario (distintos a la lista original de la
fase 3, que usaba nombres tipo "Juegos sin materiales/de imaginación"):
Juegos rápidos y sencillos (3+, primera subárea creada) · Juegos de
movimiento (3+) · Juegos de observación (4+) · Juegos de memoria (4+) ·
Juegos de palabras (5+) · Juegos de lógica (5+) · Juegos de retos (6+) ·
Juegos para jugar en familia (3+). Las 7 subáreas pendientes aún no
tienen contenido — no inventarlo, esperar a que se proporcione al crear
cada página.

- **`juegos-rapidos-y-sencillos.html` (primera subárea de Juegos, 3+, CON
  CONTENIDO REAL Y APROBADO)**: mismo patrón exacto `.pec-act-*` que
  Manualidades y Experimentos (8 actividades, callout de supervisión,
  sin placeholder visible de intro). Juegos no tiene hub propio (no
  existe `juegos.html`), así que el breadcrumb "Planes en casa · Juegos"
  enlaza a `planes-en-casa.html`, mismo patrón provisional usado en
  Experimentos. Criterio de seguridad: nada de objetos pequeños/
  cortantes/frágiles, escondites seguros (nunca cerca de enchufes,
  ventanas, escaleras o espacios donde el niño pueda quedar atrapado),
  espacio libre suficiente para juegos de movimiento. Huérfana a
  propósito, indexable, en sitemap.
- **`juegos-de-movimiento.html` (segunda subárea de Juegos, 3+, CON
  CONTENIDO REAL Y APROBADO)**: mismo patrón exacto. Criterio de
  seguridad propio: superficie estable y despejada en todos los
  recorridos, nada de escaleras/muebles como obstáculos/superficies
  elevadas, cinta adhesiva bien fijada sin riesgo de resbalón. Mismo
  breadcrumb provisional a `planes-en-casa.html`.
- **`juegos-de-observacion.html` (tercera subárea de Juegos, 4+, CON
  CONTENIDO REAL Y APROBADO)**: mismo patrón exacto. Enfoque
  exclusivamente en mirar/localizar/comparar/describir — nunca
  convertidas en juegos de memoria o de lógica. Mismo breadcrumb
  provisional a `planes-en-casa.html`.
- **`juegos-de-memoria.html` (cuarta subárea de Juegos, 4+, CON
  CONTENIDO REAL Y APROBADO)**: mismo patrón exacto. Trabaja memoria
  mediante secuencias, parejas, posiciones y sonidos — movimientos y
  gestos siempre lentos y seguros, sonidos suaves, sin objetos frágiles
  ni pequeños. Mismo breadcrumb provisional a `planes-en-casa.html`.
- **`juegos-de-palabras.html` (quinta subárea de Juegos, 5+, CON
  CONTENIDO REAL Y APROBADO)**: mismo patrón exacto. Todas las 8
  actividades son sin materiales (expresión oral, rimas, descripciones,
  cadenas de palabras) — nunca convertidas en ejercicios escolares de
  lectoescritura. Mismo breadcrumb provisional a `planes-en-casa.html`.
- **`juegos-de-logica.html` (sexta subárea de Juegos, 5+, CON CONTENIDO
  REAL Y APROBADO)**: mismo patrón exacto. Trabaja clasificación, orden,
  secuencias, relaciones y elección de forma lúdica — nunca convertidas
  en ejercicios escolares formales ni en juegos de memoria/palabras.
  Mismo breadcrumb provisional a `planes-en-casa.html`.
- **`juegos-de-retos.html` (séptima subárea de Juegos, 6+, CON CONTENIDO
  REAL Y APROBADO)**: mismo patrón exacto. Retos exclusivamente mentales
  y creativos (historias, soluciones, categorías, pistas, instrucciones,
  inventar) — nunca retos físicos, cronómetros de presión ni
  competición que genere frustración; "El reto de inventar" es solo
  imaginativo, no requiere construir nada físicamente. Mismo breadcrumb
  provisional a `planes-en-casa.html`.
- **`juegos-para-jugar-en-familia.html` (octava y última subárea de
  Juegos, 4+, CON CONTENIDO REAL Y APROBADO)**: mismo patrón exacto.
  Cierra el bloque Juegos (8/8 subáreas). Actividades cooperativas entre
  varias personas (turnos, adivinar, construir juntos) — nunca
  competitivas, sin ganadores/perdedores, sin cronómetros de presión.
- **BLOQUE JUEGOS COMPLETO (8/8 subáreas con contenido real)**: rápidos
  y sencillos (3+), movimiento (3+), observación (4+), memoria (4+),
  palabras (5+), lógica (5+), retos (6+), para jugar en familia (4+).
- **HUBS de Experimentos y Juegos creados** (`experimentos.html`,
  `juegos.html`), mismo patrón exacto que `manualidades.html` (grid
  `.pec-hub-*`, callout al final). A diferencia de Manualidades, estos
  hubs se crearon cuando TODAS sus subáreas ya existían, así que las 7 y
  8 tarjetas respectivamente son enlaces reales desde el primer momento,
  sin ninguna pendiente. Los textos de subtítulo de ambos hubs reutilizan
  verbatim la descripción ya aprobada de su tarjeta en
  `planes-en-casa.html`; las descripciones de cada tarjeta del grid las
  redacté yo (parafraseando el contenido real de cada subárea, sin
  inventar datos) — no vinieron dadas literalmente, a diferencia de las
  8 tarjetas del hub de Manualidades. **Las 15 páginas de subárea de
  Experimentos y Juegos NO se tocaron**: sus breadcrumbs siguen
  apuntando a `planes-en-casa.html` en vez de a sus hubs reales —
  inconsistencia conocida, igual que pasó con Manualidades antes de la
  fase de corrección; pendiente de unificar si se pide.
- **`planes-en-casa.html`**: las tarjetas "Experimentos" y "Juegos" ahora
  enlazan a sus hubs reales (antes eran `<div>` sin enlazar porque no
  existían). "Cocinar juntos" sigue sin enlazar (no tiene ninguna página
  todavía). Ver bloque "Crear y construir" más abajo para esa tarjeta.

### Crear y construir — ÁREA ELIMINADA (19/08)

El área completa se eliminó del proyecto a petición del usuario ("la
información es repetitiva"). Antes de borrar, se rescató una subárea:

- **`construcciones-con-plastilina.html` pasó a formar parte de
  Manualidades** (no se borró): se sacó su tarjeta del hub de Crear y
  construir y se añadió a `manualidades.html` (ahora 10 tarjetas, texto
  "Diez formas de crear..."), con nuevo tono `--craft-accent:#C08267`
  (clay/terracota suave, distinto de los ya usados). Su breadcrumb,
  JSON-LD y footer se actualizaron para apuntar a Manualidades en vez de
  a Crear y construir (icono `ti-palette`).
- **Borrados permanentemente** (no estaban en git, sin posibilidad de
  recuperación): `crear-y-construir.html` (hub) y sus otras 5 subáreas —
  `construcciones-y-estructuras.html`, `retos-de-construccion.html`,
  `construcciones-con-materiales-reciclados.html`, `crear-vehiculos.html`,
  `construir-casas-y-refugios.html`.
- `planes-en-casa.html`: tarjeta "Crear y construir" eliminada, grid
  pasó de 5 a 4 tarjetas (Manualidades, Experimentos, Juegos, Cocinar
  juntos) — `.pec-grid` cambiado a `repeat(4, 1fr)` (fila única, sin
  huérfanos) con un breakpoint intermedio a 2 columnas entre 641-900px;
  texto "Cinco formas..." → "Cuatro formas...".
- `tools/generate_sitemap.py`: las 6 URLs borradas se quitaron del set
  `GUIDES` (no se añadieron a `EXCLUDE`, porque a diferencia de
  `preparaciones-sin-horno.html` estos archivos ya no existen en disco).
  `sitemap.xml` regenerado.
- Si el usuario vuelve a pedir esta área en el futuro, no existe ningún
  archivo que reutilizar — habría que crearla desde cero.
- **`cocinar-juntos.html` (HUB, creado)**: mismo patrón exacto que los
  otros 4 hubs. Subtítulo reutiliza verbatim la descripción ya aprobada
  de la tarjeta en `planes-en-casa.html`. Introducción (`.cat-hero-2-body`)
  la redacté yo (no vino dada), igual que se hizo con el hub de Crear y
  construir. Grid con **1 sola tarjeta real** (Cocina fácil).
  `planes-en-casa.html`: la tarjeta "Cocinar juntos" ahora enlaza a este
  hub — con esto, **las 5 tarjetas del hub principal son ya enlaces
  reales, la corrección de navegación queda 100% completa**.
- **`cocina-facil.html` (primera subárea de Cocinar juntos, 3+, CON
  CONTENIDO REAL Y APROBADO)**: mismo patrón `.pec-act-*` que el resto
  del proyecto, con una diferencia intencional: el campo "Materiales" se
  etiqueta **"Ingredientes"** (mismo icono, misma clase, misma
  posición) por ser contenido de cocina — documentar este ajuste de
  etiqueta como el patrón a seguir en el resto de subáreas de Cocinar
  juntos. Enfoque: PONER → AÑADIR → MEZCLAR → APLASTAR → COMBINAR (nunca
  recetas completas ni cocción por parte del niño). Criterio de
  seguridad estricto: nunca fuego, horno, aceite caliente ni cuchillos
  para el niño; cualquier corte/pelado lo hace el adulto previamente;
  aviso de comprobar alergias con lácteos/avena. Enlazada desde
  `cocinar-juntos.html`.
- **`decorar-y-montar.html` (segunda subárea de Cocinar juntos, 3+, CON
  CONTENIDO REAL Y APROBADO)**: mismo patrón exacto (campo "Ingredientes").
  Enfoque: COLOCAR → MONTAR → COMBINAR → DECORAR → CREAR sobre una
  preparación que el adulto deja lista — nunca cocinar desde cero (eso
  es "Cocina fácil"). Regla especial: nunca palillos, brochetas ni
  pinchos — verificado sin esos términos; "Ordena la fruta" coloca la
  fruta en un plato, sin pincharla.
- **`mezclar-ingredientes.html` (tercera subárea de Cocinar juntos, 3+,
  CON CONTENIDO REAL Y APROBADO)**: mismo patrón exacto (campo
  "Ingredientes"). Enfoque: COMBINAR → MEZCLAR → OBSERVAR → COMPARAR —
  el protagonista es el cambio de textura/color al mezclar, nunca una
  receta completa.
- Las 3 subáreas de Cocinar juntos comparten el mismo criterio de
  seguridad: nunca fuego/horno/aceite caliente/cuchillos para el niño,
  con aviso de comprobar alergias e intolerancias (lácteos, avena).
- **`recetas-sencillas.html` (cuarta y última subárea de Cocinar juntos,
  4+, CON CONTENIDO REAL Y APROBADO)**: mismo patrón `.pec-act-*` (campo
  "Ingredientes"), pero con **6 fichas en vez de 8** — el usuario pidió
  exactamente 6 recetas y explícitamente prohibió rellenar hasta 8.
  Recetas: Mantequilla casera en tarro, Limonada casera, Polos caseros
  de fruta, Gazpacho suave, Hummus sencillo, Batido de cacao y plátano.
  Ninguna usa fuente de calor (horno/fuego/sartén/agua o aceite
  caliente/microondas) — verificado. **Ajuste de seguridad aplicado por
  Claude sobre el contenido dado**: la regla global de esta subárea dice
  que batidora/exprimidor los usa EXCLUSIVAMENTE el adulto, pero el
  texto original de "Limonada casera" tenía al niño exprimiendo el
  limón — se cambió ese paso para que el adulto exprima y el niño solo
  coloque las mitades, dejando el resto de la receta intacta. Enlazada
  desde `cocinar-juntos.html`.
- **CIERRE DEFINITIVO DE "COCINAR JUNTOS" (19/08)**: el usuario declaró
  la sección cerrada en exactamente estas 4 subáreas: Cocina fácil (4+, edad actualizada el 19/08 — antes 3+),
  Decorar y montar (3+), Mezclar ingredientes (3+), Recetas sencillas
  (4+). No ampliar, no crear nuevas subáreas ni actividades salvo
  petición expresa; no reintroducir recetas con horno/fuego/sartén/agua
  caliente/microondas. **`preparaciones-sin-horno.html` queda retirada**
  de esta estructura: desenlazada del hub, excluida de `sitemap.xml`
  (añadida a `EXCLUDE` en `tools/generate_sitemap.py` con comentario
  explicativo) y no debe recuperarse ni volver a enlazarse. El archivo
  se dejó en disco sin borrar (acción destructiva no solicitada
  explícitamente) — si el usuario confirma que quiere eliminarlo del
  repo, borrarlo entonces. "Recetas de varios pasos" y cualquier otra
  categoría culinaria nueva tampoco deben crearse salvo petición
  expresa. Regla de calidad fijada por el usuario para el futuro de esta
  sección: priorizar variedad e interés sobre cantidad — nunca rellenar
  con actividades repetitivas solo para alcanzar un número.

### Cabeceras fotográficas de los 5 hubs (aprobadas, 19/08)

Las páginas hub de las 5 áreas (`manualidades.html`, `experimentos.html`,
`juegos.html`, `crear-y-construir.html`, `cocinar-juntos.html`) llevan una
fotografía editorial en la cabecera, sustituyendo el `.cat-hero-2-top`
solo-texto que tenían antes. **La landing `planes-en-casa.html` NO lleva
foto** — sigue con sus 5 tarjetas de icono de color, sin tocar.

**Origen de las fotos**: Pexels (licencia gratuita, uso comercial
permitido), elegidas a mano en el chat tras descartar bastantes
candidatas por look "banco de imágenes"/saturadas/con marca reconocible
(p.ej. se descartó una con fichas tipo Carcassonne, y una con bloques
"Jenga" nombrados explícitamente en la descripción de Pexels). Criterio:
luz natural, composición editorial limpia, tonos suaves, preferencia por
manos/objetos sobre rostros identificables (con alguna excepción cuando
el usuario lo pidió explícitamente, ver Juegos). Fuente/autor de cada
una, por si hay que dar crédito o revisar la licencia:
- Manualidades: "Child Painting with Watercolors in Mexico" — Allan
  González.
- Experimentos: "Girl Dropping Blue Dye on Bowl with Water" — cottonbro
  studio.
- Juegos: "Close-Up Photograph of a Child Laughing with His Mother" —
  Ana Bregantin. Única de las 5 elegida deliberadamente **con rostros
  visibles** — el usuario pidió explícitamente una foto de un padre/madre
  riendo con su hijo, sin apenas objetos alrededor, en vez de una escena
  de "objetos de juego" como las otras candidatas.
- Crear y construir: "Girl in White Long Sleeve Shirt Writing on White
  Paper" — cottonbro studio. Única con rostro parcialmente visible (niña
  mirando hacia abajo, no a cámara); se aceptó como principal por no
  haber encontrado alternativa horizontal sin rostro igual de buena.
- Cocinar juntos: "Girls Cutting Out Cookie Shapes from Dough" — Andy
  Barbour.

**Procesado**: originales descargados a
`images/cabecera/planes-en-casa/*.jpg` y recortados a WebP con
`tools/process_hero_photos.py` (script reproducible — reejecutar si se
cambia alguna foto o el recorte). Dos tamaños de salida según
orientación del original:
- Horizontales (Juegos, Crear y construir, Cocinar juntos): 1400×580,
  pensadas para el patrón banner a ancho completo.
- Verticales (Manualidades, Experimentos): 700×900, pensadas para el
  patrón lateral.

**Patrón "banner horizontal"** (Juegos, Crear y construir, Cocinar
juntos) — clases `.pec-hero-photo` / `.pec-hero-photo-overlay` /
`.pec-hero-photo-content`, copiadas tal cual en el `<style>` propio de
cada una de las 3 páginas (no hay hoja compartida para esto, igual que el
resto del sistema `.pec-hub-*`): foto a ancho completo del bloque
`.cat-hero-2`, `border-radius:20px`, degradado inferior
`linear-gradient` que usa `color-mix(in srgb, var(--accent) 60%,
#1C1C1E)` — es decir, el degradado se tiñe con el acento propio de cada
área, nunca un negro genérico igual en las 5. Breadcrumb, `<h1>` y
subtítulo van superpuestos en blanco sobre la foto, dentro de
`.pec-hero-photo-content`. El párrafo largo de introducción
(`.cat-hero-2-body`), cuando la página lo tiene, se queda **debajo** de
la foto en flujo normal — nunca superpuesto, para no arriesgar
legibilidad de un párrafo largo sobre una fotografía.

**Patrón "lateral"** (Manualidades, Experimentos, fotos verticales) —
clases `.pec-hero-split` / `.pec-hero-split-photo` /
`.pec-hero-split-content`: foto en columna fija de 300px de ancho junto
al bloque de texto (breadcrumb/h1/subtítulo, y el `.cat-hero-2-body`
cuando existe, dentro de la misma columna de texto en vez de debajo).
`.pec-hero-split-content` usa `justify-content:flex-start` (no
`center`) para que el texto arranque a la misma altura que el borde
superior de la foto — quedó mal centrado verticalmente en un primer
intento y se corrigió a petición del usuario. En móvil (`≤768px`) ambos
patrones apilan foto arriba/texto abajo (o viceversa según el patrón).

**Antes de repetir este patrón en una página nueva**: seguir el mismo
proceso — elegir foto en Pexels con estos mismos criterios, procesarla
con `tools/process_hero_photos.py` (añadiendo su entrada al diccionario
`HORIZONTAL`/`VERTICAL` del script), y replicar las clases CSS
exactamente como están en estas 5 páginas.

**Las 4 áreas** (Crear y construir eliminada el 19/08, ver más abajo) **y
sus subtipos futuros** (edad = orientativa editorial, no frontera de
desarrollo — ver regla de edades más abajo):

- **Manualidades** (10 subáreas reales, ver "ESTADO ACTUAL" más abajo):
  Manualidades fáciles (2+) · Dibujo y pintura (2+) ·
  Manualidades con papel (4+) · Manualidades con cartón (4+) ·
  Manualidades con materiales reciclados (4+) · Recortar y pegar (5+) ·
  Manualidades con varios pasos (5+) · Construcciones con plastilina
  (5+, movida desde Crear y construir el 19/08) · Manualidades de
  creación y diseño (6+) · Manualidades creativas avanzadas (7+).
- **Experimentos**: Experimentos fáciles (3+) · Experimentos con colores
  (4+) · Agua y líquidos (4+) · Naturaleza y plantas (4+) · Reacciones y
  transformaciones (5+) · Luces y sombras (5+, renombrada el 19/08 —
  antes "Luz, sombras y electricidad"; el archivo sigue llamándose
  `luz-sombras-y-electricidad.html`, solo cambió el título visible) ·
  Pequeños
  científicos — todas creadas o pendientes en ese orden (ver más abajo).
  "Imanes y movimiento" estaba en una lista intermedia pero el usuario la
  eliminó explícitamente del bloque — no existe y no debe volver a
  añadirse. Nombres de subtipo distintos a la lista original de la fase 3
  (que usaba nombres tipo "Experimentos con agua/aire/hielo/imanes"); las
  2 subáreas pendientes aún no tienen edad orientativa asignada — no
  inventarla, esperar a que se proporcione al crear cada página.
- **Juegos**: Juegos fáciles (2+) · Juegos sin materiales (3+) · Juegos
  de imaginación (3+) · Juegos de observación (3+) · Juegos con papel y
  lápiz (4+) · Juegos para dos (4+) · Juegos para hermanos (4+) · Juegos
  familiares (5+) · Juegos de estrategia (7+).
- **Crear y construir**: Construcciones fáciles (3+) · Construir con
  cajas (3+) · Construir con papel y cartón (4+) · Crear vehículos (4+) ·
  Construir casas y refugios (4+) · Crear circuitos (5+) · Proyectos de
  construcción (6+) · Retos de construcción (7+).
- **Cocinar juntos** (CERRADA el 19/08, ver bloque "CIERRE DEFINITIVO"
  más arriba — no ampliar): Cocina fácil (4+) · Decorar y montar (3+) ·
  Mezclar ingredientes (3+) · Recetas sencillas (4+). "Preparaciones sin
  horno" y "Recetas de varios pasos" quedaron descartadas explícitamente
  y no deben recuperarse. En cocina, "a partir de X años" se refiere a
  poder participar con supervisión adulta adecuada — nunca afirmar que
  un niño de esa edad cocina de forma autónoma.

**Regla de formulación de edades** (aplica a todo el contenido futuro de
esta sección): nunca frases de desarrollo infantil ("los niños de 4 años
pueden...", "a los 5 años ya debería..."). Usar siempre "A partir de X
años" y, cuando corresponda, añadir "Con supervisión adulta cuando sea
necesario". La edad es orientativa: una actividad concreta puede encajar
en una edad ligeramente distinta según su dificultad, materiales y
supervisión necesaria.

**No forzar las franjas de edad generales de la web** (0-6 meses, 6-12
meses, 1-10 años): "Planes en casa" no tiene por qué cubrir todas esas
franjas. Si un área empieza en 2+, empieza en 2+ — nunca inventar
actividades para bebés solo para rellenar la estructura.

### Manualidades — arquitectura detallada (primera área en desarrollo)

Única área trabajada en profundidad por ahora; Experimentos, Juegos,
Crear y construir y Cocinar juntos siguen solo con la lista de subtipos
de arriba, sin desarrollar. Todavía no existe ninguna página de subtipo
ni actividad de Manualidades — esto es solo la arquitectura aprobada
antes de crear contenido real.

Finalidad de cada una de las 8 subáreas:
- **Manualidades fáciles (2+)**: propuestas muy sencillas para empezar —
  pocos materiales, pocos pasos, preparación rápida, resultado sencillo,
  fácil de adaptar.
- **Dibujo y pintura (2+)**: dibujo libre, pintura, estampación, mezclas
  de colores, pintar con distintos materiales, propuestas temáticas.
  Enfoque en disfrutar creando, nunca enseñanza académica del dibujo.
- **Manualidades con papel (4+, editada el 19/08 — antes 3+)**: el papel como material principal —
  doblar, pegar, crear figuras, collage, decoración, personajes,
  animales, flores, elementos para jugar.
- **Manualidades con cartón (4+)**: el cartón como material principal —
  cajas transformadas, casas, vehículos, animales, escenarios, pequeños
  teatros, juegos hechos con cartón, objetos decorativos.
- **Manualidades con materiales reciclados (4+)**: reutilizar objetos
  cotidianos (rollos de cartón, cajas, envases limpios, tapones, papel,
  tubos...). Nunca materiales peligrosos ni envases con riesgo — solo
  materiales domésticos sencillos y seguros.
- **Recortar y pegar (5+, edad actualizada el 19/08 — antes 4+)**: collages, figuras, animales, personajes,
  composiciones, tarjetas, decoraciones. Cuando haya tijeras, indicar
  claramente cuándo hace falta supervisión adulta y qué herramientas son
  apropiadas para la edad.
- **Manualidades con varios pasos (5+)**: algo más elaboradas — varios
  pasos, mayor precisión, preparación de materiales, instrucciones algo
  más largas, resultado más elaborado.
- **Manualidades creativas avanzadas (7+)**: proyectos más largos, mayor
  autonomía, varios materiales, planificación, mayor precisión.
  "Avanzadas" es solo clasificación editorial de dificultad, nunca una
  afirmación sobre el desarrollo del niño.

**Plantilla futura de página de subárea** (no crear todavía, es el
modelo estructural para cuando se apruebe contenido real):
- H1 con patrón `Manualidades <tipo> para niños a partir de <X> años`.
- Introducción breve.
- Sección "Ideas de manualidades" con una o varias actividades, cada una
  con: título, edad orientativa ("A partir de X años"), materiales,
  pasos, dificultad, tiempo aproximado y supervisión si procede.

**Filtros futuros de la sección** (no implementar todavía, dejar la
arquitectura compatible con ellos): por edad (2+ a 10+), por materiales
(papel, cartón, pintura, reciclado...), por tiempo (10/20/30 min, 1 hora)
y por dificultad (fácil, media, más elaborada).

**SEO**: intención de búsqueda práctica ("manualidades fáciles para
niños", "manualidades para niños de 3 años", "manualidades con papel",
"manualidades con cartón", "manualidades para días de lluvia"), sin
sobreoptimizar — el contenido debe responder a la necesidad real antes
que a la keyword.

**Enfoque visual**: mismo lenguaje visual de Lauderem (limpio, alegre,
creativo, familiar, editorial, fácil de consultar) — nunca estética
saturada de colores tipo guardería, y sin emojis decorativos ya que el
sistema visual usa iconografía Tabler propia.

**Pendiente para próximas fases** (no empezar sin que el usuario lo
pida): validar y aprobar esta arquitectura de Manualidades; cuando esté
aprobada, empezar a crear el primer contenido real (todavía no páginas
de subtipo ni actividades). Experimentos, Juegos, Crear y construir y
Cocinar juntos siguen pendientes de este mismo nivel de detalle.

## Cabeceras fotográficas de "Vida en familia" (aprobadas, 19/08)

Las 7 páginas de artículo de la sección "Vida en familia" —
`comprar-mejor.html`, `organizacion-y-hogar.html`,
`cumpleanos-y-celebraciones.html`, `lectura-y-cultura-infantil.html`,
`pantallas-y-ocio.html`, `viajes-y-vacaciones.html`,
`consumo-responsable.html` — llevan foto de cabecera, mismo sistema
`.pec-hero-photo` / `.pec-hero-split` ya usado en los hubs de "Planes en
casa" (ver bloque "Cabeceras fotográficas de los 5 hubs" más arriba),
replicado en el `<style>` propio de cada página. A diferencia de esos
hubs, estas páginas no tienen subtítulo ni `.cat-hero-2-body` en la
cabecera (solo `.cat-hero-2-chip` + `<h1>`), así que el contenido
superpuesto/lateral es más corto.

**Origen de las fotos**: Pexels, mismo criterio que "Planes en casa"
(luz natural, editorial, tonos suaves, preferencia por manos/objetos
sobre rostros). Se relajó la preferencia de "sin rostro" en 2 de las 7
(Pantallas y ocio, Viajes y vacaciones) al no encontrarse una alternativa
igual de buena sin rostro — el usuario lo aprobó explícitamente viendo
la propuesta completa. Autoría:
- Comprar mejor: "A Person in White Long Sleeves Holding a Wooden Toys
  on the Table" — kaboompics.com. No es literal "comprando": representa
  el resultado de elegir un juguete de calidad (montessori, material
  natural, sin marcas visibles). Se descartaron varias opciones por
  mostrar logotipos de marcas reales en una tienda (BRIO, Tonka, Green
  Toys) o por ser fotos de regalos navideños (demasiado estacional).
- Organización y hogar: "Retro Toys and Globe on Cabinet in Nursery
  Room" — Tatiana Syrikova. Se descartó una alternativa de armario real
  demasiado abarrotada (tipo foto inmobiliaria, con juguetes de marca
  visibles) por no encajar con el criterio "sin composiciones llenas de
  objetos".
- Cumpleaños y celebraciones: "Celebratory Cake with Lit Candles
  Indoors" — Manolya İzgi Gezgin.
- Lectura y cultura infantil: "Child Reading a Book" — leeloothefirst.
  Foto de un libro ilustrado en braille (lectura inclusiva).
- Pantallas y ocio: "Child Holding Tablet in Hands During Distance
  Learning" — Julia M. Cameron. Rostro visible a propósito, tono cálido
  y tranquilo — se descartó otra opción por ser demasiado oscura/con
  disfraz de Spider-Man (riesgo de marca Marvel).
- Viajes y vacaciones: "A Toddler Carrying a Bag While Standing Near the
  White Wall" — Cherry Ann Gonzales. Rostro visible a propósito (única
  candidata que mostraba a un niño en vez de a un adulto). El recorte
  vertical estándar del script dejaba demasiado espacio en blanco arriba
  (el sujeto ocupa solo el tercio inferior del original) y tuvo que
  ajustarse a mano — ver comentario en
  `tools/process_hero_photos_vida_en_familia.py`.
- Consumo responsable: "A Box of Donations with Pillows and Stuffed
  Animals" — Gustavo Fring. Caja con etiqueta "DONATIONS" (en inglés,
  aceptado como parte de la foto). Se prefirió sobre una alternativa de
  juguetes de madera por ser más literal (donar/reutilizar) y para no
  duplicar visualmente el mismo concepto que la foto de "Comprar mejor".

**Procesado**: originales en `images/cabecera/vida-en-familia/*.jpg`,
recortados a WebP con `tools/process_hero_photos_vida_en_familia.py`
(mismos tamaños que Planes en casa: 1400×580 horizontales, 700×900
verticales). 3 horizontales (Comprar mejor, Lectura, Pantallas) + 4
verticales (Organización, Cumpleaños, Viajes, Consumo).

## Sistema de sillitas de coche (comparativa, en desarrollo)

Extractor **independiente** de `amazon_import.py` (nunca se toca ese
archivo ni su lógica): `tools/amazon_sillas_coche.py`. Busca en Amazon
España, filtra por 17 marcas autorizadas, deduplica por ASIN y extrae 13
atributos técnicos + precio + valoración + hasta 10 reseñas por producto.
Uso: `python tools/amazon_sillas_coche.py --search "sillita coche"`.

**Capas de cada producto en el JSON:**
- `caracteristicas` / `caracteristicas_fuente`: los 13 atributos "planos"
  originales (no tocar su lógica sin pedirlo).
- `clasificacion`: capa nueva y más fina — `isofix`, `tipo_instalacion`
  (`isofix`/`cinturon_seguridad`/`null`, nunca "ISOFIX + cinturón"),
  `normativa` (`r129_isize`/`r44`/`null`, unifica R129 e i-Size como el
  mismo estándar), `grupo_r44`, `altura_r129`, `peso`, `edad`. Cada campo
  usa el envoltorio `{original, normalizado, mostrar, revisar, fuente,
  url_fuente}`. Regla dura: si un atributo no tiene evidencia textual
  explícita, `normalizado = null` — nunca inventar ni convertir R129 a
  grupo R44 por inferencia, ni edad a partir de altura/peso.
- `opiniones.muestra`: hasta 10 reseñas reales tal cual las presenta Amazon
  por defecto (nunca "las más recientes": el orden de Amazon no es
  necesariamente cronológico). `opiniones.resumen`: **lo redacta Claude
  Code a mano en el chat**, nunca un script/API — ver criterio editorial en
  memoria `feedback_sillas_coche_resumen_opiniones.md` (resumen: nunca usa
  críticas negativas, ni aisladas ni repetidas; sin categorías fijas; texto
  de transparencia fijo debajo).

**Fuente secundaria — web oficial del fabricante** (`tools/fabricante_lookup.json`):
se consulta solo cuando Amazon no confirma un dato técnico. Reglas fijadas:
1. Jerarquía: Amazon → fabricante oficial. Nunca otras tiendas,
   marketplaces, distribuidores, blogs ni comparadores.
2. **Contenido válido = solo lo VISIBLE en la ficha** (descripción,
   características, tablas, FAQs desplegadas). **Nunca** `<title>` HTML,
   meta description, datos estructurados ocultos, snippets de buscador,
   la URL o nombres de archivo — error real cometido con Maxi-Cosi Tanza:
   se leyó el `<title>` SEO ("con cinturón") como si fuera contenido de la
   página; el cuerpo visible decía "Con conectores ISOFIX" sin
   contradicción real. Al usar una herramienta de lectura de página, todo
   lo que aparezca antes de "Source element: `<main>`" es metadato y se
   descarta.
3. **Identidad de producto**: el nombre en Amazon y en el fabricante no
   tienen por qué coincidir (ej. Kinderkraft "JUNIOR FIX 2 PRO" en Amazon =
   "JUNIOR FIX 2 PLUS" en la web oficial). Cada entrada del lookup lleva
   `identidad_verificada` (bool) — exige **al menos 2 señales
   independientes** (SKU/prefijo de familia, características técnicas
   coincidentes, rango de altura, homologación...) antes de dar la
   identidad por buena; nunca solo por parecido de nombre. Si se investigó
   y no se pudo confirmar, la entrada queda con
   `identidad_verificada: false` y se avisa "posible variante/producto
   diferente" en vez de usar el dato o dejar un N/A silencioso. Cuando el
   nombre difiere pero la identidad sí se confirma, se guarda
   `aviso_nombre_diferente: true` + `nombre_amazon`/`nombre_fabricante`/
   `motivo_equivalencia`, sin ocultar la discrepancia.
4. **Contradicciones**: si Amazon y fabricante no coinciden, `revisar =
   true` y `normalizado = null` — nunca se resuelve automáticamente. Antes
   de marcar `revisar`, comprobar: ¿es el mismo producto? ¿una fuente es
   contenido no válido (SEO)? ¿es una diferencia de variante? ¿una fuente
   habla de una función distinta (p.ej. "cinturón" del arnés del niño vs.
   "cinturón" de instalación de la silla)? Solo si tras esos filtros sigue
   habiendo desacuerdo real, queda en revisar. Un humano puede resolver una
   contradicción explícitamente en el chat — se marca
   `resuelto_manualmente: true` en el lookup, con fuente
   `"fabricante_oficial (confirmado manualmente)"`, y esto no cuenta como
   resolución automática.
5. Cuando **solo el fabricante** confirma un dato, se usa igualmente como
   dato de primer nivel (`fuente = "fabricante_oficial"`) — nunca se marca
   como "inferido".
6. `tools/fabricante_lookup.json` **no es un scraper automático**:
   encontrar la página oficial del modelo exacto sin confundirla con una
   variante parecida requiere criterio editorial (se hizo a mano, producto
   a producto). Para ASIN nuevos que no estén en el lookup, la
   clasificación depende solo de Amazon hasta que se investigue y se
   añada su entrada siguiendo estas mismas reglas.

**Scripts auxiliares** (ninguno modifica el extractor): `tools/build_sillas_report.py`
(JSON+Excel con hojas Productos/Reseñas), `tools/build_sillas_comparativa.py`
(añade hoja Comparativa + cobertura), `tools/audit_sillas_na.py` (revisita
fichas en modo lectura para auditar N/A), `tools/reextraccion_lote1_clasificacion.py`
(reprocesa el lote ya cacheado tras cambios de código, sin re-scrapear Amazon).
