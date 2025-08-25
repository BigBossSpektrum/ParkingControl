"""
Comando para probar impresión real (sin simulación)
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from django.core.cache import cache
from app_page.models import Cliente
from app_impresora.printer_service import PrinterService


class Command(BaseCommand):
    help = 'Prueba la impresión real en la impresora física'

    def handle(self, *args, **options):
        # Forzar modo real
        cache.set('printer_simulation_mode', False, 86400)
        
        # Crear nueva instancia del servicio (no usar la global)
        printer_service = PrinterService()
        
        self.stdout.write(f'Modo simulación: {"Activo" if printer_service.simulation_mode else "INACTIVO (modo real)"}')
        
        # Crear cliente de prueba
        cliente = Cliente.objects.create(
            cedula='98765432',
            nombre='Prueba Impresión Real',
            telefono='3001234567',
            matricula='REAL123',
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
        self.stdout.write('🖨️  Intentando imprimir en impresora FÍSICA...')
        success = printer_service.print_qr_ticket(cliente)
        
        if success:
            self.stdout.write(self.style.SUCCESS('✅ Ticket enviado a impresora física'))
            self.stdout.write('   👀 REVISA la impresora para ver si salió el ticket')
        else:
            self.stdout.write(self.style.ERROR('❌ Error al imprimir ticket'))
        
        # Mostrar estado de la impresora
        status = printer_service.get_printer_status()
        self.stdout.write(f'Estado de impresora: {status["message"]}')
        
        self.stdout.write(f'💡 Modo actual: {"SIMULACIÓN" if printer_service.simulation_mode else "REAL - debería haber salido papel"}')
