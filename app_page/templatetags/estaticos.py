"""Etiqueta {% static_v %}: static() con huella de version.

El servidor de desarrollo sirve los estaticos sin Cache-Control ni ETag, solo
con Last-Modified. Con eso el navegador aplica cache heuristica y puede no
revalidar durante horas, asi que un cambio en un .js o .css no se ve aunque el
servidor ya entregue la version nueva.

Anadir la fecha de modificacion a la URL hace que cada cambio estrene direccion
y el navegador lo pida de nuevo, sin recargas forzadas.
"""

import os

from django import template
from django.contrib.staticfiles import finders
from django.templatetags.static import static

register = template.Library()


@register.simple_tag
def static_v(ruta):
	"""Devuelve la URL del estatico con ?v=<fecha de modificacion>."""
	url = static(ruta)
	absoluta = finders.find(ruta)
	if not absoluta:
		# En produccion con collectstatic el finder puede no resolver; la URL
		# sin huella sigue siendo valida.
		return url
	try:
		marca = int(os.path.getmtime(absoluta))
	except OSError:
		return url
	separador = '&' if '?' in url else '?'
	return f'{url}{separador}v={marca}'
