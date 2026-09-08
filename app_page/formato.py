"""Formato de fechas para las respuestas JSON y los textos de la app.

Con USE_TZ=True Django guarda todo en UTC. Las plantillas convierten solas con
el filtro |date, pero strftime() en Python no: aplicado al valor crudo imprime
la hora UTC, cinco horas por delante de America/Bogota. Por eso todo texto de
fecha que se arme en Python tiene que pasar por aqui.
"""

from django.utils import timezone

FORMATO_FECHA_HORA = '%d/%m/%Y %H:%M'


def fecha_local(valor, por_defecto=None, formato=FORMATO_FECHA_HORA):
	"""Formatea un datetime en la zona horaria local del proyecto.

	Devuelve por_defecto si el valor es None, para los muchos campos opcionales
	(fecha_salida, fecha_entrada) que se muestran como 'No registrada'.
	"""
	if not valor:
		return por_defecto
	return timezone.localtime(valor).strftime(formato)
