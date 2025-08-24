from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from .models import Cliente, Perfil

@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
	list_display = ('cedula', 'nombre', 'telefono', 'matricula', 'tipo_vehiculo', 'tiempo_parking', 'fecha_entrada', 'fecha_salida')
	search_fields = ('cedula', 'nombre', 'matricula', 'telefono')
	list_filter = ('tipo_vehiculo',)

@admin.register(Perfil)
class PerfilAdmin(admin.ModelAdmin):
	list_display = ('usuario', 'rol', 'fecha_creacion')
	list_filter = ('rol', 'fecha_creacion')
	search_fields = ('usuario__username', 'usuario__first_name', 'usuario__last_name')
	readonly_fields = ('fecha_creacion',)

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
