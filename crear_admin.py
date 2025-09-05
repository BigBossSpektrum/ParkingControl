#!/usr/bin/env python
"""
Script para crear un usuario administrador
"""
import os
import sys
import django

# Configurar Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'parking_site.settings')
django.setup()

from django.contrib.auth.models import User
from app_page.models import Perfil

def crear_admin():
    # Obtener el primer usuario
    user = User.objects.first()
    if not user:
        print("No hay usuarios en el sistema")
        return
    
    print(f"Usuario encontrado: {user.username}")
    
    # Crear o actualizar perfil a administrador
    perfil, created = Perfil.objects.get_or_create(
        usuario=user,
        defaults={'rol': 'administrador'}
    )
    
    if not created and perfil.rol != 'administrador':
        perfil.rol = 'administrador'
        perfil.save()
        print(f"Perfil actualizado a: {perfil.rol}")
    elif created:
        print(f"Perfil creado como: {perfil.rol}")
    else:
        print(f"Perfil ya era: {perfil.rol}")
    
    print(f"Es administrador: {perfil.es_administrador()}")

if __name__ == "__main__":
    crear_admin()
