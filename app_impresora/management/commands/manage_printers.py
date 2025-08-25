"""
Comando para gestionar impresoras - eliminar, activar, desactivar
"""

from django.core.management.base import BaseCommand, CommandError
from app_impresora.models import PrinterConfiguration, PrintJob


class Command(BaseCommand):
    help = 'Gestiona impresoras configuradas'

    def add_arguments(self, parser):
        parser.add_argument(
            '--delete',
            type=int,
            help='Eliminar impresora por ID'
        )
        parser.add_argument(
            '--delete-name',
            type=str,
            help='Eliminar impresora por nombre'
        )
        parser.add_argument(
            '--activate',
            type=int,
            help='Activar impresora por ID'
        )
        parser.add_argument(
            '--deactivate',
            type=int,
            help='Desactivar impresora por ID'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Forzar eliminación (elimina trabajos asociados)'
        )
        parser.add_argument(
            '--clean-jobs',
            action='store_true',
            help='Limpiar trabajos de impresión antiguos'
        )

    def handle(self, *args, **options):
        
        # Eliminar por ID
        if options['delete']:
            self.delete_printer_by_id(options['delete'], options['force'])
            return
        
        # Eliminar por nombre
        if options['delete_name']:
            self.delete_printer_by_name(options['delete_name'], options['force'])
            return
        
        # Activar impresora
        if options['activate']:
            self.activate_printer(options['activate'])
            return
        
        # Desactivar impresora
        if options['deactivate']:
            self.deactivate_printer(options['deactivate'])
            return
        
        # Limpiar trabajos
        if options['clean_jobs']:
            self.clean_old_jobs()
            return
        
        # Mostrar ayuda si no se especifica acción
        self.show_help()

    def delete_printer_by_id(self, printer_id, force=False):
        try:
            printer = PrinterConfiguration.objects.get(id=printer_id)
            self.delete_printer(printer, force)
        except PrinterConfiguration.DoesNotExist:
            raise CommandError(f'Impresora con ID {printer_id} no encontrada')

    def delete_printer_by_name(self, printer_name, force=False):
        try:
            printer = PrinterConfiguration.objects.get(name__icontains=printer_name)
            self.delete_printer(printer, force)
        except PrinterConfiguration.DoesNotExist:
            raise CommandError(f'Impresora con nombre "{printer_name}" no encontrada')
        except PrinterConfiguration.MultipleObjectsReturned:
            printers = PrinterConfiguration.objects.filter(name__icontains=printer_name)
            self.stdout.write(self.style.ERROR('Múltiples impresoras encontradas:'))
            for p in printers:
                self.stdout.write(f'  ID {p.id}: {p.name}')
            raise CommandError('Especifique un nombre más específico o use --delete con ID')

    def delete_printer(self, printer, force=False):
        # Verificar si es la única activa
        active_count = PrinterConfiguration.objects.filter(is_active=True).count()
        if printer.is_active and active_count == 1:
            raise CommandError('No puede eliminar la única impresora activa')
        
        # Verificar trabajos asociados
        jobs_count = PrintJob.objects.filter(printer=printer).count()
        
        if jobs_count > 0 and not force:
            self.stdout.write(self.style.WARNING(
                f'La impresora "{printer.name}" tiene {jobs_count} trabajos asociados.'
            ))
            self.stdout.write('Use --force para eliminar también los trabajos.')
            return
        
        if force and jobs_count > 0:
            PrintJob.objects.filter(printer=printer).delete()
            self.stdout.write(f'✅ Eliminados {jobs_count} trabajos asociados')
        
        printer_name = printer.name
        printer.delete()
        self.stdout.write(self.style.SUCCESS(f'✅ Impresora "{printer_name}" eliminada correctamente'))

    def activate_printer(self, printer_id):
        try:
            printer = PrinterConfiguration.objects.get(id=printer_id)
            
            # Desactivar todas las demás
            PrinterConfiguration.objects.update(is_active=False)
            
            # Activar la seleccionada
            printer.is_active = True
            printer.save()
            
            self.stdout.write(self.style.SUCCESS(f'✅ Impresora "{printer.name}" activada'))
            
        except PrinterConfiguration.DoesNotExist:
            raise CommandError(f'Impresora con ID {printer_id} no encontrada')

    def deactivate_printer(self, printer_id):
        try:
            printer = PrinterConfiguration.objects.get(id=printer_id)
            
            if not printer.is_active:
                self.stdout.write(self.style.WARNING(f'La impresora "{printer.name}" ya está inactiva'))
                return
            
            # Verificar si es la única activa
            active_count = PrinterConfiguration.objects.filter(is_active=True).count()
            if active_count == 1:
                self.stdout.write(self.style.WARNING(
                    'No se puede desactivar la única impresora activa. Active otra primero.'
                ))
                return
            
            printer.is_active = False
            printer.save()
            
            self.stdout.write(self.style.SUCCESS(f'✅ Impresora "{printer.name}" desactivada'))
            
        except PrinterConfiguration.DoesNotExist:
            raise CommandError(f'Impresora con ID {printer_id} no encontrada')

    def clean_old_jobs(self):
        from django.utils import timezone
        from datetime import timedelta
        
        # Eliminar trabajos más antiguos de 30 días
        cutoff_date = timezone.now() - timedelta(days=30)
        old_jobs = PrintJob.objects.filter(created_at__lt=cutoff_date)
        count = old_jobs.count()
        
        if count == 0:
            self.stdout.write('No hay trabajos antiguos para eliminar')
            return
        
        old_jobs.delete()
        self.stdout.write(self.style.SUCCESS(f'✅ Eliminados {count} trabajos antiguos'))

    def show_help(self):
        self.stdout.write(self.style.WARNING('Comandos disponibles:'))
        self.stdout.write('')
        self.stdout.write('Eliminar impresoras:')
        self.stdout.write('  python manage.py manage_printers --delete 1')
        self.stdout.write('  python manage.py manage_printers --delete-name "Principal"')
        self.stdout.write('  python manage.py manage_printers --delete 1 --force')
        self.stdout.write('')
        self.stdout.write('Activar/Desactivar:')
        self.stdout.write('  python manage.py manage_printers --activate 2')
        self.stdout.write('  python manage.py manage_printers --deactivate 1')
        self.stdout.write('')
        self.stdout.write('Mantenimiento:')
        self.stdout.write('  python manage.py manage_printers --clean-jobs')
        self.stdout.write('')
        self.stdout.write('Ver impresoras:')
        self.stdout.write('  python manage.py setup_printer --list')
