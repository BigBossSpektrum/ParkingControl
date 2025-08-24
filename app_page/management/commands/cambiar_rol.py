from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from app_page.models import Perfil

class Command(BaseCommand):
    help = 'Cambiar el rol de un usuario'

    def add_arguments(self, parser):
        parser.add_argument('username', type=str, help='Nombre de usuario')
        parser.add_argument('rol', type=str, choices=['administrador', 'empleado'], help='Nuevo rol del usuario')

    def handle(self, *args, **options):
        username = options['username']
        nuevo_rol = options['rol']
        
        try:
            usuario = User.objects.get(username=username)
            perfil = usuario.perfil if hasattr(usuario, 'perfil') else Perfil.objects.create(usuario=usuario)
            
            rol_anterior = perfil.rol
            perfil.rol = nuevo_rol
            perfil.save()
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'Usuario "{username}" actualizado exitosamente:\n'
                    f'Rol anterior: {rol_anterior}\n'
                    f'Nuevo rol: {nuevo_rol}'
                )
            )
            
        except User.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f'Usuario "{username}" no encontrado')
            )
