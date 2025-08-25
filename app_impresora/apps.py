from django.apps import AppConfig


class AppImpresoraConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'app_impresora'
    
    def ready(self):
        """Configuración inicial cuando la app está lista"""
        # Importar aquí para evitar problemas de importación circular
        from django.core.cache import cache
        
        # Si no hay configuración de simulación, establecer modo real por defecto
        if cache.get('printer_simulation_mode') is None:
            cache.set('printer_simulation_mode', False, 86400)  # Modo real por defecto
