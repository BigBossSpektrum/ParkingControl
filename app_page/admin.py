from django.contrib import admin
from .models import Cliente

@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
	list_display = ('cedula', 'nombre', 'telefono', 'matricula', 'tipo_vehiculo', 'tiempo_parking', 'fecha_entrada', 'fecha_salida')
	search_fields = ('cedula', 'nombre', 'matricula', 'telefono')
	list_filter = ('tipo_vehiculo',)
