import base64
import os
import shutil
import tempfile
from pathlib import Path
from datetime import datetime, timedelta, timezone as dt_timezone
from importlib import import_module, util
from io import BytesIO, StringIO
from unittest import mock

from django.apps import apps as django_apps
from django.conf import settings
from django.contrib.auth import authenticate
from django.contrib.staticfiles import finders
from django.contrib.auth.models import User
from django.core.management import call_command
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone as dj_timezone
from PIL import Image
from .models import Cliente, Costo, Perfil, Recaudacion, TarifaPlena, Visitante
from .formato import fecha_local
from .templatetags.estaticos import static_v
from .photo_utils import MAX_FOTO_BYTES, decodificar_foto_base64
from .views import SOPORTE


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
			'costo_otro': '90.00',
			'activa': 'on',
			'costo_fijo_auto': '8000.00',
			'costo_fijo_moto': '4000.00',
			'costo_fijo_otro': '6000.00',
		})
		self.assertRedirects(response, self.url)

		costo = Costo.get_costos_actuales()
		self.assertEqual(str(costo.costo_auto), '120.00')
		self.assertEqual(str(costo.costo_moto), '60.00')
		self.assertEqual(str(costo.costo_otro), '90.00')
		self.assertEqual(costo.actualizado_por, self.admin)

		tarifa = TarifaPlena.get_tarifa_actual()
		self.assertTrue(tarifa.activa)
		self.assertEqual(str(tarifa.costo_fijo_auto), '8000.00')
		self.assertEqual(str(tarifa.costo_fijo_otro), '6000.00')
		self.assertEqual(tarifa.actualizado_por, self.admin)

	def test_configurar_costos_redirige_al_panel(self):
		self.client.force_login(self.admin)
		response = self.client.get(reverse('configurar_costos'))
		self.assertRedirects(response, self.url)


def _data_url(formato='JPEG'):
	"""Genera una data URL valida a partir de una imagen minima real."""
	buffer = BytesIO()
	Image.new('RGB', (10, 10), color='red').save(buffer, format=formato)
	codificada = base64.b64encode(buffer.getvalue()).decode('ascii')
	mime = 'jpeg' if formato == 'JPEG' else formato.lower()
	return f'data:image/{mime};base64,{codificada}'


class DecodificarFotoBase64Tests(TestCase):
	"""La decodificacion valida el formato antes de guardar en el ImageField."""

	def test_cadena_vacia_devuelve_none(self):
		self.assertIsNone(decodificar_foto_base64(''))
		self.assertIsNone(decodificar_foto_base64('   '))
		self.assertIsNone(decodificar_foto_base64(None))

	def test_jpeg_valido_devuelve_nombre_y_contenido(self):
		nombre, contenido = decodificar_foto_base64(_data_url('JPEG'), prefijo='cliente')
		self.assertTrue(nombre.startswith('cliente_'))
		self.assertTrue(nombre.endswith('.jpg'))
		self.assertTrue(contenido.size > 0)

	def test_png_valido_devuelve_extension_png(self):
		nombre, _ = decodificar_foto_base64(_data_url('PNG'))
		self.assertTrue(nombre.endswith('.png'))

	def test_mime_no_soportado(self):
		with self.assertRaises(ValueError):
			decodificar_foto_base64('data:text/plain;base64,aG9sYQ==')

	def test_contenido_que_no_es_imagen(self):
		basura = base64.b64encode(b'no soy una imagen').decode('ascii')
		with self.assertRaises(ValueError):
			decodificar_foto_base64(f'data:image/jpeg;base64,{basura}')

	def test_payload_demasiado_grande(self):
		enorme = 'A' * (MAX_FOTO_BYTES + 1)
		with self.assertRaises(ValueError):
			decodificar_foto_base64(f'data:image/jpeg;base64,{enorme}')


class FotoCapturaTests(TestCase):
	"""La foto capturada por camara se guarda, pero nunca bloquea el registro."""

	@classmethod
	def setUpClass(cls):
		cls._media_temporal = tempfile.mkdtemp()
		cls._override = override_settings(MEDIA_ROOT=cls._media_temporal)
		cls._override.enable()
		super().setUpClass()

	@classmethod
	def tearDownClass(cls):
		super().tearDownClass()
		cls._override.disable()
		shutil.rmtree(cls._media_temporal, ignore_errors=True)

	def setUp(self):
		self.usuario = User.objects.create_user(username='portero', password='clave-segura-123')
		self.client.force_login(self.usuario)
		self.foto = _data_url()
		self.datos_visitante = {
			'action': 'registro_visitante',
			'cedula': '99887766',
			'nombre': 'Ana Gomez',
			'telefono': '3001112233',
			'torre': 'A',
			'apartamento': '101',
		}
		self.datos_cliente = {
			'cedula': '11223344',
			'nombre': 'Luis Rojas',
			'telefono': '3009998877',
			'matricula_inicio': 'ABC',
			'matricula_fin': '123',
			'tipo_vehiculo': 'Auto',
		}

	# --- Visitantes -----------------------------------------------------

	def test_visitante_con_foto(self):
		self.client.post(reverse('dashboard_visitante'), {**self.datos_visitante, 'foto_data': self.foto})
		visitante = Visitante.objects.get(cedula='99887766')
		self.assertTrue(visitante.foto)
		self.assertIn('fotos_visitantes/', visitante.foto.name)

	def test_visitante_sin_foto_se_registra_igual(self):
		self.client.post(reverse('dashboard_visitante'), self.datos_visitante)
		visitante = Visitante.objects.get(cedula='99887766')
		self.assertFalse(visitante.foto)

	def test_visitante_con_foto_invalida_se_registra_sin_foto(self):
		self.client.post(reverse('dashboard_visitante'), {**self.datos_visitante, 'foto_data': 'no-soy-una-imagen'})
		visitante = Visitante.objects.get(cedula='99887766')
		self.assertFalse(visitante.foto)

	# --- Parking --------------------------------------------------------

	def test_cliente_con_foto(self):
		response = self.client.post(
			reverse('dashboard_parking'),
			{**self.datos_cliente, 'foto_data': self.foto},
			HTTP_X_REQUESTED_WITH='XMLHttpRequest',
		)
		datos = response.json()
		self.assertTrue(datos['success'])
		cliente = Cliente.objects.get(cedula='11223344')
		self.assertTrue(cliente.foto)
		self.assertIn('fotos_clientes/', cliente.foto.name)
		self.assertEqual(datos['cliente']['foto_url'], cliente.foto.url)

	def test_cliente_sin_foto_se_registra_igual(self):
		response = self.client.post(
			reverse('dashboard_parking'),
			self.datos_cliente,
			HTTP_X_REQUESTED_WITH='XMLHttpRequest',
		)
		datos = response.json()
		self.assertTrue(datos['success'])
		self.assertIsNone(datos['cliente']['foto_url'])
		self.assertFalse(Cliente.objects.get(cedula='11223344').foto)

	def test_cliente_con_foto_invalida_se_registra_sin_foto(self):
		response = self.client.post(
			reverse('dashboard_parking'),
			{**self.datos_cliente, 'foto_data': 'no-soy-una-imagen'},
			HTTP_X_REQUESTED_WITH='XMLHttpRequest',
		)
		self.assertTrue(response.json()['success'])
		self.assertFalse(Cliente.objects.get(cedula='11223344').foto)


class DetalleClienteTests(TestCase):
	"""Modal de detalles del cliente y tabla de ultimos ingresos del panel."""

	@classmethod
	def setUpClass(cls):
		cls._media_temporal = tempfile.mkdtemp()
		cls._override = override_settings(MEDIA_ROOT=cls._media_temporal)
		cls._override.enable()
		super().setUpClass()

	@classmethod
	def tearDownClass(cls):
		super().tearDownClass()
		cls._override.disable()
		shutil.rmtree(cls._media_temporal, ignore_errors=True)

	def setUp(self):
		self.usuario = User.objects.create_user(username='portero2', password='clave-segura-123')
		self.client.force_login(self.usuario)

	def _crear_cliente(self, cedula='55443322', matricula='XYZ-987'):
		return Cliente.objects.create(
			cedula=cedula,
			nombre='Marta Diaz',
			telefono='3005554433',
			torre='B',
			apartamento='402',
			matricula=matricula,
			tipo_vehiculo='Auto',
			fecha_entrada=dj_timezone.now(),
		)

	# --- JSON del detalle -----------------------------------------------

	def test_detalle_incluye_ubicacion_y_foto_vacia(self):
		cliente = self._crear_cliente()
		response = self.client.get(reverse('ver_registro', args=[cliente.pk]), {'ajax': '1'})
		datos = response.json()
		self.assertEqual(datos['torre'], 'B')
		self.assertEqual(datos['apartamento'], '402')
		self.assertIsNone(datos['foto_url'])

	def test_detalle_incluye_url_de_la_foto(self):
		cliente = self._crear_cliente()
		nombre, contenido = decodificar_foto_base64(_data_url(), prefijo='cliente')
		cliente.foto.save(nombre, contenido, save=True)

		response = self.client.get(reverse('ver_registro', args=[cliente.pk]), {'ajax': '1'})
		self.assertEqual(response.json()['foto_url'], cliente.foto.url)

	# --- Tabla de ultimos ingresos --------------------------------------

	def test_panel_lista_los_ultimos_ingresos(self):
		antiguo = self._crear_cliente(cedula='111', matricula='AAA-111')
		reciente = self._crear_cliente(cedula='222', matricula='BBB-222')
		Cliente.objects.filter(pk=antiguo.pk).update(
			fecha_entrada=dj_timezone.now() - timedelta(hours=3)
		)

		response = self.client.get(reverse('dashboard_parking'))
		ultimos = list(response.context['ultimos_clientes'])
		self.assertEqual(ultimos[0].pk, reciente.pk)
		self.assertIn(antiguo.pk, [c.pk for c in ultimos])

	def test_panel_lista_como_maximo_cinco(self):
		for i in range(7):
			self._crear_cliente(cedula=f'90{i}', matricula=f'C{i}C-00{i}')

		response = self.client.get(reverse('dashboard_parking'))
		self.assertEqual(len(response.context['ultimos_clientes']), 5)


class MenuUsuarioTests(TestCase):
	"""Menu de configuracion del navbar: contenido segun rol y en toda pagina."""

	def setUp(self):
		self.admin = self._crear('jefa', 'administrador')
		self.empleado = self._crear('vigilante2', 'empleado')
		self.url_admin = reverse('panel_admin')
		self.url_impresora = reverse('printer_dashboard')
		self.url_clientes = reverse('lista_clientes')

	def _crear(self, username, rol, password='clave-segura-123'):
		usuario = User.objects.create_user(username=username, password=password)
		perfil = Perfil.objects.get(usuario=usuario)
		perfil.rol = rol
		perfil.save()
		return usuario

	def test_administrador_ve_los_accesos_de_administracion(self):
		self.client.force_login(self.admin)
		html = self.client.get(reverse('dashboard_parking')).content.decode()
		self.assertIn(self.url_admin, html)
		self.assertIn(self.url_impresora, html)
		self.assertIn(self.url_clientes, html)

	def test_empleado_no_ve_los_accesos_de_administracion(self):
		self.client.force_login(self.empleado)
		html = self.client.get(reverse('dashboard_parking')).content.decode()
		self.assertNotIn(self.url_admin, html)
		self.assertNotIn(self.url_impresora, html)
		self.assertIn(self.url_clientes, html)

	def test_menu_aparece_en_paginas_que_no_pasan_perfil_al_render(self):
		"""El menu vive en el navbar, asi que tiene que estar en toda pagina.

		lista_visitantes y lista_clientes no incluyen 'perfil' en su propio
		render: lo aporta el context processor user_profile_context. Si alguien
		lo quita de settings, estos accesos desaparecen y este test lo detecta.
		"""
		self.client.force_login(self.admin)
		for nombre in ('lista_visitantes', 'lista_clientes', 'dashboard_visitante'):
			with self.subTest(pagina=nombre):
				html = self.client.get(reverse(nombre)).content.decode()
				self.assertIn(self.url_admin, html)
				self.assertIn(self.url_impresora, html)

	def test_el_panel_ya_no_trae_la_botonera_antigua(self):
		self.client.force_login(self.admin)
		html = self.client.get(reverse('dashboard_parking')).content.decode()
		self.assertNotIn('acciones-dashboard', html)


class PlantillasSinComentariosRotosTests(TestCase):
	"""Django solo reconoce {# #} dentro de una misma linea.

	Un {# que no cierra en su linea deja de ser comentario y el texto restante
	se renderiza como contenido visible. Ya paso antes en este proyecto, asi que
	se vigila automaticamente en vez de confiar en la revision visual.
	"""

	# Tabulador, salto de linea y retorno de carro: los unicos caracteres de
	# control con sentido en una plantilla. Se escriben con chr() para que la
	# propia definicion no dependa de secuencias de escape.
	CONTROL_PERMITIDOS = {chr(9), chr(10), chr(13)}

	def _plantillas(self):
		raiz = Path(settings.BASE_DIR)
		for plantilla in sorted(raiz.glob('*/templates/**/*.html')):
			yield plantilla, plantilla.relative_to(raiz)

	def test_no_hay_caracteres_de_control_en_las_plantillas(self):
		"""Un byte 0x01 en lugar de '<label ...>' rompia el formulario de filtros.

		El navegador cierra el <div> en el primer '>' y pinta el resto del
		atributo como texto: en pantalla se leia class="form-label">Cedula.
		Ni grep ni una busqueda por texto lo delatan, por eso se vigila aqui.
		"""
		rotos = []
		for plantilla, relativa in self._plantillas():
			texto = plantilla.read_text(encoding="utf-8")
			for numero, linea in enumerate(texto.splitlines(), 1):
				malos = {c for c in linea if ord(c) < 32 and c not in self.CONTROL_PERMITIDOS}
				if malos:
					codigos = ", ".join(sorted(hex(ord(c)) for c in malos))
					rotos.append(f"{relativa}:{numero}: {codigos}")

		self.assertEqual(rotos, [], "Caracteres de control en plantillas: " + "; ".join(rotos))

	def test_no_hay_comentarios_de_una_almohadilla_multilinea(self):
		raiz = Path(settings.BASE_DIR)
		rotos = []

		for plantilla in sorted(raiz.glob('*/templates/**/*.html')):
			for numero, linea in enumerate(plantilla.read_text(encoding='utf-8').splitlines(), 1):
				if '{#' in linea and '#}' not in linea:
					rotos.append(f'{plantilla.relative_to(raiz)}:{numero}: {linea.strip()[:60]}')

		self.assertEqual(
			rotos, [],
			'Comentarios {# #} abiertos en varias lineas (su texto se renderiza '
			'como contenido visible). Use {% comment %}...{% endcomment %}:\n'
			+ '\n'.join(rotos)
		)


class CrearDatosMensualesTests(TestCase):
	"""El comando de datos de demostracion reparte por mes y es reversible."""

	def setUp(self):
		self.usuario = User.objects.create_superuser(
			username='jefe_demo', email='demo@parking.local', password='clave-segura-123'
		)
		# Un registro real, para comprobar que --limpiar no lo toca.
		self.real = Cliente.objects.create(
			cedula='REAL-1', nombre='Cliente Real', matricula='RRR-111',
			tipo_vehiculo='Auto', fecha_entrada=dj_timezone.now(),
		)

	def _ejecutar(self, **opciones):
		salida = StringIO()
		call_command('crear_datos_mensuales', stdout=salida, **opciones)
		return salida.getvalue()

	def test_genera_diez_por_mes_de_cada_tipo(self):
		self._ejecutar(meses=3, por_mes=10)

		self.assertEqual(Cliente.objects.filter(cedula__startswith='PRB-').count(), 30)
		self.assertEqual(Visitante.objects.filter(cedula__startswith='PRB-').count(), 30)

	def test_los_registros_quedan_repartidos_en_meses_distintos(self):
		self._ejecutar(meses=3, por_mes=10)

		# localtime(): con USE_TZ, .month sobre el valor crudo da el mes en UTC.
		meses_cliente = {
			(dj_timezone.localtime(c.fecha_entrada).year, dj_timezone.localtime(c.fecha_entrada).month)
			for c in Cliente.objects.filter(cedula__startswith='PRB-')
		}
		self.assertEqual(len(meses_cliente), 3)

	def test_no_inventa_fechas_futuras(self):
		self._ejecutar(meses=3, por_mes=10)

		ahora = dj_timezone.now()
		for cliente in Cliente.objects.filter(cedula__startswith='PRB-'):
			self.assertLessEqual(cliente.fecha_entrada, ahora)
		for visitante in Visitante.objects.filter(cedula__startswith='PRB-'):
			self.assertLessEqual(visitante.fecha_registro, ahora)

	def test_crea_un_corte_por_mes_con_fecha_propia(self):
		self._ejecutar(meses=3, por_mes=10)

		cortes = Recaudacion.objects.all()
		self.assertEqual(cortes.count(), 3)
		# fecha_corte es auto_now_add; si no se corrigiera, los tres saldrian hoy
		# y el historial (ordenado por -fecha_corte) no reflejaria los meses.
		meses_corte = {
			(dj_timezone.localtime(c.fecha_corte).year, dj_timezone.localtime(c.fecha_corte).month)
			for c in cortes
		}
		self.assertEqual(len(meses_corte), 3)
		for corte in cortes:
			self.assertGreater(corte.monto_recaudado, 0)
			self.assertLessEqual(corte.fecha_corte, dj_timezone.now())

	def test_el_mes_en_curso_deja_clientes_dentro_del_parking(self):
		self._ejecutar(meses=3, por_mes=10)

		activos = Cliente.objects.filter(cedula__startswith='PRB-', fecha_salida__isnull=True)
		self.assertEqual(activos.count(), 2)

	def test_reejecutar_no_acumula(self):
		self._ejecutar(meses=3, por_mes=10)
		self._ejecutar(meses=3, por_mes=10)

		self.assertEqual(Cliente.objects.filter(cedula__startswith='PRB-').count(), 30)
		self.assertEqual(Recaudacion.objects.count(), 3)

	def test_solo_visitantes_no_crea_clientes_ni_cortes(self):
		self._ejecutar(meses=5, por_mes=10, solo='visitantes')

		self.assertEqual(Visitante.objects.filter(cedula__startswith='PRB-').count(), 50)
		self.assertEqual(Cliente.objects.filter(cedula__startswith='PRB-').count(), 0)
		self.assertEqual(Recaudacion.objects.count(), 0)

	def test_solo_visitantes_respeta_los_clientes_de_demo_ya_creados(self):
		"""La limpieza previa solo debe alcanzar a lo que se va a regenerar."""
		self._ejecutar(meses=3, por_mes=10)
		clientes_antes = set(
			Cliente.objects.filter(cedula__startswith='PRB-').values_list('pk', flat=True)
		)
		cortes_antes = Recaudacion.objects.count()

		self._ejecutar(meses=5, por_mes=10, solo='visitantes')

		clientes_despues = set(
			Cliente.objects.filter(cedula__startswith='PRB-').values_list('pk', flat=True)
		)
		self.assertEqual(clientes_antes, clientes_despues)
		self.assertEqual(Recaudacion.objects.count(), cortes_antes)
		self.assertEqual(Visitante.objects.filter(cedula__startswith='PRB-').count(), 50)

	def test_limpiar_borra_solo_lo_de_prueba(self):
		self._ejecutar(meses=3, por_mes=10)
		self._ejecutar(limpiar=True)

		self.assertEqual(Cliente.objects.filter(cedula__startswith='PRB-').count(), 0)
		self.assertEqual(Visitante.objects.filter(cedula__startswith='PRB-').count(), 0)
		self.assertEqual(Recaudacion.objects.count(), 0)
		self.assertTrue(Cliente.objects.filter(pk=self.real.pk).exists())


class FechasEnHoraLocalTests(TestCase):
	"""Las fechas que se arman en Python deben salir en America/Bogota.

	Con USE_TZ=True, strftime() sobre el valor crudo imprime UTC: cinco horas
	por delante. Las plantillas convierten solas con |date, pero las respuestas
	JSON no, y por eso el resumen de recaudacion mostraba horas adelantadas.
	"""

	def setUp(self):
		self.usuario = User.objects.create_superuser(
			username='cajero', email='cajero@parking.local', password='clave-segura-123'
		)
		self.client.force_login(self.usuario)

	def _cliente(self, entrada, salida=None):
		return Cliente.objects.create(
			cedula='TZ-1', nombre='Prueba Zona', matricula='TZZ-001',
			tipo_vehiculo='Auto', fecha_entrada=entrada, fecha_salida=salida,
		)

	def test_fecha_local_convierte_a_bogota(self):
		# 03:00 UTC del 22/08 son las 22:00 del 21/08 en Bogota.
		instante = datetime(2026, 8, 22, 3, 0, tzinfo=dt_timezone.utc)
		self.assertEqual(fecha_local(instante), '21/08/2026 22:00')

	def test_fecha_local_devuelve_el_valor_por_defecto(self):
		self.assertIsNone(fecha_local(None))
		self.assertEqual(fecha_local(None, 'No registrada'), 'No registrada')

	def test_detalle_de_cliente_muestra_hora_local(self):
		cliente = self._cliente(datetime(2026, 8, 22, 3, 0, tzinfo=dt_timezone.utc))
		datos = self.client.get(
			reverse('ver_registro', args=[cliente.pk]), {'ajax': '1'}
		).json()
		self.assertEqual(datos['fecha_entrada'], '21/08/2026 22:00')

	def test_detalle_de_visitante_muestra_hora_local(self):
		visitante = Visitante.objects.create(cedula='TZ-V', nombre='Visita Zona')
		Visitante.objects.filter(pk=visitante.pk).update(
			fecha_registro=datetime(2026, 8, 22, 3, 0, tzinfo=dt_timezone.utc)
		)
		datos = self.client.get(
			reverse('ver_visitante', args=[visitante.pk]),
			HTTP_X_REQUESTED_WITH='XMLHttpRequest',
		).json()
		self.assertEqual(datos['visitante']['fecha_registro'], '21/08/2026 22:00')

	def test_resumen_de_recaudacion_muestra_hora_local(self):
		datos = self.client.get(reverse('resumen_recaudacion')).json()
		esperado = dj_timezone.localtime(dj_timezone.now()).strftime('%d/%m/%Y %H:%M')
		self.assertEqual(datos['resumen']['fecha_actual'], esperado)

	def test_sin_cortes_el_periodo_arranca_en_la_medianoche_local(self):
		"""timezone.now().replace(hour=0) daba las 19:00 del dia anterior."""
		self.assertFalse(Recaudacion.objects.exists())
		inicio = Recaudacion.calcular_recaudacion_actual()['fecha_inicio']

		local = dj_timezone.localtime(inicio)
		self.assertEqual((local.hour, local.minute), (0, 0))
		self.assertEqual(local.date(), dj_timezone.localdate())


class StaticVersionadoTests(TestCase):
	"""La etiqueta static_v pone huella de version en los estaticos propios.

	El runserver los sirve sin Cache-Control ni ETag, solo con Last-Modified;
	con eso el navegador cachea de forma heuristica y un cambio en un .js podia
	no verse. La huella cambia la URL en cada modificacion.
	"""

	def setUp(self):
		self.usuario = User.objects.create_superuser(
			username='revisor', email='revisor@parking.local', password='clave-segura-123'
		)
		self.client.force_login(self.usuario)

	def test_devuelve_la_url_con_huella(self):
		url = static_v('app_page/js/visitante-detalles.js')
		self.assertIn('app_page/js/visitante-detalles.js', url)
		self.assertRegex(url, r'\?v=\d+$')

	def test_la_huella_cambia_si_cambia_el_archivo(self):
		ruta = Path(finders.find('app_page/js/visitante-detalles.js'))
		antes = static_v('app_page/js/visitante-detalles.js')
		original = ruta.stat().st_mtime

		os.utime(ruta, (original + 120, original + 120))
		try:
			self.assertNotEqual(antes, static_v('app_page/js/visitante-detalles.js'))
		finally:
			os.utime(ruta, (original, original))

	def test_un_estatico_inexistente_no_rompe(self):
		self.assertEqual(static_v('app_page/js/no-existe.js'), '/static/app_page/js/no-existe.js')

	def test_las_paginas_sirven_los_scripts_versionados(self):
		for nombre in ('dashboard_visitante', 'lista_visitantes', 'dashboard_parking', 'lista_clientes'):
			with self.subTest(pagina=nombre):
				html = self.client.get(reverse(nombre)).content.decode()
				self.assertRegex(html, r'app_page/js/[\w-]+\.js\?v=\d+')


class TipoVehiculoOtroTests(TestCase):
	"""El tipo 'Otro' se puede registrar y tiene tarifa propia.

	Antes existia en TIPO_VEHICULO_CHOICES pero el desplegable escrito a mano lo
	omitia, y get_costo_por_tipo() devolvia la tarifa de Auto para cualquier tipo
	que no fuese Auto o Moto: un camion se cobraba como automovil sin aviso.
	"""

	def setUp(self):
		self.usuario = User.objects.create_superuser(
			username='cajera', email='cajera@parking.local', password='clave-segura-123'
		)
		self.client.force_login(self.usuario)

		self.costo = Costo.get_costos_actuales()
		self.costo.costo_auto = 100
		self.costo.costo_moto = 50
		self.costo.costo_otro = 200
		self.costo.save()

		self.tarifa = TarifaPlena.get_tarifa_actual()
		self.tarifa.activa = False
		self.tarifa.costo_fijo_auto = 8000
		self.tarifa.costo_fijo_moto = 4000
		self.tarifa.costo_fijo_otro = 12000
		self.tarifa.save()

	# --- Tarifas ---------------------------------------------------------

	def test_precio_por_minuto_usa_la_tarifa_de_otro(self):
		self.assertEqual(self.costo.get_costo_por_tipo('Otro'), 200)
		self.assertNotEqual(self.costo.get_costo_por_tipo('Otro'), self.costo.costo_auto)

	def test_tarifa_plena_usa_la_tarifa_de_otro(self):
		self.assertEqual(self.tarifa.get_costo_por_tipo('Otro'), 12000)

	def test_un_tipo_desconocido_sigue_cobrando_como_auto(self):
		"""El else de respaldo protege datos antiguos; no debe desaparecer."""
		self.assertEqual(self.costo.get_costo_por_tipo('Camion'), self.costo.costo_auto)
		self.assertEqual(self.tarifa.get_costo_por_tipo('Camion'), self.tarifa.costo_fijo_auto)

	# --- Registro --------------------------------------------------------

	def test_se_puede_registrar_un_vehiculo_de_tipo_otro(self):
		response = self.client.post(reverse('dashboard_parking'), {
			'cedula': '77665544',
			'nombre': 'Pedro Nel',
			'telefono': '3007776655',
			'matricula_inicio': 'OTR',
			'matricula_fin': '001',
			'tipo_vehiculo': 'Otro',
		}, HTTP_X_REQUESTED_WITH='XMLHttpRequest')

		self.assertTrue(response.json()['success'])
		cliente = Cliente.objects.get(cedula='77665544')
		self.assertEqual(cliente.tipo_vehiculo, 'Otro')

	def test_el_cobro_de_un_cliente_otro_usa_su_tarifa(self):
		entrada = dj_timezone.now() - timedelta(minutes=10)
		cliente = Cliente.objects.create(
			cedula='77665544', nombre='Pedro Nel', matricula='OTR-001',
			tipo_vehiculo='Otro', fecha_entrada=entrada, fecha_salida=dj_timezone.now(),
		)
		# 10 minutos a 200/min, no a 100/min como cobraba antes.
		self.assertEqual(cliente.calcular_costo(), 2000)

	def test_el_desplegable_ofrece_los_tres_tipos(self):
		html = self.client.get(reverse('dashboard_parking')).content.decode()
		for tipo, _ in Cliente.TIPO_VEHICULO_CHOICES:
			with self.subTest(tipo=tipo):
				self.assertIn(f'<option value="{tipo}">', html)


class CongelamientoDeCobroTests(TestCase):
	"""El cobro se fija al registrar la salida y ya no cambia si suben las tarifas.

	Cliente no guardaba ningun monto: calcular_costo() releia la tarifa singleton
	vigente en cada lectura. Subir el precio a media jornada reescribia el cobro de
	todo el historial, incluidos los cortes de caja ya cerrados, y dejaba el total
	del corte sin cuadrar con su propio detalle.
	"""

	def setUp(self):
		self.usuario = User.objects.create_user(username='cajera', password='clave-segura-123')
		# El signal post_save de User ya creo el Perfil como 'empleado'; el corte
		# de recaudacion exige rol administrador.
		perfil = Perfil.objects.get(usuario=self.usuario)
		perfil.rol = 'administrador'
		perfil.save()
		self.client.force_login(self.usuario)

		self.costo = Costo.get_costos_actuales()
		self.costo.costo_auto = 100
		self.costo.costo_moto = 50
		self.costo.costo_otro = 200
		self.costo.save()

		self.tarifa = TarifaPlena.get_tarifa_actual()
		self.tarifa.activa = False
		self.tarifa.costo_fijo_auto = 8000
		self.tarifa.costo_fijo_moto = 4000
		self.tarifa.costo_fijo_otro = 12000
		self.tarifa.save()

	# --- Utilidades ------------------------------------------------------

	def _entrar(self, minutos, matricula='ABC-123', tipo='Auto'):
		"""Registra un vehiculo que entro hace `minutos` y sigue dentro."""
		return Cliente.objects.create(
			cedula='1122334455', nombre='Ana Ruiz', matricula=matricula,
			tipo_vehiculo=tipo,
			fecha_entrada=dj_timezone.now() - timedelta(minutes=minutos),
		)

	def _salir(self, cliente):
		"""Registra la salida por la vista, que es donde debe congelarse el cobro."""
		response = self.client.post(reverse('dashboard_parking'), {
			'confirmar_salida': 'true',
			'cliente_id': cliente.id,
		}, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
		self.assertTrue(response.json()['success'])
		cliente.refresh_from_db()
		return cliente

	def _subir_tarifas(self):
		self.costo.costo_auto = 500
		self.costo.costo_moto = 250
		self.costo.costo_otro = 900
		self.costo.save()

	# --- Congelamiento del cobro -----------------------------------------

	def test_la_salida_guarda_el_monto_cobrado(self):
		cliente = self._salir(self._entrar(minutos=10))
		self.assertIsNotNone(cliente.monto_cobrado)
		self.assertEqual(cliente.calcular_costo(), 1000)  # 10 min a 100/min

	def test_la_salida_por_codigo_tambien_congela_el_cobro(self):
		"""salida_qr registra la salida por su cuenta; no puede quedarse sin congelar."""
		cliente = self._entrar(minutos=10, matricula='QR-001')
		response = self.client.post(reverse('salida_qr'), {
			'codigo': str(cliente.id),
		}, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
		self.assertTrue(response.json()['success'])

		self._subir_tarifas()
		cliente.refresh_from_db()
		self.assertEqual(cliente.calcular_costo(), 1000)

	def test_subir_el_precio_no_recobra_a_quien_ya_salio(self):
		cliente = self._salir(self._entrar(minutos=10))
		self._subir_tarifas()
		cliente.refresh_from_db()
		self.assertEqual(cliente.calcular_costo(), 1000)

	def test_el_vehiculo_aun_dentro_si_toma_la_tarifa_nueva(self):
		"""No hay que congelar de mas: cotizar un carro dentro sigue siendo en vivo."""
		cliente = self._entrar(minutos=10)
		self._subir_tarifas()
		salida = cliente.fecha_entrada + timedelta(minutes=10)
		self.assertEqual(cliente.calcular_costo_temporal(salida), 5000)

	def test_activar_la_tarifa_plena_no_reetiqueta_cobros_pasados(self):
		cliente = self._salir(self._entrar(minutos=10))
		self.tarifa.activa = True
		self.tarifa.save()
		cliente.refresh_from_db()
		self.assertEqual(cliente.calcular_costo(), 1000)
		self.assertFalse(cliente.es_tarifa_plena())
		self.assertNotIn('Tarifa Plena', cliente.costo_formateado())

	def test_la_tarifa_plena_vigente_al_salir_queda_registrada(self):
		self.tarifa.activa = True
		self.tarifa.save()
		cliente = self._salir(self._entrar(minutos=10))
		self.assertEqual(cliente.calcular_costo(), 8000)
		self.assertTrue(cliente.es_tarifa_plena())

		# Apagar el interruptor global tampoco debe reabrir el cobro.
		self.tarifa.activa = False
		self.tarifa.save()
		cliente.refresh_from_db()
		self.assertEqual(cliente.calcular_costo(), 8000)
		self.assertTrue(cliente.es_tarifa_plena())

	def test_la_tarifa_unitaria_aplicada_queda_registrada(self):
		cliente = self._salir(self._entrar(minutos=10))
		self._subir_tarifas()
		cliente.refresh_from_db()
		# "Tarifa Base" en ver_registro.html sale de aqui.
		self.assertEqual(cliente.costo_por_tiempo(), 100)

	def test_un_registro_sin_monto_congelado_sigue_calculando_en_vivo(self):
		"""Respaldo para el historial anterior a la migracion (monto_cobrado nulo)."""
		cliente = Cliente.objects.create(
			cedula='999', matricula='OLD-001', tipo_vehiculo='Auto',
			fecha_entrada=dj_timezone.now() - timedelta(minutes=10),
			fecha_salida=dj_timezone.now(),
		)
		self.assertIsNone(cliente.monto_cobrado)
		self.assertEqual(cliente.calcular_costo(), 1000)

	# --- Cortes de recaudacion -------------------------------------------

	def test_el_corte_cerrado_cuadra_con_su_detalle_tras_cambiar_precios(self):
		self._salir(self._entrar(minutos=10, matricula='AAA-111'))
		self._salir(self._entrar(minutos=20, matricula='BBB-222'))

		response = self.client.post(reverse('corte_recaudacion'), {'observaciones': ''})
		self.assertTrue(response.json()['success'])
		corte = Recaudacion.objects.latest('fecha_corte')
		self.assertEqual(float(corte.monto_recaudado), 3000)

		self._subir_tarifas()

		detalle = corte.get_clientes_atendidos()
		self.assertEqual(sorted(d['costo'] for d in detalle), [1000.0, 2000.0])
		self.assertEqual(sum(d['costo'] for d in detalle), float(corte.monto_recaudado))

	def test_la_migracion_congela_el_historial_existente(self):
		"""Guarda del backfill de 0020, que corre sobre registros ya cerrados.

		La base de pruebas esta vacia cuando se aplican las migraciones, asi que el
		recorrido de clientes solo se ejercita invocandolo aqui con datos reales.
		"""
		migracion = import_module('app_page.migrations.0020_congelar_cobro_en_cliente')

		ahora = dj_timezone.now()
		viejos = {
			tipo: Cliente.objects.create(
				cedula='5555555555', matricula=f'OLD-{tipo}', tipo_vehiculo=tipo,
				fecha_entrada=ahora - timedelta(minutes=10), fecha_salida=ahora,
			)
			for tipo in ('Auto', 'Moto', 'Otro')
		}
		dentro = self._entrar(minutos=10, matricula='IN-001')

		migracion.congelar_historial(django_apps, None)

		for tipo, esperado in (('Auto', 1000), ('Moto', 500), ('Otro', 2000)):
			with self.subTest(tipo=tipo):
				viejos[tipo].refresh_from_db()
				self.assertEqual(float(viejos[tipo].monto_cobrado), esperado)
				self.assertEqual(float(viejos[tipo].tarifa_aplicada), esperado / 10)

		# Un vehiculo que sigue dentro no tiene cobro que congelar.
		dentro.refresh_from_db()
		self.assertIsNone(dentro.monto_cobrado)

	def test_el_periodo_abierto_no_se_reprecia(self):
		self._salir(self._entrar(minutos=10))
		antes = Recaudacion.calcular_recaudacion_actual()['monto_total']
		self._subir_tarifas()
		despues = Recaudacion.calcular_recaudacion_actual()['monto_total']

		self.assertEqual(antes, 1000)
		self.assertEqual(despues, antes)


class ManualSoporteTests(TestCase):
	"""Manual y soporte: acceso, filtrado por rol y datos de contacto."""

	def setUp(self):
		self.url = reverse('manual_soporte')
		self.admin = self._crear(username='jefa', rol='administrador')
		self.empleado = self._crear(username='auxiliar', rol='empleado')

	def _crear(self, username, rol, password='clave-segura-123'):
		usuario = User.objects.create_user(username=username, password=password)
		# El signal post_save de User ya creo el Perfil como 'empleado'.
		perfil = Perfil.objects.get(usuario=usuario)
		perfil.rol = rol
		perfil.save()
		return usuario

	def test_manual_requiere_login(self):
		response = self.client.get(self.url)
		self.assertEqual(response.status_code, 302)
		self.assertIn(reverse('login'), response['Location'])

	def test_empleado_accede_al_manual(self):
		self.client.force_login(self.empleado)
		response = self.client.get(self.url)
		self.assertEqual(response.status_code, 200)
		self.assertTemplateUsed(response, 'app_page/manual_soporte.html')
		self.assertContains(response, 'Registrar la salida y cobrar')

	def test_empleado_no_ve_secciones_de_administrador(self):
		self.client.force_login(self.empleado)
		response = self.client.get(self.url)
		self.assertNotContains(response, 'Solo administrador')
		self.assertNotContains(response, 'Configurar las tarifas')

	def test_administrador_ve_secciones_de_administrador(self):
		self.client.force_login(self.admin)
		response = self.client.get(self.url)
		self.assertContains(response, 'Solo administrador')
		self.assertContains(response, 'Configurar las tarifas')
		self.assertContains(response, 'corte de caja')

	def test_datos_de_soporte_en_la_pagina(self):
		self.client.force_login(self.empleado)
		response = self.client.get(self.url)
		self.assertContains(response, SOPORTE['whatsapp_url'])
		self.assertContains(response, SOPORTE['correo'])

	def test_enlace_de_ayuda_en_la_navegacion(self):
		"""El empleado tiene que poder llegar al manual desde cualquier pagina."""
		self.client.force_login(self.empleado)
		response = self.client.get(reverse('dashboard_parking'))
		self.assertContains(response, self.url)


class PresentacionManualTests(TestCase):
	"""La presentacion (docs/presentacion) tiene que seguir al manual en pantalla.

	El guion de las diapositivas repite, resumido, lo que explica
	manual_soporte.html. Si alguien renombra o borra una seccion del manual, la
	presentacion queda contando algo que ya no existe y nadie se entera hasta
	proyectarla. Estos tests atan las dos cosas por el id de la seccion.
	"""

	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		ruta = Path(settings.BASE_DIR) / 'docs' / 'presentacion' / 'contenido.py'
		especificacion = util.spec_from_file_location('presentacion_contenido', ruta)
		cls.contenido = util.module_from_spec(especificacion)
		especificacion.loader.exec_module(cls.contenido)

		manual = Path(settings.BASE_DIR) / 'app_page' / 'templates' / 'app_page' / 'manual_soporte.html'
		cls.manual_html = manual.read_text(encoding='utf-8')

	def test_cada_diapositiva_apunta_a_una_seccion_del_manual(self):
		for diapositiva in self.contenido.DIAPOSITIVAS:
			identificador = diapositiva['id']
			if identificador in self.contenido.IDS_SOLO_PRESENTACION:
				continue
			with self.subTest(diapositiva=identificador):
				self.assertIn(
					f'id="{identificador}"', self.manual_html,
					f'La diapositiva "{identificador}" ya no tiene seccion en el manual',
				)

	def test_las_excepciones_siguen_siendo_excepciones(self):
		"""Si el manual gana una de esas secciones, sobra tenerla exceptuada."""
		for identificador in self.contenido.IDS_SOLO_PRESENTACION:
			with self.subTest(diapositiva=identificador):
				self.assertNotIn(
					f'id="{identificador}"', self.manual_html,
					f'"{identificador}" ya existe en el manual: quitelo de IDS_SOLO_PRESENTACION',
				)

	def test_cada_diapositiva_tiene_texto_y_captura_propia(self):
		archivos = []
		for diapositiva in self.contenido.DIAPOSITIVAS:
			with self.subTest(diapositiva=diapositiva['id']):
				self.assertTrue(diapositiva['pasos'], 'La diapositiva no explica ningun paso')
				self.assertTrue(diapositiva['captura']['archivo'])
				archivos.append(diapositiva['captura']['archivo'])

		self.assertEqual(len(archivos), len(set(archivos)), 'Dos diapositivas comparten captura')
