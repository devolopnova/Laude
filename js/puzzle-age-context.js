/*
  Navegacion contextual entre las paginas de puzzles por edad y los
  articulos generales de puzzles (puzzle-3d.html y
  puzzles-y-rompecabezas.html). Al salir de una pagina de edad hacia
  cualquiera de esos dos articulos se guarda esa edad en localStorage;
  ambos articulos leen ese valor para adaptar su acceso "Puzzles por
  edad". Sin peticiones al servidor, sin recargas ni dependencias
  externas.
*/
(function () {
  var STORAGE_KEY = 'puzzleAgeContext';

  var AGE_PAGES = {
    'puzzles-0-6-meses.html': '0-6 meses',
    'puzzles-6-12-meses.html': '6-12 meses',
    'puzzles-1-ano.html': '1 año',
    'puzzles-2-anos.html': '2 años',
    'puzzles-3-anos.html': '3 años',
    'puzzles-4-anos.html': '4 años',
    'puzzles-5-anos.html': '5 años',
    'puzzles-6-anos.html': '6 años',
    'puzzles-7-anos.html': '7 años',
    'puzzles-8-anos.html': '8 años',
    'puzzles-9-anos.html': '9 años',
    'puzzles-10-anos.html': '10 años'
  };

  // Paginas generales cuyo acceso "Puzzles por edad" debe adaptarse.
  var TARGET_PAGES = ['puzzle-3d.html', 'puzzles-y-rompecabezas.html'];

  function currentFile() {
    var path = window.location.pathname;
    return path.substring(path.lastIndexOf('/') + 1) || '';
  }

  var file = currentFile();

  // En una pagina de puzzles por edad: al pulsar cualquiera de los
  // accesos hacia los articulos generales, guardar de que edad se viene.
  if (Object.prototype.hasOwnProperty.call(AGE_PAGES, file)) {
    TARGET_PAGES.forEach(function (target) {
      var link = document.querySelector('.specials-card[href="' + target + '"]');
      if (link) {
        link.addEventListener('click', function () {
          try {
            localStorage.setItem(STORAGE_KEY, JSON.stringify({ file: file, label: AGE_PAGES[file] }));
          } catch (e) {}
        });
      }
    });
  }

  // En puzzle-3d.html o puzzles-y-rompecabezas.html: leer el contexto
  // guardado y adaptar el acceso "Puzzles por edad". Si no hay contexto
  // (o no es valido), se deja el acceso generico ya presente en el HTML.
  if (TARGET_PAGES.indexOf(file) !== -1) {
    var card = document.querySelector('[data-puzzle-age-card]');
    if (!card) return;

    var ctx = null;
    try {
      var raw = localStorage.getItem(STORAGE_KEY);
      if (raw) ctx = JSON.parse(raw);
    } catch (e) {}

    var isValid = ctx && ctx.file && AGE_PAGES[ctx.file] === ctx.label;
    if (!isValid) return;

    var nameEl = card.querySelector('.puzzle-other-name');
    var descEl = card.querySelector('.puzzle-other-desc');
    var btnEl = card.querySelector('.puzzle-other-btn');

    card.setAttribute('href', ctx.file);
    if (nameEl) nameEl.textContent = 'Puzzles para ' + ctx.label;
    if (descEl) descEl.textContent = 'Encuentra puzzles pensados para niños y niñas de ' + ctx.label + '.';
    if (btnEl) btnEl.textContent = 'Ver puzzles para ' + ctx.label + ' →';
  }
})();
