import json
from unittest import mock

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import PrinterConfiguration, PrintJob


class BaseImpresoraTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='operario', password='clave123')
        self.client.login(username='operario', password='clave123')

    def crear_impresora(self, nombre, activa=False):
        return PrinterConfiguration.objects.create(
            name=nombre,
            printer_type='USB',
            connection_string=f'{nombre} Receipt',
            is_active=activa,
        )

    def post_json(self, url_name, payload, *args):
        return self.client.post(
            reverse(url_name, args=args),
            data=json.dumps(payload),
            content_type='application/json',
        )


class ExclusividadImpresoraActivaTests(BaseImpresoraTests):
    def test_guardar_activa_desactiva_las_demas(self):
        a = self.crear_impresora('A', activa=True)
        b = self.crear_impresora('B', activa=True)

        a.refresh_from_db()
        self.assertFalse(a.is_active)
        self.assertTrue(b.is_active)
        self.assertEqual(PrinterConfiguration.objects.filter(is_active=True).count(), 1)

    def test_guardar_inactiva_no_toca_a_las_demas(self):
        a = self.crear_impresora('A', activa=True)
        self.crear_impresora('B', activa=False)

        a.refresh_from_db()
        self.assertTrue(a.is_active)


class EliminarImpresoraTests(BaseImpresoraTests):
    def test_elimina_la_unica_impresora_activa(self):
        impresora = self.crear_impresora('Unica', activa=True)
        PrintJob.objects.create(printer=impresora, client_id=1, status='SUCCESS')
        PrintJob.objects.create(printer=impresora, client_id=2, status='FAILED')

        respuesta = self.post_json('delete_printer', {'printer_id': impresora.id})
        datos = respuesta.json()

        self.assertTrue(datos['success'], datos.get('message'))
        self.assertEqual(datos['jobs_deleted'], 2)
        self.assertEqual(PrinterConfiguration.objects.count(), 0)
        self.assertEqual(PrintJob.objects.count(), 0)

    def test_al_borrar_la_activa_se_promueve_otra(self):
        activa = self.crear_impresora('Activa', activa=True)
        self.crear_impresora('Reserva', activa=False)

        respuesta = self.post_json('delete_printer', {'printer_id': activa.id})

        self.assertTrue(respuesta.json()['success'])
        self.assertEqual(PrinterConfiguration.objects.filter(is_active=True).count(), 1)
        self.assertEqual(PrinterConfiguration.objects.get(is_active=True).name, 'Reserva')

    def test_borrar_una_inactiva_no_cambia_la_activa(self):
        activa = self.crear_impresora('Activa', activa=True)
        otra = self.crear_impresora('Otra', activa=False)

        self.post_json('delete_printer', {'printer_id': otra.id})

        activa.refresh_from_db()
        self.assertTrue(activa.is_active)


class CambiarImpresoraSeleccionadaTests(BaseImpresoraTests):
    def test_desactivar_la_unica_activa_esta_permitido(self):
        impresora = self.crear_impresora('Unica', activa=True)

        respuesta = self.post_json(
            'toggle_printer_status', {'printer_id': impresora.id, 'activate': False}
        )

        self.assertTrue(respuesta.json()['success'], respuesta.json().get('message'))
        self.assertEqual(PrinterConfiguration.objects.filter(is_active=True).count(), 0)

    def test_activar_otra_deja_solo_esa_activa(self):
        a = self.crear_impresora('A', activa=True)
        b = self.crear_impresora('B', activa=False)

        respuesta = self.post_json(
            'toggle_printer_status', {'printer_id': b.id, 'activate': True}
        )

        self.assertTrue(respuesta.json()['success'])
        a.refresh_from_db()
        b.refresh_from_db()
        self.assertFalse(a.is_active)
        self.assertTrue(b.is_active)
        self.assertEqual(PrinterConfiguration.objects.filter(is_active=True).count(), 1)


class EditarImpresoraTests(BaseImpresoraTests):
    def datos_formulario(self, **overrides):
        datos = {
            'name': 'Caja principal',
            'printer_type': 'NETWORK',
            'connection_string': '192.168.1.50:9100',
            'paper_width': '58',
            'chars_per_line': '32',
            'is_active': 'on',
        }
        datos.update(overrides)
        return datos

    def test_editar_no_crea_una_impresora_nueva(self):
        impresora = self.crear_impresora('Vieja', activa=True)

        respuesta = self.client.post(
            reverse('edit_printer', args=[impresora.id]), self.datos_formulario()
        )

        self.assertTrue(respuesta.json()['success'], respuesta.json().get('message'))
        self.assertEqual(PrinterConfiguration.objects.count(), 1)

        impresora.refresh_from_db()
        self.assertEqual(impresora.name, 'Caja principal')
        self.assertEqual(impresora.printer_type, 'NETWORK')
        self.assertEqual(impresora.connection_string, '192.168.1.50:9100')
        self.assertEqual(impresora.paper_width, 58)
        self.assertEqual(impresora.chars_per_line, 32)

    def test_sin_marcar_activa_no_la_activa(self):
        impresora = self.crear_impresora('Vieja', activa=False)
        datos = self.datos_formulario()
        del datos['is_active']

        self.client.post(reverse('edit_printer', args=[impresora.id]), datos)

        impresora.refresh_from_db()
        self.assertFalse(impresora.is_active)

    def test_nombre_vacio_devuelve_400_y_no_modifica_nada(self):
        impresora = self.crear_impresora('Vieja', activa=True)

        respuesta = self.client.post(
            reverse('edit_printer', args=[impresora.id]),
            self.datos_formulario(name='   '),
        )

        self.assertEqual(respuesta.status_code, 400)
        self.assertFalse(respuesta.json()['success'])
        impresora.refresh_from_db()
        self.assertEqual(impresora.name, 'Vieja')

    def test_tipo_de_conexion_invalido_devuelve_400(self):
        impresora = self.crear_impresora('Vieja', activa=True)

        respuesta = self.client.post(
            reverse('edit_printer', args=[impresora.id]),
            self.datos_formulario(printer_type='BLUETOOTH'),
        )

        self.assertEqual(respuesta.status_code, 400)
        impresora.refresh_from_db()
        self.assertEqual(impresora.printer_type, 'USB')

    def test_get_precarga_la_impresora(self):
        impresora = self.crear_impresora('Caja 1', activa=True)

        respuesta = self.client.get(reverse('edit_printer', args=[impresora.id]))

        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(respuesta.context['printer'], impresora)

    def test_sin_id_se_crea_una_nueva(self):
        self.crear_impresora('Existente', activa=True)

        respuesta = self.client.post(reverse('printer_config'), self.datos_formulario())

        self.assertTrue(respuesta.json()['success'])
        self.assertEqual(PrinterConfiguration.objects.count(), 2)
        self.assertEqual(PrinterConfiguration.objects.filter(is_active=True).count(), 1)


class ConexionImpresoraTests(TestCase):
    """El enrutado USB decide entre nombre de Windows y libusb."""

    def servicio_con(self, connection_string):
        from .printer_service import PrinterService

        servicio = PrinterService.__new__(PrinterService)
        servicio.printer_config = PrinterConfiguration(
            name='X', printer_type='USB', connection_string=connection_string
        )
        return servicio

    def test_nombre_de_windows_usa_win32raw(self):
        servicio = self.servicio_con('Caja 1')

        with mock.patch.object(servicio, '_instancia_win32') as win32, \
                mock.patch.object(servicio, '_instancia_usb_directa') as usb:
            servicio._get_printer_instance()

        win32.assert_called_once_with('Caja 1')
        usb.assert_not_called()

    def test_usb_direct_usa_libusb(self):
        servicio = self.servicio_con('USB_DIRECT')

        with mock.patch.object(servicio, '_instancia_win32') as win32, \
                mock.patch.object(servicio, '_instancia_usb_directa') as usb:
            servicio._get_printer_instance()

        usb.assert_called_once()
        win32.assert_not_called()

    def test_auto_heredado_se_trata_como_usb_directo(self):
        servicio = self.servicio_con('auto')

        with mock.patch.object(servicio, '_instancia_win32') as win32, \
                mock.patch.object(servicio, '_instancia_usb_directa') as usb:
            servicio._get_printer_instance()

        usb.assert_called_once()
        win32.assert_not_called()

    def test_falta_de_libusb_da_un_mensaje_accionable(self):
        servicio = self.servicio_con('USB_DIRECT')

        with mock.patch(
            'app_impresora.printer_service.Usb',
            side_effect=Exception('No backend available'),
        ):
            with self.assertRaises(Exception) as ctx:
                servicio._instancia_usb_directa()

        mensaje = str(ctx.exception)
        self.assertIn('libusb', mensaje)
        self.assertIn('nombre de Windows', mensaje)


class MensajeDeErrorAlImprimirTests(BaseImpresoraTests):
    def test_la_vista_devuelve_la_causa_real_del_fallo(self):
        from app_page.models import Cliente

        impresora = self.crear_impresora('Caja', activa=True)
        cliente = Cliente.objects.create(
            cedula='99887766', nombre='Ana Ruiz', matricula='XYZ-987'
        )
        PrintJob.objects.create(
            printer=impresora,
            client_id=cliente.id,
            status='FAILED',
            error_message='Error en _print_with_custom_design: No backend available',
        )

        with mock.patch(
            'app_impresora.views.printer_service.print_qr_ticket', return_value=False
        ):
            respuesta = self.client.post(
                reverse('print_client_qr', args=[cliente.id]),
                HTTP_X_REQUESTED_WITH='XMLHttpRequest',
            )

        datos = respuesta.json()
        self.assertFalse(datos['success'])
        self.assertIn('No backend available', datos['message'])


class ProbarImpresoraTests(BaseImpresoraTests):
    def test_si_la_prueba_falla_no_cambia_la_impresora_activa(self):
        activa = self.crear_impresora('Activa', activa=True)
        otra = self.crear_impresora('Otra', activa=False)

        with mock.patch(
            'app_impresora.views.printer_service.test_printer',
            side_effect=RuntimeError('sin hardware'),
        ):
            self.client.post(reverse('test_specific_printer', args=[otra.id]))

        activa.refresh_from_db()
        otra.refresh_from_db()
        self.assertTrue(activa.is_active)
        self.assertFalse(otra.is_active)
