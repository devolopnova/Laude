---
name: planes-familia
description: Genera y gestiona propuestas de "Planes en familia" (lugares y actividades familiares fuera de casa, organizadas por provincia) mediante investigación web y verificación editorial, antes de publicarlas en el sitio. Se activa con los comandos "crear plan [PROVINCIA]", "revisar plan [PROVINCIA]", "aplicar plan [PROVINCIA]" y "actualizar plan [PROVINCIA]". Funciona para cualquier provincia de España, no solo Barcelona.
---

# Skill: Planes en familia

Este skill produce, revisa y (solo bajo un comando explícito) publica listados
de hasta 18 lugares/planes familiares por provincia, siguiendo un proceso de
investigación web reproducible. Es la versión formalizada y reutilizable del
proceso ya validado manualmente para Barcelona.

**El skill es genérico por diseño.** `[PROVINCIA]` es siempre una variable de
entrada, nunca un valor fijo. Nada en este documento debe interpretarse como
limitado a Barcelona: Barcelona es únicamente la primera provincia con la que
se probará el skill una vez instalado, no un caso especial de su lógica. Debe
poder ejecutarse tal cual para cualquier provincia española —incluidas Murcia,
Albacete o Alicante— sin tocar este archivo.

## Diferencia editorial con "Planes en casa"

El proyecto ya tiene una sección `planes-en-casa.html` con actividades para
hacer **dentro de casa** (manualidades, experimentos, juegos, cocinar juntos).
"Planes en familia" es un concepto distinto y no debe confundirse ni
mezclarse con ella:

- **Planes en casa** = actividades para realizar en casa con materiales
  caseros, sin necesidad de desplazarse.
- **Planes en familia** = lugares y actividades familiares **fuera de casa**
  (museos, parques, atracciones, teatros...), organizados geográficamente por
  provincia.

Este skill solo gestiona el segundo concepto. No debe tocar, reutilizar ni
reescribir contenido de `planes-en-casa.html` ni de sus subpáginas.

## Principio rector: separación estricta entre investigar y publicar

Ningún comando de este skill excepto `aplicar plan` puede escribir, editar o
publicar nada en el sitio web. Los demás son de solo lectura respecto al
sitio (pueden leer `CLAUDE.md`, páginas existentes, etc. para contexto, pero
nunca modificarlas).

## Comandos

| Comando | Qué hace | ¿Puede tocar la web? |
|---|---|---|
| `crear plan [PROVINCIA]` | Ejecuta la FASE A completa: investigación → cribado → comparación → selección de hasta 18 → datos definitivos → JSON + Excel → validación. | **No** |
| `revisar plan [PROVINCIA]` | Carga el JSON ya generado y presenta el plan para revisión editorial humana. Permite ajustes puntuales. Marca el plan como `reviewed` si el usuario confirma. | No |
| `aplicar plan [PROVINCIA]` | Publica el plan en el sitio. Requiere `plan_status: "reviewed"` y `validation.status: "ok"`. | **Sí — es el único comando que puede** |
| `actualizar plan [PROVINCIA]` | Repite la FASE A desde cero y genera una propuesta **nueva**, sin sobrescribir la versión ya aplicada. | No |

`[PROVINCIA]` se toma literalmente de lo que escriba el usuario tras "plan"
(p. ej. en *"crear plan Murcia"*, `[PROVINCIA]` = `Murcia`). El skill debe
funcionar igual sea cual sea el nombre de provincia recibido — no hay ninguna
lista cerrada de provincias soportadas ni lógica condicionada al nombre.

## Convención de archivos

Cada provincia tiene su propia carpeta de trabajo, nunca mezclada con otras:

```
tools/output/planes-familia/<provincia-slug>/
  plan.json               ← última propuesta generada por "crear plan" o "actualizar plan"
  plan.xlsx                ← copia de revisión editorial (generada junto al JSON)
  plan.applied.json        ← snapshot del último plan efectivamente publicado (solo existe tras un "aplicar plan")
```

`<provincia-slug>` = nombre de la provincia recibida en minúsculas, sin
acentos ni ñ, con espacios sustituidos por guiones (p. ej. `barcelona`,
`murcia`, `albacete`, `alicante`). Esta normalización se aplica siempre igual,
sea cual sea la provincia — no requiere mantenimiento por provincia.

`actualizar plan` **nunca sobrescribe `plan.applied.json`**. Escribe un nuevo
`plan.json` (sobrescribiendo el borrador anterior no aplicado) para que el
usuario lo compare contra lo ya publicado antes de decidir si lo aplica.

---

## FASE A — `crear plan [PROVINCIA]` / `actualizar plan [PROVINCIA]`

Ambos comandos ejecutan exactamente este proceso, con `{PROVINCIA}`
sustituida por el valor recibido. La única diferencia entre ambos es que
`actualizar plan` se usa cuando ya existe un `plan.applied.json` previo y
debe dejarlo intacto (ver comando `actualizar plan` en la Fase B).

### Fase A.1 — Búsquedas

Realizar exactamente estas 3 búsquedas:

1. `"planes con niños {PROVINCIA}"`
2. `"actividades con niños {PROVINCIA}"`
3. `"qué hacer con niños {PROVINCIA}"`

De cada búsqueda, analizar únicamente los **5 primeros resultados
orgánicos**. No buscar más allá de esos 5 por búsqueda. Esto da un máximo de
**15 páginas candidatas** en total (menos si hay duplicados entre las 3
búsquedas).

### Fase A.2 — Cribado de fuentes

De los resultados, quedarse solo con páginas que sean:

- guías de planes con niños;
- listados de actividades infantiles;
- recopilaciones de lugares para visitar en familia;
- artículos tipo "10/20/30/50 lugares...";
- rankings de mejores planes;
- guías familiares (de la provincia o de una ciudad dentro de ella).

Descartar:

- hoteles y alojamientos;
- plataformas de reservas (tickets, tours, actividades reservables como
  resultado principal);
- tiendas;
- publicidad;
- redes sociales;
- páginas exclusivamente promocionales de un único negocio;
- páginas que no sean realmente una guía o listado de planes;
- resultados sin información útil sobre lugares o actividades familiares.

No es necesario conseguir 5 fuentes válidas por búsqueda. Se trabaja solo con
las que superen el cribado, documentando también las descartadas y el motivo
del descarte en `sources_analyzed` / notas internas.

### Fase A.3 — Extracción

Entrar en cada fuente válida y leer su contenido completo (no solo título o
snippet de búsqueda). Extraer únicamente lugares o actividades **concretos y
visitables**.

No extraer:

- categorías generales;
- títulos de secciones;
- fechas;
- autores;
- botones;
- navegación;
- publicidad;
- artículos relacionados.

### Fase A.4 — Normalización

Agrupar variantes del mismo lugar (p. ej. "Tibidabo" / "Parc d'Atraccions
Tibidabo" / "Tibidabo Park" → un solo lugar). No agrupar lugares distintos
solo porque el nombre se parezca.

### Fase A.5 — Comparación

Para cada lugar normalizado, calcular:

- **evidencias** (`evidence_count`): número de artículos que lo recomiendan.
- **medios independientes** (`independent_source_count`): número de dominios
  distintos que lo recomiendan.

**Regla obligatoria:** varios artículos del mismo medio cuentan como
**evidencias diferentes**, pero como **un solo medio independiente**. Por
ejemplo, 3 artículos publicados por el mismo blog sobre esa provincia = 3
evidencias + 1 medio independiente, nunca 3 medios independientes.

Además de estos dos números, tener en cuenta al comparar: relevancia
familiar del lugar, variedad de tipos de plan (no seleccionar solo museos, o
solo parques), y reconocimiento/interés del lugar. El ranking final no se
basa únicamente en el orden de aparición en Google.

### Fase A.6 — Selección de hasta 18 lugares

Seleccionar como máximo 18 lugares:

- puestos 1–15 → `status: "primary"`;
- puestos 16–18 → `status: "backup"`.

Los backups existen para poder sustituir posteriormente, en `revisar plan`, a
un primary que editorialmente no convenza, sin tener que volver a investigar.

**No forzar el número 18.** Si el cribado y la comparación no arrojan
suficientes candidatos con calidad editorial real (relevancia familiar
genuina, algo de respaldo entre fuentes), generar menos de 18 en vez de
rellenar con lugares débiles, irrelevantes o mal justificados. Documentar en
`selection_notes` cuántos se buscaban y cuántos se consiguieron, y por qué.

**No continuar a la Fase A.7 hasta tener cerrada esta selección.** Título,
descripción, URL y dirección definitivos no se investigan antes de este
punto, ni para los seleccionados ni para los descartados.

### Regla editorial obligatoria — Diversificación del patrimonio histórico/arqueológico

Esta regla se aplica **durante la Fase A.6** (cribado y selección de
candidatos), nunca como corrección posterior de un ranking ya cerrado. Es
general para **todas las provincias** — ninguna provincia queda exenta de
ella la próxima vez que se ejecute su Fase A (incluida una futura
`actualizar plan Tarragona`).

**No es retroactiva.** Los planes ya generados antes de que esta regla
existiera (Barcelona, Valencia, Tarragona) no se revisan ni se regeneran
solo por la existencia de esta regla — se quedan tal como están. La regla
se aplica a partir de ahora hacia adelante, la primera vez que la Fase A.6
de cualquier provincia (nueva o ya existente) se vuelva a ejecutar.

"Planes en familia" debe estar orientado principalmente a experiencias y
lugares con atractivo real para niños y familias, no simplemente a lugares
turísticos que puedan visitarse acompañado de niños. Los lugares cuyo
atractivo principal sea patrimonio histórico o arqueológico —por ejemplo
anfiteatros romanos, circos romanos, teatros romanos, ruinas arqueológicas,
restos romanos, murallas, cascos históricos y lugares de características
equivalentes— pueden incluirse cuando tengan interés familiar, pero deben
considerarse propuestas **secundarias** dentro de la selección:

1. Ningún lugar de este tipo puede ocupar las posiciones 1–6 del ranking
   `primary` cuando existan alternativas familiares válidas para esas
   posiciones.
2. Estos lugares solo pueden aparecer a partir de la posición 7.
3. Como máximo **2 lugares** de este tipo entre los 15 `primary` de una
   provincia.
4. Si hay 3, 4 o más candidatos de esta naturaleza, no se incluyen todos por
   el simple hecho de estar bien posicionados en las búsquedas —
   seleccionar como máximo los 2 con mayor interés familiar y/o mayor
   diferenciación entre sí.
5. No dar por hecho que un castillo pertenece automáticamente a esta
   categoría. Un castillo puede ocupar una posición superior si presenta un
   atractivo familiar claro (por su visita, entorno, actividades, historia
   especialmente atractiva para niños o experiencia familiar).
6. La presencia de patrimonio histórico/arqueológico nunca debe dejar la
   lista final excesivamente concentrada en propuestas similares — la
   selección debe buscar diversidad real de experiencias.
7. Cuando existan candidatos válidos, la prioridad editorial de las
   primeras posiciones debe favorecer experiencias con atractivo
   infantil/familiar más evidente: animales, ciencia, naturaleza, parques,
   ocio, actividades, experiencias interactivas, museos especialmente
   adecuados para familias, etc.
8. Esta regla no significa eliminar el patrimonio histórico: uno o dos
   lugares de este tipo son perfectamente válidos y aportan variedad a la
   guía. Lo que se pretende evitar es que una provincia termine con una
   lista dominada por anfiteatros, circos, ruinas, cascos históricos y
   lugares similares.

### Fase A.7 — Datos definitivos (solo sobre los ya seleccionados)

Solo ahora, y solo para los lugares seleccionados en la Fase A.6, investigar:

**Título** — nombre correcto y reconocible del lugar.

**Descripción** — 2–4 frases, redactada específicamente para Lauderem
(original, no copiada literalmente de ninguna fuente). Debe explicar
claramente: qué es el lugar, qué puede encontrar allí una familia, y qué tipo
de experiencia o plan ofrece. Nunca genérica ("es un museo situado en...").
Nunca con características inventadas: solo lo verificado en la
investigación.

**URL oficial** (`official_url`) — buscar y verificar la web oficial del
propio lugar. Nunca usar como URL principal la página de descubrimiento
(el medio/guía donde se encontró el lugar) si existe una web oficial
identificable — esa URL de descubrimiento se conserva en `sources`, no en
`official_url`. Si no se puede verificar una web oficial con suficiente
seguridad: `"official_url": null` y `"url_verified": false`. Nunca inventar
URLs.

**Dirección** (`address`) — buscar únicamente después de haber seleccionado
los candidatos finales, preferentemente en la web oficial o una fuente
fiable. No es necesaria una investigación exhaustiva: si no está disponible
de forma clara, usar `null` y continuar, sin deducirla ni inventarla.

**Discrepancias de dirección entre fuentes:** priorizar en este orden:
1. la fuente oficial del propio lugar;
2. si no hay fuente oficial con dirección, la dirección en la que coincidan
   varias fuentes independientes;
3. si sigue sin resolverse, `"address": null`.

Nunca elegir una dirección al azar entre varias contradictorias ni inventar
una intermedia.

### Fase A.8 — Rastro de auditoría dentro de cada lugar

Cada lugar del JSON conserva, además de sus datos definitivos:

- `sources`: lista de fuentes de descubrimiento que lo recomendaron (nombre,
  dominio, URL, evidencia textual).
- `evidence_count`: calculado en la Fase A.5.
- `independent_source_count`: calculado en la Fase A.5.

Este rastro existe para poder justificar editorialmente, en cualquier
momento (incluido durante `revisar plan`), por qué aparece cada lugar en el
plan — no es información desechable tras la selección.

### Fase A.9 — Generación de salida

Generar, en `tools/output/planes-familia/<provincia-slug>/`:

1. **`plan.json`** — la **fuente de verdad**. Es el único artefacto
   estructurado que `aplicar plan` leerá para publicar en la web. Esquema
   completo más abajo.
2. **`plan.xlsx`** — copia de revisión editorial, no la fuente de verdad. Una
   fila por lugar, con columnas legibles: rank, status, name, description,
   official_url, url_verified, address, evidence_count,
   independent_source_count, y una columna de fuentes resumida. Pensado para
   que un humano lo revise fuera de Claude Code si lo prefiere.

### Fase A.10 — Validación

Validar `plan.json` antes de darlo por terminado. Cada problema encontrado
se clasifica en una de estas dos categorías:

**Errores bloqueantes** (impiden que el plan pueda pasar a `aplicar plan`):

- JSON inválido o mal formado.
- Estructura incorrecta (faltan claves obligatorias del esquema).
- Campos obligatorios ausentes o vacíos (`name`, `description`,
  `province`, `rank`, `status`).
- Lugares duplicados (mismo lugar dos veces, por nombre normalizado o por
  `official_url`), incluidos duplicados bajo nombres ligeramente distintos
  que en realidad son el mismo lugar.
- Incoherencia entre `name` y `official_url` (la URL no corresponde
  razonablemente al lugar nombrado).
- `status` con un valor fuera de `"primary"` / `"backup"`.
- `rank` repetido, ausente, o fuera del rango esperado (1–18, o 1–N si hay
  menos de 18 lugares).
- Número de `primary` que no coincide con `min(15, total de lugares)`, o
  `backup` que no coincide con el resto.
- `evidence_count` menor que `independent_source_count` (imposible: nunca
  puede haber más medios independientes que evidencias totales).
- Descripciones incoherentes con el resto de datos del propio lugar (p. ej.
  describen un tipo de plan que no encaja con el `name`).

**Advertencias** (no impiden aplicar el plan, pero deben mostrarse siempre
con claridad al usuario en `revisar plan`):

- `address: null` por no haberse podido verificar.
- `official_url: null` por no haberse encontrado una web oficial con
  suficiente seguridad.
- Información limitada sobre un lugar (pocas evidencias o descripción corta
  dentro del rango permitido).
- Empate editorial entre dos lugares candidatos a un mismo puesto.
- Menos de 18 candidatos disponibles en total.
- URL oficial encontrada pero de baja confianza (p. ej. el sitio bloqueó la
  verificación automática y solo hay corroboración indirecta por búsqueda,
  no por lectura directa de la página).

Si hay **errores bloqueantes**: `plan_status: "draft_with_issues"` y
`validation.status: "issues_found"`, listando cada error en
`validation.issues` con su categoría, descripción y el lugar afectado (si
aplica). El plan no puede marcarse `reviewed` ni aplicarse hasta corregirlos.

Si solo hay advertencias (o ninguna incidencia): `plan_status: "draft"` y
`validation.status: "ok"`, con las advertencias igualmente listadas en
`validation.issues` (categoría `warning`) para que `revisar plan` las
muestre.

**`crear plan` y `actualizar plan` terminan aquí. Ninguno de los dos escribe
ni modifica ningún archivo del sitio público** (HTML, CSS, `sitemap.xml`,
navbar, etc.) **ni ejecuta código de aplicación.** Ambas fases producen
exclusivamente datos (`plan.json` + `plan.xlsx`).

---

## Esquema de `plan.json`

```json
{
  "province": "",
  "province_slug": "",
  "generated_at": "",
  "searches": [
    "planes con niños {PROVINCIA}",
    "actividades con niños {PROVINCIA}",
    "qué hacer con niños {PROVINCIA}"
  ],
  "plan_status": "draft | draft_with_issues | reviewed | applied",
  "selection_notes": "",
  "sources_analyzed": [
    {
      "name": "",
      "domain": "",
      "url": "",
      "title": "",
      "included": true,
      "exclusion_reason": null,
      "places_extracted_approx": 0
    }
  ],
  "validation": {
    "status": "ok | issues_found",
    "issues": [
      {
        "severity": "blocking | warning",
        "category": "",
        "message": "",
        "place_rank": null
      }
    ]
  },
  "places": [
    {
      "rank": 1,
      "status": "primary",
      "name": "",
      "description": "",
      "official_url": null,
      "url_verified": false,
      "address": null,
      "evidence_count": 0,
      "independent_source_count": 0,
      "sources": [
        { "name": "", "domain": "", "url": "", "evidence": "" }
      ]
    }
  ]
}
```

Notas sobre el esquema:

- `sources_analyzed` incluye también las páginas descartadas en el cribado
  (`included: false` + `exclusion_reason`), para dejar constancia de que se
  revisaron los 15 candidatos.
- `places` puede tener menos de 18 elementos si la Fase A.6 no encontró
  suficientes candidatos válidos — nunca se rellena artificialmente para
  llegar a 18.
- Este esquema es el mismo para cualquier provincia; no cambia ni se
  extiende por provincia.

---

## FASE B — comandos posteriores a la investigación

Estos tres comandos quedan definidos ahora en su contrato (qué reciben, qué
producen, qué condiciones exigen), para que el usuario pueda empezar a
invocarlos por nombre. Su lógica interna de aplicación sobre el sitio (qué
HTML exacto se genera, con qué plantilla) se desarrollará en detalle cuando
se aborde esa fase — no se implementa en esta primera versión del skill, y
por eso `crear plan`, `revisar plan` y `actualizar plan` no generan ningún
código de aplicación.

### `revisar plan [PROVINCIA]`

- Lee `tools/output/planes-familia/<provincia-slug>/plan.json`. Si no
  existe, informa que hay que ejecutar `crear plan [PROVINCIA]` primero.
- Muestra siempre el ranking completo (1–18 o los que haya) con su estado
  (`primary`/`backup`), descripción, URL y dirección.
- Muestra siempre, con claridad, los errores bloqueantes y las advertencias
  de `validation.issues`, diferenciando unos de otras.
- Si hay errores bloqueantes, deja claro que el plan no puede aplicarse
  todavía y qué haría falta corregir.
- Permite ajustes puntuales sobre el JSON existente a petición explícita del
  usuario (p. ej. "cambia el puesto 14 por el suplente 17", "corrige esta
  descripción", "vuelve a comprobar esta dirección"), conservando el rastro
  de auditoría (`sources`, `evidence_count`, `independent_source_count`) de
  cada lugar tocado.
- No repite la investigación completa por sí solo — solo re-investiga un
  dato puntual si el usuario lo pide expresamente para ese lugar concreto.
- Marca `plan_status: "reviewed"` únicamente cuando el usuario confirme
  explícitamente que el plan le convence tal como está.
- No modifica nada del sitio web bajo ninguna circunstancia.

### `aplicar plan [PROVINCIA]`

- **Único comando de todo el skill autorizado a modificar el sitio.**
- Requiere `plan_status: "reviewed"` **y** `validation.status: "ok"` (sin
  errores bloqueantes pendientes). Si cualquiera de las dos condiciones no
  se cumple, se niega a aplicar y explica exactamente qué falta.
- Al aplicar, sigue las reglas y checklist de `CLAUDE.md` para páginas HTML
  nuevas del proyecto (GA4, AdSense, canonical, meta description, enlace
  interno desde otra página real, regeneración de `sitemap.xml`, validación
  básica de HTML) — este skill no las repite, se remite a `CLAUDE.md` como
  fuente de esas reglas.
- No hace commit ni push automático salvo que el usuario lo pida
  explícitamente en esa misma conversación, siguiendo las reglas generales
  ya establecidas para este proyecto.
- Redacta y publica el **texto SEO introductorio de cabecera** de la
  provincia siguiendo la regla fija de la siguiente sección — nunca deja el
  subtítulo genérico ("Lugares para visitar y planes para hacer en familia
  en [PROVINCIA].") como texto final.
- Añade la **nota de transparencia sobre las imágenes** al final de la
  página, siguiendo la regla fija de la sección correspondiente más abajo.
- **Nunca añade un `<footer>` con el texto genérico** "Planes en familia es
  la sección de Lauderem con lugares y planes para hacer en familia fuera
  de casa, organizados por provincia." — ese footer se quitó explícitamente
  de las páginas de provincia el 23/08/2026 (redundante con la nota de
  transparencia y con el propio hub); la página de provincia termina justo
  después del párrafo `.pf-disclaimer`, sin footer propio. Sí sigue
  existiendo en el hub raíz `planes-en-familia.html`, que no se toca.
- Al terminar, copia el plan aplicado a
  `tools/output/planes-familia/<provincia-slug>/plan.applied.json` y marca
  `plan_status: "applied"` en el `plan.json` de trabajo.

### Texto SEO introductorio de cabecera (regla fija, aplica en todo `aplicar plan`)

Cada página de provincia lleva, debajo del `<h1>Planes en familia en
[PROVINCIA]</h1>` y antes del listado de tarjetas, un párrafo único
`<p class="cat-hero-2-body">...</p>` (sustituye al antiguo
`<p class="cat-hero-2-subtitle">` genérico — esa clase ya no se usa en estas
páginas). Regla establecida el 22/08/2026, aplicada retroactivamente a
Barcelona, Valencia, Tarragona, Lleida y Girona; se aplica igual a toda
provincia nueva:

- **Longitud**: 35–50 palabras.
- **Tres expresiones obligatorias, cada una exactamente una vez, en frases
  distintas y naturales**:
  1. `"planes con niños"`
  2. `"actividades"` (la palabra sola — **nunca** `"actividades con niños"`,
     para no repetir "niños" más de lo necesario; dentro de una página
     titulada "Planes en familia en [PROVINCIA]" queda perfectamente
     contextualizada sin la coletilla).
  3. `"qué hacer con niños"`
- No repetir ninguna de las tres. No usar "niños" más veces de las
  estrictamente necesarias (en la práctica, solo dentro de esas dos frases
  que lo requieren — 2 apariciones totales, ni una más).
- **Específico de la provincia, nunca genérico con el nombre cambiado**:
  antes de redactar, leer los lugares reales ya seleccionados en
  `plan.json`/la página (nombres de `places`) y las características propias
  de la provincia (costa, montaña, patrimonio, parques temáticos,
  naturaleza...), e incorporar 2–4 referencias concretas de esa provincia.
  Nunca reutilizar la misma estructura de frase de una provincia en otra.
- Vocabulario de apoyo natural (usar cuando tenga sentido, no todos a la
  vez): planes familiares, excursiones, lugares para visitar, experiencias
  en familia, ocio familiar, naturaleza, cultura, patrimonio, aire libre.
- Tono cercano, natural, atractivo, útil — nunca publicitario ni
  sobreoptimizado (sin keyword stuffing, sin frases forzadas solo para
  encajar una keyword).
- **Prohibido mencionar**: investigación, verificación, metodología,
  fuentes, proceso editorial, selección de lugares, SEO. El usuario debe
  sentir que lee una introducción útil a los planes de esa provincia, no una
  explicación de cómo se hizo la página.
- Ejemplos ya publicados (una vez por provincia, no reutilizables tal
  cual para otra): Barcelona → Zoo/Tibidabo/CosmoCaixa; Valencia → Ciudad de
  las Artes y las Ciencias/Oceanogràfic/Bioparc/Jardines del Turia;
  Tarragona → Costa Daurada/Delta de l'Ebre/PortAventura World/Ferrari Land;
  Lleida → Pirineo/Aigüestortes/Parc Astronòmic del Montsec; Girona →
  naturaleza/excursiones/Costa Brava (ver HTML de cada página para el texto
  exacto).

### Nota de transparencia sobre las imágenes (regla fija, aplica en todo `aplicar plan`)

Cada página de provincia lleva, al final del contenido — después de todas
las tarjetas de lugar (`</div>` que cierra `.pf-place-list`) y antes del
`<footer>` — un párrafo con esta nota, **texto exactamente igual en todas
las provincias, sin variarlo ni una palabra**:

```html
  <p class="pf-disclaimer">Las imágenes de esta página son meramente ilustrativas y pueden no coincidir exactamente con el aspecto real o actual de cada lugar. Se utilizan como apoyo visual para ayudarte a descubrir nuevos planes en familia. Antes de organizar tu visita, consulta la web oficial del destino para ver imágenes reales del lugar y comprobar horarios, precios, actividades, accesos y demás información actualizada.</p>
```

Regla establecida el 23/08/2026, aplicada retroactivamente a las 6
provincias ya publicadas en ese momento (Barcelona, Tarragona, Valencia,
Lleida, Girona, Madrid); se aplica igual a toda provincia nueva.

- Clase `.pf-disclaimer` ya definida en `css/site.css` (compartida, no
  duplicar en el `<style>` propio de cada página; ajustada el 23/08/2026 a
  caja informativa tras feedback del usuario — no era solo un párrafo
  suelto): caja con fondo crema muy suave (`#FBF8F1`), borde fino
  `1px solid var(--line)`, `border-radius:13px`, `padding:18px 20px`,
  `margin-top:30px` respecto a la última tarjeta, ancho igual al del
  contenido de la página (sin `max-width` propio, hereda el de `.wrap`).
  Tipografía más discreta que el contenido principal (`font-size:12.5px`,
  gris/azul suave vía `color-mix` sobre `var(--ink-soft)`). Nunca un aviso
  legal ni un elemento destacado — debe leerse como nota secundaria
  elegante, sin título ni icono.
- Nunca dentro de una tarjeta de lugar (`.pfb-card`/`.pf-place-row`) — es un
  párrafo de página, hermano de `.pf-place-list`, no un hijo de ninguna
  tarjeta.
- Sin título encima ("Aviso", "Nota", etc.) — el párrafo va solo.
- "web oficial" se queda como texto normal, no como enlace: la nota es
  genérica de toda la página (no de un lugar concreto), así que no hay una
  única web oficial a la que enlazar sin ambigüedad — cada tarjeta ya tiene
  su propio enlace "Visitar web oficial" individual.
- No confundir con el texto SEO introductorio de la sección anterior (ese
  va debajo del `<h1>`, este va al final de la página) — ambos son
  independientes y coexisten.

### `actualizar plan [PROVINCIA]`

- Repite íntegra la FASE A (búsquedas, cribado, extracción, normalización,
  comparación, selección de hasta 18, datos definitivos, salida y
  validación) y escribe un `plan.json` **nuevo**.
- Nunca sobrescribe `plan.applied.json`, y no publica nada por sí mismo — el
  resultado es, de nuevo, un borrador (`draft` o `draft_with_issues`)
  pendiente de pasar por `revisar plan` y, después, si se decide, por
  `aplicar plan`.
- Útil para detectar lugares cerrados, cambios de URL o dirección, o nuevos
  planes que hayan aparecido desde la última vez.

---

## Reglas absolutas (aplican a todos los comandos)

- No inventar lugares, URLs, direcciones ni características de las
  descripciones.
- No confundir una categoría, título de sección o elemento de navegación con
  un lugar real.
- No contar varios artículos del mismo medio como varios medios
  independientes: 1 medio = 1 `independent_source_count`, aunque tenga
  varios artículos (`evidence_count`).
- Analizar únicamente los 5 primeros resultados orgánicos de cada una de las
  3 búsquedas — nunca más.
- Cerrar primero la selección de hasta 18 lugares (Fase A.6) antes de
  investigar título, descripción, URL oficial o dirección definitivos
  (Fase A.7).
- No investigar datos detallados de lugares que no hayan sido seleccionados.
- Ante discrepancias de dirección: fuente oficial > consistencia entre
  fuentes independientes > `null`. Nunca inventar ni deducir.
- El JSON debe ser válido y completo; el Excel es una copia de revisión, no
  la fuente de verdad (el JSON lo es).
- Solo `aplicar plan` puede modificar el sitio web. `crear plan`,
  `revisar plan` y `actualizar plan` son de solo lectura respecto al sitio.
- No generar código de aplicación (scripts de publicación) como parte de
  `crear plan`, `revisar plan` ni `actualizar plan` — esas fases producen
  datos, no automatizaciones. La automatización de `aplicar plan` se
  desarrollará en una fase posterior.
- El skill nunca depende del nombre de una provincia concreta: toda la
  lógica anterior debe funcionar igual para cualquier provincia española que
  reciba como `[PROVINCIA]`.
- No mezclar ni confundir este contenido con la sección "Planes en casa"
  (`planes-en-casa.html` y sus subpáginas), que cubre un tipo de plan
  distinto (actividades dentro de casa, no lugares para visitar).
