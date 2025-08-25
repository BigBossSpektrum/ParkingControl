"""
Comando de debug para probar conexión Win32Raw directamente
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from django.core.cache import cache
from app_page.models import Cliente


class Command(BaseCommand):
    help = 'Debug de conexión Win32Raw directa'

    def handle(self, *args, **options):
        try:
            self.stdout.write('🔍 Probando conexión Win32Raw directa...')
            
            # Importar Win32Raw
            from escpos.printer import Win32Raw
            
            printer_name = "EPSON TM-T88V Receipt"
            self.stdout.write(f'Intentando conectar a: {printer_name}')
            
            # Crear instancia de impresora
            printer = Win32Raw(printer_name)
            
            self.stdout.write('✅ Conexión exitosa!')
            
            # Probar impresión simple
            self.stdout.write('🖨️  Probando impresión simple...')
            printer.text("PRUEBA DE IMPRESION\n")
            printer.text("Fecha: " + str(timezone.now()) + "\n")
            printer.text("===========================\n")
            printer.cut()
            printer.close()
            
            self.stdout.write(self.style.SUCCESS('✅ Impresión enviada exitosamente!'))
            self.stdout.write('👀 REVISA la impresora - debería haber salido un ticket de prueba')
            
        except ImportError as e:
            self.stdout.write(self.style.ERROR(f'Error de importación: {e}'))
            self.stdout.write('Instalar: pip install pywin32')
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error de conexión: {e}'))
            self.stdout.write('Verifica que:')
            self.stdout.write('1. La impresora esté encendida y conectada')
            self.stdout.write('2. El nombre de la impresora sea exacto')
            self.stdout.write('3. No haya trabajos en cola bloqueando la impresora')
