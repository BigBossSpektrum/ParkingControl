from django.db import models
from django.contrib.auth.models import User

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
        # Solo administrador puede ver la lista completa
        return self.es_administrador()
    
    class Meta:
        verbose_name = 'Perfil'
        verbose_name_plural = 'Perfiles'
