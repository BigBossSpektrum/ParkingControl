"""Crea la base de datos de demostracion para las capturas del manual.

Arranca de cero cada vez: borra demo.sqlite3, migra y siembra registros
evidentemente ficticios. Asi las diapositivas nunca muestran placas, cedulas ni
fotos de clientes reales.

Uso:  env\\Scripts\\python docs\\presentacion\\sembrar_demo.py
"""

import os
import shutil
import sys
from datetime import timedelta
from io import BytesIO
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]
DEMO_DIR = BASE_DIR / 'docs' / 'presentacion'


def preparar_django():
    """Deja Django listo apuntando a la base de demo, no a la real."""
    sys.path.insert(0, str(BASE_DIR))
    os.environ['DJANGO_SETTINGS_MODULE'] = 'parking_site.settings_demo'
    import django
    django.setup()


def _imagen_ficticia(texto, tamano=(640, 480)):
    """Foto de relleno: un rectangulo gris con un rotulo que dice que es demo."""
    from PIL import Image, ImageDraw

    img = Image.new('RGB', tamano, (222, 226, 230))
    draw = ImageDraw.Draw(img)
    draw.rectangle([8, 8, tamano[0] - 8, tamano[1] - 8], outline=(140, 146, 152), width=3)
    caja = draw.textbbox((0, 0), texto)
    draw.text(
        ((tamano[0] - (caja[2] - caja[0])) // 2, (tamano[1] - (caja[3] - caja[1])) // 2),
        texto,
        fill=(90, 97, 105),
    )
    buffer = BytesIO()
    img.save(buffer, format='JPEG')
    buffer.seek(0)
    return buffer


def sembrar():
    from django.contrib.auth.models import User
    from django.core.files.base import ContentFile
    from django.utils import timezone

    from app_page.models import Cliente, Costo, Perfil, TarifaPlena, Visitante

    ahora = timezone.now()

    # --- Usuarios -----------------------------------------------------------
    # El signal post_save de User ya crea el Perfil, por eso aqui se actualiza
    # el rol en lugar de crearlo.
    admin = User.objects.create_superuser(
        username='demo', email='demo@parkingcontrol.local', password='demo12345',
        first_name='Ana', last_name='Torres',
    )
    Perfil.objects.filter(usuario=admin).update(rol='administrador')

    for username, nombre, apellido in [
        ('portero.dia', 'Carlos', 'Ramirez'),
        ('portero.noche', 'Luisa', 'Marin'),
    ]:
        empleado = User.objects.create_user(
            username=username, password='demo12345',
            first_name=nombre, last_name=apellido,
        )
        Perfil.objects.filter(usuario=empleado).update(rol='empleado')

    # --- Tarifas ------------------------------------------------------------
    costos = Costo.get_costos_actuales()
    costos.costo_auto = 100
    costos.costo_moto = 60
    costos.costo_otro = 150
    costos.actualizado_por = admin
    costos.save()

    tarifa = TarifaPlena.get_tarifa_actual()
    tarifa.activa = False
    tarifa.costo_fijo_auto = 8000
    tarifa.costo_fijo_moto = 5000
    tarifa.costo_fijo_otro = 12000
    tarifa.actualizado_por = admin
    tarifa.save()

    # --- Vehiculos todavia dentro (uno por tipo) ----------------------------
    dentro = [
        ('DEM01A', 'Auto', '1020304050', 'Mariana Ospina', '3001112233', '3', '302', 95),
        ('DEM02B', 'Moto', '1020304051', 'Jorge Betancur', '3002223344', '1', '104', 40),
        ('DEM03C', 'Otro', '1020304052', 'Sara Villegas', '3003334455', '5', '501', 15),
    ]
    for matricula, tipo, cedula, nombre, telefono, torre, apto, minutos in dentro:
        cliente = Cliente.objects.create(
            matricula=matricula, tipo_vehiculo=tipo, cedula=cedula, nombre=nombre,
            telefono=telefono, torre=torre, apartamento=apto,
            fecha_entrada=ahora - timedelta(minutes=minutos),
        )
        cliente.generate_clean_qr()
        cliente.save()

    # --- Vehiculos ya cobrados: dan cifras al resumen de recaudacion --------
    cerrados = [
        ('DEM10D', 'Auto', '1020304060', 'Pedro Gaviria', '3004445566', '2', '201', 240, 130),
        ('DEM11E', 'Moto', '1020304061', 'Camila Restrepo', '3005556677', '4', '405', 300, 180),
        ('DEM12F', 'Auto', '1020304062', 'Andres Zapata', '3006667788', '1', '108', 200, 90),
        ('DEM13G', 'Otro', '1020304063', 'Diana Cardona', '3007778899', '3', '310', 150, 45),
    ]
    for matricula, tipo, cedula, nombre, telefono, torre, apto, entro_hace, salio_hace in cerrados:
        cliente = Cliente.objects.create(
            matricula=matricula, tipo_vehiculo=tipo, cedula=cedula, nombre=nombre,
            telefono=telefono, torre=torre, apartamento=apto,
            fecha_entrada=ahora - timedelta(minutes=entro_hace),
            fecha_salida=ahora - timedelta(minutes=salio_hace),
        )
        cliente.generate_clean_qr()
        # Mismo congelado que hace la vista de salida: el monto queda fijo.
        cliente.congelar_cobro()
        cliente.save()

    # El registro que se usa para la diapositiva de detalle lleva foto, para que
    # la captura muestre la ficha completa.
    con_foto = Cliente.objects.filter(fecha_salida__isnull=False).order_by('id').first()
    con_foto.foto.save(
        f'demo_{con_foto.id}.jpg',
        ContentFile(_imagen_ficticia('Foto de demostracion').read()),
        save=True,
    )

    # --- Visitantes ---------------------------------------------------------
    for cedula, nombre, telefono, torre, apto in [
        ('1030405060', 'Elena Quintero', '3011112233', '2', '206'),
        ('1030405061', 'Ruben Alzate', '3012223344', '4', '402'),
    ]:
        Visitante.objects.create(
            cedula=cedula, nombre=nombre, telefono=telefono, torre=torre, apartamento=apto,
        )

    return {
        'admin': 'demo',
        'password': 'demo12345',
        'pk_cliente': con_foto.pk,
        'cedula_dentro': dentro[0][2],
    }


def main():
    base = DEMO_DIR / 'demo.sqlite3'
    if base.exists():
        base.unlink()
    media = DEMO_DIR / 'media_demo'
    if media.exists():
        shutil.rmtree(media)

    preparar_django()

    from django.core.management import call_command
    call_command('migrate', verbosity=0, interactive=False)

    datos = sembrar()
    print(f"Base de demo lista: {base}")
    print(f"Usuario: {datos['admin']} / {datos['password']}")
    return datos


if __name__ == '__main__':
    main()
