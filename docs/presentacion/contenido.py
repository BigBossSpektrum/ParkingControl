"""Guion de la presentacion: una entrada por pantalla del sistema.

Es la unica fuente del texto de las diapositivas. El texto resume el manual en
pantalla (app_page/templates/app_page/manual_soporte.html): si alli cambia el
procedimiento, hay que cambiarlo aqui tambien, y el test
PresentacionManualTests avisa cuando una seccion deja de existir.

Cada entrada lleva, ademas del texto, como conseguir su captura:

    'archivo'  nombre del PNG dentro de capturas/
    'url'      ruta a visitar; admite {pk_cliente}, que capturar.py resuelve
    'selector' recorte a capturar; None captura el viewport completo
    'accion'   paso extra antes de disparar la captura (ver capturar.py)
"""

# Ids que la presentacion agrega y el manual no tiene como seccion propia: son
# pantallas que el manual explica dentro de otra seccion, pero que en
# diapositivas necesitan su propia imagen.
IDS_SOLO_PRESENTACION = {
    'en-parking',
    'salida-cobro',
    'visitantes-lista',
    'detalle',
    'ayuda',
}

PORTADA = {
    'titulo': 'Parking Control',
    'subtitulo': 'Manual de uso, pantalla por pantalla',
}

DIAPOSITIVAS = [
    {
        'id': 'arrancar',
        'titulo': '1. Arrancar el sistema',
        'captura': {'archivo': 'arrancar.png', 'url': None, 'selector': None, 'accion': 'consola'},
        'pasos': [
            'Haga doble clic en ParkingControl.exe, en el escritorio.',
            'Se abre una ventana negra: es el sistema funcionando. Déjela abierta.',
            'A los pocos segundos el navegador abre solo la pantalla de entrada.',
            'Si vuelve a hacer doble clic con el sistema encendido, sale un menú '
            'para reabrir el navegador o detener el servidor.',
        ],
        'aviso': 'Cerrar la ventana negra apaga el sistema: nadie podrá registrar '
                 'entradas ni salidas hasta volver a abrirlo.',
        'solo_admin': False,
    },
    {
        'id': 'entrar',
        'titulo': '2. Entrar al sistema',
        'captura': {'archivo': 'entrar.png', 'url': '/login/', 'selector': None, 'accion': None},
        'pasos': [
            'Escriba el usuario y la contraseña que le entregó el administrador.',
            'Pulse Iniciar sesión.',
            'Empleado: registra entradas, salidas y visitantes.',
            'Administrador: además configura tarifas, gestiona usuarios y hace el '
            'corte de caja.',
        ],
        'aviso': 'No comparta su contraseña: todo lo que se registra queda asociado '
                 'al usuario con la sesión abierta. Al terminar el turno, pulse Salir.',
        'solo_admin': False,
    },
    {
        'id': 'contadores',
        'titulo': '3. Los contadores de la barra superior',
        'captura': {'archivo': 'contadores.png', 'url': '/parking/', 'selector': 'nav.navbar', 'accion': None},
        'pasos': [
            'Clientes hoy: vehículos que entraron hoy, hayan salido o no.',
            'En parking: vehículos que entraron y todavía no han salido.',
            'Visitantes hoy: visitantes registrados en el día.',
            'A la derecha aparece su usuario y, entre paréntesis, su rol.',
        ],
        'aviso': 'Si "En parking" no cuadra con los puestos ocupados, casi siempre '
                 'es porque quedó una salida sin registrar. Avise al administrador.',
        'solo_admin': False,
    },
    {
        'id': 'entrada',
        'titulo': '4. Registrar la entrada de un vehículo',
        'captura': {'archivo': 'entrada.png', 'url': '/parking/',
                    'selector': 'div.card:has(#registroForm)', 'accion': None},
        'pasos': [
            'Entre a Parking en la barra superior.',
            'Escriba la placa del vehículo.',
            'Elija el tipo: Auto, Moto u Otro. Cada tipo tiene su propia tarifa.',
            'Complete lo que aplique: cédula, nombre, teléfono, torre y apartamento.',
            'Si quiere dejar constancia del estado del vehículo, tome la foto. Es opcional.',
            'Registre: el sistema genera el QR y manda el tiquete a la impresora.',
        ],
        'aviso': 'La hora de entrada la pone el sistema. No hay que escribirla. Entregue '
                 'el tiquete y advierta que lo necesita para salir.',
        'solo_admin': False,
    },
    {
        'id': 'en-parking',
        'titulo': '5. Ver los vehículos que están dentro',
        'captura': {'archivo': 'en-parking.png', 'url': '/parking/',
                    'selector': 'div.card:has(table.table)', 'accion': None},
        'pasos': [
            'Debajo de los formularios está la tabla de los últimos vehículos registrados.',
            'Muestra placa, tipo, hora de entrada y el tiempo que lleva dentro.',
            'Sirve para comprobar de un vistazo que lo registrado coincide con el patio.',
        ],
        'aviso': None,
        'solo_admin': False,
    },
    {
        'id': 'salida',
        'titulo': '6. Registrar la salida',
        'captura': {'archivo': 'salida.png', 'url': '/salida/', 'selector': None, 'accion': None},
        'pasos': [
            'Entre a Registrar salida.',
            'Escanee el QR del tiquete con el lector: el campo ya está enfocado.',
            'Si el cliente perdió el tiquete o el QR no lee, escriba la placa a mano.',
            'Confirme la búsqueda para ver el detalle del cobro.',
        ],
        'aviso': None,
        'solo_admin': False,
    },
    {
        'id': 'salida-cobro',
        'titulo': '7. Cobrar antes de confirmar',
        'captura': {'archivo': 'salida-cobro.png', 'url': '/parking/',
                    'selector': '.swal2-popup', 'accion': 'salida_cobro'},
        'pasos': [
            'El sistema muestra la hora de entrada, el tiempo transcurrido y el monto.',
            'Cobre al cliente y solo entonces confirme la salida.',
            'Al confirmar, el vehículo deja de contar en "En parking".',
        ],
        'aviso': 'El cobro queda congelado: si más adelante cambian los precios, ese '
                 'registro no se recalcula, para que los cortes ya cerrados sigan '
                 'cuadrando. Es el comportamiento correcto, no un error.',
        'solo_admin': False,
    },
    {
        'id': 'visitantes',
        'titulo': '8. Registrar visitantes',
        'captura': {'archivo': 'visitantes.png', 'url': '/visitantes/',
                    'selector': 'div.card:has(#registroVisitanteForm)', 'accion': None},
        'pasos': [
            'Entre a Visitante en la barra superior.',
            'Complete los datos de la persona y a qué torre y apartamento va.',
            'Si lo necesita, tome la foto. Es opcional.',
            'Registre.',
        ],
        'aviso': 'Los visitantes son personas que entran sin dejar vehículo en cobro: '
                 'se registran aparte y no generan cobro.',
        'solo_admin': False,
    },
    {
        'id': 'visitantes-lista',
        'titulo': '9. Histórico de visitantes',
        'captura': {'archivo': 'visitantes-lista.png', 'url': '/visitantes/lista/',
                    'selector': None, 'accion': None},
        'pasos': [
            'La lista guarda todos los visitantes, del más reciente al más antiguo.',
            'Cada fila muestra cédula, nombre, teléfono y a dónde iba.',
            'Es lo que hay que consultar cuando preguntan quién entró y a qué apartamento.',
        ],
        'aviso': None,
        'solo_admin': False,
    },
    {
        'id': 'lista',
        'titulo': '10. Lista de autos parkeados',
        'captura': {'archivo': 'lista.png', 'url': '/clientes/', 'selector': None, 'accion': None},
        'pasos': [
            'Están todos los registros, activos y cerrados, con buscador y paginación.',
            'Ver: abre el detalle con sus datos, la foto y el QR generado.',
            'Editar: corrige datos mal digitados, por ejemplo una placa.',
            'Eliminar: borra el registro. Es definitivo.',
        ],
        'aviso': 'Use Eliminar solo para registros creados por error. Para corregir una '
                 'placa mal escrita, edite: no cree un segundo registro.',
        'solo_admin': True,
    },
    {
        'id': 'detalle',
        'titulo': '11. Detalle de un registro',
        # Pagina completa: el QR queda por debajo del pliegue y la diapositiva
        # lo menciona.
        'captura': {'archivo': 'detalle.png', 'url': '/clientes/registro/{pk_cliente}/',
                    'selector': None, 'accion': None, 'pagina_completa': True},
        'pasos': [
            'Se abre desde el botón Ver de la lista.',
            'Muestra los datos del cliente, las horas de entrada y salida y el tiempo.',
            'Incluye el desglose del cobro y la tarifa que se aplicó.',
            'Abajo quedan el QR del tiquete y la foto, si se tomó.',
        ],
        'aviso': None,
        'solo_admin': True,
    },
    {
        'id': 'tarifas',
        'titulo': '12. Configurar las tarifas',
        'captura': {'archivo': 'tarifas.png', 'url': '/administracion/',
                    'selector': 'div.col-xl-10 > div.card >> nth=0', 'accion': None},
        'pasos': [
            'Las tarifas se editan en Administración. Hay dos modalidades y solo una se aplica.',
            'Precio por minuto: tiempo de estancia por el precio del minuto, con un '
            'valor propio para Auto, Moto y Otro.',
            'Tarifa plena: cuando está activa se cobra un costo fijo por vehículo, sin '
            'importar el tiempo. Sirve para eventos o jornadas de precio único.',
            'Ajuste los valores, active o desactive la tarifa plena y guarde.',
        ],
        'aviso': 'El cambio afecta solo a las salidas que se registren a partir de ese '
                 'momento. Los registros ya cerrados conservan su monto.',
        'solo_admin': True,
    },
    {
        'id': 'usuarios',
        'titulo': '13. Usuarios y roles',
        'captura': {'archivo': 'usuarios.png', 'url': '/administracion/',
                    'selector': 'div.col-xl-10 > div.card >> nth=1', 'accion': None},
        'pasos': [
            'Crear usuario: nombre de usuario, contraseña y rol.',
            'Cambiar rol: pasa a un usuario de empleado a administrador o al revés.',
            'Activar o desactivar: el usuario desactivado no puede entrar, pero sus '
            'registros se conservan. Es lo que se usa cuando alguien deja el puesto.',
            'Restablecer contraseña: le asigna una nueva.',
        ],
        'aviso': 'El sistema no le deja cambiarse el rol a usted mismo, desactivar su '
                 'propia cuenta, ni degradar al último administrador activo.',
        'solo_admin': True,
    },
    {
        'id': 'recaudacion',
        'titulo': '14. Recaudación y corte de caja',
        'captura': {'archivo': 'recaudacion.png', 'url': '/clientes/',
                    'selector': '#modalResumenRecaudacion .modal-content', 'accion': 'abrir_recaudacion'},
        'pasos': [
            'En la lista de clientes, pulse Resumen de Recaudación.',
            'El resumen suma lo cobrado en las salidas registradas desde el último corte.',
            'Compare esa cifra con el dinero que hay en caja.',
            'Si cuadra, realice el corte.',
        ],
        'aviso': 'El corte cierra el período y el siguiente resumen empieza en cero. No '
                 'se puede deshacer: revise antes de confirmar.',
        'solo_admin': True,
    },
    {
        'id': 'impresora',
        'titulo': '15. Configurar la impresora',
        'captura': {'archivo': 'impresora.png', 'url': '/impresora/', 'selector': None, 'accion': None},
        'pasos': [
            'Se entra desde el menú del usuario, en Configurar impresora.',
            'Allí se elige el dispositivo y se prueba la conexión.',
            'Se puede lanzar una impresión de prueba para comprobar el papel.',
        ],
        'aviso': 'Si el tiquete no sale, este es el primer sitio donde mirar. El registro '
                 'queda guardado aunque no se imprima.',
        'solo_admin': True,
    },
    {
        'id': 'ayuda',
        'titulo': '16. Ayuda dentro del sistema',
        'captura': {'archivo': 'ayuda.png', 'url': '/manual/', 'selector': None, 'accion': None},
        'pasos': [
            'El botón Ayuda de la barra superior abre este mismo manual en pantalla.',
            'Trae el índice, las preguntas frecuentes y los datos de soporte.',
            'Se puede imprimir con el botón Imprimir manual.',
            'Muestra solo lo que corresponde a su rol.',
        ],
        'aviso': None,
        'solo_admin': False,
    },
]
