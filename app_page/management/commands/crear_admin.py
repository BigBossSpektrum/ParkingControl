from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from app_page.models import Perfil

class Command(BaseCommand):
    help = 'Crear un usuario administrador (superusuario con perfil de administrador)'

    def add_arguments(self, parser):
        parser.add_argument('--username', type=str, default='admin', help='Nombre de usuario (por defecto: admin)')
        parser.add_argument('--password', type=str, default='admin123', help='Contraseña (por defecto: admin123)')
        parser.add_argument('--email', type=str, default='admin@parkingcontrol.local', help='Correo electronico')

    def handle(self, *args, **options):
        username = options['username']
        password = options['password']
        email = options['email']

        usuario = User.objects.filter(username=username).first()

        if usuario:
            usuario.set_password(password)
            usuario.email = email
            usuario.is_staff = True
            usuario.is_superuser = True
            usuario.save()
            self.stdout.write(
                self.style.WARNING(f'El usuario "{username}" ya existia: contraseña y permisos actualizados')
            )
        else:
            usuario = User.objects.create_superuser(
                username=username,
                email=email,
                password=password
            )
            self.stdout.write(
                self.style.SUCCESS(f'Usuario "{username}" creado como superusuario')
            )

        # El signal post_save de User ya crea un Perfil con rol 'empleado',
        # por eso aqui se obtiene y se promueve en lugar de crearlo.
        perfil, creado = Perfil.objects.get_or_create(
            usuario=usuario,
            defaults={'rol': 'administrador'}
        )

        if not creado and perfil.rol != 'administrador':
            perfil.rol = 'administrador'
            perfil.save()

        self.stdout.write(
            self.style.SUCCESS(
                'Administrador listo:\n'
                f'Usuario: {username}\n'
                f'Contraseña: {password}\n'
                f'Rol: {perfil.get_rol_display()}\n'
                f'Es administrador: {perfil.es_administrador()}'
            )
        )
