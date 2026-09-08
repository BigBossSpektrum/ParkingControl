#!/usr/bin/env python
"""Lanzador de escritorio para ParkingControl.

Arranca el servidor de desarrollo de Django y abre el navegador en la URL local.
Pensado para empaquetarse con PyInstaller (ver construir_exe.ps1): solo usa la
libreria estandar, de modo que el .exe resultante es un lanzador ligero que se
apoya en el Python instalado en el equipo, no un empaquetado de Django.
"""
import ctypes
import os
import shutil
import socket
import subprocess
import sys
import time
import webbrowser
from pathlib import Path

# --- Configuracion -----------------------------------------------------------
RUTA_FIJA = r"C:\ParkingControl"   # ruta de instalacion en el equipo de produccion
HOST = "127.0.0.1"
PUERTO = 8000
ESPERA_MAXIMA = 60                 # segundos que esperamos a que responda el servidor
TITULO = "ParkingControl - servidor"
# -----------------------------------------------------------------------------

URL = f"http://{HOST}:{PUERTO}/"

SW_MINIMIZE = 6
ES_WINDOWS = sys.platform == "win32"


def _preparar_consola():
    """Evita UnicodeEncodeError con acentos en consolas Windows heredadas.

    line_buffering ademas hace que nuestros mensajes salgan al momento aunque la
    salida este redirigida a un archivo, y no se queden detras de los logs del
    servidor hijo.
    """
    for flujo in (sys.stdout, sys.stderr):
        if flujo is None:
            continue
        try:
            flujo.reconfigure(encoding="utf-8", errors="replace", line_buffering=True)
        except Exception:
            pass


def _ventana_consola():
    """Handle de la ventana de consola, o 0 si no hay (--windowed, otro SO...)."""
    if not ES_WINDOWS:
        return 0
    try:
        return ctypes.windll.kernel32.GetConsoleWindow()
    except Exception:
        return 0


def titular_consola():
    """Nombra la ventana para poder reconocerla en la barra de tareas."""
    if not ES_WINDOWS:
        return
    try:
        ctypes.windll.kernel32.SetConsoleTitleW(TITULO)
    except Exception:
        pass


def minimizar_consola():
    """Manda la consola a la barra de tareas. True si se pudo."""
    ventana = _ventana_consola()
    if not ventana:
        return False
    try:
        ctypes.windll.user32.ShowWindow(ventana, SW_MINIMIZE)
        return True
    except Exception:
        return False


def pausar():
    """Deja el mensaje de error visible cuando se ejecuta con doble clic."""
    try:
        input("\nPresiona Enter para cerrar...")
    except Exception:
        pass


def abortar(*lineas):
    print()
    for linea in lineas:
        print(linea)
    pausar()
    sys.exit(1)


def carpeta_del_programa():
    """Carpeta donde vive el .exe (o el .py si se ejecuta sin empaquetar).

    Se usa la ubicacion del ejecutable y no el directorio de trabajo, para que
    tambien funcione desde un acceso directo del Escritorio.
    """
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


def resolver_raiz():
    """Primera ruta que contenga manage.py: la fija, y si no, la del programa."""
    candidatas = []
    for ruta in (Path(RUTA_FIJA), carpeta_del_programa()):
        if ruta not in candidatas:
            candidatas.append(ruta)

    for ruta in candidatas:
        if (ruta / "manage.py").is_file():
            return ruta

    abortar(
        "No se encontro el proyecto ParkingControl (falta manage.py).",
        "Se busco en:",
        *[f"  - {ruta}" for ruta in candidatas],
        "",
        f"Instala el proyecto en {RUTA_FIJA} o coloca este ejecutable",
        "en la misma carpeta que manage.py.",
    )


def resolver_python(raiz):
    """Comando de Python a usar, como lista de argumentos."""
    # 1) Entorno virtual dentro del proyecto, si existe.
    for nombre in ("env", ".venv", "venv"):
        for relativa in (("Scripts", "python.exe"), ("bin", "python")):
            candidato = raiz.joinpath(nombre, *relativa)
            if candidato.is_file():
                return [str(candidato)]

    # 2) Python del PATH. Se descarta el alias de Microsoft Store, que abre la
    #    tienda en lugar de ejecutar Python.
    for nombre in ("python", "python3"):
        ruta = shutil.which(nombre)
        if ruta and "windowsapps" not in ruta.lower():
            return [ruta]

    # 3) Lanzador oficial de Windows.
    ruta = shutil.which("py")
    if ruta:
        return [ruta, "-3"]

    abortar(
        "No se encontro ninguna instalacion de Python.",
        "",
        "Instala Python 3.12 desde https://www.python.org/downloads/",
        'y marca la casilla "Add python.exe to PATH" durante la instalacion.',
    )


def verificar_dependencias(comando, raiz):
    """Comprueba que Django este instalado para el interprete elegido."""
    try:
        resultado = subprocess.run(
            [*comando, "-c", "import django"],
            cwd=str(raiz),
            capture_output=True,
            text=True,
        )
    except OSError as exc:
        abortar(f"No se pudo ejecutar {' '.join(comando)}: {exc}")

    if resultado.returncode != 0:
        detalle = (resultado.stderr or "").strip().splitlines()
        abortar(
            "Django no esta instalado para este Python:",
            f"  {' '.join(comando)}",
            *([f"  {detalle[-1]}"] if detalle else []),
            "",
            "Instala las dependencias abriendo una consola en",
            f"  {raiz}",
            "y ejecutando:",
            f"  {' '.join(comando)} -m pip install -r requirements.txt",
        )


def puerto_ocupado():
    try:
        with socket.create_connection((HOST, PUERTO), timeout=0.3):
            return True
    except OSError:
        return False


def _salida_de(comando):
    """Ejecuta un comando de Windows y devuelve su salida como texto.

    Se decodifica con errors='replace' porque solo buscamos patrones ASCII
    (numeros, ':' y nombres de proceso) y la pagina de codigos de la consola
    varia de un equipo a otro.
    """
    try:
        resultado = subprocess.run(
            comando,
            capture_output=True,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
    except OSError:
        return ""
    return resultado.stdout.decode("utf-8", "replace")


def pid_en_puerto():
    """PID del proceso que escucha en PUERTO, o None."""
    if not ES_WINDOWS:
        return None
    sufijo = f":{PUERTO}"
    for linea in _salida_de(["netstat", "-ano", "-p", "TCP"]).splitlines():
        partes = linea.split()
        # Formato: Proto  Direccion local  Direccion remota  Estado  PID
        if len(partes) < 5 or partes[3].upper() != "LISTENING":
            continue
        if partes[1].endswith(sufijo) and partes[4].isdigit():
            return int(partes[4])
    return None


def nombre_proceso(pid):
    """Nombre del ejecutable de un PID, o cadena vacia si no se pudo averiguar."""
    salida = _salida_de(["tasklist", "/FI", f"PID eq {pid}", "/FO", "CSV", "/NH"])
    primera = salida.strip().splitlines()
    if not primera or not primera[0].startswith('"'):
        return ""
    return primera[0].split('","')[0].strip('"')


def detener_servidor():
    """Mata el proceso que ocupa el puerto, si es un Python."""
    pid = pid_en_puerto()
    if pid is None:
        print("\nNo se pudo identificar el proceso que ocupa el puerto.")
        pausar()
        return 1

    nombre = nombre_proceso(pid)
    if nombre.lower() not in ("python.exe", "pythonw.exe"):
        print()
        print(f"El puerto {PUERTO} lo ocupa otro programa, no ParkingControl:")
        print(f"  PID {pid} - {nombre or 'desconocido'}")
        print("No se detuvo nada.")
        pausar()
        return 1

    print(f"\nDeteniendo el servidor (PID {pid})...")
    _salida_de(["taskkill", "/PID", str(pid), "/F"])

    limite = time.monotonic() + 10
    while time.monotonic() < limite:
        if not puerto_ocupado():
            print("Servidor detenido.")
            pausar()
            return 0
        time.sleep(0.25)

    print(f"El puerto {PUERTO} sigue ocupado. Revisa el Administrador de tareas.")
    pausar()
    return 1


def menu_servidor_en_marcha():
    """Ofrece abrir el navegador o detener el servidor que ya esta corriendo."""
    print(f"\nYa hay un servidor de ParkingControl en {URL}")
    print()
    print("  [Enter]  Abrir el navegador")
    print("  [D]      Detener el servidor")
    try:
        respuesta = input("\nOpcion: ").strip().lower()
    except Exception:
        respuesta = ""

    if respuesta == "d":
        return detener_servidor()

    print("Abriendo el navegador...")
    webbrowser.open(URL)
    return 0


def esperar_servidor(proceso):
    """True cuando el puerto responde; False si el proceso murio o hubo timeout."""
    limite = time.monotonic() + ESPERA_MAXIMA
    while time.monotonic() < limite:
        if puerto_ocupado():
            return True
        if proceso.poll() is not None:
            return False
        time.sleep(0.25)
    return False


def main():
    _preparar_consola()
    titular_consola()

    raiz = resolver_raiz()
    print(f"ParkingControl - proyecto en {raiz}")

    if puerto_ocupado():
        return menu_servidor_en_marcha()

    comando = resolver_python(raiz)
    verificar_dependencias(comando, raiz)
    print(f"Python: {' '.join(comando)}")
    print(f"Iniciando el servidor en {URL}")
    print("Cierra esta ventana (o pulsa Ctrl+C) para detenerlo.\n")

    entorno = {**os.environ, "PYTHONUNBUFFERED": "1"}
    try:
        proceso = subprocess.Popen(
            [*comando, "manage.py", "runserver", f"{HOST}:{PUERTO}", "--noreload"],
            cwd=str(raiz),
            env=entorno,
        )
    except OSError as exc:
        abortar(f"No se pudo iniciar el servidor: {exc}")

    if not esperar_servidor(proceso):
        if proceso.poll() is None:
            proceso.terminate()
            abortar(
                f"El servidor no respondio en {ESPERA_MAXIMA} segundos.",
                "Revisa los mensajes de error de arriba.",
            )
        abortar(
            "El servidor se detuvo durante el arranque.",
            "Revisa los mensajes de error de arriba.",
        )

    print(f"\nServidor listo. Abriendo {URL}\n")
    webbrowser.open(URL)

    # Damos tiempo a que la ventana del navegador aparezca y tome el foco antes
    # de mandar la consola a la barra de tareas.
    time.sleep(1.0)
    print("Esta ventana se minimiza y sigue trabajando en segundo plano.")
    print("Restaurala desde la barra de tareas para ver los registros,")
    print("o cierrala para detener el servidor.\n")
    minimizar_consola()

    try:
        return proceso.wait()
    except KeyboardInterrupt:
        print("\nDeteniendo el servidor...")
    finally:
        # Ni un Ctrl+C ni un error inesperado deben dejar el servidor huerfano
        # ocupando el puerto.
        if proceso.poll() is None:
            proceso.terminate()
            try:
                proceso.wait(timeout=10)
            except subprocess.TimeoutExpired:
                proceso.kill()
    return 0


if __name__ == "__main__":
    sys.exit(main())
