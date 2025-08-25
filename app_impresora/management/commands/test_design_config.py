from django.core.management.base import BaseCommand
from django.core.cache import cache
from app_impresora.models import TicketDesignConfiguration
import json

class Command(BaseCommand):
    help = 'Probar configuración de diseño de tickets'

    def add_arguments(self, parser):
        parser.add_argument('--create', action='store_true', help='Crear configuración de prueba')
        parser.add_argument('--show', action='store_true', help='Mostrar configuración actual')
        parser.add_argument('--test', action='store_true', help='Probar configuración')

    def handle(self, *args, **options):
        if options['create']:
            self.create_test_config()
        elif options['show']:
            self.show_current_config()
        elif options['test']:
            self.test_config()
        else:
            self.stdout.write('Uso: --create, --show, o --test')

    def create_test_config(self):
        """Crear una configuración de prueba"""
        try:
            # Crear configuración personalizada
            config = TicketDesignConfiguration.objects.create(
                name="Configuración de Prueba",
                font='arial',
                font_size=14,
                ticket_width=80,
                show_logo=True,
                show_fecha=True,
                show_qr=True,
                show_footer=True,
                header_text="PARKING EMPRESARIAL\nSistema Avanzado de Control",
                footer_text="Mantenga su ticket seguro\nGracias por visitarnos\nwww.parking.com",
                is_active=True
            )
            
            self.stdout.write(
                self.style.SUCCESS(f'✅ Configuración creada: {config.name}')
            )
            self.stdout.write(f'   - Fuente: {config.font}')
            self.stdout.write(f'   - Tamaño: {config.font_size}px')
            self.stdout.write(f'   - Ancho: {config.ticket_width}mm')
            self.stdout.write(f'   - Encabezado: {config.header_text[:30]}...')
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Error creando configuración: {e}')
            )

    def show_current_config(self):
        """Mostrar configuración actual"""
        try:
            # Mostrar desde BD
            active_config = TicketDesignConfiguration.objects.filter(is_active=True).first()
            
            self.stdout.write(self.style.SUCCESS('\n📋 CONFIGURACIÓN ACTIVA EN BD:'))
            if active_config:
                self.stdout.write(f'   Nombre: {active_config.name}')
                self.stdout.write(f'   Fuente: {active_config.font}')
                self.stdout.write(f'   Tamaño: {active_config.font_size}px')
                self.stdout.write(f'   Ancho: {active_config.ticket_width}mm')
                self.stdout.write(f'   Logo: {"Sí" if active_config.show_logo else "No"}')
                self.stdout.write(f'   Fecha: {"Sí" if active_config.show_fecha else "No"}')
                self.stdout.write(f'   QR: {"Sí" if active_config.show_qr else "No"}')
                self.stdout.write(f'   Footer: {"Sí" if active_config.show_footer else "No"}')
                self.stdout.write(f'   Encabezado: {active_config.header_text}')
                self.stdout.write(f'   Pie: {active_config.footer_text}')
            else:
                self.stdout.write('   No hay configuración activa en BD')
            
            # Mostrar desde cache
            cache_config = cache.get('printer_design_config', {})
            self.stdout.write(self.style.WARNING('\n💾 CONFIGURACIÓN EN CACHE:'))
            if cache_config:
                self.stdout.write(f'   {json.dumps(cache_config, indent=4, ensure_ascii=False)}')
            else:
                self.stdout.write('   No hay configuración en cache')
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Error mostrando configuración: {e}')
            )

    def test_config(self):
        """Probar configuración con el servicio de impresión"""
        try:
            from app_impresora.printer_service import printer_service
            
            # Datos de prueba
            cliente_data = {
                'cedula': '12345678',
                'nombre': 'Cliente de Prueba',
                'tipo_vehiculo': 'auto',
                'placa': 'TEST-456'
            }
            
            self.stdout.write(self.style.SUCCESS('\n🖨️  PROBANDO CONFIGURACIÓN:'))
            self.stdout.write('   Enviando ticket de prueba...')
            
            # Probar impresión
            success = printer_service.print_preview_ticket(cliente_data)
            
            if success:
                self.stdout.write(
                    self.style.SUCCESS('✅ Ticket de prueba enviado correctamente')
                )
            else:
                self.stdout.write(
                    self.style.ERROR('❌ Error enviando ticket de prueba')
                )
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Error probando configuración: {e}')
            )
