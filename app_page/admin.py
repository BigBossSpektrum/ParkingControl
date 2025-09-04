from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from .models import Cliente, Perfil, Costo, TarifaPlena

@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
	list_display = ('cedula', 'nombre', 'telefono', 'torre', 'apartamento', 'matricula', 'tipo_vehiculo', 'tiempo_parking', 'fecha_entrada', 'fecha_salida')
	search_fields = ('cedula', 'nombre', 'matricula', 'telefono', 'torre', 'apartamento')
	list_filter = ('tipo_vehiculo',)

@admin.register(Perfil)
class PerfilAdmin(admin.ModelAdmin):
	list_display = ('usuario', 'rol', 'fecha_creacion')
	list_filter = ('rol', 'fecha_creacion')
	search_fields = ('usuario__username', 'usuario__first_name', 'usuario__last_name')
	readonly_fields = ('fecha_creacion',)

@admin.register(Costo)
class CostoAdmin(admin.ModelAdmin):
	list_display = ('costo_auto', 'costo_moto', 'fecha_actualizacion', 'actualizado_por')
	readonly_fields = ('fecha_actualizacion', 'actualizado_por')
	
	def has_change_permission(self, request, obj=None):
		"""Solo administradores pueden modificar los costos"""
		if request.user.is_superuser:
			return True
		
		try:
			perfil = request.user.perfil
			return perfil.puede_editar_costos()
		except:
			return False
	
	def has_delete_permission(self, request, obj=None):
		"""Solo administradores pueden eliminar costos"""
		return self.has_change_permission(request, obj)
	
	def has_add_permission(self, request):
		"""Solo administradores pueden agregar costos"""
		return self.has_change_permission(request)
	
	def save_model(self, request, obj, form, change):
		"""Guarda quién actualizó los costos"""
		obj.actualizado_por = request.user
		super().save_model(request, obj, form, change)
	
	def get_queryset(self, request):
		"""Limita a un solo registro de configuración"""
		qs = super().get_queryset(request)
		return qs.filter(id=1)  # Solo el registro principal

@admin.register(TarifaPlena)
class TarifaPlenaAdmin(admin.ModelAdmin):
	list_display = ('activa', 'costo_fijo_auto', 'costo_fijo_moto', 'fecha_actualizacion', 'actualizado_por')
	readonly_fields = ('fecha_actualizacion', 'actualizado_por')
	
	fieldsets = (
		('Estado de la Tarifa', {
			'fields': ('activa',),
			'description': 'Activar o desactivar la tarifa plena con costo fijo'
		}),
		('Costos Fijos', {
			'fields': ('costo_fijo_auto', 'costo_fijo_moto'),
			'description': 'Costos fijos cuando la tarifa plena está activa'
		}),
		('Información del Sistema', {
			'fields': ('fecha_actualizacion', 'actualizado_por'),
			'classes': ('collapse',)
		})
	)
	
	def has_change_permission(self, request, obj=None):
		"""Solo administradores pueden modificar la tarifa plena"""
		if request.user.is_superuser:
			return True
		
		try:
			perfil = request.user.perfil
			return perfil.puede_editar_costos()
		except:
			return False
	
	def has_delete_permission(self, request, obj=None):
		"""No se puede eliminar la configuración de tarifa plena"""
		return False
	
	def has_add_permission(self, request):
		"""Solo se permite un registro de tarifa plena"""
		return not TarifaPlena.objects.exists()
	
	def save_model(self, request, obj, form, change):
		"""Guarda quién actualizó la tarifa plena"""
		obj.actualizado_por = request.user
		super().save_model(request, obj, form, change)
	
	def get_queryset(self, request):
		"""Limita a un solo registro de configuración"""
		qs = super().get_queryset(request)
		return qs.filter(id=1)  # Solo el registro principal

# Inline para mostrar el perfil en el admin de Usuario
class PerfilInline(admin.StackedInline):
	model = Perfil
	can_delete = False
	verbose_name = 'Perfil'
	verbose_name_plural = 'Perfil'

# Extender el UserAdmin para incluir el perfil
class UsuarioConPerfilAdmin(UserAdmin):
	inlines = (PerfilInline,)

# Re-registrar el User admin con el perfil incluido
admin.site.unregister(User)
admin.site.register(User, UsuarioConPerfilAdmin)
