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
