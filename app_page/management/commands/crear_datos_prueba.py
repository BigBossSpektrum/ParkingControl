from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import datetime, timedelta
from app_page.models import Cliente, Recaudacion
from django.contrib.auth.models import User

class Command(BaseCommand):
    help = 'Crea datos de prueba para el sistema de recaudación'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clientes',
            type=int,
            default=5,
            help='Número de clientes de prueba a crear',
        )

    def handle(self, *args, **options):
        num_clientes = options['clientes']
        
        # Obtener o crear un usuario administrador
        try:
            admin_user = User.objects.filter(is_superuser=True).first()
            if not admin_user:
                admin_user = User.objects.create_superuser(
                    username='admin_test',
                    email='admin@test.com',
                    password='admin123'
                )
                self.stdout.write('Usuario administrador creado: admin_test/admin123')
        except Exception as e:
            self.stdout.write(f'Error creando usuario: {e}')
            return

        # Crear clientes de prueba con salidas registradas
        ahora = timezone.now()
        clientes_creados = []

        for i in range(num_clientes):
            # Crear fechas de entrada y salida aleatorias en los últimos días
            dias_atras = 3 - (i % 3)  # Distribuir en los últimos 3 días
            hora_entrada = ahora - timedelta(days=dias_atras, hours=2+i, minutes=30)
            hora_salida = hora_entrada + timedelta(hours=1+i, minutes=15)

            cliente = Cliente.objects.create(
                cedula=f'1234567{i:02d}',
                nombre=f'Cliente Prueba {i+1}',
                telefono=f'300123456{i}',
                torre=f'{(i % 5) + 1}' if i % 2 == 0 else '',
                apartamento=f'{(i % 10) + 100}' if i % 2 == 0 else '',
                matricula=f'ABC-{i+100}',
                tipo_vehiculo=['Auto', 'Moto', 'Otro'][i % 3],
                fecha_entrada=hora_entrada,
                fecha_salida=hora_salida
            )
            
            clientes_creados.append(cliente)
            self.stdout.write(f'Cliente creado: {cliente.nombre} - ${cliente.calcular_costo():,.2f}')

        # Crear un corte de recaudación de prueba
        if clientes_creados:
            # Calcular período del corte
            fecha_inicio = min(c.fecha_entrada for c in clientes_creados if c.fecha_entrada)
            fecha_fin = max(c.fecha_salida for c in clientes_creados if c.fecha_salida)
            
            # Calcular monto total
            monto_total = sum(c.calcular_costo() for c in clientes_creados)
            
            # Crear el corte
            corte = Recaudacion.objects.create(
                usuario=admin_user,
                monto_recaudado=monto_total,
                fecha_inicio=fecha_inicio,
                fecha_fin=fecha_fin,
                numero_clientes=len(clientes_creados),
                observaciones='Corte de prueba generado automáticamente'
            )
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'Corte de recaudación creado: ${monto_total:,.2f} con {len(clientes_creados)} clientes'
                )
            )

        # Crear algunos clientes adicionales sin salida (activos)
        for i in range(2):
            hora_entrada = ahora - timedelta(hours=i+1)
            cliente_activo = Cliente.objects.create(
                cedula=f'9876543{i:02d}',
                nombre=f'Cliente Activo {i+1}',
                telefono=f'300987654{i}',
                matricula=f'XYZ-{i+200}',
                tipo_vehiculo=['Auto', 'Moto'][i % 2],
                fecha_entrada=hora_entrada,
                fecha_salida=None  # Sin salida, cliente activo
            )
            self.stdout.write(f'Cliente activo creado: {cliente_activo.nombre}')

        self.stdout.write(
            self.style.SUCCESS(
                f'Datos de prueba creados exitosamente:\n'
                f'- {num_clientes} clientes con salida registrada\n'
                f'- 1 corte de recaudación\n'
                f'- 2 clientes activos (sin salida)'
            )
        )
