"""Toma las capturas de cada pantalla para la presentacion del manual.

Siembra la base de demo, levanta un runserver aparte contra ella, entra con el
usuario de demostracion y guarda un PNG por diapositiva en capturas/.

Necesita conexion a internet: las plantillas cargan Bootstrap, Bootstrap Icons y
SweetAlert2 desde jsDelivr, y sin ellos las capturas salen sin estilos.

Uso:  env\\Scripts\\python docs\\presentacion\\capturar.py
"""

import os
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]
DEMO_DIR = BASE_DIR / 'docs' / 'presentacion'
CAPTURAS_DIR = DEMO_DIR / 'capturas'

# Puerto propio: no pisa el 8000 del sistema en uso ni el 8765 del lanzador.
HOST = '127.0.0.1'
PUERTO = 8799
BASE_URL = f'http://{HOST}:{PUERTO}'

sys.path.insert(0, str(DEMO_DIR))
sys.path.insert(0, str(BASE_DIR))

from contenido import DIAPOSITIVAS  # noqa: E402


def arrancar_servidor():
    """Levanta runserver contra la base de demo y espera a que responda."""
    entorno = os.environ.copy()
    entorno['DJANGO_SETTINGS_MODULE'] = 'parking_site.settings_demo'
    proceso = subprocess.Popen(
        [sys.executable, 'manage.py', 'runserver', f'{HOST}:{PUERTO}', '--noreload'],
        cwd=str(BASE_DIR),
        env=entorno,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    limite = time.time() + 60
    while time.time() < limite:
        if proceso.poll() is not None:
            raise RuntimeError('El servidor de demo murio al arrancar')
        try:
            urllib.request.urlopen(f'{BASE_URL}/login/', timeout=2)
            return proceso
        except urllib.error.HTTPError:
            return proceso  # responde, aunque sea con un codigo de error
        except (urllib.error.URLError, OSError):
            time.sleep(0.5)

    proceso.terminate()
    raise RuntimeError('El servidor de demo no respondio a tiempo')


def dibujar_consola(destino):
    """Dibuja la ventana del lanzador: el .exe no se captura con un navegador."""
    from PIL import Image, ImageDraw, ImageFont

    ancho, alto = 900, 480
    img = Image.new('RGB', (ancho, alto), (12, 12, 12))
    draw = ImageDraw.Draw(img)

    # Barra de titulo, para que se reconozca como la ventana negra del manual.
    draw.rectangle([0, 0, ancho, 38], fill=(32, 32, 32))

    def fuente(nombre, tamano):
        try:
            return ImageFont.truetype(nombre, tamano)
        except OSError:
            return ImageFont.load_default()

    titulo = fuente('segoeui.ttf', 18)
    mono = fuente('consola.ttf', 17)

    draw.text((16, 9), 'ParkingControl', fill=(220, 220, 220), font=titulo)

    lineas = [
        ('  Parking Control', (255, 255, 255)),
        ('', None),
        ('  Iniciando el servidor...', (200, 200, 200)),
        ('  Servidor listo en http://127.0.0.1:8000', (120, 220, 140)),
        ('  Abriendo el navegador...', (200, 200, 200)),
        ('', None),
        ('  No cierre esta ventana mientras use el sistema.', (240, 200, 100)),
        ('', None),
        ('  Si vuelve a abrir ParkingControl.exe:', (200, 200, 200)),
        ('    [A] Abrir el navegador de nuevo', (180, 200, 240)),
        ('    [D] Detener el servidor', (180, 200, 240)),
        ('    [S] Salir sin hacer nada', (180, 200, 240)),
    ]
    y = 66
    for texto, color in lineas:
        if texto:
            draw.text((24, y), texto, fill=color, font=mono)
        y += 30

    img.save(destino)


def capturar_elemento(page, selector, destino):
    elemento = page.locator(selector).first
    elemento.scroll_into_view_if_needed()
    page.wait_for_timeout(200)
    elemento.screenshot(path=str(destino))


def esperar_estable(page):
    """Espera al CDN, pero sin abortar la captura si la red va lenta."""
    try:
        page.wait_for_load_state('networkidle', timeout=15000)
    except Exception:
        pass
    page.wait_for_timeout(400)


def main():
    CAPTURAS_DIR.mkdir(parents=True, exist_ok=True)

    import sembrar_demo
    datos = sembrar_demo.main()

    from playwright.sync_api import sync_playwright

    servidor = arrancar_servidor()
    fallidas = []
    try:
        with sync_playwright() as pw:
            navegador = pw.chromium.launch()
            contexto = navegador.new_context(
                viewport={'width': 1440, 'height': 900},
                device_scale_factor=2,
                locale='es-CO',
            )
            page = contexto.new_page()

            # Sesion como administrador: es el rol que ve todas las pantallas.
            page.goto(f'{BASE_URL}/login/')
            esperar_estable(page)
            dibujar_consola(CAPTURAS_DIR / 'arrancar.png')
            page.screenshot(path=str(CAPTURAS_DIR / 'entrar.png'))

            page.fill('#id_username', datos['admin'])
            page.fill('#id_password', datos['password'])
            page.click('#loginForm button[type="submit"]')
            page.wait_for_load_state('load')

            for diapositiva in DIAPOSITIVAS:
                captura = diapositiva['captura']
                archivo = captura['archivo']
                destino = CAPTURAS_DIR / archivo

                # Ya resueltas antes de iniciar sesion.
                if archivo in ('arrancar.png', 'entrar.png'):
                    continue

                try:
                    url = captura['url'].format(pk_cliente=datos['pk_cliente'])
                    page.goto(f'{BASE_URL}{url}')
                    esperar_estable(page)

                    accion = captura['accion']
                    if accion == 'salida_cobro':
                        # Busca un vehiculo que sigue dentro y se detiene en el
                        # modal del cobro: no se confirma la salida, para que el
                        # resto de capturas lo siga mostrando en el parking.
                        page.fill('#id_codigo', datos['cedula_dentro'])
                        page.click('#submitSalidaBtn')
                        page.wait_for_selector('.swal2-popup', timeout=20000)
                        page.wait_for_timeout(600)
                    elif accion == 'abrir_recaudacion':
                        page.click('#btnResumenRecaudacion')
                        page.wait_for_selector('#modalResumenRecaudacion.show', timeout=20000)
                        page.wait_for_timeout(900)

                    if captura['selector']:
                        capturar_elemento(page, captura['selector'], destino)
                    else:
                        page.screenshot(path=str(destino),
                                        full_page=captura.get('pagina_completa', False))

                    print(f'  ok  {archivo}')
                except Exception as error:
                    fallidas.append((archivo, str(error).splitlines()[0]))
                    print(f'  --  {archivo}: {error}')

            navegador.close()
    finally:
        servidor.terminate()
        servidor.wait(timeout=15)

    total = len(DIAPOSITIVAS)
    print(f'\nCapturas en {CAPTURAS_DIR}: {total - len(fallidas)} de {total}')
    if fallidas:
        print('Fallaron:')
        for archivo, error in fallidas:
            print(f'  - {archivo}: {error}')
    return 1 if fallidas else 0


if __name__ == '__main__':
    sys.exit(main())
