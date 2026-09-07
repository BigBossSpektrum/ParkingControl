"""Decodificación de fotografías capturadas por cámara (data URL base64).

El widget de cámara del navegador entrega la foto como una data URL
("data:image/jpeg;base64,...") en un campo oculto del formulario, no como un
archivo subido. Este módulo la convierte en algo que un ImageField pueda guardar.
"""

import base64
import binascii
import re
from io import BytesIO

from django.core.files.base import ContentFile
from django.utils import timezone
from PIL import Image

# Tamaño máximo del payload base64. El widget captura a 640x480 con calidad 0.8
# (~80 KB en base64), así que este límite sólo ataja envíos anómalos.
MAX_FOTO_BYTES = 2 * 1024 * 1024

_DATA_URL_RE = re.compile(r'^data:image/(jpeg|jpg|png);base64,', re.IGNORECASE)

_EXTENSIONES = {
	'jpeg': 'jpg',
	'jpg': 'jpg',
	'png': 'png',
}


def decodificar_foto_base64(data_url, prefijo='foto'):
	"""Convierte una data URL de imagen en (nombre_archivo, ContentFile).

	Devuelve None si data_url está vacía: la fotografía es opcional.
	Lanza ValueError si el contenido no es una imagen válida o excede el tamaño
	máximo, para que quien llama pueda descartarla sin abortar el registro.
	"""
	if not data_url or not data_url.strip():
		return None

	data_url = data_url.strip()

	coincidencia = _DATA_URL_RE.match(data_url)
	if not coincidencia:
		raise ValueError('El formato de la fotografía no es válido (se espera JPEG o PNG en base64).')

	payload = data_url[coincidencia.end():]
	if len(payload) > MAX_FOTO_BYTES:
		raise ValueError('La fotografía excede el tamaño máximo permitido.')

	try:
		datos = base64.b64decode(payload, validate=True)
	except (binascii.Error, ValueError):
		raise ValueError('La fotografía no se pudo decodificar.')

	if not datos:
		raise ValueError('La fotografía está vacía.')

	# verify() confirma que el contenido es realmente una imagen antes de
	# guardarlo en el ImageField.
	try:
		Image.open(BytesIO(datos)).verify()
	except Exception:
		raise ValueError('La fotografía no es una imagen válida.')

	extension = _EXTENSIONES[coincidencia.group(1).lower()]
	nombre = f"{prefijo}_{timezone.now().strftime('%Y%m%d%H%M%S%f')}.{extension}"

	return nombre, ContentFile(datos)
