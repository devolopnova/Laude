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
