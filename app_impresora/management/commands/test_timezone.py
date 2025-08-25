from django.core.management.base import BaseCommand
from django.utils import timezone
from django.conf import settings
import pytz

class Command(BaseCommand):
    help = 'Prueba la configuración de zona horaria'

    def handle(self, *args, **options):
        self.stdout.write('=== CONFIGURACION DE ZONA HORARIA ===')
        self.stdout.write(f'Zona horaria: {settings.TIME_ZONE}')
        self.stdout.write(f'Idioma: {settings.LANGUAGE_CODE}')
        self.stdout.write(f'USE_TZ: {settings.USE_TZ}')
        self.stdout.write('')
        
        # Mostrar hora actual
        now_utc = timezone.now()
        
        # Convertir a zona horaria de Bogotá
        bogota_tz = pytz.timezone('America/Bogota')
        now_bogota = now_utc.astimezone(bogota_tz)
        
        self.stdout.write(f'Hora UTC: {now_utc}')
        self.stdout.write(f'Hora Bogota: {now_bogota}')
        self.stdout.write(f'Formato ticket: {now_bogota.strftime("%d/%m/%Y %H:%M")}')
        self.stdout.write('')
        
        # Crear un cliente de prueba para ver las fechas
        from app_page.models import Cliente
        cliente_test = Cliente(
            cedula='TEST',
            nombre='Prueba Timezone',
            matricula='TIME-TEST',
            fecha_entrada=timezone.now()
        )
        
        self.stdout.write('=== FORMATO EN TICKET ===')
        fecha_entrada_bogota = cliente_test.fecha_entrada.astimezone(bogota_tz)
        fecha_entrada_formatted = fecha_entrada_bogota.strftime('%d/%m/%Y %H:%M')
        self.stdout.write(f'Fecha entrada (Bogota): {fecha_entrada_formatted}')
        
        self.stdout.write(self.style.SUCCESS('Configuracion de zona horaria verificada'))
