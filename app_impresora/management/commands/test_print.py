"""
Comando para probar la impresión automática con un cliente de prueba
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from app_page.models import Cliente
from app_impresora.printer_service import printer_service


class Command(BaseCommand):
    help = 'Prueba la impresión automática creando un cliente de prueba'

    def add_arguments(self, parser):
        parser.add_argument(
            '--simulation',
            action='store_true',
            help='Habilitar modo simulación para la prueba'
        )

    def handle(self, *args, **options):
        if options['simulation']:
            printer_service.enable_simulation_mode(True)
            self.stdout.write(self.style.SUCCESS('Modo simulación habilitado'))
        else:
            # Recargar configuración de simulación desde cache
            printer_service.reload_simulation_mode()

        # Crear cliente de prueba
        cliente = Cliente.objects.create(
            cedula='12345678',
            nombre='Cliente de Prueba',
            telefono='3001234567',
            matricula='TEST123',
            tipo_vehiculo='Auto',
            fecha_entrada=timezone.now()
        )
        
        self.stdout.write(f'Cliente creado con ID: {cliente.id}')
        
        # Generar QR limpio
        qr_generated = cliente.generate_clean_qr()
        if qr_generated:
            self.stdout.write(self.style.SUCCESS('Código QR limpio generado exitosamente'))
            cliente.save()
        else:
            self.stdout.write(self.style.ERROR('Error generando código QR limpio'))
            return
        
        # Intentar impresión
        self.stdout.write('Intentando imprimir ticket...')
        success = printer_service.print_qr_ticket(cliente)
        
        if success:
            self.stdout.write(self.style.SUCCESS('✅ Ticket impreso exitosamente'))
        else:
            self.stdout.write(self.style.ERROR('❌ Error al imprimir ticket'))
        
        # Mostrar estado de la impresora
        status = printer_service.get_printer_status()
        self.stdout.write(f'Estado de impresora: {status["message"]}')
        
        self.stdout.write(f'Modo simulación: {"Activo" if printer_service.simulation_mode else "Inactivo"}')
