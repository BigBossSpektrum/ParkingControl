"""
Comando para gestionar el modo simulación del sistema de impresión
"""

from django.core.management.base import BaseCommand
from django.core.cache import cache
from app_impresora.printer_service import PrinterService


class Command(BaseCommand):
    help = 'Gestiona el modo simulación del sistema de impresión'

    def add_arguments(self, parser):
        parser.add_argument(
            '--enable',
            action='store_true',
            help='Habilitar modo simulación'
        )
        parser.add_argument(
            '--disable',
            action='store_true',
            help='Deshabilitar modo simulación (usar impresora real)'
        )
        parser.add_argument(
            '--status',
            action='store_true',
            help='Mostrar estado actual del modo simulación'
        )

    def handle(self, *args, **options):
        if options['enable']:
            cache.set('printer_simulation_mode', True, 86400)
            # Recargar instancia global
            from app_impresora.printer_service import printer_service
            printer_service.reload_simulation_mode()
            self.stdout.write(
                self.style.SUCCESS('✅ Modo simulación HABILITADO')
            )
            self.stdout.write('   Las impresiones se simularán (no se enviará a hardware)')
            
        elif options['disable']:
            cache.set('printer_simulation_mode', False, 86400)
            # Recargar instancia global
            from app_impresora.printer_service import printer_service
            printer_service.reload_simulation_mode()
            self.stdout.write(
                self.style.SUCCESS('🖨️  Modo simulación DESHABILITADO')
            )
            self.stdout.write('   Las impresiones se enviarán a la impresora física')
            
        elif options['status']:
            service = PrinterService()
            mode = cache.get('printer_simulation_mode', True)
            if mode:
                self.stdout.write(
                    self.style.WARNING('🎭 Modo simulación: ACTIVO')
                )
            else:
                self.stdout.write(
                    self.style.SUCCESS('🖨️  Modo simulación: INACTIVO (modo real)')
                )
                
        else:
            # Mostrar estado actual por defecto
            service = PrinterService()
            mode = cache.get('printer_simulation_mode', True)
            
            self.stdout.write('📊 ESTADO DEL MODO SIMULACIÓN')
            self.stdout.write('=' * 40)
            
            if mode:
                self.stdout.write(
                    self.style.WARNING('🎭 Modo: SIMULACIÓN ACTIVA')
                )
                self.stdout.write('   • Las impresiones se simularán')
                self.stdout.write('   • No se enviará a hardware real')
            else:
                self.stdout.write(
                    self.style.SUCCESS('🖨️  Modo: IMPRESIÓN REAL')
                )
                self.stdout.write('   • Las impresiones se envían a impresora física')
                self.stdout.write('   • Asegúrate de que la impresora esté conectada')
            
            self.stdout.write('\n💡 COMANDOS DISPONIBLES:')
            self.stdout.write('   python manage.py simulation_mode --enable   (activar simulación)')
            self.stdout.write('   python manage.py simulation_mode --disable  (usar impresora real)')
            self.stdout.write('   python manage.py simulation_mode --status   (ver estado)')
