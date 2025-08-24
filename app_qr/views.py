from django.http import HttpResponse

def test_barcode(request):
	return HttpResponse('Prueba de lector de código de barras OK')
from django.shortcuts import render

# Create your views here.
