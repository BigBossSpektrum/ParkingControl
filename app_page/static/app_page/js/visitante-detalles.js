/**
 * Modal de detalles de un visitante.
 *
 * Compartido por el panel de visitantes y la lista completa: ambos muestran el
 * mismo modal desde el boton de ojo de sus tablas.
 *
 * Depende de SweetAlert2, cargado globalmente en base.html.
 */
function verDetalles(visitanteId) {
    // Mostrar spinner
    Swal.fire({
        title: 'Cargando...',
        text: 'Obteniendo información del visitante',
        allowOutsideClick: false,
        didOpen: () => {
            Swal.showLoading()
        }
    });

    fetch(`/visitantes/ver/${visitanteId}/`, {
        method: 'GET',
        headers: {
            'X-Requested-With': 'XMLHttpRequest'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            const visitante = data.visitante;

            // Sin foto se muestra un marcador: dejar el hueco vacio hace
            // pensar que la funcion no anda, sobre todo en registros antiguos.
            const fotoHtml = visitante.foto_url
                ? `<div class="text-center mb-3">
                       <img src="${visitante.foto_url}" alt="Fotografía de ${visitante.nombre}"
                            style="max-width: 200px;" class="rounded border">
                   </div>`
                : `<div class="text-center mb-3">
                       <div class="border rounded d-inline-flex flex-column align-items-center justify-content-center text-body-secondary"
                            style="width: 200px; height: 150px;">
                           <i class="bi bi-person-bounding-box fs-1"></i>
                           <small class="mt-2">Sin imagen registrada</small>
                       </div>
                   </div>`;

            Swal.fire({
                title: `👤 ${visitante.nombre}`,
                html: `
                    <div class="text-start">
                        ${fotoHtml}
                        <div class="row">
                            <div class="col-6">
                                <p><strong><i class="bi bi-card-text me-2"></i>Cédula:</strong><br>
                                <span class="badge badge-contador">${visitante.cedula}</span></p>
                            </div>
                            <div class="col-6">
                                <p><strong><i class="bi bi-telephone me-2"></i>Teléfono:</strong><br>
                                ${visitante.telefono}</p>
                            </div>
                        </div>
                        <div class="row">
                            <div class="col-6">
                                <p><strong><i class="bi bi-building me-2"></i>Torre:</strong><br>
                                <span class="badge badge-contador">${visitante.torre}</span></p>
                            </div>
                            <div class="col-6">
                                <p><strong><i class="bi bi-door-open me-2"></i>Apartamento:</strong><br>
                                <span class="badge badge-contador">${visitante.apartamento}</span></p>
                            </div>
                        </div>
                        <hr>
                        <p><strong><i class="bi bi-building-check me-2"></i>Ubicación Completa:</strong><br>
                        ${visitante.ubicacion_completa}</p>
                        <hr>
                        <div class="text-body-secondary small">
                            <p><i class="bi bi-calendar me-2"></i>Registrado: ${visitante.fecha_registro}</p>
                            <p><i class="bi bi-arrow-repeat me-2"></i>Actualizado: ${visitante.fecha_actualizacion}</p>
                        </div>
                    </div>
                `,
                width: '500px',
                confirmButtonText: 'Cerrar',
                confirmButtonColor: '#146c2e'
            });
        } else {
            // Los decoradores de permisos responden con 'error'; el resto con 'mensaje'.
            Swal.fire({
                title: 'Error',
                text: data.mensaje || data.error || 'Error al cargar los detalles',
                icon: 'error',
                confirmButtonColor: '#146c2e'
            });
        }
    })
    .catch(error => {
        console.error('Error:', error);
        Swal.fire({
            title: 'Error de conexión',
            text: 'No se pudo conectar con el servidor',
            icon: 'error',
            confirmButtonColor: '#146c2e'
        });
    });
}
