from django.contrib import admin
from django.contrib import admin
from .models import PrinterConfiguration, PrintJob

@admin.register(PrinterConfiguration)
class PrinterConfigurationAdmin(admin.ModelAdmin):
    list_display = ['name', 'model', 'printer_type', 'is_active', 'created_at']
    list_filter = ['printer_type', 'is_active', 'model']
    search_fields = ['name', 'model', 'connection_string']
    list_editable = ['is_active']
    
    fieldsets = (
        ('Información General', {
            'fields': ('name', 'model', 'is_active')
        }),
        ('Configuración de Conexión', {
            'fields': ('printer_type', 'connection_string')
        }),
        ('Configuración de Papel', {
            'fields': ('paper_width', 'chars_per_line')
        }),
    )

@admin.register(PrintJob)
class PrintJobAdmin(admin.ModelAdmin):
    list_display = ['id', 'client_id', 'printer', 'content_type', 'status', 'created_at', 'completed_at']
    list_filter = ['status', 'content_type', 'printer', 'created_at']
    search_fields = ['client_id', 'printer__name']
    readonly_fields = ['created_at', 'completed_at']
    
    fieldsets = (
        ('Información del Trabajo', {
            'fields': ('printer', 'client_id', 'content_type')
        }),
        ('Estado', {
            'fields': ('status', 'error_message')
        }),
        ('Tiempos', {
            'fields': ('created_at', 'completed_at')
        }),
    )
