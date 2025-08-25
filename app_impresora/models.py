from django.db import models
from django.conf import settings
import json

class PrinterConfiguration(models.Model):
    """Configuración de la impresora"""
    PRINTER_TYPES = [
        ('USB', 'USB'),
        ('SERIAL', 'Serial'),
        ('NETWORK', 'Red'),
    ]
    
    name = models.CharField(max_length=100, verbose_name="Nombre de la impresora")
    printer_type = models.CharField(
        max_length=10, 
        choices=PRINTER_TYPES, 
        default='USB',
        verbose_name="Tipo de conexión"
    )
    connection_string = models.CharField(
        max_length=255, 
        verbose_name="Cadena de conexión",
        help_text="Para USB: nombre de la impresora, Para Serial: puerto COM, Para Red: IP:Puerto"
    )
    is_active = models.BooleanField(default=True, verbose_name="Activa")
    model = models.CharField(max_length=50, default="Epson M244A", verbose_name="Modelo")
    
    # Configuraciones específicas de impresión
    paper_width = models.IntegerField(default=80, verbose_name="Ancho del papel (mm)")
    chars_per_line = models.IntegerField(default=48, verbose_name="Caracteres por línea")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Configuración de Impresora"
        verbose_name_plural = "Configuraciones de Impresoras"
    
    def __str__(self):
        return f"{self.name} - {self.model}"


class TicketDesignConfiguration(models.Model):
    """Configuración de diseño para los tickets"""
    FONT_CHOICES = [
        ('courier', 'Courier New'),
        ('arial', 'Arial'),
        ('times', 'Times New Roman'),
    ]
    
    name = models.CharField(max_length=100, verbose_name="Nombre de la configuración", default="Configuración por defecto")
    
    # Configuración de fuente y tamaño
    font = models.CharField(max_length=20, choices=FONT_CHOICES, default='courier', verbose_name="Fuente")
    font_size = models.IntegerField(default=12, verbose_name="Tamaño de fuente")
    ticket_width = models.IntegerField(default=80, verbose_name="Ancho del ticket (mm)")
    
    # Elementos a mostrar
    show_logo = models.BooleanField(default=True, verbose_name="Mostrar logo/encabezado")
    show_fecha = models.BooleanField(default=True, verbose_name="Mostrar fecha y hora")
    show_qr = models.BooleanField(default=True, verbose_name="Mostrar código QR")
    show_footer = models.BooleanField(default=True, verbose_name="Mostrar pie de página")
    
    # Textos personalizables
    header_text = models.TextField(
        default="SISTEMA DE PARKING\nControl de Acceso", 
        verbose_name="Texto del encabezado",
        help_text="Use \\n para saltos de línea"
    )
    footer_text = models.TextField(
        default="Conserve este ticket\nGracias por su visita", 
        verbose_name="Texto del pie de página",
        help_text="Use \\n para saltos de línea"
    )
    
    # Configuración activa
    is_active = models.BooleanField(default=False, verbose_name="Configuración activa")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Configuración de Diseño de Ticket"
        verbose_name_plural = "Configuraciones de Diseño de Tickets"
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        # Solo una configuración puede estar activa a la vez
        if self.is_active:
            TicketDesignConfiguration.objects.filter(is_active=True).update(is_active=False)
        super().save(*args, **kwargs)
    
    def to_dict(self):
        """Convierte la configuración a diccionario para usar en el servicio de impresión"""
        return {
            'font': self.font,
            'fontSize': self.font_size,
            'ticketWidth': self.ticket_width,
            'showLogo': self.show_logo,
            'showFecha': self.show_fecha,
            'showQr': self.show_qr,
            'showFooter': self.show_footer,
            'headerText': self.header_text,
            'footerText': self.footer_text
        }
    
    @classmethod
    def get_active_config(cls):
        """Obtiene la configuración activa o crea una por defecto"""
        active_config = cls.objects.filter(is_active=True).first()
        if not active_config:
            active_config = cls.objects.create(
                name="Configuración por defecto",
                is_active=True
            )
        return active_config


class PrintJob(models.Model):
    """Registro de trabajos de impresión"""
    STATUS_CHOICES = [
        ('PENDING', 'Pendiente'),
        ('PRINTING', 'Imprimiendo'),
        ('SUCCESS', 'Exitoso'),
        ('FAILED', 'Fallido'),
    ]
    
    printer = models.ForeignKey(PrinterConfiguration, on_delete=models.CASCADE)
    client_id = models.IntegerField(verbose_name="ID del Cliente")
    content_type = models.CharField(max_length=20, default='QR_CODE', verbose_name="Tipo de contenido")
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PENDING')
    error_message = models.TextField(blank=True, null=True, verbose_name="Mensaje de error")
    
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(blank=True, null=True)
    
    class Meta:
        verbose_name = "Trabajo de Impresión"
        verbose_name_plural = "Trabajos de Impresión"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Print Job {self.id} - Cliente {self.client_id} - {self.status}"
