from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from PIL import Image, ImageDraw, ImageFont
import qrcode
from io import BytesIO
from django.core.files.base import ContentFile

class Cliente(models.Model):
	TIPO_VEHICULO_CHOICES = [
		('Auto', 'Auto'),
		('Moto', 'Moto'),
		('Otro', 'Otro'),
	]
	cedula = models.CharField(max_length=20, blank=True, null=True)
	nombre = models.CharField(max_length=100, blank=True, null=True)
	telefono = models.CharField(max_length=20, blank=True, null=True)
	torre = models.CharField(max_length=10, blank=True, null=True, help_text='Torre del apartamento')
	apartamento = models.CharField(max_length=10, blank=True, null=True, help_text='Número de apartamento')
	matricula = models.CharField(max_length=20)
	tipo_vehiculo = models.CharField(max_length=10, choices=TIPO_VEHICULO_CHOICES, default='Auto')
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
			extra_height = 140 if ubicacion_str else 120  # Espacio extra si hay ubicación
			new_height = height + extra_height
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
			
			# Información de torre y apartamento
			ubicacion_str = ""
			if self.torre or self.apartamento:
				torre = self.torre or ""
				apartamento = self.apartamento or ""
				if torre and apartamento:
					ubicacion_str = f"Torre {torre} - Apt {apartamento}"
				elif torre:
					ubicacion_str = f"Torre {torre}"
				elif apartamento:
					ubicacion_str = f"Apartamento {apartamento}"
			
			# Posiciones del texto
			text_y = height + 10
			line_height = 20
			
			# Centrar texto (compatible con versiones anteriores de Pillow)
			# Calcular ancho del texto para centrarlo manualmente
			current_y = text_y
			
			id_bbox = draw.textbbox((0, 0), id_str, font=font_large)
			id_width = id_bbox[2] - id_bbox[0]
			draw.text(((new_width - id_width) // 2, current_y), id_str, fill='black', font=font_large)
			current_y += line_height
			
			matricula_bbox = draw.textbbox((0, 0), matricula_str, font=font_small)
			matricula_width = matricula_bbox[2] - matricula_bbox[0]
			draw.text(((new_width - matricula_width) // 2, current_y), matricula_str, fill='black', font=font_small)
			current_y += line_height
			
			# Agregar información de ubicación si existe
			if ubicacion_str:
				ubicacion_bbox = draw.textbbox((0, 0), ubicacion_str, font=font_small)
				ubicacion_width = ubicacion_bbox[2] - ubicacion_bbox[0]
				draw.text(((new_width - ubicacion_width) // 2, current_y), ubicacion_str, fill='black', font=font_small)
				current_y += line_height
			
			hora_bbox = draw.textbbox((0, 0), hora_str, font=font_small)
			hora_width = hora_bbox[2] - hora_bbox[0]
			draw.text(((new_width - hora_width) // 2, current_y), hora_str, fill='black', font=font_small)
			current_y += line_height
			
			tipo_text = f"Tipo: {self.get_tipo_vehiculo_display()}"
			tipo_bbox = draw.textbbox((0, 0), tipo_text, font=font_small)
			tipo_width = tipo_bbox[2] - tipo_bbox[0]
			draw.text(((new_width - tipo_width) // 2, current_y), tipo_text, fill='black', font=font_small)
			
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

	def generate_clean_qr(self):
		"""Genera un QR limpio sin información adicional"""
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
			
			# Crear imagen del QR limpia
			qr_image = qr_img.make_image(fill_color="black", back_color="white")
			# Convertir a RGB si no está en RGB
			if qr_image.mode != 'RGB':
				qr_image = qr_image.convert('RGB')
			
			# Guardar imagen directamente sin agregar texto
			buf = BytesIO()
			qr_image.save(buf, format='PNG')
			buf.seek(0)
			
			filename = f"qr_{self.id}_{self.fecha_entrada.strftime('%Y%m%d%H%M%S')}.png"
			self.qr_image.save(filename, ContentFile(buf.read()), save=False)
			
			return True
			
		except Exception as e:
			print(f"Error generando QR limpio para cliente {self.id}: {e}")
			return False

	def get_display_name(self):
		"""Devuelve el nombre del cliente o un valor por defecto"""
		return self.nombre or 'Cliente sin nombre'
	
	def get_display_cedula(self):
		"""Devuelve la cédula del cliente o un valor por defecto"""
		return self.cedula or 'Sin cédula'
	
	def get_display_telefono(self):
		"""Devuelve el teléfono del cliente o un valor por defecto"""
		return self.telefono or 'Sin teléfono'
	
	def get_display_torre(self):
		"""Devuelve la torre del cliente o un valor por defecto"""
		return self.torre or 'Sin torre'
	
	def get_display_apartamento(self):
		"""Devuelve el apartamento del cliente o un valor por defecto"""
		return self.apartamento or 'Sin apartamento'
	
	def tiempo_formateado(self):
		"""Calcula y formatea el tiempo transcurrido en el parking"""
		if not self.fecha_entrada:
			return "Sin entrada"
		
		# Determinar fecha final: salida si existe, sino fecha actual
		fecha_fin = self.fecha_salida if self.fecha_salida else timezone.now()
		
		# Calcular diferencia
		diferencia = fecha_fin - self.fecha_entrada
		
		# Extraer componentes
		total_segundos = int(diferencia.total_seconds())
		horas = total_segundos // 3600
		minutos = (total_segundos % 3600) // 60
		
		# Formatear resultado
		if horas > 0:
			if minutos > 0:
				return f"{horas}h {minutos}m"
			else:
				return f"{horas}h"
		elif minutos > 0:
			return f"{minutos}m"
		else:
			return "< 1m"
	
	def tiempo_en_minutos(self):
		"""Devuelve el tiempo total en minutos para cálculos"""
		if not self.fecha_entrada:
			return 0
		
		fecha_fin = self.fecha_salida if self.fecha_salida else timezone.now()
		diferencia = fecha_fin - self.fecha_entrada
		return int(diferencia.total_seconds() // 60)
	
	def tiempo_detallado(self):
		"""Devuelve información detallada del tiempo para tooltips o reportes"""
		if not self.fecha_entrada:
			return "Sin fecha de entrada"
		
		fecha_fin = self.fecha_salida if self.fecha_salida else timezone.now()
		diferencia = fecha_fin - self.fecha_entrada
		
		total_segundos = int(diferencia.total_seconds())
		dias = total_segundos // 86400
		horas = (total_segundos % 86400) // 3600
		minutos = (total_segundos % 3600) // 60
		
		partes = []
		if dias > 0:
			partes.append(f"{dias} día{'s' if dias != 1 else ''}")
		if horas > 0:
			partes.append(f"{horas} hora{'s' if horas != 1 else ''}")
		if minutos > 0:
			partes.append(f"{minutos} minuto{'s' if minutos != 1 else ''}")
		
		if not partes:
			return "Menos de 1 minuto"
		
		return ", ".join(partes)

	def calcular_costo(self):
		"""Calcula el costo total basado en el tiempo y tipo de vehículo"""
		if not self.fecha_entrada:
			return 0.00
		
		# Verificar si la tarifa plena está activa
		tarifa_plena = TarifaPlena.get_tarifa_actual()
		
		if tarifa_plena.activa:
			# Si la tarifa plena está activa, usar costo fijo
			return float(tarifa_plena.get_costo_por_tipo(self.tipo_vehiculo))
		else:
			# Si no, usar el cálculo por minutos normal
			costos = Costo.get_costos_actuales()
			tiempo_minutos = max(1, self.tiempo_en_minutos())
			costo_por_minuto = costos.get_costo_por_tipo(self.tipo_vehiculo)
			return float(costo_por_minuto) * tiempo_minutos
	
	def costo_formateado(self):
		"""Devuelve el costo formateado como string"""
		costo = self.calcular_costo()
		tarifa_plena = TarifaPlena.get_tarifa_actual()
		
		if tarifa_plena.activa:
			return f"${costo:,.2f} (Tarifa Plena)"
		else:
			return f"${costo:,.2f}"
	
	def es_tarifa_plena(self):
		"""Verifica si este cliente está usando tarifa plena"""
		tarifa_plena = TarifaPlena.get_tarifa_actual()
		return tarifa_plena.activa

	def costo_por_tiempo(self):
		"""Calcula el costo por minuto del tipo de vehículo"""
		if not hasattr(self, '_costo_por_tiempo'):
			costos = Costo.get_costos_actuales()
			self._costo_por_tiempo = costos.get_costo_por_tipo(self.tipo_vehiculo)
		return float(self._costo_por_tiempo)
	
	def calcular_costo_temporal(self, fecha_salida_temporal):
		"""Calcula el costo total basado en una fecha de salida temporal (sin modificar el registro)"""
		if not self.fecha_entrada:
			return 0.00
		
		# Verificar si la tarifa plena está activa
		tarifa_plena = TarifaPlena.get_tarifa_actual()
		
		if tarifa_plena.activa:
			# Si la tarifa plena está activa, usar costo fijo
			return float(tarifa_plena.get_costo_por_tipo(self.tipo_vehiculo))
		else:
			# Si no, usar el cálculo por minutos normal
			costos = Costo.get_costos_actuales()
			# Calcular minutos temporalmente
			delta = fecha_salida_temporal - self.fecha_entrada
			tiempo_minutos = max(1, int(delta.total_seconds() // 60))
			costo_por_minuto = costos.get_costo_por_tipo(self.tipo_vehiculo)
			return float(costo_por_minuto) * tiempo_minutos
	
	def costo_formateado_temporal(self, fecha_salida_temporal):
		"""Devuelve el costo temporal formateado como string"""
		costo = self.calcular_costo_temporal(fecha_salida_temporal)
		tarifa_plena = TarifaPlena.get_tarifa_actual()
		
		if tarifa_plena.activa:
			return f"${costo:,.2f} (Tarifa Plena)"
		else:
			return f"${costo:,.2f}"
	
	def tiempo_por_costo(self):
		"""Calcula la relación tiempo transcurrido dividido por el costo total"""
		costo_total = self.calcular_costo()
		if costo_total == 0:
			return 0
		
		tiempo_minutos = self.tiempo_en_minutos()
		if tiempo_minutos == 0:
			return 0
		
		# Retorna minutos por peso gastado
		return tiempo_minutos / costo_total
	
	def tiempo_por_costo_formateado(self):
		"""Devuelve la relación tiempo/costo formateada"""
		if not self.fecha_entrada:
			return "Sin entrada"
		
		relacion = self.tiempo_por_costo()
		if relacion == 0:
			return "0 min/$"
		
		if relacion >= 1:
			return f"{relacion:.1f} min/$"
		else:
			# Si es menos de 1 minuto por peso, mostrar como centavos por minuto
			costo_por_minuto = 1 / relacion if relacion > 0 else 0
			return f"${costo_por_minuto:.0f}/min"
	
	def tarifa_completa(self):
		"""Devuelve una tarifa completa con costo total y eficiencia"""
		if not self.fecha_entrada:
			return "Sin entrada"
		
		costo_total = self.calcular_costo()
		tiempo_costo = self.tiempo_por_costo_formateado()
		
		return f"${costo_total:,.0f} ({tiempo_costo})"
	
	def costo_por_tiempo_formateado(self):
		"""Devuelve el costo por hora formateado"""
		costo_hora = self.costo_por_tiempo()
		return f"${costo_hora:,.2f}/h"

	def __str__(self):
		nombre = self.nombre or 'Sin nombre'
		cedula = self.cedula or f'ID:{self.id}'
		return f"{nombre} ({cedula}) - {self.matricula}"


class Perfil(models.Model):
	ROLES_CHOICES = [
		('administrador', 'Administrador'),
		('empleado', 'Empleado'),
	]
	
	usuario = models.OneToOneField(User, on_delete=models.CASCADE)
	rol = models.CharField(
		max_length=20, 
		choices=ROLES_CHOICES, 
		default='empleado'
	)
	fecha_creacion = models.DateTimeField(auto_now_add=True)
	
	def __str__(self):
		return f"{self.usuario.username} - {self.get_rol_display()}"
	
	def es_administrador(self):
		return self.rol == 'administrador'
	
	def es_empleado(self):
		return self.rol == 'empleado'
	
	def puede_agregar_usuario(self):
		# Ambos roles pueden agregar usuarios
		return True
	
	def puede_registrar_salida(self):
		# Ambos roles pueden registrar salida
		return True
	
	def puede_editar_cliente(self):
		# Solo administrador puede editar
		return self.es_administrador()
	
	def puede_eliminar_cliente(self):
		# Solo administrador puede eliminar
		return self.es_administrador()
	
	def puede_ver_lista_completa(self):
		# Tanto administrador como empleado pueden ver la lista completa
		return True
	
	def puede_editar_costos(self):
		# Solo administrador puede editar costos
		return self.es_administrador()
	
	class Meta:
		verbose_name = 'Perfil'
		verbose_name_plural = 'Perfiles'


class Visitante(models.Model):
	cedula = models.CharField(max_length=20, blank=True, null=True, verbose_name="Cédula")
	nombre = models.CharField(max_length=100, blank=True, null=True, verbose_name="Nombre completo")
	telefono = models.CharField(max_length=20, blank=True, null=True, verbose_name="Número de teléfono")
	torre = models.CharField(max_length=10, blank=True, null=True, help_text='Torre del apartamento que visita', verbose_name="Torre")
	apartamento = models.CharField(max_length=10, blank=True, null=True, help_text='Número de apartamento que visita', verbose_name="Apartamento")
	fecha_registro = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de registro")
	fecha_actualizacion = models.DateTimeField(auto_now=True, verbose_name="Última actualización")
	
	def get_display_name(self):
		"""Devuelve el nombre del visitante o un valor por defecto"""
		return self.nombre or 'Visitante sin nombre'
	
	def get_display_cedula(self):
		"""Devuelve la cédula del visitante o un valor por defecto"""
		return self.cedula or 'Sin cédula'
	
	def get_display_telefono(self):
		"""Devuelve el teléfono del visitante o un valor por defecto"""
		return self.telefono or 'Sin teléfono'
	
	def get_display_torre(self):
		"""Devuelve la torre que visita o un valor por defecto"""
		return self.torre or 'Sin torre'
	
	def get_display_apartamento(self):
		"""Devuelve el apartamento que visita o un valor por defecto"""
		return self.apartamento or 'Sin apartamento'
	
	def get_ubicacion_completa(self):
		"""Devuelve la ubicación completa (torre + apartamento)"""
		if self.torre and self.apartamento:
			return f"Torre {self.torre} - Apt {self.apartamento}"
		elif self.torre:
			return f"Torre {self.torre}"
		elif self.apartamento:
			return f"Apartamento {self.apartamento}"
		else:
			return "Sin ubicación especificada"
	
	def __str__(self):
		nombre = self.nombre or 'Sin nombre'
		cedula = self.cedula or f'ID:{self.id}'
		ubicacion = self.get_ubicacion_completa()
		return f"{nombre} ({cedula}) - {ubicacion}"
	
	class Meta:
		verbose_name = 'Visitante'
		verbose_name_plural = 'Visitantes'
		ordering = ['-fecha_registro']


class Costo(models.Model):
	"""Modelo para manejar los costos del parking por tipo de vehículo"""
	costo_auto = models.DecimalField(
		max_digits=10, 
		decimal_places=2, 
		default=0.00,
		verbose_name="Costo por minuto - Auto",
		help_text="Costo en pesos por minuto de estacionamiento para autos"
	)
	costo_moto = models.DecimalField(
		max_digits=10, 
		decimal_places=2, 
		default=0.00,
		verbose_name="Costo por minuto - Moto",
		help_text="Costo en pesos por minuto de estacionamiento para motos"
	)
	fecha_actualizacion = models.DateTimeField(auto_now=True)
	actualizado_por = models.ForeignKey(
		User, 
		on_delete=models.SET_NULL, 
		null=True, 
		blank=True,
		verbose_name="Actualizado por"
	)
	
	def __str__(self):
		return f"Auto: ${self.costo_auto}/min - Moto: ${self.costo_moto}/min"
	
	def get_costo_por_tipo(self, tipo_vehiculo):
		"""Devuelve el costo por minuto según el tipo de vehículo"""
		if tipo_vehiculo.lower() == 'auto':
			return self.costo_auto
		elif tipo_vehiculo.lower() == 'moto':
			return self.costo_moto
		else:
			return self.costo_auto  # Por defecto auto
	
	@classmethod
	def get_costos_actuales(cls):
		"""Obtiene los costos actuales, creando registro si no existe"""
		costo, created = cls.objects.get_or_create(
			id=1,  # Solo un registro de costos
			defaults={
				'costo_auto': 1.00,  # Valores por defecto: $1 por minuto
				'costo_moto': 0.50   # $0.50 por minuto
			}
		)
		return costo
	
	class Meta:
		verbose_name = 'Configuración de Costos'
		verbose_name_plural = 'Configuración de Costos'


class TarifaPlena(models.Model):
	"""Modelo para manejar la tarifa plena con costo fijo"""
	activa = models.BooleanField(
		default=False,
		verbose_name="Tarifa plena activa",
		help_text="Activar/desactivar la tarifa plena con costo fijo"
	)
	costo_fijo_auto = models.DecimalField(
		max_digits=10, 
		decimal_places=2, 
		default=0.00,
		verbose_name="Costo fijo - Auto",
		help_text="Costo fijo en pesos para autos cuando la tarifa plena está activa"
	)
	costo_fijo_moto = models.DecimalField(
		max_digits=10, 
		decimal_places=2, 
		default=0.00,
		verbose_name="Costo fijo - Moto",
		help_text="Costo fijo en pesos para motos cuando la tarifa plena está activa"
	)
	fecha_actualizacion = models.DateTimeField(auto_now=True)
	actualizado_por = models.ForeignKey(
		User, 
		on_delete=models.SET_NULL, 
		null=True, 
		blank=True,
		verbose_name="Actualizado por"
	)
	
	def __str__(self):
		estado = "Activa" if self.activa else "Inactiva"
		return f"Tarifa Plena ({estado}) - Auto: ${self.costo_fijo_auto} - Moto: ${self.costo_fijo_moto}"
	
	def get_costo_por_tipo(self, tipo_vehiculo):
		"""Devuelve el costo fijo según el tipo de vehículo"""
		if tipo_vehiculo.lower() == 'auto':
			return self.costo_fijo_auto
		elif tipo_vehiculo.lower() == 'moto':
			return self.costo_fijo_moto
		else:
			return self.costo_fijo_auto  # Por defecto auto
	
	@classmethod
	def get_tarifa_actual(cls):
		"""Obtiene la configuración actual de tarifa plena, creando registro si no existe"""
		tarifa, created = cls.objects.get_or_create(
			id=1,  # Solo un registro de tarifa plena
			defaults={
				'activa': False,
				'costo_fijo_auto': 5000.00,  # Valores por defecto
				'costo_fijo_moto': 3000.00
			}
		)
		return tarifa
	
	class Meta:
		verbose_name = 'Tarifa Plena'
		verbose_name_plural = 'Tarifa Plena'


class Recaudacion(models.Model):
	"""Modelo para registrar los cortes de recaudación del parking"""
	usuario = models.ForeignKey(
		User, 
		on_delete=models.CASCADE,
		verbose_name="Usuario que realizó el corte",
		help_text="Usuario que realizó el corte de recaudación"
	)
	monto_recaudado = models.DecimalField(
		max_digits=12, 
		decimal_places=2,
		verbose_name="Monto recaudado",
		help_text="Total recaudado en el período"
	)
	fecha_inicio = models.DateTimeField(
		verbose_name="Fecha inicio del corte",
		help_text="Fecha y hora de inicio del período de recaudación"
	)
	fecha_fin = models.DateTimeField(
		verbose_name="Fecha fin del corte",
		help_text="Fecha y hora de fin del período de recaudación"
	)
	fecha_corte = models.DateTimeField(
		auto_now_add=True,
		verbose_name="Fecha del corte",
		help_text="Fecha y hora cuando se realizó el corte"
	)
	numero_clientes = models.PositiveIntegerField(
		default=0,
		verbose_name="Número de clientes",
		help_text="Cantidad de clientes atendidos en el período"
	)
	observaciones = models.TextField(
		blank=True,
		null=True,
		verbose_name="Observaciones",
		help_text="Observaciones adicionales sobre el corte"
	)
	
	def __str__(self):
		return f"Corte {self.id} - ${self.monto_recaudado:,.2f} ({self.fecha_corte.strftime('%d/%m/%Y %H:%M')})"
	
	@classmethod
	def get_ultimo_corte(cls):
		"""Obtiene la fecha del último corte realizado"""
		ultimo_corte = cls.objects.order_by('-fecha_corte').first()
		if ultimo_corte:
			return ultimo_corte.fecha_fin
		return None
	
	@classmethod
	def calcular_recaudacion_actual(cls):
		"""Calcula la recaudación desde el último corte"""
		fecha_ultimo_corte = cls.get_ultimo_corte()
		
		# Filtrar clientes que han salido desde el último corte
		clientes_query = Cliente.objects.filter(fecha_salida__isnull=False)
		
		if fecha_ultimo_corte:
			clientes_query = clientes_query.filter(fecha_salida__gt=fecha_ultimo_corte)
		
		# Calcular el total recaudado
		total_recaudado = 0
		numero_clientes = 0
		
		for cliente in clientes_query:
			total_recaudado += cliente.calcular_costo()
			numero_clientes += 1
		
		fecha_inicio = fecha_ultimo_corte or timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
		
		return {
			'monto_total': total_recaudado,
			'numero_clientes': numero_clientes,
			'fecha_inicio': fecha_inicio,
			'fecha_actual': timezone.now(),
			'clientes': clientes_query
		}
	
	class Meta:
		verbose_name = 'Recaudación'
		verbose_name_plural = 'Recaudaciones'
		ordering = ['-fecha_corte']
