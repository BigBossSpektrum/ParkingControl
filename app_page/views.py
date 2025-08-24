from django.conf import settings
import os
# --- VISTA PARA VER REGISTRO Y QR ---
from django.utils import timezone


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
	return render(request, 'app_page/ver_registro.html', {'cliente': cliente})

# --- FORMULARIOS ---
class ClienteForm(forms.ModelForm):

	matricula_inicio = forms.CharField(label='Matrícula (3 letras)', max_length=3, min_length=3)
	matricula_fin = forms.CharField(label='Matrícula (3 finales)', max_length=3, min_length=3)

	class Meta:
		model = Cliente
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
				return redirect('portal_opciones')
			else:
				form.add_error(None, 'Usuario o contraseña incorrectos')
	else:
		form = LoginForm()
	return render(request, 'app_page/login.html', {'form': form})

def logout_view(request):
	auth_logout(request)
	return redirect('login')

@login_required
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
def index(request):
	from django.utils import timezone
	if request.method == 'POST':
		print('POST recibido:', request.POST)
		form = ClienteForm(request.POST)
		if form.is_valid():
			print('Form válido. Cedula:', form.cleaned_data.get('cedula'))
			cliente = form.save(commit=False)
			cliente.fecha_entrada = timezone.now()
			# Guardar primero para obtener el id
			cliente.save()
			try:
				import qrcode
				from django.core.files.base import ContentFile
				qr_data = f"ID: {cliente.id}\nCédula: {cliente.cedula}\nNombre: {cliente.nombre}\nMatrícula: {cliente.matricula}\nFecha Entrada: {cliente.fecha_entrada.strftime('%Y-%m-%d %H:%M')}"
				qr_img = qrcode.make(qr_data)
				buf = BytesIO()
				qr_img.save(buf, format='PNG')
				buf.seek(0)
				cliente.qr_image.save(f"qr_{cliente.id}_{cliente.fecha_entrada.strftime('%Y%m%d%H%M%S')}.png", ContentFile(buf.read()), save=False)
				print('QR generado y guardado:', cliente.qr_image.name)
			except Exception as e:
				print('Error generando QR:', e)
			# Generar código de barras con el id
			try:
				import barcode
				from barcode.writer import ImageWriter
				barcode_class = barcode.get_barcode_class('code128')
				barcode_data = str(cliente.id)
				barcode_img = barcode_class(barcode_data, writer=ImageWriter())
				barcode_buf = BytesIO()
				barcode_img.write(barcode_buf)
				barcode_buf.seek(0)
				cliente.barcode_image.save(f"barcode_{cliente.id}_{cliente.fecha_entrada.strftime('%Y%m%d%H%M%S')}.png", ContentFile(barcode_buf.read()), save=False)
				print('Barcode generado y guardado:', cliente.barcode_image.name)
			except Exception as e:
				print('Error generando barcode:', e)
			cliente.save()
			return redirect('lista_clientes')
		else:
			print('Form inválido. Errores:', form.errors)
	else:
		form = ClienteForm(initial={'cedula': ''})
	return render(request, 'app_page/registar_usuario.html', {'form': form})

@login_required
def editar_cliente(request, pk):
	cliente = get_object_or_404(Cliente, pk=pk)
	if request.method == 'POST':
		form = ClienteForm(request.POST, instance=cliente)
		if form.is_valid():
			form.save()
			return redirect('lista_clientes')
	else:
		form = ClienteForm(instance=cliente)
	return render(request, 'app_page/registar_usuario.html', {'form': form, 'editar': True, 'cliente': cliente})

@login_required
def eliminar_cliente(request, pk):
	cliente = get_object_or_404(Cliente, pk=pk)
	if request.method == 'POST':
		cliente.delete()
		return redirect('lista_clientes')
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
		)
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
def salida_qr(request):
	mensaje = ''
	if request.method == 'POST':
		form = SalidaQRForm(request.POST)
		if form.is_valid():
			codigo = form.cleaned_data['codigo']
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
				mensaje = f'Salida registrada para {cliente.nombre}.'
			else:
				mensaje = 'Cliente no encontrado.'
	else:
		form = SalidaQRForm()
	return render(request, 'app_page/salida_qr.html', {'form': form, 'mensaje': mensaje})
