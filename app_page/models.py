from django.db import models

class Cliente(models.Model):
	TIPO_VEHICULO_CHOICES = [
		('carro', 'Carro'),
		('moto', 'Moto'),
		('otro', 'Otro'),
	]
	cedula = models.CharField(max_length=20, unique=True)
	nombre = models.CharField(max_length=100)
	telefono = models.CharField(max_length=20)
	matricula = models.CharField(max_length=20)
	tipo_vehiculo = models.CharField(max_length=10, choices=TIPO_VEHICULO_CHOICES, default='carro')
	tiempo_parking = models.PositiveIntegerField(null=True, blank=True, help_text='Tiempo en minutos')
	fecha_entrada = models.DateTimeField(null=True, blank=True)
	fecha_salida = models.DateTimeField(null=True, blank=True)

	def __str__(self):
		return f"{self.nombre} ({self.cedula})"
from django.db import models

# Create your models here.
