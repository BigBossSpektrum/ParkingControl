from .decorators import get_user_profile
from .models import Cliente
from django.utils import timezone

def user_profile_context(request):
    """Context processor que agrega el perfil del usuario y estadísticas a todos los templates"""
    if request.user.is_authenticated:
        perfil = get_user_profile(request.user)
        
        # Estadísticas básicas para la barra de navegación
        clientes_hoy = Cliente.objects.filter(
            fecha_entrada__date=timezone.now().date()
        ).count()
        
        clientes_en_parking = Cliente.objects.filter(
            fecha_salida__isnull=True
        ).count()
        
        return {
            'perfil': perfil,
            'clientes_hoy': clientes_hoy,
            'clientes_en_parking': clientes_en_parking,
        }
    return {}
