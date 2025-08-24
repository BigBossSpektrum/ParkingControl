from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login as auth_login
from django import forms

class LoginForm(forms.Form):
	username = forms.CharField(label='Usuario')
	password = forms.CharField(widget=forms.PasswordInput, label='Contraseña')

def login_view(request):
	# Si el usuario ya está autenticado, redirigir al dashboard
	if request.user.is_authenticated:
		return redirect('dashboard')
		
	if request.method == 'POST':
		form = LoginForm(request.POST)
		if form.is_valid():
			user = authenticate(request, username=form.cleaned_data['username'], password=form.cleaned_data['password'])
			if user is not None:
				auth_login(request, user)
				# Verificar si hay un 'next' parameter para redirección
				next_url = request.GET.get('next')
				if next_url:
					return redirect(next_url)
				return redirect('dashboard')
			else:
				form.add_error(None, 'Usuario o contraseña incorrectos')
	else:
		form = LoginForm()
	return render(request, 'app_registration/login.html', {'form': form})
from django.shortcuts import render

# Create your views here.
