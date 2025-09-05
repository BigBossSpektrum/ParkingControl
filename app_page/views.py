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
from .models import Cliente, Costo, Visitante, TarifaPlena, Recaudacion
from .decorators import require_edit_permission, require_delete_permission, require_view_list_permission, get_user_profile

# Importar el servicio de impresión
try:
    from app_impresora.printer_service import printer_service
    PRINTER_AVAILABLE = True
except ImportError:
    PRINTER_AVAILABLE = False
    printer_service = None

# Configurar logger
logger = logging.getLogger(__name__)

def procesar_confirmacion_salida(request, is_ajax):
	"""Función para procesar la confirmación de salida después de mostrar el costo"""
	try:
		cliente_id = request.POST.get('cliente_id')
		if not cliente_id:
			return JsonResponse({
				'success': False,
				'mensaje': 'ID de cliente no proporcionado.'
			})
		
		try:
			cliente = Cliente.objects.get(id=cliente_id, fecha_salida__isnull=True)
		except Cliente.DoesNotExist:
			return JsonResponse({
				'success': False,
				'mensaje': 'Cliente no encontrado o ya tiene salida registrada.'
			})
		except Cliente.MultipleObjectsReturned:
			# Si hay múltiples, tomar el más reciente
			cliente = Cliente.objects.filter(id=cliente_id, fecha_salida__isnull=True).order_by('-fecha_entrada').first()
			if not cliente:
				return JsonResponse({
					'success': False,
					'mensaje': 'Cliente no encontrado o ya tiene salida registrada.'
				})
		
		# Ahora sí registrar la salida
		cliente.fecha_salida = timezone.now()
		cliente.save()
		
		# Calcular tiempo en parking
		if cliente.fecha_entrada:
			delta = cliente.fecha_salida - cliente.fecha_entrada
			minutos = int(delta.total_seconds() // 60)
			tiempo_str = f"{minutos} minutos"
		else:
			tiempo_str = "Tiempo no disponible"
		
		# Calcular costo total final
		costo_total = cliente.calcular_costo()
		costo_formateado = cliente.costo_formateado()
		
		# Si es petición AJAX, devolver JSON
		if is_ajax:
			return JsonResponse({
				'success': True,
				'salida_confirmada': True,
				'mensaje': f'Salida registrada exitosamente para {cliente.get_display_name()}',
				'cliente': {
					'nombre': cliente.get_display_name(),
					'cedula': cliente.get_display_cedula(),
					'matricula': cliente.matricula,
					'tipo_vehiculo': cliente.get_tipo_vehiculo_display(),
					'fecha_entrada': cliente.fecha_entrada.strftime('%d/%m/%Y %H:%M') if cliente.fecha_entrada else 'No registrada',
					'fecha_salida': cliente.fecha_salida.strftime('%d/%m/%Y %H:%M'),
					'tiempo_total': tiempo_str,
					'costo_total': costo_total,
					'costo_formateado': costo_formateado,
					'es_tarifa_plena': cliente.es_tarifa_plena()
				}
			})
		
		return JsonResponse({
			'success': True,
			'mensaje': f'Salida registrada para {cliente.get_display_name()}.'
		})
		
	except Cliente.DoesNotExist:
		return JsonResponse({
			'success': False,
			'mensaje': 'Cliente no encontrado o ya tiene salida registrada.'
		})
	except Exception as e:
		logger.error(f"Error en procesar_confirmacion_salida: {str(e)}")
		return JsonResponse({
			'success': False,
			'mensaje': 'Error interno del servidor.'
		})

# --- DASHBOARD: Panel principal con ambos formularios ---
@login_required
@csrf_protect
def dashboard(request):
	return redirect('dashboard_parking')

# --- DASHBOARD PARKING: Panel principal para vehículos ---
@login_required
@csrf_protect
def dashboard_parking(request):
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
		
		# Verificar PRIMERO si es confirmación de salida
		if request.POST.get('confirmar_salida') == 'true':
			logger.info("Processing salida confirmation")
			return procesar_confirmacion_salida(request, is_ajax)
		
		if 'codigo' in request.POST:
			logger.info("Processing salida (exit) form")
			
			# Si no es confirmación, solo obtener información del cliente
			salida_form = SalidaQRForm(request.POST)
			if salida_form.is_valid():
				codigo = salida_form.cleaned_data['codigo'].strip()
				cliente = None
				
				# Buscar por ID (numérico)
				if codigo.isdigit():
					try:
						cliente = Cliente.objects.filter(id=int(codigo), fecha_salida__isnull=True).first()
					except (Cliente.DoesNotExist, ValueError):
						pass
				
				# Si no se encontró por ID, buscar por cédula
				if not cliente:
					try:
						# Usar filter().first() para obtener el primer cliente activo con esa cédula
						cliente = Cliente.objects.filter(cedula=codigo, fecha_salida__isnull=True).order_by('-fecha_entrada').first()
					except Cliente.DoesNotExist:
						cliente = None
				
				if cliente:
					# NO registrar salida aún, solo calcular información
					fecha_salida_temporal = timezone.now()
					
					# Calcular tiempo en parking
					if cliente.fecha_entrada:
						delta = fecha_salida_temporal - cliente.fecha_entrada
						minutos = int(delta.total_seconds() // 60)
						tiempo_str = f"{minutos} minutos"
					else:
						tiempo_str = "Tiempo no disponible"
					
					# Calcular costo total (sin registrar salida)
					costo_total = cliente.calcular_costo_temporal(fecha_salida_temporal)
					costo_formateado = cliente.costo_formateado_temporal(fecha_salida_temporal)
					
					# Si es petición AJAX, devolver JSON con información para confirmar
					if is_ajax:
						return JsonResponse({
							'success': True,
							'mostrar_confirmacion': True,
							'mensaje': f'Cliente encontrado: {cliente.get_display_name()}',
							'cliente': {
								'id': cliente.id,
								'nombre': cliente.get_display_name(),
								'cedula': cliente.get_display_cedula(),
								'matricula': cliente.matricula,
								'tipo_vehiculo': cliente.get_tipo_vehiculo_display(),
								'fecha_entrada': cliente.fecha_entrada.strftime('%d/%m/%Y %H:%M') if cliente.fecha_entrada else 'No registrada',
								'fecha_salida_estimada': fecha_salida_temporal.strftime('%d/%m/%Y %H:%M'),
								'tiempo_total': tiempo_str,
								'costo_total': costo_total,
								'costo_formateado': costo_formateado,
								'es_tarifa_plena': cliente.es_tarifa_plena()
							}
						})
					
					mensaje_salida = f'Cliente encontrado: {cliente.get_display_name()}. Confirme para registrar salida.'
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
					
					# Generar QR limpio sin datos adicionales
					qr_generated = cliente.generate_clean_qr()
					logger.info(f"QR generation result: {qr_generated}")
					cliente.save()
					logger.info("Cliente saved again after QR generation")
					
					# Intentar impresión automática del ticket
					print_success = False
					print_message = ""
					
					if PRINTER_AVAILABLE and printer_service:
						try:
							print_success = printer_service.print_qr_ticket(cliente)
							if print_success:
								print_message = "Ticket impreso automáticamente"
								logger.info(f"Ticket printed successfully for client {cliente.id}")
							else:
								print_message = "Error al imprimir ticket automáticamente"
								logger.warning(f"Failed to print ticket for client {cliente.id}")
						except Exception as print_error:
							print_message = f"Error de impresión: {str(print_error)}"
							logger.error(f"Printing error for client {cliente.id}: {print_error}")
					else:
						print_message = "Servicio de impresión no disponible"
						logger.info("Printer service not available")
					
					# Si es petición AJAX, devolver JSON
					if is_ajax:
						logger.info("Returning AJAX success response")
						response_data = {
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
							},
							'print_result': {
								'success': print_success,
								'message': print_message
							}
						}
						return JsonResponse(response_data)
					
					# Para requests normales, agregar mensaje de impresión
					if print_success:
						message_success = 'Cliente registrado correctamente. Ticket impreso.'
					else:
						message_success = f'Cliente registrado correctamente. {print_message}'
					
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
	
	return render(request, 'app_page/dashboard_parking.html', {
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
	
	# Obtener perfil del usuario para el template
	perfil = get_user_profile(request.user)
	
	return render(request, 'app_page/ver_registro.html', {
		'cliente': cliente,
		'perfil': perfil
	})

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
		fields = ['cedula', 'nombre', 'telefono', 'torre', 'apartamento', 'matricula_inicio', 'matricula_fin', 'tipo_vehiculo']
		widgets = {
			'cedula': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: 12345678'}),
			'nombre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre completo'}),
			'telefono': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: 3001234567'}),
			'torre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: A, B, C, 1, 2'}),
			'apartamento': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: 101, 502'}),
			'tipo_vehiculo': forms.Select(attrs={'class': 'form-control'}),
		}
		labels = {
			'cedula': 'Cédula (Opcional)',
			'nombre': 'Nombre Completo (Opcional)',
			'telefono': 'Teléfono (Opcional)',
			'torre': 'Torre (Opcional)',
			'apartamento': 'Apartamento (Opcional)',
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
			models.Q(matricula__icontains=buscar) |
			models.Q(torre__icontains=buscar) |
			models.Q(apartamento__icontains=buscar) |
			models.Q(telefono__icontains=buscar)
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
	
	# Obtener configuración de tarifa plena
	tarifa_plena = TarifaPlena.get_tarifa_actual()
	
	context = {
		'page_obj': page_obj,
		'estado': estado,
		'buscar': buscar,
		'fecha_inicio': fecha_inicio,
		'fecha_fin': fecha_fin,
		'perfil': perfil,
		'tarifa_plena': tarifa_plena,
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
				if 'torre' in request.POST:
					cliente.torre = request.POST['torre']
				if 'apartamento' in request.POST:
					cliente.apartamento = request.POST['apartamento']
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
				'torre': cliente.get_display_torre(),
				'apartamento': cliente.get_display_apartamento(),
				'matricula': cliente.matricula,
				'tipo_vehiculo': cliente.tipo_vehiculo,
			}
			return JsonResponse(data)
		
		# Para peticiones normales (fallback), redirigir a lista de clientes
		return redirect('lista_clientes')

class ClienteEditForm(forms.ModelForm):
	class Meta:
		model = Cliente
		fields = ['nombre', 'telefono', 'torre', 'apartamento', 'matricula', 'tipo_vehiculo']
		widgets = {
			'nombre': forms.TextInput(attrs={'class': 'form-control'}),
			'telefono': forms.TextInput(attrs={'class': 'form-control'}),
			'torre': forms.TextInput(attrs={'class': 'form-control'}),
			'apartamento': forms.TextInput(attrs={'class': 'form-control'}),
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
					cliente = Cliente.objects.filter(id=int(codigo), fecha_salida__isnull=True).first()
				except (Cliente.DoesNotExist, ValueError):
					pass
			
			# Si no se encontró por ID, buscar por cédula
			if not cliente:
				try:
					# Usar filter().first() para obtener el primer cliente activo con esa cédula
					cliente = Cliente.objects.filter(cedula=codigo, fecha_salida__isnull=True).order_by('-fecha_entrada').first()
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
				
				# Calcular costo total
				costo_total = cliente.calcular_costo()
				costo_formateado = cliente.costo_formateado()
				
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
							'tiempo_total': tiempo_str,
							'costo_total': costo_total,
							'costo_formateado': costo_formateado,
							'es_tarifa_plena': cliente.es_tarifa_plena()
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


class CostoForm(forms.ModelForm):
	"""Formulario para configurar los costos del parking"""
	class Meta:
		model = Costo
		fields = ['costo_auto', 'costo_moto']
		widgets = {
			'costo_auto': forms.NumberInput(attrs={
				'class': 'form-control', 
				'placeholder': 'Ej: 1.00',
				'step': '0.01',
				'min': '0'
			}),
			'costo_moto': forms.NumberInput(attrs={
				'class': 'form-control', 
				'placeholder': 'Ej: 0.50',
				'step': '0.01',
				'min': '0'
			}),
		}
		labels = {
			'costo_auto': 'Costo por minuto - Auto ($)',
			'costo_moto': 'Costo por minuto - Moto ($)',
		}


@login_required
def configurar_costos(request):
	"""Vista para configurar los costos del parking - Solo administradores"""
	try:
		perfil = get_user_profile(request.user)
		if not perfil.puede_editar_costos():
			return render(request, 'app_page/sin_permiso.html', {
				'mensaje': 'No tiene permisos para configurar los costos del parking.'
			})
	except:
		return render(request, 'app_page/sin_permiso.html', {
			'mensaje': 'No tiene un perfil asignado.'
		})
	
	# Obtener o crear la configuración de costos
	costo = Costo.get_costos_actuales()
	
	if request.method == 'POST':
		form = CostoForm(request.POST, instance=costo)
		if form.is_valid():
			costo_obj = form.save(commit=False)
			costo_obj.actualizado_por = request.user
			costo_obj.save()
			
			return render(request, 'app_page/configurar_costos.html', {
				'form': CostoForm(instance=costo_obj),
				'mensaje_exito': 'Costos actualizados correctamente.',
				'costo': costo_obj
			})
		else:
			return render(request, 'app_page/configurar_costos.html', {
				'form': form,
				'mensaje_error': 'Por favor, corrija los errores en el formulario.',
				'costo': costo
			})
	else:
		form = CostoForm(instance=costo)
	
	return render(request, 'app_page/configurar_costos.html', {
		'form': form,
		'costo': costo
	})


@login_required
def portal_opciones(request):
	"""Vista del portal de opciones principal"""
	# Contar clientes registrados hoy
	hoy = timezone.now().date()
	conteo_hoy = Cliente.objects.filter(fecha_entrada__date=hoy).count()
	
	# Obtener últimos 5 registros
	ultimos = Cliente.objects.all().order_by('-fecha_entrada')[:5]

# --- DASHBOARD VISITANTE: Panel principal para visitantes ---
@login_required
@csrf_protect
def dashboard_visitante(request):
	mensaje_error = ''
	message_success = ''

	if request.method == 'POST':
		action = request.POST.get('action')
		
		if action == 'registro_visitante':
			# Procesar registro de visitante
			cedula = request.POST.get('cedula', '').strip()
			nombre = request.POST.get('nombre', '').strip()
			telefono = request.POST.get('telefono', '').strip()
			torre = request.POST.get('torre', '').strip()
			apartamento = request.POST.get('apartamento', '').strip()
			
			# Validaciones básicas
			if not cedula or not nombre or not torre or not apartamento:
				mensaje_error = 'Por favor complete todos los campos obligatorios'
			else:
				try:
					# Crear visitante
					visitante = Visitante.objects.create(
						cedula=cedula,
						nombre=nombre,
						telefono=telefono,
						torre=torre,
						apartamento=apartamento
					)
					message_success = f'Visitante {nombre} registrado exitosamente'
				except Exception as e:
					mensaje_error = f'Error al registrar visitante: {str(e)}'

	# Obtener estadísticas
	hoy = timezone.now().date()
	visitantes_hoy = Visitante.objects.filter(fecha_registro__date=hoy).count()
	total_visitantes = Visitante.objects.count()
	
	# Obtener últimos visitantes
	ultimos_visitantes = Visitante.objects.all().order_by('-fecha_registro')[:5]
	
	# Obtener perfil del usuario
	perfil = get_user_profile(request.user)
	
	return render(request, 'app_page/dashboard_visitante.html', {
		'mensaje_error': mensaje_error,
		'message_success': message_success,
		'visitantes_hoy': visitantes_hoy,
		'total_visitantes': total_visitantes,
		'ultimos_visitantes': ultimos_visitantes,
		'perfil': perfil,
		'today': timezone.now().date(),
	})

# --- LISTA DE VISITANTES ---
@login_required
def lista_visitantes(request):
	# Obtener parámetros de filtro
	cedula_buscar = request.GET.get('cedula', '').strip()
	nombre_buscar = request.GET.get('nombre', '').strip()
	torre_buscar = request.GET.get('torre', '').strip()
	apartamento_buscar = request.GET.get('apartamento', '').strip()
	
	# Filtrar visitantes
	visitantes = Visitante.objects.all().order_by('-fecha_registro')
	
	# Aplicar filtros
	if cedula_buscar:
		visitantes = visitantes.filter(cedula__icontains=cedula_buscar)
	
	if nombre_buscar:
		visitantes = visitantes.filter(nombre__icontains=nombre_buscar)
	
	if torre_buscar:
		visitantes = visitantes.filter(torre__icontains=torre_buscar)
	
	if apartamento_buscar:
		visitantes = visitantes.filter(apartamento__icontains=apartamento_buscar)
	
	# Paginación
	paginator = Paginator(visitantes, 20)
	page_number = request.GET.get('page', 1)
	page_obj = paginator.get_page(page_number)
	
	# Estadísticas
	hoy = timezone.now().date()
	inicio_semana = hoy - timezone.timedelta(days=hoy.weekday())
	
	total_visitantes = Visitante.objects.count()
	visitantes_hoy = Visitante.objects.filter(fecha_registro__date=hoy).count()
	visitantes_semana = Visitante.objects.filter(fecha_registro__date__gte=inicio_semana).count()
	torres_activas = Visitante.objects.exclude(torre__isnull=True).exclude(torre='').values('torre').distinct().count()
	
	# Obtener perfil del usuario
	perfil = get_user_profile(request.user)
	
	context = {
		'visitantes': page_obj,
		'total_visitantes': total_visitantes,
		'visitantes_hoy': visitantes_hoy,
		'visitantes_semana': visitantes_semana,
		'torres_activas': torres_activas,
		'perfil': perfil,
	}
	
	return render(request, 'app_page/lista_visitantes.html', context)

# --- TOGGLE TARIFA PLENA ---
@login_required
def toggle_tarifa_plena(request):
	"""Vista para activar/desactivar la tarifa plena"""
	if request.method != 'POST':
		return JsonResponse({'success': False, 'mensaje': 'Método no permitido'})
	
	# Verificar permisos
	try:
		perfil = get_user_profile(request.user)
		if not perfil.puede_editar_costos():
			return JsonResponse({
				'success': False, 
				'mensaje': 'No tiene permisos para cambiar la tarifa plena'
			})
	except:
		return JsonResponse({
			'success': False, 
			'mensaje': 'No tiene un perfil asignado'
		})
	
	# Detectar petición AJAX
	is_ajax = (
		request.headers.get('X-Requested-With') == 'XMLHttpRequest' or
		request.content_type == 'application/json'
	)
	
	if not is_ajax:
		return JsonResponse({'success': False, 'mensaje': 'Solo se permiten peticiones AJAX'})
	
	try:
		import json
		data = json.loads(request.body)
		activar = data.get('activar', False)
		
		# Obtener o crear la configuración de tarifa plena
		tarifa_plena = TarifaPlena.get_tarifa_actual()
		tarifa_plena.activa = activar
		tarifa_plena.actualizado_por = request.user
		tarifa_plena.save()
		
		mensaje = f"Tarifa plena {'activada' if activar else 'desactivada'} exitosamente"
		
		return JsonResponse({
			'success': True,
			'mensaje': mensaje,
			'activa': tarifa_plena.activa,
			'costo_fijo_auto': float(tarifa_plena.costo_fijo_auto),
			'costo_fijo_moto': float(tarifa_plena.costo_fijo_moto)
		})
		
	except json.JSONDecodeError:
		return JsonResponse({'success': False, 'mensaje': 'Datos JSON inválidos'})
	except Exception as e:
		return JsonResponse({'success': False, 'mensaje': f'Error: {str(e)}'})

	return render(request, 'app_page/portal_opciones.html', {
		'conteo_hoy': conteo_hoy,
		'ultimos': ultimos
	})

# --- VISTAS PARA GESTIÓN DE VISITANTES ---

@login_required
@require_view_list_permission
def ver_visitante(request, pk):
	"""Vista para ver detalles de un visitante"""
	visitante = get_object_or_404(Visitante, pk=pk)
	
	if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
		# Respuesta AJAX para modal
		return JsonResponse({
			'success': True,
			'visitante': {
				'id': visitante.id,
				'cedula': visitante.get_display_cedula(),
				'nombre': visitante.get_display_name(),
				'telefono': visitante.get_display_telefono(),
				'torre': visitante.get_display_torre(),
				'apartamento': visitante.get_display_apartamento(),
				'ubicacion_completa': visitante.get_ubicacion_completa(),
				'fecha_registro': visitante.fecha_registro.strftime('%d/%m/%Y %H:%M'),
				'fecha_actualizacion': visitante.fecha_actualizacion.strftime('%d/%m/%Y %H:%M'),
			}
		})
	
	return render(request, 'app_page/ver_visitante.html', {
		'visitante': visitante
	})

@login_required
@require_edit_permission
def editar_visitante(request, pk):
	"""Vista para editar un visitante"""
	visitante = get_object_or_404(Visitante, pk=pk)
	
	if request.method == 'POST':
		if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
			try:
				import json
				data = json.loads(request.body)
				
				# Validar campos requeridos
				if not data.get('nombre') or not data.get('cedula'):
					return JsonResponse({
						'success': False,
						'mensaje': 'Nombre y cédula son campos obligatorios'
					})
				
				# Actualizar visitante
				visitante.nombre = data.get('nombre').strip()
				visitante.cedula = data.get('cedula').strip().upper()
				visitante.telefono = data.get('telefono', '').strip()
				visitante.torre = data.get('torre', '').strip()
				visitante.apartamento = data.get('apartamento', '').strip()
				visitante.save()
				
				return JsonResponse({
					'success': True,
					'mensaje': f'Visitante {visitante.get_display_name()} actualizado exitosamente'
				})
				
			except json.JSONDecodeError:
				return JsonResponse({
					'success': False,
					'mensaje': 'Datos JSON inválidos'
				})
			except Exception as e:
				return JsonResponse({
					'success': False,
					'mensaje': f'Error al actualizar: {str(e)}'
				})
	
	# GET request o respuesta no AJAX
	if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
		return JsonResponse({
			'success': True,
			'visitante': {
				'id': visitante.id,
				'cedula': visitante.cedula,
				'nombre': visitante.nombre,
				'telefono': visitante.telefono,
				'torre': visitante.torre,
				'apartamento': visitante.apartamento,
			}
		})
	
	return render(request, 'app_page/editar_visitante.html', {
		'visitante': visitante
	})

@login_required
@require_delete_permission
def eliminar_visitante(request, pk):
	"""Vista para eliminar un visitante"""
	visitante = get_object_or_404(Visitante, pk=pk)
	
	if request.method == 'POST':
		if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
			try:
				nombre_visitante = visitante.get_display_name()
				visitante.delete()
				
				return JsonResponse({
					'success': True,
					'mensaje': f'Visitante {nombre_visitante} eliminado exitosamente'
				})
				
			except Exception as e:
				return JsonResponse({
					'success': False,
					'mensaje': f'Error al eliminar: {str(e)}'
				})
	
	return JsonResponse({
		'success': False,
		'mensaje': 'Método no permitido'
	})


# --- VISTAS DE RECAUDACIÓN ---

@login_required
def resumen_recaudacion(request):
	"""Vista para obtener el resumen de recaudación actual"""
	try:
		# Obtener datos de recaudación actual
		datos_recaudacion = Recaudacion.calcular_recaudacion_actual()
		
		# Obtener historial de cortes recientes (últimos 10)
		historial_cortes = Recaudacion.objects.all()[:10]
		
		# Debug logging
		logger.info(f"Número de cortes encontrados: {historial_cortes.count()}")
		
		response_data = {
			'success': True,
			'resumen': {
				'monto_total': float(datos_recaudacion['monto_total']),
				'monto_formateado': f"${datos_recaudacion['monto_total']:,.2f}",
				'numero_clientes': datos_recaudacion['numero_clientes'],
				'fecha_inicio': datos_recaudacion['fecha_inicio'].strftime('%d/%m/%Y %H:%M'),
				'fecha_actual': datos_recaudacion['fecha_actual'].strftime('%d/%m/%Y %H:%M'),
			},
			'historial': []
		}
		
		# Agregar historial de cortes
		for corte in historial_cortes:
			try:
				clientes_atendidos = corte.get_clientes_atendidos()
				logger.info(f"Corte {corte.id}: {len(clientes_atendidos)} clientes")
				response_data['historial'].append({
					'id': corte.id,
					'monto': float(corte.monto_recaudado),
					'monto_formateado': f"${corte.monto_recaudado:,.2f}",
					'fecha_corte': corte.fecha_corte.strftime('%d/%m/%Y %H:%M'),
					'numero_clientes': corte.numero_clientes,
					'usuario': corte.usuario.get_full_name() or corte.usuario.username,
					'periodo': f"{corte.fecha_inicio.strftime('%d/%m/%Y %H:%M')} - {corte.fecha_fin.strftime('%d/%m/%Y %H:%M')}",
					'clientes_atendidos': clientes_atendidos
				})
			except Exception as e:
				logger.error(f"Error procesando corte {corte.id}: {str(e)}")
		
		logger.info(f"Respuesta final: {len(response_data['historial'])} cortes en historial")
		return JsonResponse(response_data)
		
	except Exception as e:
		logger.error(f"Error en resumen_recaudacion: {str(e)}")
		return JsonResponse({
			'success': False,
			'mensaje': 'Error al obtener el resumen de recaudación.'
		})


@login_required
def realizar_corte_recaudacion(request):
	"""Vista para realizar el corte de recaudación"""
	if request.method != 'POST':
		return JsonResponse({
			'success': False,
			'mensaje': 'Método no permitido'
		})
	
	try:
		# Verificar permisos (solo administradores)
		perfil = get_user_profile(request.user)
		if not perfil.es_administrador():
			return JsonResponse({
				'success': False,
				'mensaje': 'No tienes permisos para realizar cortes de recaudación.'
			})
		
		# Obtener datos de recaudación actual
		datos_recaudacion = Recaudacion.calcular_recaudacion_actual()
		
		# Verificar que hay algo que cortar
		if datos_recaudacion['monto_total'] <= 0:
			return JsonResponse({
				'success': False,
				'mensaje': 'No hay recaudación para realizar el corte.'
			})
		
		# Obtener observaciones del formulario
		observaciones = request.POST.get('observaciones', '').strip()
		
		# Crear el registro de corte
		corte = Recaudacion.objects.create(
			usuario=request.user,
			monto_recaudado=datos_recaudacion['monto_total'],
			fecha_inicio=datos_recaudacion['fecha_inicio'],
			fecha_fin=datos_recaudacion['fecha_actual'],
			numero_clientes=datos_recaudacion['numero_clientes'],
			observaciones=observaciones
		)
		
		return JsonResponse({
			'success': True,
			'mensaje': f'Corte de recaudación realizado exitosamente. Total: ${datos_recaudacion["monto_total"]:,.2f}',
			'corte': {
				'id': corte.id,
				'monto': float(corte.monto_recaudado),
				'monto_formateado': f"${corte.monto_recaudado:,.2f}",
				'numero_clientes': corte.numero_clientes,
				'fecha_corte': corte.fecha_corte.strftime('%d/%m/%Y %H:%M'),
				'usuario': corte.usuario.get_full_name() or corte.usuario.username
			}
		})
		
	except Exception as e:
		logger.error(f"Error en realizar_corte_recaudacion: {str(e)}")
		return JsonResponse({
			'success': False,
			'mensaje': 'Error al realizar el corte de recaudación.'
		})
