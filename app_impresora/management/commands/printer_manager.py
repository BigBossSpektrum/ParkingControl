"""
Comando maestro para gestión completa de impresoras
"""

from django.core.management.base import BaseCommand
from django.core.cache import cache
from app_impresora.models import PrinterConfiguration, PrintJob


class Command(BaseCommand):
    help = 'Comando maestro para gestión completa de impresoras'

    def add_arguments(self, parser):
        parser.add_argument(
            '--status',
            action='store_true',
            help='Mostrar estado completo del sistema'
        )
        parser.add_argument(
            '--clean',
            action='store_true',
            help='Limpiar todas las configuraciones y empezar de cero'
        )
        parser.add_argument(
            '--reset',
            action='store_true',
            help='Resetear a configuración por defecto'
        )

    def handle(self, *args, **options):
        if options['status']:
            self.show_complete_status()
            return

        if options['clean']:
            self.clean_all()
            return

        if options['reset']:
            self.reset_to_default()
            return

        # Mostrar menú principal
        self.show_main_menu()

    def show_complete_status(self):
        """Muestra estado completo del sistema"""
        self.stdout.write('🖨️  ESTADO COMPLETO DEL SISTEMA DE IMPRESIÓN')
        self.stdout.write('=' * 60)
        
        # Impresoras configuradas
        printers = PrinterConfiguration.objects.all()
        active_printer = printers.filter(is_active=True).first()
        
        self.stdout.write(f'\n📋 IMPRESORAS CONFIGURADAS: {printers.count()}')
        if printers.exists():
            for printer in printers:
                status = "🟢 ACTIVA" if printer.is_active else "⚪ Inactiva"
                self.stdout.write(f'   • {printer.name} - {status}')
                self.stdout.write(f'     Tipo: {printer.get_printer_type_display()}')
                self.stdout.write(f'     Conexión: {printer.connection_string}')
        else:
            self.stdout.write('   ❌ No hay impresoras configuradas')
        
        # Modo simulación
        simulation_mode = cache.get('printer_simulation_mode', True)
        mode_text = "🎭 SIMULACIÓN" if simulation_mode else "🖨️  REAL"
        self.stdout.write(f'\n🔄 MODO ACTUAL: {mode_text}')
        
        # Trabajos de impresión
        total_jobs = PrintJob.objects.count()
        recent_jobs = PrintJob.objects.order_by('-created_at')[:5]
        success_jobs = PrintJob.objects.filter(status='SUCCESS').count()
        failed_jobs = PrintJob.objects.filter(status='FAILED').count()
        
        self.stdout.write(f'\n📊 ESTADÍSTICAS DE TRABAJOS:')
        self.stdout.write(f'   Total: {total_jobs}')
        self.stdout.write(f'   Exitosos: {success_jobs}')
        self.stdout.write(f'   Fallidos: {failed_jobs}')
        
        if recent_jobs.exists():
            self.stdout.write(f'\n📝 TRABAJOS RECIENTES:')
            for job in recent_jobs:
                status_icon = "✅" if job.status == 'SUCCESS' else "❌" if job.status == 'FAILED' else "⏳"
                self.stdout.write(f'   {status_icon} #{job.id} - Cliente {job.client_id} - {job.created_at.strftime("%d/%m %H:%M")}')
        
        # Comandos disponibles
        self.stdout.write(f'\n💡 COMANDOS ÚTILES:')
        self.stdout.write('   • python manage.py add_simple_printer --auto')
        self.stdout.write('   • python manage.py simulation_mode --disable')
        self.stdout.write('   • python manage.py test_real_print')
        self.stdout.write('   • python manage.py verify_system')

    def clean_all(self):
        """Limpiar todas las configuraciones"""
        self.stdout.write('🧹 LIMPIEZA COMPLETA DEL SISTEMA')
        self.stdout.write('=' * 40)
        
        # Confirmación
        confirm = input('⚠️  ¿Estás seguro? Esto eliminará TODAS las configuraciones (y/n): ')
        if confirm.lower() != 'y':
            self.stdout.write('❌ Operación cancelada')
            return
        
        try:
            # Eliminar trabajos de impresión
            jobs_count = PrintJob.objects.count()
            PrintJob.objects.all().delete()
            self.stdout.write(f'✅ Eliminados {jobs_count} trabajos de impresión')
            
            # Eliminar configuraciones de impresora
            printers_count = PrinterConfiguration.objects.count()
            PrinterConfiguration.objects.all().delete()
            self.stdout.write(f'✅ Eliminadas {printers_count} configuraciones de impresora')
            
            # Limpiar cache
            cache.delete('printer_simulation_mode')
            self.stdout.write('✅ Cache limpiado')
            
            self.stdout.write('\n🎉 LIMPIEZA COMPLETADA')
            self.stdout.write('💡 Usa: python manage.py add_simple_printer --auto para empezar')
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Error durante la limpieza: {e}'))

    def reset_to_default(self):
        """Resetear a configuración por defecto"""
        self.stdout.write('🔄 RESETEO A CONFIGURACIÓN POR DEFECTO')
        self.stdout.write('=' * 50)
        
        try:
            # Limpiar configuraciones existentes
            PrinterConfiguration.objects.all().delete()
            PrintJob.objects.all().delete()
            
            # Establecer modo simulación
            cache.set('printer_simulation_mode', True, 86400)
            
            # Crear impresora por defecto
            default_printer = PrinterConfiguration.objects.create(
                name='Impresora por Defecto',
                model='Epson Thermal',
                printer_type='USB',
                connection_string='default',
                is_active=True
            )
            
            self.stdout.write('✅ Configuración por defecto creada')
            self.stdout.write(f'   • Impresora: {default_printer.name}')
            self.stdout.write('   • Modo: Simulación activado')
            self.stdout.write('')
            self.stdout.write('💡 Para configurar impresora real:')
            self.stdout.write('   python manage.py add_simple_printer --auto')
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Error durante el reseteo: {e}'))

    def show_main_menu(self):
        """Muestra menú principal"""
        self.stdout.write('🖨️  GESTIÓN DE IMPRESORAS - MENÚ PRINCIPAL')
        self.stdout.write('=' * 50)
        self.stdout.write('')
        self.stdout.write('📊 INFORMACIÓN:')
        self.stdout.write('   --status    Mostrar estado completo del sistema')
        self.stdout.write('')
        self.stdout.write('🔧 CONFIGURACIÓN:')
        self.stdout.write('   Ver: python manage.py add_simple_printer')
        self.stdout.write('   Auto: python manage.py add_simple_printer --auto')
        self.stdout.write('')
        self.stdout.write('🧪 PRUEBAS:')
        self.stdout.write('   python manage.py test_real_print')
        self.stdout.write('   python manage.py verify_system')
        self.stdout.write('')
        self.stdout.write('⚙️  MODO:')
        self.stdout.write('   python manage.py simulation_mode --disable')
        self.stdout.write('   python manage.py simulation_mode --enable')
        self.stdout.write('')
        self.stdout.write('🧹 MANTENIMIENTO:')
        self.stdout.write('   --clean     Limpiar todas las configuraciones')
        self.stdout.write('   --reset     Resetear a configuración por defecto')
        self.stdout.write('')
        self.stdout.write('🌐 INTERFAZ WEB:')
        self.stdout.write('   http://localhost:8000/impresora/')
