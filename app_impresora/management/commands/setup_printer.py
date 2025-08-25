"""
Comando de gestión para configurar la impresora Epson M244A
"""

from django.core.management.base import BaseCommand, CommandError
from django.core.management import call_command
from app_impresora.models import PrinterConfiguration
from app_impresora.printer_service import printer_service


class Command(BaseCommand):
    help = 'Configura la impresora Epson M244A para el sistema de parking'

    def add_arguments(self, parser):
        parser.add_argument(
            '--name',
            type=str,
            default='Epson M244A Principal',
            help='Nombre de la impresora'
        )
        parser.add_argument(
            '--type',
            type=str,
            choices=['USB', 'SERIAL', 'NETWORK'],
            default='USB',
            help='Tipo de conexión (USB, SERIAL, NETWORK)'
        )
        parser.add_argument(
            '--connection',
            type=str,
            help='Cadena de conexión (nombre impresora, puerto COM, o IP:Puerto)'
        )
        parser.add_argument(
            '--test',
            action='store_true',
            help='Probar la impresora después de configurarla'
        )
        parser.add_argument(
            '--list',
            action='store_true',
            help='Mostrar impresoras configuradas'
        )

    def handle(self, *args, **options):
        if options['list']:
            self.list_printers()
            return

        if not options['connection']:
            self.stdout.write(
                self.style.ERROR('Debe especificar la cadena de conexión con --connection')
            )
            self.show_examples()
            return

        try:
            # Desactivar otras impresoras
            PrinterConfiguration.objects.update(is_active=False)
            
            # Crear nueva configuración
            printer_config = PrinterConfiguration.objects.create(
                name=options['name'],
                printer_type=options['type'],
                connection_string=options['connection'],
                is_active=True,
                model='Epson M244A'
            )
            
            self.stdout.write(
                self.style.SUCCESS(f'Impresora configurada exitosamente: {printer_config.name}')
            )
            
            # Probar la impresora si se solicita
            if options['test']:
                self.stdout.write('Probando la impresora...')
                success, message = printer_service.test_printer()
                
                if success:
                    self.stdout.write(self.style.SUCCESS(f'Prueba exitosa: {message}'))
                else:
                    self.stdout.write(self.style.WARNING(f'Prueba falló: {message}'))
            
        except Exception as e:
            raise CommandError(f'Error configurando la impresora: {str(e)}')

    def list_printers(self):
        printers = PrinterConfiguration.objects.all()
        
        if not printers:
            self.stdout.write(self.style.WARNING('No hay impresoras configuradas'))
            return
        
        self.stdout.write(self.style.SUCCESS('Impresoras configuradas:'))
        self.stdout.write('')
        
        for printer in printers:
            status = "ACTIVA" if printer.is_active else "Inactiva"
            style = self.style.SUCCESS if printer.is_active else self.style.WARNING
            
            self.stdout.write(f'  • {printer.name}')
            self.stdout.write(f'    Modelo: {printer.model}')
            self.stdout.write(f'    Tipo: {printer.get_printer_type_display()}')
            self.stdout.write(f'    Conexión: {printer.connection_string}')
            self.stdout.write(style(f'    Estado: {status}'))
            self.stdout.write('')

    def show_examples(self):
        self.stdout.write('')
        self.stdout.write(self.style.WARNING('Ejemplos de uso:'))
        self.stdout.write('')
        self.stdout.write('Para conexión USB:')
        self.stdout.write('  python manage.py setup_printer --type USB --connection "EPSON TM-M244A Receipt"')
        self.stdout.write('')
        self.stdout.write('Para conexión Serial:')
        self.stdout.write('  python manage.py setup_printer --type SERIAL --connection "COM3"')
        self.stdout.write('')
        self.stdout.write('Para conexión de Red:')
        self.stdout.write('  python manage.py setup_printer --type NETWORK --connection "192.168.1.100:9100"')
        self.stdout.write('')
        self.stdout.write('Para probar después de configurar:')
        self.stdout.write('  python manage.py setup_printer --type USB --connection "EPSON TM-M244A Receipt" --test')
        self.stdout.write('')
        self.stdout.write('Para ver impresoras configuradas:')
        self.stdout.write('  python manage.py setup_printer --list')
