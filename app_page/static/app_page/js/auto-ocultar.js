/* ==========================================================================
   Parking Control - auto-ocultar
   Oculta solo cualquier elemento marcado con data-auto-ocultar="<ms>".
   El elemento se desvanece y despues sale del flujo (display:none), de modo
   que el contenido inferior sube y no queda hueco.

   Uso:  <div class="row mb-4" data-auto-ocultar="5000"> ... </div>

   Los estilos .auto-ocultar-fade / .auto-ocultar-oculto viven en
   app_page/css/theme.css.
   ========================================================================== */

(function () {
    'use strict';

    var RETARDO_POR_DEFECTO = 5000;
    var DURACION_FUNDIDO = 500; // debe coincidir con la transicion de theme.css

    function prefiereMenosMovimiento() {
        return window.matchMedia &&
               window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    }

    function retirarDelFlujo(el) {
        el.style.display = 'none';
    }

    function programarOcultado(el) {
        var retardo = parseInt(el.getAttribute('data-auto-ocultar'), 10);
        if (isNaN(retardo) || retardo < 0) {
            retardo = RETARDO_POR_DEFECTO;
        }

        // Sin animacion si el usuario la ha desactivado en el sistema.
        if (prefiereMenosMovimiento()) {
            window.setTimeout(function () {
                retirarDelFlujo(el);
            }, retardo);
            return;
        }

        // La clase de transicion la pone el JS, no la plantilla: si el
        // JavaScript no se ejecuta, el aviso simplemente sigue visible.
        el.classList.add('auto-ocultar-fade');

        window.setTimeout(function () {
            var yaRetirado = false;

            function finalizar() {
                if (yaRetirado) {
                    return;
                }
                yaRetirado = true;
                retirarDelFlujo(el);
            }

            el.addEventListener('transitionend', finalizar);
            // Respaldo por si transitionend no llega (pestaña en segundo
            // plano, transicion interrumpida, etc.).
            window.setTimeout(finalizar, DURACION_FUNDIDO + 100);

            el.classList.add('auto-ocultar-oculto');
        }, retardo);
    }

    function iniciar() {
        var elementos = document.querySelectorAll('[data-auto-ocultar]');
        Array.prototype.forEach.call(elementos, programarOcultado);
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', iniciar);
    } else {
        iniciar();
    }
})();
