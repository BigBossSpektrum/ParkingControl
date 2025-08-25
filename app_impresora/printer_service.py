"""
Servicio de impresión para integración con impresoras térmicas Epson
Especialmente configurado para el modelo M244A
"""

import os
import logging
from io import BytesIO
from PIL import Image
from django.conf import settings
from django.utils import timezone
from django.core.cache import cache
from escpos.printer import Usb, Serial, Network
from escpos.exceptions import Error as EscposError
from .models import PrinterConfiguration, PrintJob

logger = logging.getLogger(__name__)

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
    
    def _get_printer_instance(self):
        """Obtiene una instancia de la impresora basada en la configuración"""
        if not self.printer_config:
            raise Exception("No hay impresora configurada")
        
        try:
            if self.printer_config.printer_type == 'USB':
                connection = self.printer_config.connection_string
                
                # Si tenemos un nombre de impresora de Windows, usar Win32Raw directamente
                if connection and ("Receipt" in connection or "EPSON" in connection):
                    logger.info(f"Usando Win32Raw para impresora Windows: {connection}")
                    from escpos.printer import Win32Raw
                    printer = Win32Raw(connection)
                else:
                    # Para impresoras USB directas, intentar encontrar automáticamente
                    logger.info("Intentando conexión USB directa con vendor/product IDs")
                    try:
                        # Intentar con los IDs comunes de Epson
                        printer = Usb(0x04b8, 0x0202)  # Epson M244A común
                    except:
                        try:
                            printer = Usb(0x04b8, 0x0e15)  # Otro ID común de Epson
                        except:
                            raise Exception("No se pudo conectar por USB directo")
                            
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
        """Imprime un ticket con código QR para el cliente"""
        # Recargar configuración antes de cada impresión
        self.reload_printer_config()
        
        if not self.printer_config:
            logger.error("No hay impresora configurada")
            return False
            
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
                
                print_job.status = 'SUCCESS'
                print_job.completed_at = timezone.now()
                print_job.save()
                
                logger.info(f"✅ SIMULACIÓN: Ticket 'impreso' exitosamente para cliente {cliente.id}")
                return True
            
            printer = self._get_printer_instance()
            
            # Configurar la impresora
            printer.set(align='center', font='a', bold=True, double_height=True)
            
            # Encabezado
            printer.text("SISTEMA DE PARKING\n")
            printer.text("=" * self.printer_config.chars_per_line + "\n")
            
            # Información del cliente
            printer.set(align='left', font='a', bold=False, double_height=False)
            printer.text(f"ID: {cliente.id}\n")
            
            if cliente.nombre:
                nombre_truncado = cliente.nombre[:30]  # Truncar si es muy largo
                printer.text(f"Cliente: {nombre_truncado}\n")
            
            if cliente.cedula:
                printer.text(f"Cedula: {cliente.cedula}\n")
                
            printer.text(f"Matricula: {cliente.matricula}\n")
            printer.text(f"Vehiculo: {cliente.get_tipo_vehiculo_display()}\n")
            
            if cliente.fecha_entrada:
                fecha_str = cliente.fecha_entrada.strftime('%d/%m/%Y %H:%M')
                printer.text(f"Entrada: {fecha_str}\n")
            
            printer.text("-" * self.printer_config.chars_per_line + "\n")
            
            # Imprimir código QR si existe
            if cliente.qr_image and os.path.exists(cliente.qr_image.path):
                try:
                    # Cargar y procesar la imagen QR
                    qr_image = Image.open(cliente.qr_image.path)
                    
                    # Redimensionar para impresora térmica (aproximadamente 200px para papel de 80mm)
                    qr_size = min(200, self.printer_config.paper_width * 2)
                    qr_image = qr_image.resize((qr_size, qr_size), Image.Resampling.LANCZOS)
                    
                    # Convertir a modo compatible con la impresora
                    if qr_image.mode != 'RGB':
                        qr_image = qr_image.convert('RGB')
                    
                    # Imprimir la imagen QR
                    printer.image(qr_image, center=True)
                    
                except Exception as e:
                    logger.error(f"Error imprimiendo imagen QR: {e}")
                    printer.text("ERROR: No se pudo imprimir QR\n")
            
            # Pie de página
            printer.text("\n")
            printer.set(align='center', font='a', bold=False)
            printer.text("Conserve este ticket\n")
            printer.text("para la salida\n")
            printer.text("=" * self.printer_config.chars_per_line + "\n")
            
            # Cortar papel
            printer.cut()
            
            # Cerrar conexión
            printer.close()
            
            # Actualizar estado del trabajo
            print_job.status = 'SUCCESS'
            print_job.completed_at = timezone.now()
            print_job.save()
            
            logger.info(f"Ticket impreso exitosamente para cliente {cliente.id}")
            return True
            
        except Exception as e:
            error_msg = f"Error imprimiendo ticket: {str(e)}"
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
            printer.text(f"Fecha: {timezone.now().strftime('%d/%m/%Y %H:%M')}\n")
            
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

# Instancia global del servicio
printer_service = PrinterService()
