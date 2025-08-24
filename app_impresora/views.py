from django.http import HttpResponse

def test_printer(request):
	return HttpResponse('Prueba de impresora térmica OK')
from django.shortcuts import render

# Create your views here.
