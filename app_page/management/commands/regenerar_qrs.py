from django.core.management.base import BaseCommand
from app_page.models import Cliente

class Command(BaseCommand):
    help = 'Regenera códigos QR con datos para todos los clientes'

    def add_arguments(self, parser):
        parser.add_argument(
            '--cliente-id',
            type=int,
            help='ID específico del cliente para regenerar QR',
        )

    def handle(self, *args, **options):
        if options['cliente_id']:
            try:
                cliente = Cliente.objects.get(id=options['cliente_id'])
                self.stdout.write(f"Regenerando QR para cliente {cliente.id}: {cliente.nombre}")
                if cliente.generate_qr_with_data():
                    cliente.save()
                    self.stdout.write(
                        self.style.SUCCESS(f'QR regenerado exitosamente para {cliente.nombre}')
                    )
                else:
                    self.stdout.write(
                        self.style.ERROR(f'Error al regenerar QR para {cliente.nombre}')
                    )
            except Cliente.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'Cliente con ID {options["cliente_id"]} no encontrado')
                )
        else:
            clientes = Cliente.objects.filter(fecha_entrada__isnull=False)
            total = clientes.count()
            exitosos = 0
            
            self.stdout.write(f"Regenerando QRs para {total} clientes...")
            
            for cliente in clientes:
                self.stdout.write(f"Procesando cliente {cliente.id}: {cliente.nombre}")
                if cliente.generate_qr_with_data():
                    cliente.save()
                    exitosos += 1
                    self.stdout.write(f"  ✓ QR generado exitosamente")
                else:
                    self.stdout.write(f"  ✗ Error al generar QR")
            
            self.stdout.write(
                self.style.SUCCESS(f'Proceso completado: {exitosos}/{total} QRs regenerados')
            )
