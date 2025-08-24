
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

# --- FORMULARIOS ---
class ClienteForm(forms.ModelForm):
	class Meta:
		model = Cliente
		fields = ['cedula', 'nombre', 'telefono', 'matricula', 'fecha_entrada', 'fecha_salida']
		widgets = {
			'fecha_entrada': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
			'fecha_salida': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
		}

class LoginForm(forms.Form):
	username = forms.CharField(label='Usuario')
	password = forms.CharField(widget=forms.PasswordInput, label='Contraseña')

class SalidaQRForm(forms.Form):
	cedula = forms.CharField(label='Escanee el código QR o ingrese la cédula')

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
	return render(request, 'app_page/portal_opciones.html')

@login_required
def index(request):
	if request.method == 'POST':
		form = ClienteForm(request.POST)
		if form.is_valid():
			cliente = form.save()
			return redirect('lista_clientes')
	else:
		form = ClienteForm()
	return render(request, 'app_page/index.html', {'form': form})

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
	return render(request, 'app_page/index.html', {'form': form, 'editar': True, 'cliente': cliente})

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
	return render(request, 'app_page/lista_clientes.html', {'page_obj': page_obj, 'query': query})

@login_required
def salida_qr(request):
	mensaje = ''
	if request.method == 'POST':
		form = SalidaQRForm(request.POST)
		if form.is_valid():
			cedula = form.cleaned_data['cedula']
			try:
				cliente = Cliente.objects.get(cedula=cedula)
				from django.utils import timezone
				cliente.fecha_salida = timezone.now()
				cliente.save()
				mensaje = f'Salida registrada para {cliente.nombre}.'
			except Cliente.DoesNotExist:
				mensaje = 'Cliente no encontrado.'
	else:
		form = SalidaQRForm()
	return render(request, 'app_page/salida_qr.html', {'form': form, 'mensaje': mensaje})
