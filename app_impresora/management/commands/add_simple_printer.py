"""
Comando simplificado para agregar impresoras
"""

from django.core.management.base import BaseCommand
from django.core.cache import cache
from app_impresora.models import PrinterConfiguration
import subprocess
import json


class Command(BaseCommand):
    help = 'Agregar impresora de forma simplificada'

    def add_arguments(self, parser):
        parser.add_argument(
            '--auto',
            action='store_true',
            help='Detectar y configurar automáticamente la primera impresora térmica'
        )
        parser.add_argument(
            '--name',
            type=str,
            help='Nombre para la impresora'
        )
        parser.add_argument(
            '--windows',
            type=str,
            help='Nombre de impresora Windows específica'
        )
        parser.add_argument(
            '--ip',
            type=str,
            help='Dirección IP para impresora en red'
        )
        parser.add_argument(
            '--port',
            type=int,
            default=9100,
            help='Puerto para impresora en red (default: 9100)'
        )
        parser.add_argument(
            '--list',
            action='store_true',
            help='Listar impresoras Windows disponibles'
        )

    def handle(self, *args, **options):
        if options['list']:
            self.list_windows_printers()
            return

        if options['auto']:
            self.auto_setup()
            return

        if options['windows']:
            self.setup_windows_printer(options['windows'], options['name'])
            return

        if options['ip']:
            self.setup_network_printer(options['ip'], options['port'], options['name'])
            return

        # Mostrar ayuda
        self.show_help()

    def list_windows_printers(self):
        """Lista impresoras Windows disponibles"""
        self.stdout.write('🔍 IMPRESORAS WINDOWS DISPONIBLES:')
        self.stdout.write('=' * 50)
        
        try:
            printers = self.get_windows_printers()
            
            if not printers:
                self.stdout.write(self.style.WARNING('No se encontraron impresoras'))
                return
            
            for i, printer in enumerate(printers, 1):
                thermal_indicator = " ⭐ (TÉRMICA)" if self.is_thermal_printer(printer['name']) else ""
                self.stdout.write(f"{i}. {printer['name']}{thermal_indicator}")
                self.stdout.write(f"   Driver: {printer.get('driver', 'N/A')}")
                self.stdout.write(f"   Puerto: {printer.get('port', 'N/A')}")
                self.stdout.write("")
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error: {e}'))

    def auto_setup(self):
        """Configuración automática"""
        self.stdout.write('🚀 CONFIGURACIÓN AUTOMÁTICA')
        self.stdout.write('=' * 40)
        
        try:
            printers = self.get_windows_printers()
            thermal_printers = [p for p in printers if self.is_thermal_printer(p['name'])]
            
            if not thermal_printers:
                self.stdout.write(self.style.WARNING('❌ No se encontraron impresoras térmicas'))
                self.stdout.write('💡 Usa --list para ver impresoras disponibles')
                return
            
            printer = thermal_printers[0]
            name = f"{printer['name']} (Auto)"
            
            # Desactivar otras
            PrinterConfiguration.objects.update(is_active=False)
            
            # Crear nueva
            new_printer = PrinterConfiguration.objects.create(
                name=name,
                model='Epson Thermal',
                printer_type='USB',
                connection_string=printer['name'],
                is_active=True
            )
            
            self.stdout.write(self.style.SUCCESS(f'✅ Impresora configurada: {name}'))
            self.stdout.write(f'   ID: {new_printer.id}')
            self.stdout.write(f'   Conexión: {printer["name"]}')
            
            # Desactivar simulación
            cache.set('printer_simulation_mode', False, 86400)
            self.stdout.write(self.style.SUCCESS('🖨️  Modo real activado'))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Error: {e}'))

    def setup_windows_printer(self, printer_name, custom_name=None):
        """Configurar impresora Windows específica"""
        name = custom_name or f"{printer_name} (Manual)"
        
        try:
            # Desactivar otras
            PrinterConfiguration.objects.update(is_active=False)
            
            # Crear nueva
            new_printer = PrinterConfiguration.objects.create(
                name=name,
                model='Windows Printer',
                printer_type='USB',
                connection_string=printer_name,
                is_active=True
            )
            
            self.stdout.write(self.style.SUCCESS(f'✅ Impresora Windows configurada: {name}'))
            self.stdout.write(f'   ID: {new_printer.id}')
            self.stdout.write(f'   Conexión: {printer_name}')
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Error: {e}'))

    def setup_network_printer(self, ip, port, custom_name=None):
        """Configurar impresora en red"""
        name = custom_name or f"Red {ip}"
        connection = f"{ip}:{port}"
        
        try:
            # Desactivar otras
            PrinterConfiguration.objects.update(is_active=False)
            
            # Crear nueva
            new_printer = PrinterConfiguration.objects.create(
                name=name,
                model='Network Printer',
                printer_type='NETWORK',
                connection_string=connection,
                is_active=True
            )
            
            self.stdout.write(self.style.SUCCESS(f'✅ Impresora en red configurada: {name}'))
            self.stdout.write(f'   ID: {new_printer.id}')
            self.stdout.write(f'   Conexión: {connection}')
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Error: {e}'))

    def get_windows_printers(self):
        """Obtiene impresoras Windows"""
        try:
            cmd = [
                'powershell', '-Command',
                'Get-Printer | Select-Object Name, DriverName, PortName | ConvertTo-Json'
            ]
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                printers_data = json.loads(result.stdout) if result.stdout.strip() else []
                if not isinstance(printers_data, list):
                    printers_data = [printers_data]
                
                return [
                    {
                        'name': p.get('Name', ''),
                        'driver': p.get('DriverName', ''),
                        'port': p.get('PortName', '')
                    }
                    for p in printers_data
                ]
        except Exception as e:
            raise Exception(f"Error obteniendo impresoras: {e}")
        
        return []

    def is_thermal_printer(self, printer_name):
        """Detecta si es impresora térmica"""
        thermal_keywords = [
            'thermal', 'receipt', 'tm-', 'epson', 'star', 'citizen',
            'pos', 'ticket', 'tmu', 'tsp', 'térmica'
        ]
        
        return any(keyword in printer_name.lower() for keyword in thermal_keywords)

    def show_help(self):
        """Muestra ayuda de uso"""
        self.stdout.write('🖨️  AGREGAR IMPRESORA - AYUDA')
        self.stdout.write('=' * 40)
        self.stdout.write('')
        self.stdout.write('📋 COMANDOS DISPONIBLES:')
        self.stdout.write('')
        self.stdout.write('🔍 Listar impresoras disponibles:')
        self.stdout.write('   python manage.py add_simple_printer --list')
        self.stdout.write('')
        self.stdout.write('🚀 Configuración automática (recomendado):')
        self.stdout.write('   python manage.py add_simple_printer --auto')
        self.stdout.write('')
        self.stdout.write('🪟 Configurar impresora Windows específica:')
        self.stdout.write('   python manage.py add_simple_printer --windows "EPSON TM-T88V Receipt"')
        self.stdout.write('   python manage.py add_simple_printer --windows "Mi Impresora" --name "Caja 1"')
        self.stdout.write('')
        self.stdout.write('🌐 Configurar impresora en red:')
        self.stdout.write('   python manage.py add_simple_printer --ip 192.168.1.100')
        self.stdout.write('   python manage.py add_simple_printer --ip 192.168.1.100 --port 9100 --name "Red Principal"')
        self.stdout.write('')
        self.stdout.write('💡 TIP: Usa --auto para la configuración más rápida!')
