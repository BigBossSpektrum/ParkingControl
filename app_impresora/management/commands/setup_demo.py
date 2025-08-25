"""
Comando para configurar rápidamente el sistema para demos y pruebas
"""

from django.core.management.base import BaseCommand
from app_impresora.models import PrinterConfiguration
from app_impresora.printer_service import printer_service


class Command(BaseCommand):
    help = 'Configura el sistema para modo demo con impresión simulada'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Configurando sistema para modo demo...'))
        
        # Verificar si ya hay una impresora configurada
        printer = PrinterConfiguration.objects.filter(is_active=True).first()
        
        if not printer:
            # Crear configuración de impresora demo
            printer = PrinterConfiguration.objects.create(
                name='Impresora Demo (Simulación)',
                printer_type='USB',
                connection_string='DEMO_PRINTER',
                is_active=True,
                model='Epson M244A'
            )
            self.stdout.write(f'✅ Impresora demo creada: {printer.name}')
        else:
            self.stdout.write(f'✅ Impresora existente: {printer.name}')
        
        # Habilitar modo simulación
        printer_service.enable_simulation_mode(True)
        self.stdout.write('✅ Modo simulación habilitado')
        
        # Mostrar estado
        status = printer_service.get_printer_status()
        self.stdout.write(f'📊 Estado: {status["message"]}')
        
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('🎉 Sistema configurado para demo:'))
        self.stdout.write('   • Impresora configurada')
        self.stdout.write('   • Modo simulación activo')
        self.stdout.write('   • Listo para registrar clientes')
        self.stdout.write('')
        self.stdout.write('Ahora puede registrar clientes y verá que se "imprimen" tickets automáticamente.')
        self.stdout.write('Acceda a http://127.0.0.1:8000/impresora/ para gestionar la impresora.')
