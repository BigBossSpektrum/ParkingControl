from .decorators import get_user_profile
from .models import Cliente, Visitante
from django.utils import timezone

def user_profile_context(request):
    """Context processor que agrega el perfil del usuario y estadísticas a todos los templates"""
    if request.user.is_authenticated:
        perfil = get_user_profile(request.user)
        
        # Estadísticas básicas para la barra de navegación
        # localdate() da la fecha en TIME_ZONE (America/Bogota); now().date()
        # daria la fecha UTC y a partir de las 19:00 locales no coincidirian.
        hoy = timezone.localdate()
        
        clientes_hoy = Cliente.objects.filter(
            fecha_entrada__date=hoy
        ).count()
        
        clientes_en_parking = Cliente.objects.filter(
            fecha_salida__isnull=True
        ).count()
        
        visitantes_hoy = Visitante.objects.filter(
            fecha_registro__date=hoy
        ).count()
        
        return {
            'perfil': perfil,
            'clientes_hoy': clientes_hoy,
            'clientes_en_parking': clientes_en_parking,
            'visitantes_hoy': visitantes_hoy,
        }
    return {}
