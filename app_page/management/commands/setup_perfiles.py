from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from app_page.models import Perfil

class Command(BaseCommand):
    help = 'Crear perfiles para usuarios existentes y configurar roles'

    def handle(self, *args, **options):
        # Crear perfiles para usuarios que no tengan uno
        usuarios_sin_perfil = User.objects.filter(perfil__isnull=True)
        perfiles_creados = 0
        
        for usuario in usuarios_sin_perfil:
            Perfil.objects.create(usuario=usuario, rol='empleado')
            perfiles_creados += 1
            self.stdout.write(
                self.style.SUCCESS(f'Perfil creado para {usuario.username} (empleado)')
            )
        
        # Asignar el primer usuario como administrador
        primer_usuario = User.objects.filter(is_superuser=True).first()
        if primer_usuario and hasattr(primer_usuario, 'perfil'):
            primer_usuario.perfil.rol = 'administrador'
            primer_usuario.perfil.save()
            self.stdout.write(
                self.style.SUCCESS(f'{primer_usuario.username} configurado como administrador')
            )
        elif primer_usuario:
            Perfil.objects.create(usuario=primer_usuario, rol='administrador')
            self.stdout.write(
                self.style.SUCCESS(f'Perfil de administrador creado para {primer_usuario.username}')
            )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Proceso completado. {perfiles_creados} perfiles creados.'
            )
        )
