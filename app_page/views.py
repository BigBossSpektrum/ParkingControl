import os
from io import BytesIO
import qrcode
import logging
from django.conf import settings
from django.utils import timezone
from django.views.decorators.csrf import csrf_protect
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django import forms
from django.db import models
from django.core.files.base import ContentFile
from .models import Cliente
from .decorators import require_edit_permission, require_delete_permission, require_view_list_permission, get_user_profile

# Configurar logger
logger = logging.getLogger(__name__)

# --- DASHBOARD: Panel principal con ambos formularios ---
@login_required
@csrf_protect
def dashboard(request):
	logger.info(f"Dashboard accessed by user: {request.user.username}")
	logger.info(f"Request method: {request.method}")
	if request.method == 'POST':
		logger.info(f"POST data: {request.POST}")
	
	mensaje_salida = ''
	message_success = ''
	salida_form = SalidaQRForm()
	registro_form = ClienteForm()

	if request.method == 'POST':
		logger.info("Processing POST request")
		# Detectar petición AJAX
		is_ajax = (
			request.headers.get('X-Requested-With') == 'XMLHttpRequest' or
			request.content_type == 'application/json' or
			request.GET.get('ajax') == '1' or
			request.POST.get('ajax') == '1' or
			'application/json' in request.headers.get('Accept', '')
		)
		logger.info(f"Is AJAX request: {is_ajax}")
		
		if 'codigo' in request.POST:
			logger.info("Processing salida (exit) form")
			salida_form = SalidaQRForm(request.POST)
			if salida_form.is_valid():
				codigo = salida_form.cleaned_data['codigo'].strip()
				cliente = None
				
				# Buscar por ID (numérico)
				if codigo.isdigit():
					try:
						cliente = Cliente.objects.get(id=int(codigo), fecha_salida__isnull=True)
					except Cliente.DoesNotExist:
						pass
				
				# Si no se encontró por ID, buscar por cédula
				if not cliente:
					try:
						cliente = Cliente.objects.get(cedula=codigo, fecha_salida__isnull=True)
					except Cliente.DoesNotExist:
						cliente = None
				
				if cliente:
					cliente.fecha_salida = timezone.now()
					cliente.save()
					
					# Calcular tiempo en parking
					if cliente.fecha_entrada:
						delta = cliente.fecha_salida - cliente.fecha_entrada
						minutos = int(delta.total_seconds() // 60)
						tiempo_str = f"{minutos} minutos"
					else:
						tiempo_str = "Tiempo no disponible"
					
					# Si es petición AJAX, devolver JSON
					if is_ajax:
						return JsonResponse({
							'success': True,
							'mensaje': f'Salida registrada exitosamente para {cliente.get_display_name()}',
							'cliente': {
								'nombre': cliente.get_display_name(),
								'cedula': cliente.get_display_cedula(),
								'matricula': cliente.matricula,
								'tipo_vehiculo': cliente.get_tipo_vehiculo_display(),
								'fecha_entrada': cliente.fecha_entrada.strftime('%d/%m/%Y %H:%M') if cliente.fecha_entrada else 'No registrada',
								'fecha_salida': cliente.fecha_salida.strftime('%d/%m/%Y %H:%M'),
								'tiempo_total': tiempo_str
							}
						})
					
					mensaje_salida = f'Salida registrada para {cliente.get_display_name()}.'
				else:
					# Si es petición AJAX, devolver JSON
					if is_ajax:
						return JsonResponse({
							'success': False,
							'mensaje': 'Cliente no encontrado o ya tiene salida registrada.'
						})
					
					mensaje_salida = 'Cliente no encontrado.'
			else:
				# Si es petición AJAX, devolver JSON
				if is_ajax:
					return JsonResponse({
						'success': False,
						'mensaje': 'Código inválido. Por favor, verifique e intente nuevamente.'
					})
				
				mensaje_salida = 'Código inválido.'
		else:
			# Manejar formulario de registro
			logger.info("Processing registro (registration) form")
			registro_form = ClienteForm(request.POST)
			logger.info(f"Form data received: {request.POST}")
			logger.info(f"Form is valid: {registro_form.is_valid()}")
			
			if registro_form.is_valid():
				logger.info("Form validation passed")
				try:
					cliente = registro_form.save(commit=False)
					cliente.fecha_entrada = timezone.now()
					cliente.save()
					logger.info(f"Cliente saved with ID: {cliente.id}")
					
					# Generar QR con datos adicionales
					qr_generated = cliente.generate_qr_with_data()
					logger.info(f"QR generation result: {qr_generated}")
					cliente.save()
					logger.info("Cliente saved again after QR generation")
					
					# Si es petición AJAX, devolver JSON
					if is_ajax:
						logger.info("Returning AJAX success response")
						return JsonResponse({
							'success': True,
							'mensaje': 'Cliente registrado exitosamente',
							'cliente': {
								'id': cliente.id,
								'nombre': cliente.get_display_name(),
								'cedula': cliente.get_display_cedula(),
								'matricula': cliente.matricula,
								'tipo_vehiculo': cliente.get_tipo_vehiculo_display(),
								'fecha_entrada': cliente.fecha_entrada.strftime('%d/%m/%Y %H:%M'),
								'qr_url': cliente.qr_image.url if cliente.qr_image else None
							}
						})
					
					message_success = 'Cliente registrado correctamente.'
					registro_form = ClienteForm()  # Limpiar formulario
					logger.info("Registration completed successfully")
				except Exception as e:
					logger.error(f"Error during client registration: {str(e)}")
					if is_ajax:
						return JsonResponse({
							'success': False,
							'mensaje': f'Error al registrar cliente: {str(e)}'
						})
			else:
				logger.warning(f"Form validation failed. Errors: {registro_form.errors}")
				# Si es petición AJAX con errores
				if is_ajax:
					errors = {}
					for field, error_list in registro_form.errors.items():
						errors[field] = error_list
					logger.info(f"Returning AJAX error response: {errors}")
					return JsonResponse({
						'success': False,
						'mensaje': 'Hay errores en el formulario',
						'errors': errors
					})
	# Obtener perfil del usuario
	perfil = get_user_profile(request.user)
	
	return render(request, 'app_page/dashboard.html', {
		'salida_form': salida_form,
		'registro_form': registro_form,
		'mensaje_salida': mensaje_salida,
		'message_success': message_success,
		'perfil': perfil,
	})

# --- VISTA PARA VER REGISTRO Y QR ---
@login_required
def ver_registro(request, pk):
	cliente = get_object_or_404(Cliente, pk=pk)
	
	# Detectar petición AJAX de múltiples formas
	is_ajax = (
		request.headers.get('X-Requested-With') == 'XMLHttpRequest' or
		request.content_type == 'application/json' or
		request.GET.get('ajax') == '1' or
		request.POST.get('ajax') == '1' or
		'application/json' in request.headers.get('Accept', '')
	)
	
	# Si es una petición AJAX, devolver JSON
	if is_ajax:
		data = {
			'nombre': cliente.get_display_name(),
			'cedula': cliente.get_display_cedula(),
			'telefono': cliente.get_display_telefono(),
			'matricula': cliente.matricula,
			'tipo_vehiculo': cliente.get_tipo_vehiculo_display(),
			'fecha_entrada': cliente.fecha_entrada.strftime('%d/%m/%Y %H:%M') if cliente.fecha_entrada else None,
			'fecha_salida': cliente.fecha_salida.strftime('%d/%m/%Y %H:%M') if cliente.fecha_salida else None,
			'qr_url': cliente.qr_image.url if cliente.qr_image else None,
		}
		return JsonResponse(data)
	
	return render(request, 'app_page/ver_registro.html', {'cliente': cliente})

# --- FORMULARIOS ---
class ClienteForm(forms.ModelForm):
	matricula_inicio = forms.CharField(
		max_length=3, 
		required=True,
		widget=forms.TextInput(attrs={'class': 'form-control text-uppercase', 'placeholder': 'ABC'})
	)
	matricula_fin = forms.CharField(
		max_length=3, 
		required=True,
		widget=forms.TextInput(attrs={'class': 'form-control text-uppercase', 'placeholder': '123'})
	)
	
	class Meta:
		model = Cliente
		fields = ['cedula', 'nombre', 'telefono', 'matricula_inicio', 'matricula_fin', 'tipo_vehiculo']
		widgets = {
			'cedula': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: 12345678'}),
			'nombre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre completo'}),
			'telefono': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: 3001234567'}),
			'tipo_vehiculo': forms.Select(attrs={'class': 'form-control'}),
		}
		labels = {
			'cedula': 'Cédula (Opcional)',
			'nombre': 'Nombre Completo (Opcional)',
			'telefono': 'Teléfono (Opcional)',
			'tipo_vehiculo': 'Tipo de Vehículo',
		}
	
	def save(self, commit=True):
		instance = super().save(commit=False)
		matricula_inicio = self.cleaned_data.get('matricula_inicio', '').upper()
		matricula_fin = self.cleaned_data.get('matricula_fin', '').upper()
		instance.matricula = f"{matricula_inicio}-{matricula_fin}"
		if commit:
			instance.save()
		return instance

class SalidaQRForm(forms.Form):
	codigo = forms.CharField(label='Escanee el código de barras/QR o ingrese la cédula o ID')

# --- VISTAS ---
def login_view(request):
	if request.method == 'POST':
		form = LoginForm(request.POST)
		if form.is_valid():
			user = authenticate(request, username=form.cleaned_data['username'], password=form.cleaned_data['password'])
			if user is not None:
				auth_login(request, user)
				return redirect('dashboard')
			else:
				error = 'Usuario o contraseña incorrectos'
				return render(request, 'registration/login.html', {'form': form, 'error': error})
	else:
		form = LoginForm()
	return render(request, 'registration/login.html', {'form': form})

def logout_view(request):
	auth_logout(request)
	return redirect('login')

class LoginForm(forms.Form):
	username = forms.CharField(max_length=150, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Usuario'}))
	password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Contraseña'}))

# Lista de clientes con paginación y filtros AJAX
@login_required
def lista_clientes(request):
	# Obtener parámetros de filtro
	estado = request.GET.get('estado', 'todos')
	buscar = request.GET.get('buscar', '')
	fecha_inicio = request.GET.get('fecha_inicio', '')
	fecha_fin = request.GET.get('fecha_fin', '')
	
	# Filtrar clientes
	clientes = Cliente.objects.all().order_by('-fecha_entrada')
	
	# Filtro por estado
	if estado == 'en_parking':
		clientes = clientes.filter(fecha_salida__isnull=True)
	elif estado == 'salidos':
		clientes = clientes.filter(fecha_salida__isnull=False)
	
	# Filtro por búsqueda
	if buscar:
		clientes = clientes.filter(
			models.Q(nombre__icontains=buscar) |
			models.Q(cedula__icontains=buscar) |
			models.Q(matricula__icontains=buscar)
		)
	
	# Filtro por rango de fechas
	if fecha_inicio:
		try:
			fecha_inicio_dt = timezone.datetime.strptime(fecha_inicio, '%Y-%m-%d')
			fecha_inicio_dt = timezone.make_aware(fecha_inicio_dt.replace(hour=0, minute=0, second=0))
			clientes = clientes.filter(fecha_entrada__gte=fecha_inicio_dt)
		except ValueError:
			pass
	
	if fecha_fin:
		try:
			fecha_fin_dt = timezone.datetime.strptime(fecha_fin, '%Y-%m-%d')
			fecha_fin_dt = timezone.make_aware(fecha_fin_dt.replace(hour=23, minute=59, second=59))
			clientes = clientes.filter(fecha_entrada__lte=fecha_fin_dt)
		except ValueError:
			pass
	
	# Paginación
	paginator = Paginator(clientes, 10)
	page_number = request.GET.get('page', 1)
	page_obj = paginator.get_page(page_number)
	
	# Obtener perfil del usuario
	perfil = get_user_profile(request.user)
	
	context = {
		'page_obj': page_obj,
		'estado': estado,
		'buscar': buscar,
		'fecha_inicio': fecha_inicio,
		'fecha_fin': fecha_fin,
		'perfil': perfil,
	}
	
	return render(request, 'app_page/lista_clientes.html', context)

# Editar cliente
@require_edit_permission
def editar_cliente(request, pk):
	cliente = get_object_or_404(Cliente, pk=pk)
	
	# Detectar petición AJAX de múltiples formas
	is_ajax = (
		request.headers.get('X-Requested-With') == 'XMLHttpRequest' or
		request.content_type == 'application/json' or
		request.GET.get('ajax') == '1' or
		request.POST.get('ajax') == '1' or
		'application/json' in request.headers.get('Accept', '')
	)
	
	if request.method == 'POST':
		# Si es petición AJAX
		if is_ajax:
			try:
				# Actualizar campos permitidos
				if 'nombre' in request.POST:
					cliente.nombre = request.POST['nombre']
				if 'telefono' in request.POST:
					cliente.telefono = request.POST['telefono']
				if 'matricula' in request.POST:
					cliente.matricula = request.POST['matricula']
				if 'tipo_vehiculo' in request.POST:
					cliente.tipo_vehiculo = request.POST['tipo_vehiculo']
				
				cliente.save()
				
				return JsonResponse({
					'success': True,
					'mensaje': 'Cliente actualizado exitosamente'
				})
			except Exception as e:
				return JsonResponse({
					'success': False,
					'mensaje': f'Error al actualizar: {str(e)}'
				})
		
		# Formulario normal
		form = ClienteEditForm(request.POST, instance=cliente)
		if form.is_valid():
			form.save()
			return redirect('lista_clientes')
	else:
		# Si es petición AJAX para obtener datos
		if is_ajax:
			data = {
				'nombre': cliente.get_display_name(),
				'telefono': cliente.get_display_telefono(),
				'matricula': cliente.matricula,
				'tipo_vehiculo': cliente.tipo_vehiculo,
			}
			return JsonResponse(data)
		
		# Para peticiones normales (fallback), redirigir a lista de clientes
		return redirect('lista_clientes')

class ClienteEditForm(forms.ModelForm):
	class Meta:
		model = Cliente
		fields = ['nombre', 'telefono', 'matricula', 'tipo_vehiculo']
		widgets = {
			'nombre': forms.TextInput(attrs={'class': 'form-control'}),
			'telefono': forms.TextInput(attrs={'class': 'form-control'}),
			'matricula': forms.TextInput(attrs={'class': 'form-control'}),
			'tipo_vehiculo': forms.Select(attrs={'class': 'form-control'}),
		}

# Eliminar cliente
@require_delete_permission
def eliminar_cliente(request, pk):
	cliente = get_object_or_404(Cliente, pk=pk)
	
	# Detectar petición AJAX de múltiples formas
	is_ajax = (
		request.headers.get('X-Requested-With') == 'XMLHttpRequest' or
		request.content_type == 'application/json' or
		request.GET.get('ajax') == '1' or
		request.POST.get('ajax') == '1' or
		'application/json' in request.headers.get('Accept', '')
	)
	
	if request.method == 'POST':
		cliente.delete()
		
		# Si es petición AJAX
		if is_ajax:
			return JsonResponse({'success': True, 'mensaje': 'Cliente eliminado exitosamente'})
		
		return redirect('lista_clientes')
	
	# Si es petición AJAX para obtener datos de confirmación
	if is_ajax:
		data = {
			'nombre': cliente.get_display_name(),
			'cedula': cliente.get_display_cedula(),
		}
		return JsonResponse(data)
	
	# Para peticiones normales (fallback), redirigir a lista de clientes
	return redirect('lista_clientes')

def salida_qr(request):
	if request.method == 'POST':
		# Debug: Imprimir headers para diagnóstico
		print(f"Headers recibidos: {dict(request.headers)}")
		print(f"Content-Type: {request.content_type}")
		print(f"X-Requested-With: {request.headers.get('X-Requested-With')}")
		
		# Detectar petición AJAX de múltiples formas
		is_ajax = (
			request.headers.get('X-Requested-With') == 'XMLHttpRequest' or
			request.content_type == 'application/json' or
			request.GET.get('ajax') == '1' or
			request.POST.get('ajax') == '1' or
			'application/json' in request.headers.get('Accept', '')
		)
		
		print(f"Es petición AJAX: {is_ajax}")
		
		form = SalidaQRForm(request.POST)
		if form.is_valid():
			codigo = form.cleaned_data['codigo'].strip()
			cliente = None
			
			# Buscar por ID (numérico)
			if codigo.isdigit():
				try:
					cliente = Cliente.objects.get(id=int(codigo), fecha_salida__isnull=True)
				except Cliente.DoesNotExist:
					pass
			
			# Si no se encontró por ID, buscar por cédula
			if not cliente:
				try:
					cliente = Cliente.objects.get(cedula=codigo, fecha_salida__isnull=True)
				except Cliente.DoesNotExist:
					cliente = None
			
			if cliente:
				from django.utils import timezone
				cliente.fecha_salida = timezone.now()
				cliente.save()
				
				# Calcular tiempo en parking
				if cliente.fecha_entrada:
					delta = cliente.fecha_salida - cliente.fecha_entrada
					minutos = int(delta.total_seconds() // 60)
					tiempo_str = f"{minutos} minutos"
				else:
					tiempo_str = "Tiempo no disponible"
				
				# Si es petición AJAX, devolver JSON
				if is_ajax:
					return JsonResponse({
						'success': True,
						'mensaje': f'Salida registrada exitosamente para {cliente.nombre}',
						'cliente': {
							'nombre': cliente.nombre,
							'cedula': cliente.cedula,
							'matricula': cliente.matricula,
							'tipo_vehiculo': cliente.get_tipo_vehiculo_display(),
							'fecha_entrada': cliente.fecha_entrada.strftime('%d/%m/%Y %H:%M') if cliente.fecha_entrada else 'No registrada',
							'fecha_salida': cliente.fecha_salida.strftime('%d/%m/%Y %H:%M'),
							'tiempo_total': tiempo_str
						}
					})
				
				# Para peticiones normales (fallback)
				mensaje = f'Salida registrada exitosamente para {cliente.nombre}.'
				cliente_info = {
					'nombre': cliente.nombre,
					'cedula': cliente.cedula,
					'matricula': cliente.matricula,
					'tipo_vehiculo': cliente.get_tipo_vehiculo_display(),
					'fecha_entrada': cliente.fecha_entrada.strftime('%d/%m/%Y %H:%M') if cliente.fecha_entrada else 'No registrada',
					'fecha_salida': cliente.fecha_salida.strftime('%d/%m/%Y %H:%M'),
					'tiempo_total': tiempo_str
				}
			else:
				# Si es petición AJAX, devolver JSON
				if is_ajax:
					return JsonResponse({
						'success': False,
						'mensaje': 'Cliente no encontrado o ya tiene salida registrada.'
					})
				
				mensaje = 'Cliente no encontrado o ya tiene salida registrada.'
				cliente_info = None
		else:
			# Si es petición AJAX, devolver JSON
			if is_ajax:
				return JsonResponse({
					'success': False,
					'mensaje': 'Código inválido. Por favor, verifique e intente nuevamente.'
				})
			
			mensaje = 'Código inválido. Por favor, verifique e intente nuevamente.'
			cliente_info = None
		
		# Para peticiones normales (fallback)
		return render(request, 'app_page/salida_qr.html', {
			'form': form, 
			'mensaje': mensaje,
			'cliente_info': cliente_info
		})
	else:
		form = SalidaQRForm()
		return render(request, 'app_page/salida_qr.html', {'form': form})
