"""
Servicio de impresión para integración con impresoras térmicas Epson
Especialmente configurado para el modelo M244A
"""

import os
import logging
from io import BytesIO
from PIL import Image
import pytz
from django.conf import settings
from django.utils import timezone
from django.core.cache import cache
from escpos.printer import Usb, Serial, Network
from escpos.exceptions import Error as EscposError
from .models import PrinterConfiguration, PrintJob

logger = logging.getLogger(__name__)

# Valor de connection_string que indica "USB directo por vendor/product id",
# en contraposición al nombre de una impresora instalada en Windows.
USB_DIRECTO = 'USB_DIRECT'


def get_bogota_time(dt=None):
    """Convierte una fecha/hora a la zona horaria de Bogotá"""
    if dt is None:
        dt = timezone.now()
    
    bogota_tz = pytz.timezone('America/Bogota')
    return dt.astimezone(bogota_tz)

class PrinterService:
    """Servicio para manejar la impresión en impresoras térmicas"""
    
    def __init__(self):
        self.active_printer = None
        self.printer_config = None
        # Cargar modo simulación desde cache/configuración
        self.simulation_mode = cache.get('printer_simulation_mode', True)  # Por defecto True para demos
        self._load_active_printer()
        logger.info(f"PrinterService inicializado - Modo simulación: {self.simulation_mode}")
    
    def _load_active_printer(self):
        """Carga la configuración de la impresora activa"""
        try:
            self.printer_config = PrinterConfiguration.objects.filter(is_active=True).first()
            if not self.printer_config:
                logger.warning("No hay impresoras configuradas como activas")
                return False
                
            logger.info(f"Impresora activa cargada: {self.printer_config.name}")
            return True
        except Exception as e:
            logger.error(f"Error cargando configuración de impresora: {e}")
            return False
    
    def reload_printer_config(self):
        """Recarga la configuración de la impresora"""
        return self._load_active_printer()
    
    def enable_simulation_mode(self, enable=True):
        """Habilita o deshabilita el modo simulación"""
        self.simulation_mode = enable
        # Guardar en cache para persistir entre reinicios
        cache.set('printer_simulation_mode', enable, 86400)  # 24 horas
        if enable:
            logger.info("Modo simulación HABILITADO - Las impresiones se simularán")
        else:
            logger.info("Modo simulación DESHABILITADO - Se intentará imprimir en hardware real")
    
    def reload_simulation_mode(self):
        """Recarga el modo simulación desde el cache"""
        self.simulation_mode = cache.get('printer_simulation_mode', True)
        logger.info(f"Modo simulación recargado: {self.simulation_mode}")
        return self.simulation_mode
    
    def _instancia_win32(self, nombre):
        """Conecta con una impresora instalada en Windows por su nombre exacto."""
        try:
            from escpos.printer import Win32Raw
        except ImportError:
            raise Exception(
                "La conexión por nombre de impresora de Windows solo está "
                "disponible en Windows."
            )

        try:
            return Win32Raw(nombre)
        except Exception as e:
            raise Exception(
                f"No se pudo abrir la impresora de Windows '{nombre}': {e}. "
                f"Comprueba que el nombre coincide exactamente con el de "
                f"Panel de Control > Dispositivos e Impresoras."
            )

    def _instancia_usb_directa(self):
        """Conecta por USB con los vendor/product id habituales de Epson."""
        ultimo_error = None
        for vendor, product in ((0x04b8, 0x0202), (0x04b8, 0x0e15)):
            try:
                return Usb(vendor, product)
            except Exception as e:
                ultimo_error = e

        if 'no backend available' in str(ultimo_error).lower():
            raise Exception(
                "No se pudo conectar por USB directo: falta el backend libusb. "
                "Edita la impresora y elige su nombre de Windows como cadena de "
                "conexión en lugar de USB directo."
            )

        raise Exception(f"No se pudo conectar por USB directo: {ultimo_error}")

    def _get_printer_instance(self):
        """Obtiene una instancia de la impresora basada en la configuración"""
        if not self.printer_config:
            raise Exception("No hay impresora configurada")
        
        try:
            if self.printer_config.printer_type == 'USB':
                connection = (self.printer_config.connection_string or '').strip()

                # 'auto' es un valor heredado del formulario antiguo de alta, que
                # enviaba esa cadena en lugar del nombre real de la impresora.
                if connection and connection not in (USB_DIRECTO, 'auto'):
                    # La cadena de conexión es el nombre de la impresora en Windows.
                    logger.info(f"Usando Win32Raw para impresora Windows: {connection}")
                    printer = self._instancia_win32(connection)
                else:
                    # USB directo por vendor/product id: necesita el backend libusb.
                    logger.info("Intentando conexión USB directa con vendor/product IDs")
                    printer = self._instancia_usb_directa()

            elif self.printer_config.printer_type == 'SERIAL':
                port = self.printer_config.connection_string
                printer = Serial(port, baudrate=9600, timeout=1)
                
            elif self.printer_config.printer_type == 'NETWORK':
                host_port = self.printer_config.connection_string.split(':')
                host = host_port[0]
                port = int(host_port[1]) if len(host_port) > 1 else 9100
                printer = Network(host, port)
                
            else:
                raise Exception(f"Tipo de impresora no soportado: {self.printer_config.printer_type}")
                
            return printer
            
        except Exception as e:
            logger.error(f"Error conectando con la impresora: {e}")
            raise
    
    def print_qr_ticket(self, cliente):
        """Imprime un ticket con código QR para el cliente usando configuración personalizada"""
        # Recargar configuración antes de cada impresión
        self.reload_printer_config()
        
        if not self.printer_config:
            logger.error("No hay impresora configurada")
            return False
        
        # Cargar configuración de diseño personalizada desde BD o cache
        design_config = self._load_design_config()
        logger.info(f"Usando configuración de diseño: {design_config}")
            
        # Crear registro de trabajo de impresión
        print_job = PrintJob.objects.create(
            printer=self.printer_config,
            client_id=cliente.id,
            content_type='QR_CODE',
            status='PENDING'
        )
        
        try:
            print_job.status = 'PRINTING'
            print_job.save()
            
            # Modo simulación para pruebas sin hardware
            if self.simulation_mode:
                logger.info(f"🎭 SIMULACIÓN: Imprimiendo ticket para cliente {cliente.id}")
                logger.info(f"   - Datos: {cliente.get_display_name()} - {cliente.matricula}")
                logger.info(f"   - QR: {cliente.qr_image.url if cliente.qr_image else 'No disponible'}")
                logger.info(f"   - Impresora: {self.printer_config.name}")
                logger.info(f"   - Configuración de diseño aplicada: {design_config}")
                
                print_job.status = 'SUCCESS'
                print_job.completed_at = timezone.now()
                print_job.save()
                
                logger.info(f"✅ SIMULACIÓN: Ticket 'impreso' exitosamente para cliente {cliente.id}")
                return True

            # Imprimir con configuración personalizada
            return self._print_with_custom_design(cliente, print_job, design_config)
            
        except Exception as e:
            error_msg = f"Error imprimiendo ticket: {str(e)}"
            logger.error(error_msg)
            
            print_job.status = 'FAILED'
            print_job.error_message = error_msg
            print_job.completed_at = timezone.now()
            print_job.save()
            
            return False

    def _load_design_config(self):
        """Carga la configuración de diseño desde BD o cache"""
        try:
            from .models import TicketDesignConfiguration
            
            # Intentar cargar desde la base de datos
            active_config = TicketDesignConfiguration.objects.filter(is_active=True).first()
            
            if active_config:
                config = active_config.to_dict()
                logger.info(f"Configuración cargada desde BD: {active_config.name}")
                return config
            else:
                # Fallback al cache
                config = cache.get('printer_design_config', {})
                if config:
                    logger.info("Configuración cargada desde cache")
                    return config
                else:
                    logger.info("Usando configuración por defecto")
                    return {}
                    
        except Exception as e:
            logger.warning(f"Error cargando configuración de diseño: {e}, usando por defecto")
            return {}

    def _print_with_custom_design(self, cliente, print_job, design_config=None):
        """Imprime el ticket aplicando la configuración de diseño personalizada"""
        if not design_config:
            design_config = {}
            
        # Configuración por defecto
        default_config = {
            'font': 'courier',
            'fontSize': 12,
            'ticketWidth': 80,
            'showLogo': True,
            'showFecha': True,
            'showQr': True,
            'showFooter': True,
            'headerText': 'SISTEMA DE PARKING\nControl de Acceso',
            'footerText': 'Conserve este ticket\nGracias por su visita'
        }
        
        # Combinar configuración por defecto con la personalizada
        config = {**default_config, **design_config}
        
        try:
            printer = self._get_printer_instance()
            
            # Configurar codificación
            printer.charcode('CP437')
            
            # Encabezado personalizado
            if config.get('showLogo', True):
                printer.set(align='center', bold=True, double_width=True, double_height=True)
                header_lines = config.get('headerText', 'SISTEMA DE PARKING').split('\n')
                for line in header_lines:
                    printer.text(line + '\n')
                    
                printer.text('=' * 32 + '\n')
                printer.text('\n')
            
            # Información del cliente con formato personalizado
            printer.set(align='left', bold=False, double_width=False, double_height=False)
            
            if config.get('showFecha', True):
                fecha_actual = get_bogota_time()
                printer.text(f"Fecha: {fecha_actual.strftime('%d/%m/%Y %H:%M')}\n")
            
            printer.text(f"ID: {cliente.id}\n")
            printer.text(f"Cedula: {cliente.cedula or 'N/A'}\n")
            printer.text(f"Nombre: {cliente.nombre or 'N/A'}\n")
            
            # Información de ubicación (torre y apartamento)
            if cliente.torre or cliente.apartamento:
                if cliente.torre and cliente.apartamento:
                    printer.text(f"Ubicacion: Torre {cliente.torre} - Apt {cliente.apartamento}\n")
                elif cliente.torre:
                    printer.text(f"Torre: {cliente.torre}\n")
                elif cliente.apartamento:
                    printer.text(f"Apartamento: {cliente.apartamento}\n")
            
            printer.text(f"Vehiculo: {cliente.get_tipo_vehiculo_display()}\n")
            printer.text(f"Matricula: {cliente.matricula}\n")
            
            if cliente.fecha_entrada:
                fecha_entrada_bogota = get_bogota_time(cliente.fecha_entrada)
                fecha_entrada = fecha_entrada_bogota.strftime('%d/%m/%Y %H:%M')
                printer.text(f"Entrada: {fecha_entrada}\n")
            
            printer.text('\n')
            
            # Código QR personalizado
            if config.get('showQr', True) and cliente.qr_image:
                try:
                    if os.path.exists(cliente.qr_image.path):
                        qr_image = Image.open(cliente.qr_image.path)
                        
                        # Redimensionar según la configuración
                        qr_size = min(200, int(config.get('ticketWidth', 80)) * 2)
                        qr_image = qr_image.resize((qr_size, qr_size), Image.Resampling.LANCZOS)
                        
                        if qr_image.mode != 'RGB':
                            qr_image = qr_image.convert('RGB')
                        
                        printer.set(align='center')
                        printer.image(qr_image, center=True)
                        printer.text('\n')
                        
                except Exception as qr_error:
                    logger.warning(f"Error procesando QR: {qr_error}")
                    # En caso de error, no imprimir nada para mantener el QR limpio
                    pass
            
            # Pie de página personalizado
            if config.get('showFooter', True):
                printer.set(align='center', bold=False)
                printer.text('-' * 32 + '\n')
                footer_lines = config.get('footerText', 'Gracias por su visita').split('\n')
                for line in footer_lines:
                    printer.text(line + '\n')
            
            # Cortar papel
            printer.text('\n' * 3)
            printer.cut()
            
            printer.close()
            
            # Actualizar estado del trabajo
            print_job.status = 'SUCCESS'
            print_job.completed_at = timezone.now()
            print_job.save()
            
            logger.info(f"Ticket impreso exitosamente para cliente {cliente.id} con configuración personalizada")
            return True
            
        except Exception as e:
            error_msg = f"Error en _print_with_custom_design: {str(e)}"
            logger.error(error_msg)
            
            print_job.status = 'FAILED'
            print_job.error_message = error_msg
            print_job.completed_at = timezone.now()
            print_job.save()
            
            return False

    def test_printer(self):
        """Prueba la conexión y funcionalidad de la impresora"""
        if not self.printer_config:
            return False, "No hay impresora configurada"
            
        try:
            printer = self._get_printer_instance()
            
            # Imprimir página de prueba
            printer.set(align='center', font='a', bold=True, double_height=True)
            printer.text("PRUEBA DE IMPRESORA\n")
            printer.text("=" * self.printer_config.chars_per_line + "\n")
            
            printer.set(align='left', font='a', bold=False, double_height=False)
            printer.text(f"Modelo: {self.printer_config.model}\n")
            printer.text(f"Conexion: {self.printer_config.printer_type}\n")
            fecha_bogota = get_bogota_time()
            printer.text(f"Fecha: {fecha_bogota.strftime('%d/%m/%Y %H:%M')}\n")
            
            printer.text("-" * self.printer_config.chars_per_line + "\n")
            printer.text("Si puede leer este texto,\n")
            printer.text("la impresora funciona correctamente.\n")
            printer.text("=" * self.printer_config.chars_per_line + "\n")
            
            printer.cut()
            printer.close()
            
            logger.info("Prueba de impresora exitosa")
            return True, "Impresora funcionando correctamente"
            
        except Exception as e:
            error_msg = f"Error en prueba de impresora: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
    
    def get_printer_status(self):
        """Obtiene el estado actual de la impresora"""
        if not self.printer_config:
            return {
                'configured': False,
                'connected': False,
                'message': 'No hay impresora configurada'
            }
        
        try:
            printer = self._get_printer_instance()
            printer.close()  # Solo probamos la conexión
            
            return {
                'configured': True,
                'connected': True,
                'printer_name': self.printer_config.name,
                'printer_model': self.printer_config.model,
                'connection_type': self.printer_config.printer_type,
                'message': 'Impresora conectada y lista'
            }
            
        except Exception as e:
            return {
                'configured': True,
                'connected': False,
                'printer_name': self.printer_config.name,
                'printer_model': self.printer_config.model,
                'connection_type': self.printer_config.printer_type,
                'message': f'Error de conexión: {str(e)}'
            }

    def print_preview_ticket(self, cliente_data, design_config=None):
        """
        Imprime un ticket de previsualización con datos personalizados
        
        Args:
            cliente_data (dict): Datos del cliente para el ticket
            design_config (dict): Configuración de diseño personalizada
        """
        try:
            # Verificar modo simulación
            simulation_mode = cache.get('printer_simulation_mode', False)
            
            if simulation_mode:
                logger.info("=== MODO SIMULACIÓN ACTIVO ===")
                logger.info(f"Simulando impresión de ticket de previsualización para: {cliente_data.get('nombre', 'Cliente')}")
                logger.info(f"Configuración de diseño aplicada: {design_config}")
                return True
            
            # Cargar configuración de diseño desde BD si no se proporciona
            if not design_config:
                design_config = self._load_design_config()
                
            # Configuración por defecto si no hay ninguna
            default_config = {
                'font': 'courier',
                'fontSize': 12,
                'ticketWidth': 80,
                'showLogo': True,
                'showFecha': True,
                'showQr': True,
                'showFooter': True,
                'headerText': 'SISTEMA DE PARKING\nControl de Acceso',
                'footerText': 'Conserve este ticket\nGracias por su visita'
            }
            
            # Combinar configuración por defecto con la personalizada
            config = {**default_config, **design_config}
            
            logger.info(f"Imprimiendo ticket de previsualización con configuración: {config}")
            
            # Verificar configuración de impresora
            if not self.printer_config:
                logger.error("No hay impresora configurada")
                return False
                
            printer = self._get_printer_instance()
            
            # Configurar codificación
            printer.charcode('CP437')
            
            # Encabezado personalizado
            if config.get('showLogo', True):
                printer.set(align='center', bold=True, double_width=True, double_height=True)
                header_lines = config.get('headerText', 'SISTEMA DE PARKING').split('\n')
                for line in header_lines:
                    printer.text(line + '\n')
                    
                printer.text('=' * 32 + '\n')
                printer.text('\n')
            
            # Información del cliente con formato personalizado
            printer.set(align='left', bold=False)
            
            if config.get('showFecha', True):
                fecha_actual = get_bogota_time()
                printer.text(f"Fecha: {fecha_actual.strftime('%d/%m/%Y %H:%M')}\n")
                
            printer.text(f"Cedula: {cliente_data.get('cedula', 'N/A')}\n")
            printer.text(f"Nombre: {cliente_data.get('nombre', 'N/A')}\n")
            
            # Información de ubicación (torre y apartamento)
            torre = cliente_data.get('torre', '')
            apartamento = cliente_data.get('apartamento', '')
            if torre or apartamento:
                if torre and apartamento:
                    printer.text(f"Ubicacion: Torre {torre} - Apt {apartamento}\n")
                elif torre:
                    printer.text(f"Torre: {torre}\n")
                elif apartamento:
                    printer.text(f"Apartamento: {apartamento}\n")
            
            printer.text(f"Vehiculo: {cliente_data.get('tipo_vehiculo', 'auto').upper()}\n")
            printer.text(f"Placa: {cliente_data.get('placa', 'N/A')}\n")
            
            printer.text('\n')
            
            # Código QR personalizado
            if config.get('showQr', True):
                qr_data = f"PREVIEW_{cliente_data.get('cedula', '000000')}_{fecha_actual.strftime('%Y%m%d%H%M')}"
                printer.set(align='center')
                try:
                    printer.qr(qr_data, size=6)
                except Exception as qr_error:
                    logger.warning(f"Error generando QR: {qr_error}")
                    # En caso de error, no imprimir nada para mantener el QR limpio
                    pass
                
                printer.text('\n')
            
            # Pie de página personalizado
            if config.get('showFooter', True):
                printer.set(align='center', bold=False)
                printer.text('-' * 32 + '\n')
                footer_lines = config.get('footerText', 'Gracias por su visita').split('\n')
                for line in footer_lines:
                    printer.text(line + '\n')
                    
                printer.text('** TICKET DE PREVISUALIZACIÓN **\n')
            
            # Cortar papel
            printer.text('\n' * 3)
            printer.cut()
            
            printer.close()
            
            logger.info(f"Ticket de previsualización impreso exitosamente para {cliente_data.get('nombre', 'Cliente')}")
            return True
            
        except Exception as e:
            error_msg = f"Error imprimiendo ticket de previsualización: {str(e)}"
            logger.error(error_msg)
            return False

# Instancia global del servicio
printer_service = PrinterService()
