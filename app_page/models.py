from django.db import models
from django.utils import timezone
from PIL import Image, ImageDraw, ImageFont
import qrcode
from io import BytesIO
from django.core.files.base import ContentFile

class Cliente(models.Model):
	TIPO_VEHICULO_CHOICES = [
		('carro', 'Carro'),
		('moto', 'Moto'),
		('otro', 'Otro'),
	]
	cedula = models.CharField(max_length=20)
	nombre = models.CharField(max_length=100)
	telefono = models.CharField(max_length=20)
	matricula = models.CharField(max_length=20)
	tipo_vehiculo = models.CharField(max_length=10, choices=TIPO_VEHICULO_CHOICES, default='carro')
	tiempo_parking = models.PositiveIntegerField(null=True, blank=True, help_text='Tiempo en minutos')
	fecha_entrada = models.DateTimeField(null=True, blank=True)
	fecha_salida = models.DateTimeField(null=True, blank=True)
	qr_image = models.ImageField(upload_to='qr_codes/', null=True, blank=True)

	def generate_qr_with_data(self):
		"""Genera un QR con datos adicionales integrados en la imagen"""
		if not self.fecha_entrada:
			return False
			
		try:
			# Crear QR con el ID del cliente
			qr_data = str(self.id)
			qr_img = qrcode.QRCode(
				version=1,
				error_correction=qrcode.constants.ERROR_CORRECT_L,
				box_size=10,
				border=4,
			)
			qr_img.add_data(qr_data)
			qr_img.make(fit=True)
			
			# Crear imagen del QR
			qr_image = qr_img.make_image(fill_color="black", back_color="white")
			# Convertir a RGB si no está en RGB
			if qr_image.mode != 'RGB':
				qr_image = qr_image.convert('RGB')
			
			# Crear imagen más grande para agregar datos
			width, height = qr_image.size
			new_height = height + 120  # Espacio para texto
			new_width = max(width, 400)  # Ancho mínimo
			
			# Crear imagen final
			final_img = Image.new('RGB', (new_width, new_height), 'white')
			
			# Centrar QR en la imagen
			qr_x = (new_width - width) // 2
			final_img.paste(qr_image, (qr_x, 0))
			
			# Agregar texto con información
			draw = ImageDraw.Draw(final_img)
			
			try:
				# Intentar cargar fuente
				font_large = ImageFont.truetype("arial.ttf", 16)
				font_small = ImageFont.truetype("arial.ttf", 12)
			except:
				# Fuente por defecto si no encuentra arial
				font_large = ImageFont.load_default()
				font_small = ImageFont.load_default()
			
			# Datos a mostrar
			fecha_str = self.fecha_entrada.strftime('%d/%m/%Y %H:%M')
			matricula_str = f"Matrícula: {self.matricula}"
			hora_str = f"Entrada: {fecha_str}"
			id_str = f"ID: {self.id}"
			
			# Posiciones del texto
			text_y = height + 10
			
			# Centrar texto (compatible con versiones anteriores de Pillow)
			# Calcular ancho del texto para centrarlo manualmente
			id_bbox = draw.textbbox((0, 0), id_str, font=font_large)
			id_width = id_bbox[2] - id_bbox[0]
			draw.text(((new_width - id_width) // 2, text_y), id_str, fill='black', font=font_large)
			
			matricula_bbox = draw.textbbox((0, 0), matricula_str, font=font_small)
			matricula_width = matricula_bbox[2] - matricula_bbox[0]
			draw.text(((new_width - matricula_width) // 2, text_y + 25), matricula_str, fill='black', font=font_small)
			
			hora_bbox = draw.textbbox((0, 0), hora_str, font=font_small)
			hora_width = hora_bbox[2] - hora_bbox[0]
			draw.text(((new_width - hora_width) // 2, text_y + 45), hora_str, fill='black', font=font_small)
			
			tipo_text = f"Tipo: {self.get_tipo_vehiculo_display()}"
			tipo_bbox = draw.textbbox((0, 0), tipo_text, font=font_small)
			tipo_width = tipo_bbox[2] - tipo_bbox[0]
			draw.text(((new_width - tipo_width) // 2, text_y + 65), tipo_text, fill='black', font=font_small)
			
			# Guardar imagen
			buf = BytesIO()
			final_img.save(buf, format='PNG')
			buf.seek(0)
			
			filename = f"qr_data_{self.id}_{self.fecha_entrada.strftime('%Y%m%d%H%M%S')}.png"
			self.qr_image.save(filename, ContentFile(buf.read()), save=False)
			
			return True
			
		except Exception as e:
			print(f"Error generando QR con datos para cliente {self.id}: {e}")
			return False

	def __str__(self):
		return f"{self.nombre} ({self.cedula})"
