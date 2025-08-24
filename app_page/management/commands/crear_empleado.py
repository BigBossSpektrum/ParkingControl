from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from app_page.models import Perfil

class Command(BaseCommand):
    help = 'Crear un usuario empleado de prueba'

    def handle(self, *args, **options):
        # Verificar si ya existe
        if User.objects.filter(username='empleado').exists():
            self.stdout.write(
                self.style.WARNING('El usuario "empleado" ya existe')
            )
            return
        
        # Crear usuario empleado
        usuario_empleado = User.objects.create_user(
            username='empleado',
            password='empleado123',
            first_name='Juan',
            last_name='Empleado'
        )
        
        # Crear perfil de empleado
        Perfil.objects.create(usuario=usuario_empleado, rol='empleado')
        
        self.stdout.write(
            self.style.SUCCESS(
                'Usuario empleado creado exitosamente:\n'
                'Usuario: empleado\n'
                'Contraseña: empleado123\n'
                'Rol: Empleado'
            )
        )
