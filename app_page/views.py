<<<<<<< HEAD
import os
from io import BytesIO
import barcode
from barcode.writer import ImageWriter
import qrcode
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

# --- DASHBOARD: Panel principal con ambos formularios ---
@login_required
@csrf_protect
def dashboard(request):
	mensaje_salida = ''
	message_success = ''
	salida_form = SalidaQRForm()
	registro_form = ClienteForm()
	
	if request.method == 'POST':
		# Detectar petición AJAX
		is_ajax = (
			request.headers.get('X-Requested-With') == 'XMLHttpRequest' or
			request.content_type == 'application/json' or
			request.GET.get('ajax') == '1' or
			request.POST.get('ajax') == '1' or
			'application/json' in request.headers.get('Accept', '')
		)
		
		if 'codigo' in request.POST:
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
					
					mensaje_salida = f'Salida registrada para {cliente.nombre}.'
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
			registro_form = ClienteForm(request.POST)
			if registro_form.is_valid():
				cliente = registro_form.save(commit=False)
				cliente.fecha_entrada = timezone.now()
				cliente.save()
				# Generar QR con datos adicionales
				cliente.generate_qr_with_data()
				cliente.save()
				message_success = 'Cliente registrado correctamente.'
				registro_form = ClienteForm()  # Limpiar formulario
	
	return render(request, 'app_page/dashboard.html', {
		'salida_form': salida_form,
		'registro_form': registro_form,
		'mensaje_salida': mensaje_salida,
		'message_success': message_success,
	})

# --- VISTA PARA VER REGISTRO Y QR ---
=======
from django.conf import settings
import os
# --- VISTA PARA VER REGISTRO Y QR ---
from django.utils import timezone
>>>>>>> 7395215fdcd9c30411c8dbe2b5120de6ba911bbd


# --- IMPORTS ---
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django import forms
from django.db import models
from .models import Cliente
import barcode
from barcode.writer import ImageWriter
from io import BytesIO
from django.core.files.base import ContentFile

@login_required
def ver_registro(request, pk):
	cliente = get_object_or_404(Cliente, pk=pk)
<<<<<<< HEAD
	
	if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.GET.get('ajax'):
		# Calcular tiempo en parking
		minutos = None
		if cliente.fecha_entrada and cliente.fecha_salida:
			delta = cliente.fecha_salida - cliente.fecha_entrada
			minutos = int(delta.total_seconds() // 60)
		
		return JsonResponse({
			'id': cliente.id,
			'cedula': cliente.cedula,
			'nombre': cliente.nombre,
			'telefono': cliente.telefono,
			'matricula': cliente.matricula,
			'tipo_vehiculo': cliente.get_tipo_vehiculo_display(),
			'fecha_entrada': cliente.fecha_entrada.strftime('%Y-%m-%d %H:%M:%S') if cliente.fecha_entrada else None,
			'fecha_salida': cliente.fecha_salida.strftime('%Y-%m-%d %H:%M:%S') if cliente.fecha_salida else None,
			'tiempo_parking': f"{minutos} minutos" if minutos is not None else "En parking",
			'qr_image_url': cliente.qr_image.url if cliente.qr_image else None,
		})
	
=======
>>>>>>> 7395215fdcd9c30411c8dbe2b5120de6ba911bbd
	return render(request, 'app_page/ver_registro.html', {'cliente': cliente})

# --- FORMULARIOS ---
class ClienteForm(forms.ModelForm):

	matricula_inicio = forms.CharField(label='Matrícula (3 letras)', max_length=3, min_length=3)
	matricula_fin = forms.CharField(label='Matrícula (3 finales)', max_length=3, min_length=3)

	class Meta:
		model = Cliente
<<<<<<< HEAD
		fields = ['cedula', 'nombre', 'telefono', 'tipo_vehiculo', 'tiempo_parking']

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		# Si hay instancia, dividir la matrícula
		if self.instance and self.instance.matricula:
			partes = self.instance.matricula.split('-')
			if len(partes) == 2:
				self.fields['matricula_inicio'].initial = partes[0]
				self.fields['matricula_fin'].initial = partes[1]

	def clean(self):
		cleaned = super().clean()
		ini = cleaned.get('matricula_inicio', '').upper()
		fin = cleaned.get('matricula_fin', '').upper()
		import re
		if not re.match(r'^[A-Z]{3}$', ini):
			self.add_error('matricula_inicio', 'Debe ser 3 letras mayúsculas')
		if not re.match(r'^[0-9A-Z]{3}$', fin):
			self.add_error('matricula_fin', 'Debe ser 3 caracteres alfanuméricos')
		if not self.errors:
			cleaned['matricula'] = f"{ini}-{fin}"
		return cleaned

	def save(self, commit=True):
		self.instance.matricula = self.cleaned_data.get('matricula', '')
		return super().save(commit)

	def clean_matricula(self):
		matricula = self.cleaned_data['matricula'].upper()
		import re
		if len(matricula) != 7:
			raise forms.ValidationError('La matrícula debe tener exactamente 7 caracteres (ej: JAW-12P)')
		if '-' not in matricula:
			raise forms.ValidationError('La matrícula debe contener un guion (ej: JAW-12P)')
		if not re.match(r'^[A-Z]{3}-[0-9A-Z]{3}$', matricula):
			raise forms.ValidationError('Formato inválido. Ejemplo válido: JAW-12P')
		return matricula
=======
		fields = ['cedula', 'nombre', 'telefono', 'matricula', 'tipo_vehiculo', 'tiempo_parking']
>>>>>>> 7395215fdcd9c30411c8dbe2b5120de6ba911bbd

class LoginForm(forms.Form):
	username = forms.CharField(label='Usuario')
	password = forms.CharField(widget=forms.PasswordInput, label='Contraseña')

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
				form.add_error(None, 'Usuario o contraseña incorrectos')
	else:
		form = LoginForm()
	return render(request, 'app_registration/login.html', {'form': form})

def logout_view(request):
	auth_logout(request)
	return redirect('login')

@login_required
<<<<<<< HEAD
=======
def portal_opciones(request):
	from django.utils import timezone
	hoy = timezone.now().date()
	clientes_hoy = Cliente.objects.filter(fecha_entrada__date=hoy)
	conteo_hoy = clientes_hoy.count()
	ultimos = Cliente.objects.order_by('-fecha_entrada')[:5]
	return render(request, 'app_page/portal_opciones.html', {
	    'conteo_hoy': conteo_hoy,
	    'ultimos': ultimos,
	})

@login_required
>>>>>>> 7395215fdcd9c30411c8dbe2b5120de6ba911bbd
def index(request):
	from django.utils import timezone
	if request.method == 'POST':
		print('POST recibido:', request.POST)
		form = ClienteForm(request.POST)
		if form.is_valid():
<<<<<<< HEAD
			cliente = form.save(commit=False)
			cliente.fecha_entrada = timezone.now()
			# Guardar primero para obtener el id
			cliente.save()
			# Generar QR con datos adicionales
			cliente.generate_qr_with_data()
=======
			print('Form válido. Cedula:', form.cleaned_data.get('cedula'))
			cliente = form.save(commit=False)
			cliente.fecha_entrada = timezone.now()
			# Generar QR
			import qrcode
			from django.core.files.base import ContentFile
			qr_data = f"Cédula: {cliente.cedula}\nNombre: {cliente.nombre}\nMatrícula: {cliente.matricula}\nFecha Entrada: {cliente.fecha_entrada.strftime('%Y-%m-%d %H:%M')}"
			qr_img = qrcode.make(qr_data)
			buf = BytesIO()
			qr_img.save(buf, format='PNG')
			buf.seek(0)
			cliente.qr_image.save(f"qr_{cliente.cedula}_{cliente.fecha_entrada.strftime('%Y%m%d%H%M%S')}.png", ContentFile(buf.read()), save=False)
>>>>>>> 7395215fdcd9c30411c8dbe2b5120de6ba911bbd
			cliente.save()
			return redirect('lista_clientes')
		else:
			print('Form inválido. Errores:', form.errors)
	else:
		form = ClienteForm(initial={'cedula': ''})
<<<<<<< HEAD
	return render(request, 'app_page/registar_usuario.html', {'form': form})
=======
	return render(request, 'app_page/index.html', {'form': form})
>>>>>>> 7395215fdcd9c30411c8dbe2b5120de6ba911bbd

@login_required
def editar_cliente(request, pk):
	cliente = get_object_or_404(Cliente, pk=pk)
	if request.method == 'POST':
		form = ClienteForm(request.POST, instance=cliente)
		if form.is_valid():
			form.save()
			if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
				return JsonResponse({'success': True, 'message': 'Cliente actualizado correctamente'})
			return redirect('lista_clientes')
		else:
			if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
				return JsonResponse({'success': False, 'errors': form.errors})
	else:
		form = ClienteForm(instance=cliente)
	
	if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.GET.get('ajax'):
		# Devolver datos del cliente para el modal
		return JsonResponse({
			'id': cliente.id,
			'cedula': cliente.cedula,
			'nombre': cliente.nombre,
			'telefono': cliente.telefono,
			'tipo_vehiculo': cliente.tipo_vehiculo,
			'matricula_inicio': cliente.matricula.split('-')[0] if '-' in cliente.matricula else '',
			'matricula_fin': cliente.matricula.split('-')[1] if '-' in cliente.matricula else '',
		})
	return render(request, 'app_page/registar_usuario.html', {'form': form, 'editar': True, 'cliente': cliente})

@login_required
def eliminar_cliente(request, pk):
	cliente = get_object_or_404(Cliente, pk=pk)
	if request.method == 'POST':
		cliente.delete()
		if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
			return JsonResponse({'success': True, 'message': 'Cliente eliminado correctamente'})
		return redirect('lista_clientes')
	
	if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.GET.get('ajax'):
		return JsonResponse({
			'id': cliente.id,
			'nombre': cliente.nombre,
			'cedula': cliente.cedula
		})
	return render(request, 'app_page/confirmar_eliminar.html', {'cliente': cliente})

@login_required
def lista_clientes(request):
	query = request.GET.get('q', '')
	clientes = Cliente.objects.all()
	if query:
		clientes = clientes.filter(
			models.Q(cedula__icontains=query) |
			models.Q(nombre__icontains=query) |
			models.Q(telefono__icontains=query) |
			models.Q(matricula__icontains=query)
		).order_by('-fecha_entrada')  # Ordenar por fecha de entrada descendente
	else:
		clientes = Cliente.objects.all().order_by('-fecha_entrada')  # Ordenar por fecha de entrada descendente
	
	paginator = Paginator(clientes, 10)  # 10 clientes por página
	page_number = request.GET.get('page')
	page_obj = paginator.get_page(page_number)
	# Calcular minutos en parking para cada cliente
	clientes_con_tiempo = []
	for cliente in page_obj:
		minutos = None
		if cliente.fecha_entrada and cliente.fecha_salida:
			delta = cliente.fecha_salida - cliente.fecha_entrada
			minutos = int(delta.total_seconds() // 60)
		clientes_con_tiempo.append((cliente, minutos))
	return render(request, 'app_page/lista_clientes.html', {
	    'page_obj': page_obj,
	    'query': query,
	    'clientes_con_tiempo': clientes_con_tiempo,
	})

@login_required
@login_required
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
