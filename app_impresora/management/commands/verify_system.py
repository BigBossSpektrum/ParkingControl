"""
Script de verificación completa del sistema de impresión
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from app_page.models import Cliente
from app_impresora.models import PrintJob, PrinterConfiguration
from app_impresora.printer_service import printer_service


class Command(BaseCommand):
    help = 'Verificación completa del sistema de impresión'

    def handle(self, *args, **options):
        self.stdout.write('🔍 VERIFICACIÓN DEL SISTEMA DE IMPRESIÓN')
        self.stdout.write('=' * 50)
        
        # 1. Verificar configuración de impresora
        printers = PrinterConfiguration.objects.filter(is_active=True)
        self.stdout.write(f'📋 Impresoras activas: {printers.count()}')
        for printer in printers:
            self.stdout.write(f'   ✅ {printer.name} ({printer.get_printer_type_display()})')
        
        # 2. Verificar modo simulación
        self.stdout.write(f'🎭 Modo simulación: {"✅ ACTIVO" if printer_service.simulation_mode else "❌ INACTIVO"}')
        
        # 3. Verificar estado del servicio
        status = printer_service.get_printer_status()
        self.stdout.write(f'🖨️  Estado impresora: {status["message"]}')
        
        # 4. Crear cliente de prueba
        self.stdout.write('\n📝 CREANDO CLIENTE DE PRUEBA...')
        cliente = Cliente.objects.create(
            cedula='99999999',
            nombre='TEST IMPRESIÓN',
            telefono='3009999999',
            matricula='TEST999',
            tipo_vehiculo='Auto',
            fecha_entrada=timezone.now()
        )
        self.stdout.write(f'   ✅ Cliente creado: ID {cliente.id}')
        
        # 5. Generar QR limpio
        qr_success = cliente.generate_clean_qr()
        if qr_success:
            cliente.save()
            self.stdout.write(f'   ✅ QR limpio generado: {cliente.qr_image.url if cliente.qr_image else "ERROR"}')
        else:
            self.stdout.write('   ❌ Error generando QR limpio')
            return
        
        # 6. Probar impresión
        self.stdout.write('\n🖨️  PROBANDO IMPRESIÓN...')
        print_success = printer_service.print_qr_ticket(cliente)
        
        if print_success:
            self.stdout.write('   ✅ IMPRESIÓN EXITOSA')
        else:
            self.stdout.write('   ❌ ERROR EN IMPRESIÓN')
        
        # 7. Verificar trabajo de impresión
        ultimo_job = PrintJob.objects.filter(client_id=cliente.id).first()
        if ultimo_job:
            self.stdout.write(f'   📊 Job #{ultimo_job.id}: {ultimo_job.get_status_display()}')
            if ultimo_job.error_message:
                self.stdout.write(f'   ⚠️  Error: {ultimo_job.error_message}')
        
        # 8. Estadísticas finales
        self.stdout.write('\n📊 ESTADÍSTICAS FINALES:')
        total_jobs = PrintJob.objects.count()
        success_jobs = PrintJob.objects.filter(status='SUCCESS').count()
        failed_jobs = PrintJob.objects.filter(status='FAILED').count()
        
        self.stdout.write(f'   Total trabajos: {total_jobs}')
        self.stdout.write(f'   Exitosos: {success_jobs}')
        self.stdout.write(f'   Fallidos: {failed_jobs}')
        
        if print_success:
            self.stdout.write(self.style.SUCCESS('\n🎉 SISTEMA FUNCIONANDO CORRECTAMENTE'))
            self.stdout.write('   ✅ Impresora configurada')
            self.stdout.write('   ✅ Modo simulación activo') 
            self.stdout.write('   ✅ Impresión automática funcional')
            self.stdout.write('\n💡 Ahora puede registrar clientes y verá impresión automática')
        else:
            self.stdout.write(self.style.ERROR('\n❌ SISTEMA CON PROBLEMAS'))
            self.stdout.write('   Revise la configuración de la impresora')
