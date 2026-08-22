from datetime import datetime, timezone as dt_timezone
from unittest import mock

from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from .models import Cliente, Costo, Perfil, TarifaPlena, Visitante


class ConteoVisitantesTests(TestCase):
	"""El conteo de 'visitantes de hoy' debe usar la fecha local (America/Bogota).

	Con USE_TZ=True, timezone.now().date() devuelve la fecha en UTC, mientras que
	el lookup __date convierte fecha_registro a la zona local. Entre las 19:00 y
	las 23:59 en Bogota las dos fechas no coinciden y el conteo daba 0.
	"""

	# 22:00 del 21/08/2026 en Bogota = 03:00 UTC del 22/08/2026.
	# La fecha local es el dia 21; la fecha UTC ya es el dia 22.
	NOCHE = datetime(2026, 8, 22, 3, 0, tzinfo=dt_timezone.utc)
	# 12:00 del 21/08/2026 en Bogota = 17:00 UTC del mismo dia (ambas coinciden).
	MEDIODIA = datetime(2026, 8, 21, 17, 0, tzinfo=dt_timezone.utc)

	def setUp(self):
		self.user = User.objects.create_user(username='vigilante', password='clave')
		self.client.force_login(self.user)

	def _crear_visitante(self, instante):
		visitante = Visitante.objects.create(
			cedula='V-1', nombre='Ana Visitante', torre='3', apartamento='302'
		)
		# fecha_registro es auto_now_add, hay que fijarla con update()
		Visitante.objects.filter(pk=visitante.pk).update(fecha_registro=instante)
		return visitante

	def test_visitante_de_la_noche_cuenta_en_el_dashboard(self):
		self._crear_visitante(self.NOCHE)
		with mock.patch('django.utils.timezone.now', return_value=self.NOCHE):
			response = self.client.get(reverse('dashboard_visitante'))
		self.assertEqual(response.context['visitantes_hoy'], 1)
		self.assertEqual(response.context['total_visitantes'], 1)

	def test_visitante_de_la_noche_cuenta_en_la_lista(self):
		self._crear_visitante(self.NOCHE)
		with mock.patch('django.utils.timezone.now', return_value=self.NOCHE):
			response = self.client.get(reverse('lista_visitantes'))
		self.assertEqual(response.context['visitantes_hoy'], 1)
		self.assertEqual(response.context['visitantes_semana'], 1)

	def test_visitante_del_mediodia_sigue_contando(self):
		self._crear_visitante(self.MEDIODIA)
		with mock.patch('django.utils.timezone.now', return_value=self.MEDIODIA):
			response = self.client.get(reverse('dashboard_visitante'))
		self.assertEqual(response.context['visitantes_hoy'], 1)

	def test_visitante_de_ayer_no_cuenta_como_de_hoy(self):
		# 21/08 a las 10:00 Bogota, consultado el 22/08 a las 10:00 Bogota
		self._crear_visitante(datetime(2026, 8, 21, 15, 0, tzinfo=dt_timezone.utc))
		dia_siguiente = datetime(2026, 8, 22, 15, 0, tzinfo=dt_timezone.utc)
		with mock.patch('django.utils.timezone.now', return_value=dia_siguiente):
			response = self.client.get(reverse('dashboard_visitante'))
		self.assertEqual(response.context['visitantes_hoy'], 0)
		self.assertEqual(response.context['total_visitantes'], 1)


class ClienteRegistroTests(TestCase):
	def setUp(self):
		self.url = reverse('index')
		self.datos_cliente = {
			'cedula': '12345678',
			'nombre': 'Juan Perez',
			'telefono': '5551234',
			'matricula': 'ABC123',
			'tipo_vehiculo': 'carro',
			'tiempo_parking': 60,
		}

	def test_registro_cliente(self):
		from django.contrib.auth.models import User
		user = User.objects.create_user(username='testuser', password='testpass')
		self.client.login(username='testuser', password='testpass')
		response = self.client.post(self.url, self.datos_cliente, follow=True)
		self.assertEqual(response.status_code, 200)
		self.assertTrue(Cliente.objects.filter(cedula='12345678').exists())
		cliente = Cliente.objects.get(cedula='12345678')
		self.assertEqual(cliente.nombre, 'Juan Perez')
		self.assertIsNotNone(cliente.fecha_entrada)

	def test_registro_cliente_requiere_login(self):
		response = self.client.post(self.url, self.datos_cliente)
		self.assertEqual(response.status_code, 302)


class PanelAdminTests(TestCase):
	"""Panel de administracion: acceso, usuarios y tarifas."""

	def setUp(self):
		self.url = reverse('panel_admin')
		self.admin = self._crear(username='jefe', rol='administrador')
		self.empleado = self._crear(username='operario', rol='empleado')

	def _crear(self, username, rol, password='clave-segura-123'):
		usuario = User.objects.create_user(username=username, password=password)
		# El signal post_save de User ya creo el Perfil como 'empleado'.
		perfil = Perfil.objects.get(usuario=usuario)
		perfil.rol = rol
		perfil.save()
		return usuario

	# --- Acceso ---------------------------------------------------------

	def test_empleado_no_accede_al_panel(self):
		self.client.force_login(self.empleado)
		response = self.client.get(self.url)
		self.assertEqual(response.status_code, 302)
		self.assertEqual(response['Location'], reverse('dashboard'))

	def test_administrador_accede_al_panel(self):
		self.client.force_login(self.admin)
		response = self.client.get(self.url)
		self.assertEqual(response.status_code, 200)
		self.assertTemplateUsed(response, 'app_page/panel_admin.html')

	# --- Usuarios -------------------------------------------------------

	def test_crear_usuario_con_rol(self):
		self.client.force_login(self.admin)
		response = self.client.post(self.url, {
			'action': 'crear_usuario',
			'username': 'nuevo',
			'first_name': 'Nueva Persona',
			'email': 'nuevo@parking.local',
			'rol': 'empleado',
			'password1': 'contrasena-larga-99',
			'password2': 'contrasena-larga-99',
		})
		self.assertRedirects(response, self.url)

		nuevo = User.objects.get(username='nuevo')
		self.assertEqual(nuevo.perfil.rol, 'empleado')
		self.assertIsNotNone(authenticate(username='nuevo', password='contrasena-larga-99'))

	def test_cambiar_rol_de_otro_usuario(self):
		self.client.force_login(self.admin)
		self.client.post(self.url, {
			'action': 'cambiar_rol',
			'usuario_id': self.empleado.pk,
			'rol': 'administrador',
		})
		self.empleado.perfil.refresh_from_db()
		self.assertEqual(self.empleado.perfil.rol, 'administrador')

	def test_admin_no_puede_desactivarse_a_si_mismo(self):
		self.client.force_login(self.admin)
		self.client.post(self.url, {
			'action': 'toggle_estado',
			'usuario_id': self.admin.pk,
		})
		self.admin.refresh_from_db()
		self.assertTrue(self.admin.is_active)

	def test_no_se_desactiva_al_unico_administrador(self):
		otro_admin = self._crear(username='jefa2', rol='administrador')
		self.client.force_login(otro_admin)
		# Con dos administradores activos, desactivar a uno si esta permitido.
		self.client.post(self.url, {'action': 'toggle_estado', 'usuario_id': self.admin.pk})
		self.admin.refresh_from_db()
		self.assertFalse(self.admin.is_active)

		# jefa2 queda como unico administrador activo: reactivamos a jefe pero
		# como empleado, asi que jefa2 sigue siendo el unico admin.
		self.admin.is_active = True
		self.admin.save()
		self.admin.perfil.rol = 'empleado'
		self.admin.perfil.save()

		self.client.post(self.url, {'action': 'toggle_estado', 'usuario_id': otro_admin.pk})
		otro_admin.refresh_from_db()
		self.assertTrue(otro_admin.is_active)

	def test_no_se_degrada_al_unico_administrador(self):
		otro_admin = self._crear(username='jefa2', rol='administrador')
		self.client.force_login(otro_admin)
		# jefe deja de ser admin: queda jefa2 como unico administrador activo.
		self.client.post(self.url, {
			'action': 'cambiar_rol', 'usuario_id': self.admin.pk, 'rol': 'empleado',
		})
		self.admin.perfil.refresh_from_db()
		self.assertEqual(self.admin.perfil.rol, 'empleado')

		# jefa2 intenta degradarse a si mismo: la guarda de "no cambiar tu
		# propio rol" lo impide.
		self.client.post(self.url, {
			'action': 'cambiar_rol', 'usuario_id': otro_admin.pk, 'rol': 'empleado',
		})
		otro_admin.perfil.refresh_from_db()
		self.assertEqual(otro_admin.perfil.rol, 'administrador')

	def test_restablecer_password(self):
		self.client.force_login(self.admin)
		self.client.post(self.url, {
			'action': 'restablecer_password',
			'usuario_id': self.empleado.pk,
			'new_password1': 'otra-clave-distinta-77',
			'new_password2': 'otra-clave-distinta-77',
		})
		self.assertIsNotNone(
			authenticate(username='operario', password='otra-clave-distinta-77')
		)
		self.assertIsNone(authenticate(username='operario', password='clave-segura-123'))

	# --- Tarifas --------------------------------------------------------

	def test_guardar_tarifas(self):
		self.client.force_login(self.admin)
		response = self.client.post(self.url, {
			'action': 'guardar_tarifas',
			'costo_auto': '120.00',
			'costo_moto': '60.00',
			'activa': 'on',
			'costo_fijo_auto': '8000.00',
			'costo_fijo_moto': '4000.00',
		})
		self.assertRedirects(response, self.url)

		costo = Costo.get_costos_actuales()
		self.assertEqual(str(costo.costo_auto), '120.00')
		self.assertEqual(str(costo.costo_moto), '60.00')
		self.assertEqual(costo.actualizado_por, self.admin)

		tarifa = TarifaPlena.get_tarifa_actual()
		self.assertTrue(tarifa.activa)
		self.assertEqual(str(tarifa.costo_fijo_auto), '8000.00')
		self.assertEqual(tarifa.actualizado_por, self.admin)

	def test_configurar_costos_redirige_al_panel(self):
		self.client.force_login(self.admin)
		response = self.client.get(reverse('configurar_costos'))
		self.assertRedirects(response, self.url)
