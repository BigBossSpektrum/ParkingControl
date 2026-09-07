/**
 * Widget de captura de fotografía por cámara.
 *
 * Toma la imagen de la webcam, la escribe como data URL JPEG en un input oculto
 * y muestra la vista previa. La foto es siempre opcional: si la cámara no está
 * disponible el widget avisa y el formulario se puede enviar sin ella.
 *
 * Uso:
 *   const camara = initCameraCapture(document.getElementById('camara_visitante'));
 *   camara.reset();  // al limpiar el formulario
 */
(function () {
    'use strict';

    // La cámara se captura a esta resolución para que el JPEG resultante pese
    // ~60 KB y quepa holgadamente en el POST del formulario.
    var ANCHO = 640;
    var ALTO = 480;
    var CALIDAD_JPEG = 0.8;

    function initCameraCapture(root) {
        if (!root) {
            return { reset: function () {} };
        }

        var video = root.querySelector('[data-cc-video]');
        var canvas = root.querySelector('[data-cc-canvas]');
        var preview = root.querySelector('[data-cc-preview]');
        var input = root.querySelector('[data-cc-input]');
        var btnStart = root.querySelector('[data-cc-start]');
        var btnShoot = root.querySelector('[data-cc-shoot]');
        var btnRetry = root.querySelector('[data-cc-retry]');
        var status = root.querySelector('[data-cc-status]');

        var stream = null;

        function mostrar(el, visible) {
            if (el) {
                el.classList.toggle('d-none', !visible);
            }
        }

        function decir(mensaje) {
            if (status) {
                status.textContent = mensaje || '';
            }
        }

        function detenerStream() {
            if (stream) {
                stream.getTracks().forEach(function (track) {
                    track.stop();
                });
                stream = null;
            }
            if (video) {
                video.srcObject = null;
            }
        }

        function estadoInicial() {
            detenerStream();
            mostrar(video, false);
            mostrar(preview, false);
            mostrar(btnStart, true);
            mostrar(btnShoot, false);
            mostrar(btnRetry, false);
        }

        function reset() {
            if (input) {
                input.value = '';
            }
            if (preview) {
                preview.removeAttribute('src');
            }
            estadoInicial();
            decir('');
        }

        if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
            if (btnStart) {
                btnStart.disabled = true;
            }
            decir('Cámara no disponible en este navegador. Puede registrar sin fotografía.');
            return { reset: reset };
        }

        function activarCamara() {
            decir('Solicitando acceso a la cámara...');
            navigator.mediaDevices.getUserMedia({
                video: { width: { ideal: ANCHO }, height: { ideal: ALTO } },
                audio: false
            }).then(function (nuevoStream) {
                stream = nuevoStream;
                video.srcObject = stream;
                mostrar(video, true);
                mostrar(preview, false);
                mostrar(btnStart, false);
                mostrar(btnShoot, true);
                mostrar(btnRetry, false);
                decir('Encuadre a la persona y presione Capturar.');
            }).catch(function (error) {
                estadoInicial();
                if (error && error.name === 'NotAllowedError') {
                    decir('Permiso de cámara denegado. Puede registrar sin fotografía.');
                } else if (error && error.name === 'NotFoundError') {
                    decir('No se detectó ninguna cámara conectada.');
                } else {
                    decir('No se pudo acceder a la cámara. Puede registrar sin fotografía.');
                }
            });
        }

        function capturar() {
            if (!stream || !video.videoWidth) {
                decir('La cámara aún no está lista. Intente de nuevo.');
                return;
            }

            canvas.width = ANCHO;
            canvas.height = ALTO;
            canvas.getContext('2d').drawImage(video, 0, 0, ANCHO, ALTO);

            var dataUrl = canvas.toDataURL('image/jpeg', CALIDAD_JPEG);
            input.value = dataUrl;
            preview.src = dataUrl;

            // Apagar la cámara en cuanto se tiene la foto.
            detenerStream();
            mostrar(video, false);
            mostrar(preview, true);
            mostrar(btnStart, false);
            mostrar(btnShoot, false);
            mostrar(btnRetry, true);
            decir('Fotografía capturada.');
        }

        if (btnStart) {
            btnStart.addEventListener('click', activarCamara);
        }
        if (btnShoot) {
            btnShoot.addEventListener('click', capturar);
        }
        if (btnRetry) {
            btnRetry.addEventListener('click', reset);
        }

        // No dejar la cámara encendida al salir de la página.
        window.addEventListener('beforeunload', detenerStream);
        window.addEventListener('pagehide', detenerStream);

        estadoInicial();
        return { reset: reset };
    }

    window.initCameraCapture = initCameraCapture;
})();
