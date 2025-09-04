from django.core.management.base import BaseCommand
from django.db.models import Count
from app_page.models import Cliente
from django.utils import timezone

class Command(BaseCommand):
    help = 'Limpia registros duplicados de clientes activos'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Solo muestra los duplicados sin eliminarlos',
        )

    def handle(self, *args, **options):
        self.stdout.write("Buscando clientes duplicados...")
        
        # Buscar clientes activos (sin fecha de salida) con la misma cédula
        clientes_activos = Cliente.objects.filter(fecha_salida__isnull=True)
        
        # Agrupar por cédula y contar
        cedulas_duplicadas = clientes_activos.values('cedula').annotate(
            count=Count('cedula')
        ).filter(count__gt=1)
        
        if not cedulas_duplicadas:
            self.stdout.write(
                self.style.SUCCESS('No se encontraron clientes duplicados activos.')
            )
            return
        
        total_eliminados = 0
        
        for item in cedulas_duplicadas:
            cedula = item['cedula']
            count = item['count']
            
            self.stdout.write(f"\nCédula {cedula} tiene {count} registros activos:")
            
            # Obtener todos los registros para esta cédula
            registros = Cliente.objects.filter(
                cedula=cedula, 
                fecha_salida__isnull=True
            ).order_by('fecha_entrada')
            
            # Mostrar todos los registros
            for i, registro in enumerate(registros):
                self.stdout.write(
                    f"  {i+1}. ID: {registro.id}, "
                    f"Entrada: {registro.fecha_entrada}, "
                    f"Matrícula: {registro.matricula}, "
                    f"Nombre: {registro.get_display_name()}"
                )
            
            if not options['dry_run']:
                # Mantener solo el más reciente (último en entrar)
                registro_mantener = registros.last()
                registros_eliminar = registros.exclude(id=registro_mantener.id)
                
                self.stdout.write(f"  Manteniendo: ID {registro_mantener.id}")
                
                for registro in registros_eliminar:
                    self.stdout.write(
                        self.style.WARNING(f"  Eliminando: ID {registro.id}")
                    )
                    registro.delete()
                    total_eliminados += 1
            else:
                self.stdout.write("  (Modo dry-run: no se eliminarán)")
        
        if options['dry_run']:
            self.stdout.write(
                self.style.WARNING('\nModo dry-run activado. No se eliminó ningún registro.')
            )
            self.stdout.write(
                'Ejecuta el comando sin --dry-run para eliminar los duplicados.'
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(f'\nSe eliminaron {total_eliminados} registros duplicados.')
            )
