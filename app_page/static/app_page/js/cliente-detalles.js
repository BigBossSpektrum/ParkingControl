/**
 * Modal de detalles de un cliente de parking.
 *
 * Compartido por el panel de parking y la lista de clientes: ambos abren el
 * mismo modal desde el boton de ojo de sus tablas.
 *
 * Depende de SweetAlert2 (cargado en base.html) y, para reimprimir, de un input
 * csrfmiddlewaretoken presente en la pagina.
 */
function verRegistro(clienteId) {
    fetch(`/clientes/registro/${clienteId}/?ajax=1`, {
        method: 'GET',
        headers: {
            'X-Requested-With': 'XMLHttpRequest',
            'Accept': 'application/json, text/javascript, */*; q=0.01'
        }
    })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            // Sin foto se muestra un marcador: dejar el hueco vacio hace
            // pensar que la funcion no anda, sobre todo en registros antiguos.
            const fotoHtml = data.foto_url
                ? `<div class="text-center mb-3">
                       <img src="${data.foto_url}" alt="Fotografía de ${data.nombre || 'el cliente'}"
                            style="max-width: 200px;" class="rounded border">
                   </div>`
                : `<div class="text-center mb-3">
                       <div class="border rounded d-inline-flex flex-column align-items-center justify-content-center text-body-secondary"
                            style="width: 200px; height: 150px;">
                           <i class="bi bi-person-bounding-box fs-1"></i>
                           <small class="mt-2">Sin imagen registrada</small>
                       </div>
                   </div>`;

            const qrImageHtml = data.qr_url ?
                `<div class="text-center my-3">
                    <img src="${data.qr_url}" alt="Código QR" style="max-width: 300px; border: 2px solid var(--pc-fg); background: #fff;">
                    <div class="small mt-2 text-body-secondary">Código QR con datos del cliente</div>
                </div>` :
                '<div class="alert alert-warning">No hay QR generado para este cliente.</div>';

            Swal.fire({
                title: `${data.nombre || 'Cliente'} (${data.cedula || 'Sin cédula'})`,
                html: `
                    <div class="text-start">
                        ${fotoHtml}
                        <p><strong>Teléfono:</strong> ${data.telefono || 'No especificado'}</p>
                        <p><strong>Torre:</strong> ${data.torre || 'No especificada'}</p>
                        <p><strong>Apartamento:</strong> ${data.apartamento || 'No especificado'}</p>
                        <p><strong>Matrícula:</strong> ${data.matricula}</p>
                        <p><strong>Tipo de Vehículo:</strong> ${data.tipo_vehiculo}</p>
                        <p><strong>Fecha Entrada:</strong> ${data.fecha_entrada || 'No registrada'}</p>
                        <p><strong>Fecha Salida:</strong> ${data.fecha_salida || 'Aún en parking'}</p>
                        ${qrImageHtml}
                    </div>
                `,
                width: '500px',
                confirmButtonColor: '#146c2e',
                confirmButtonText: 'Cerrar',
                showDenyButton: true,
                denyButtonColor: '#17a2b8',
                denyButtonText: '<i class="bi bi-printer"></i> Reimprimir Ticket',
                preConfirm: () => {
                    return true; // Solo cerrar el modal
                },
                preDeny: () => {
                    // Reimprimir ticket
                    return reimprimirTicketDesdeModal(clienteId, data.nombre);
                }
            }).then((result) => {
                if (result.isDenied) {
                    // El botón de reimprimir fue presionado
                    // La función reimprimirTicketDesdeModal ya manejó la reimpresión
                }
            });
        })
        .catch(error => {
            console.error('Error:', error);
            Swal.fire({
                icon: 'error',
                title: 'Error',
                text: 'No se pudo cargar la información del cliente',
                confirmButtonColor: '#146c2e'
            });
        });
}

function reimprimirTicketDesdeModal(clienteId, nombreCliente) {
    return new Promise((resolve, reject) => {
        // Mostrar confirmación antes de reimprimir
        Swal.fire({
            title: '¿Reimprimir ticket?',
            text: `Se imprimirá nuevamente el ticket para ${nombreCliente}`,
            icon: 'question',
            showCancelButton: true,
            confirmButtonColor: '#17a2b8',
            cancelButtonColor: '#6c757d',
            confirmButtonText: '<i class="bi bi-printer"></i> Sí, reimprimir',
            cancelButtonText: 'Cancelar',
            showLoaderOnConfirm: true,
            preConfirm: () => {
                return fetch(`/impresora/print/${clienteId}/`, {
                    method: 'POST',
                    headers: {
                        'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
                        'Content-Type': 'application/json',
                        'X-Requested-With': 'XMLHttpRequest'
                    }
                })
                .then(response => {
                    if (!response.ok) {
                        throw new Error('Error en la respuesta del servidor');
                    }
                    return response.json();
                })
                .catch(error => {
                    Swal.showValidationMessage(`Error: ${error.message}`);
                    reject(error);
                });
            },
            allowOutsideClick: () => !Swal.isLoading()
        }).then((result) => {
            if (result.isConfirmed && result.value) {
                if (result.value.success) {
                    Swal.fire({
                        title: '¡Ticket Enviado!',
                        text: result.value.message,
                        icon: 'success',
                        confirmButtonColor: '#146c2e',
                        timer: 3000,
                        showConfirmButton: false
                    });
                    resolve(true);
                } else {
                    Swal.fire({
                        title: 'Error',
                        text: result.value.message || 'Error al reimprimir el ticket',
                        icon: 'error',
                        confirmButtonColor: '#146c2e'
                    });
                    reject(new Error(result.value.message));
                }
            } else {
                resolve(false); // Usuario canceló
            }
        });
    });
}
