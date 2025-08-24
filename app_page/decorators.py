from functools import wraps
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.contrib import messages

def get_user_profile(user):
    """Obtiene el perfil del usuario, creándolo si no existe"""
    from .models import Perfil
    try:
        return user.perfil
    except Perfil.DoesNotExist:
        # Crear perfil si no existe (usuario por defecto es empleado)
        return Perfil.objects.create(usuario=user, rol='empleado')

def require_permission(permission_method):
    """Decorador para requerir permisos específicos"""
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def wrapped_view(request, *args, **kwargs):
            perfil = get_user_profile(request.user)
            
            # Verificar si el usuario tiene el permiso requerido
            if not getattr(perfil, permission_method)():
                # Detectar si es una petición AJAX
                is_ajax = (
                    request.headers.get('X-Requested-With') == 'XMLHttpRequest' or
                    request.content_type == 'application/json' or
                    request.GET.get('ajax') == '1' or
                    request.POST.get('ajax') == '1' or
                    'application/json' in request.headers.get('Accept', '')
                )
                
                if is_ajax:
                    return JsonResponse({
                        'success': False,
                        'error': 'No tienes permisos para realizar esta acción.'
                    }, status=403)
                else:
                    messages.error(request, 'No tienes permisos para realizar esta acción.')
                    return redirect('dashboard')
            
            return view_func(request, *args, **kwargs)
        return wrapped_view
    return decorator

# Decoradores específicos para cada permiso
def require_admin(view_func):
    """Decorador que requiere rol de administrador"""
    return require_permission('es_administrador')(view_func)

def require_edit_permission(view_func):
    """Decorador que requiere permiso para editar"""
    return require_permission('puede_editar_cliente')(view_func)

def require_delete_permission(view_func):
    """Decorador que requiere permiso para eliminar"""
    return require_permission('puede_eliminar_cliente')(view_func)

def require_view_list_permission(view_func):
    """Decorador que requiere permiso para ver lista completa"""
    return require_permission('puede_ver_lista_completa')(view_func)
