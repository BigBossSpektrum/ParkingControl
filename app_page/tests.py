from django.test import TestCase
from django.urls import reverse
from .models import Cliente

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
