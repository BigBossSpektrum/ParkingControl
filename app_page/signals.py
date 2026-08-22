from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import Perfil

@receiver(post_save, sender=User)
def crear_perfil_usuario(sender, instance, created, **kwargs):
    """Crear un perfil automáticamente cuando se crea un usuario"""
    if created:
        Perfil.objects.create(usuario=instance)

# Nota: aqui existia un segundo receptor que hacia instance.perfil.save() en cada
# User.save(). Al crear el usuario, Django deja el Perfil recien creado cacheado en
# instance._state.fields_cache, asi que ese receptor reescribia esa copia obsoleta y
# revertia cualquier cambio de rol posterior (por ejemplo, al actualizar last_login en
# el login siguiente). Se elimino: el perfil se guarda explicitamente donde se edita, y
# get_user_profile() en decorators.py ya crea el perfil si algun usuario antiguo no lo tiene.
