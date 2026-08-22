from datetime import datetime, timezone as dt_timezone
from unittest import mock

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from .models import Cliente, Visitante


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
