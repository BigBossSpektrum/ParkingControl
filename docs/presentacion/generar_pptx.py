"""Arma la presentacion del manual a partir de contenido.py y capturas/.

Los colores salen del tema de la aplicacion (app_page/static/app_page/css/theme.css)
para que la presentacion y el sistema se vean como lo mismo.

Uso:  env\\Scripts\\python docs\\presentacion\\generar_pptx.py
"""

import os
import sys
from pathlib import Path

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Emu, Inches, Pt

BASE_DIR = Path(__file__).resolve().parents[2]
DEMO_DIR = BASE_DIR / 'docs' / 'presentacion'
CAPTURAS_DIR = DEMO_DIR / 'capturas'
SALIDA = DEMO_DIR / 'ParkingControl-Manual.pptx'

sys.path.insert(0, str(DEMO_DIR))
sys.path.insert(0, str(BASE_DIR))

from contenido import DIAPOSITIVAS, PORTADA  # noqa: E402

# Paleta de theme.css
BG = RGBColor(0xF7, 0xF8, 0xF9)
SURFACE = RGBColor(0xFF, 0xFF, 0xFF)
SURFACE_ALT = RGBColor(0xEE, 0xF0, 0xF2)
BORDE = RGBColor(0xD6, 0xDA, 0xDE)
FG = RGBColor(0x1B, 0x1E, 0x21)
MUTED = RGBColor(0x5A, 0x61, 0x69)
ACENTO = RGBColor(0x14, 0x6C, 0x2E)
BLANCO = RGBColor(0xFF, 0xFF, 0xFF)

ANCHO = Inches(13.333)
ALTO = Inches(7.5)

BANDA_ALTO = Inches(0.95)
MARGEN = Inches(0.5)
COL_IZQ_ANCHO = Inches(4.55)
COL_DER_X = Inches(5.35)
COL_DER_ANCHO = ANCHO - COL_DER_X - MARGEN
CONTENIDO_Y = BANDA_ALTO + Inches(0.35)
CONTENIDO_ALTO = ALTO - CONTENIDO_Y - Inches(0.45)


def obtener_soporte():
    """Reutiliza la constante SOPORTE de la app: un solo sitio donde cambiarla."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'parking_site.settings')
    import django
    django.setup()
    from app_page.views import SOPORTE
    return SOPORTE


def fondo(diapositiva, color):
    relleno = diapositiva.background.fill
    relleno.solid()
    relleno.fore_color.rgb = color


def rectangulo(diapositiva, x, y, ancho, alto, color, forma=MSO_SHAPE.RECTANGLE):
    figura = diapositiva.shapes.add_shape(forma, x, y, ancho, alto)
    figura.fill.solid()
    figura.fill.fore_color.rgb = color
    figura.line.fill.background()
    figura.shadow.inherit = False
    return figura


def caja_texto(diapositiva, x, y, ancho, alto):
    figura = diapositiva.shapes.add_textbox(x, y, ancho, alto)
    marco = figura.text_frame
    marco.word_wrap = True
    marco.margin_left = 0
    marco.margin_right = 0
    marco.margin_top = 0
    marco.margin_bottom = 0
    return marco


def escribir(parrafo, texto, tamano, color, negrita=False, espacio_antes=None, interlineado=0.95):
    """Anade una corrida al parrafo; con espacio_antes, ademas lo separa.

    El espaciado es del parrafo, no de la corrida: solo lo toca quien lo pide,
    porque una segunda corrida en el mismo parrafo (el numero del paso y su
    texto, por ejemplo) lo dejaria en cero sin querer.
    """
    if espacio_antes is not None:
        parrafo.space_before = Pt(espacio_antes)
        parrafo.line_spacing = interlineado
    corrida = parrafo.add_run()
    corrida.text = texto
    corrida.font.size = Pt(tamano)
    corrida.font.color.rgb = color
    corrida.font.bold = negrita
    corrida.font.name = 'Segoe UI'
    return corrida


def banda_titulo(diapositiva, titulo, solo_admin):
    rectangulo(diapositiva, 0, 0, ANCHO, BANDA_ALTO, ACENTO)

    marco = caja_texto(diapositiva, MARGEN, Inches(0.2), Inches(9.5), Inches(0.6))
    marco.vertical_anchor = MSO_ANCHOR.MIDDLE
    escribir(marco.paragraphs[0], titulo, 26, BLANCO, negrita=True)

    if solo_admin:
        ancho_pildora = Inches(2.4)
        pildora = rectangulo(
            diapositiva, ANCHO - MARGEN - ancho_pildora, Inches(0.27),
            ancho_pildora, Inches(0.4), SURFACE, MSO_SHAPE.ROUNDED_RECTANGLE,
        )
        marco = pildora.text_frame
        marco.word_wrap = True
        parrafo = marco.paragraphs[0]
        parrafo.alignment = PP_ALIGN.CENTER
        escribir(parrafo, 'Solo administrador', 12, ACENTO, negrita=True)


AVISO_ALTO = Inches(1.35)
AVISO_SEPARACION = Inches(0.25)

# Caracteres que caben en un renglon de 14 pt a lo ancho de la columna
# izquierda. Sirve para bajar el cuerpo cuando una diapositiva trae muchos
# pasos, en lugar de dejar que el texto se meta en la caja de aviso.
CARACTERES_COLUMNA = 52

# A partir de esta proporcion (ancho/alto) la captura es una franja: puesta en
# la columna derecha se ve como un hilo perdido en el hueco, asi que la
# diapositiva pasa a maqueta de banda, con la imagen a todo lo ancho.
ASPECTO_BANDA = 3.0


def lineas_estimadas(pasos, caracteres_por_linea):
    return sum(max(1, -(-len(paso) // caracteres_por_linea)) for paso in pasos)


def bloque_pasos(diapositiva, pasos, x, y, ancho, alto):
    # Un renglon de 14 pt con su separacion ocupa algo menos de 0,32 pulgadas.
    caracteres = int(CARACTERES_COLUMNA * ancho / COL_IZQ_ANCHO)
    tamano = 14
    if lineas_estimadas(pasos, caracteres) * Inches(0.32) + len(pasos) * Inches(0.1) > alto:
        tamano = 12

    marco = caja_texto(diapositiva, x, y, ancho, alto)
    for indice, paso in enumerate(pasos):
        parrafo = marco.paragraphs[0] if indice == 0 else marco.add_paragraph()
        numero = escribir(parrafo, f'{indice + 1}.  ', tamano, ACENTO, negrita=True,
                          espacio_antes=0 if indice == 0 else 9)
        numero.font.name = 'Segoe UI'
        escribir(parrafo, paso, tamano, FG)
    return marco


def bloque_aviso(diapositiva, aviso, x, y, ancho, alto):
    rectangulo(diapositiva, x, y, ancho, alto, SURFACE_ALT)
    # Barra verde a la izquierda, igual que la caja de aviso del manual.
    rectangulo(diapositiva, x, y, Inches(0.06), alto, ACENTO)

    marco = caja_texto(diapositiva, x + Inches(0.25), y + Inches(0.14),
                       ancho - Inches(0.45), alto - Inches(0.28))
    marco.vertical_anchor = MSO_ANCHOR.MIDDLE
    escribir(marco.paragraphs[0], aviso, 11.5, MUTED)


def encajar(ancho_px, alto_px, ancho_max, alto_max):
    """Escala conservando la proporcion, sin ampliar mas alla de la caja."""
    escala = min(ancho_max / ancho_px, alto_max / alto_px)
    return Emu(int(ancho_px * escala)), Emu(int(alto_px * escala))


def aspecto_captura(archivo):
    """Proporcion ancho/alto de la captura, o None si todavia no existe."""
    ruta = CAPTURAS_DIR / archivo
    if not ruta.exists():
        return None
    from PIL import Image
    with Image.open(ruta) as imagen:
        return imagen.size[0] / imagen.size[1]


def bloque_captura(diapositiva, archivo, x, y, ancho, alto):
    ruta = CAPTURAS_DIR / archivo

    if not ruta.exists():
        marcador = rectangulo(diapositiva, x, y, ancho, alto, SURFACE_ALT)
        marcador.line.color.rgb = BORDE
        marcador.line.width = Pt(1)
        marco = marcador.text_frame
        marco.word_wrap = True
        parrafo = marco.paragraphs[0]
        parrafo.alignment = PP_ALIGN.CENTER
        escribir(parrafo, f'Falta la captura: {archivo}', 14, MUTED)
        return

    from PIL import Image
    with Image.open(ruta) as imagen:
        px_ancho, px_alto = imagen.size

    ancho_final, alto_final = encajar(px_ancho, px_alto, ancho, alto)
    x_final = x + int((ancho - ancho_final) / 2)
    y_final = y + int((alto - alto_final) / 2)

    diapositiva.shapes.add_picture(str(ruta), x_final, y_final, ancho_final, alto_final)

    marco_borde = diapositiva.shapes.add_shape(
        MSO_SHAPE.RECTANGLE, x_final, y_final, ancho_final, alto_final)
    marco_borde.fill.background()
    marco_borde.line.color.rgb = BORDE
    marco_borde.line.width = Pt(1)
    marco_borde.shadow.inherit = False


def diapositiva_portada(prs):
    diapositiva = prs.slides.add_slide(prs.slide_layouts[6])
    fondo(diapositiva, ACENTO)

    marco = caja_texto(diapositiva, Inches(1.1), Inches(2.5), Inches(11), Inches(1.4))
    escribir(marco.paragraphs[0], PORTADA['titulo'], 54, BLANCO, negrita=True)

    rectangulo(diapositiva, Inches(1.1), Inches(4.05), Inches(1.6), Inches(0.05), BLANCO)

    marco = caja_texto(diapositiva, Inches(1.1), Inches(4.35), Inches(11), Inches(0.8))
    escribir(marco.paragraphs[0], PORTADA['subtitulo'], 22, SURFACE_ALT)


def diapositiva_indice(prs):
    diapositiva = prs.slides.add_slide(prs.slide_layouts[6])
    fondo(diapositiva, BG)
    banda_titulo(diapositiva, 'Contenido', False)

    mitad = (len(DIAPOSITIVAS) + 1) // 2
    columnas = [DIAPOSITIVAS[:mitad], DIAPOSITIVAS[mitad:]]

    for indice, columna in enumerate(columnas):
        x = MARGEN + indice * Inches(6.4)
        marco = caja_texto(diapositiva, x, CONTENIDO_Y + Inches(0.2), Inches(5.9), CONTENIDO_ALTO)
        for posicion, entrada in enumerate(columna):
            parrafo = marco.paragraphs[0] if posicion == 0 else marco.add_paragraph()
            escribir(parrafo, entrada['titulo'], 16, FG,
                     espacio_antes=0 if posicion == 0 else 14)
            if entrada['solo_admin']:
                escribir(parrafo, '   ·  solo administrador', 12, MUTED)


def maquetar_columnas(diapositiva, entrada, archivo):
    """Reparto normal: pasos a la izquierda, captura a la derecha."""
    if entrada['aviso']:
        alto_pasos = CONTENIDO_ALTO - AVISO_ALTO - AVISO_SEPARACION
        bloque_pasos(diapositiva, entrada['pasos'], MARGEN, CONTENIDO_Y, COL_IZQ_ANCHO, alto_pasos)
        # Anclado al fondo de la columna: asi nunca puede chocar con los pasos,
        # midan lo que midan cuando PowerPoint los reparte en renglones.
        bloque_aviso(diapositiva, entrada['aviso'], MARGEN,
                     CONTENIDO_Y + CONTENIDO_ALTO - AVISO_ALTO, COL_IZQ_ANCHO, AVISO_ALTO)
    else:
        bloque_pasos(diapositiva, entrada['pasos'], MARGEN, CONTENIDO_Y,
                     COL_IZQ_ANCHO, CONTENIDO_ALTO)

    bloque_captura(diapositiva, archivo, COL_DER_X, CONTENIDO_Y, COL_DER_ANCHO, CONTENIDO_ALTO)


def maquetar_banda(diapositiva, entrada, archivo, aspecto):
    """Captura apaisada: va a todo lo ancho, con los pasos debajo."""
    ancho = ANCHO - 2 * MARGEN
    alto_imagen = min(int(ancho / aspecto), Inches(3.2))
    bloque_captura(diapositiva, archivo, MARGEN, CONTENIDO_Y, ancho, alto_imagen)

    y_texto = CONTENIDO_Y + alto_imagen + Inches(0.4)
    alto_texto = CONTENIDO_Y + CONTENIDO_ALTO - y_texto

    if entrada['aviso']:
        alto_aviso = Inches(0.95)
        bloque_pasos(diapositiva, entrada['pasos'], MARGEN, y_texto, ancho,
                     alto_texto - alto_aviso - AVISO_SEPARACION)
        # A todo lo ancho cada paso entra en un renglon, asi que la altura del
        # bloque es previsible y el aviso puede ir pegado debajo en vez de
        # quedar descolgado al fondo. El tope evita que se salga si algun paso
        # termina partiendose en dos.
        alto_pasos = len(entrada['pasos']) * Inches(0.36) + Inches(0.35)
        tope = CONTENIDO_Y + CONTENIDO_ALTO - alto_aviso
        bloque_aviso(diapositiva, entrada['aviso'], MARGEN,
                     min(y_texto + alto_pasos, tope), ancho, alto_aviso)
    else:
        bloque_pasos(diapositiva, entrada['pasos'], MARGEN, y_texto, ancho, alto_texto)


def diapositiva_contenido(prs, entrada):
    diapositiva = prs.slides.add_slide(prs.slide_layouts[6])
    fondo(diapositiva, BG)
    banda_titulo(diapositiva, entrada['titulo'], entrada['solo_admin'])

    archivo = entrada['captura']['archivo']
    aspecto = aspecto_captura(archivo)

    if aspecto and aspecto >= ASPECTO_BANDA:
        maquetar_banda(diapositiva, entrada, archivo, aspecto)
    else:
        maquetar_columnas(diapositiva, entrada, archivo)


def diapositiva_soporte(prs, soporte):
    diapositiva = prs.slides.add_slide(prs.slide_layouts[6])
    fondo(diapositiva, ACENTO)

    marco = caja_texto(diapositiva, Inches(1.1), Inches(1.3), Inches(11), Inches(0.9))
    escribir(marco.paragraphs[0], '¿Necesita ayuda?', 40, BLANCO, negrita=True)

    marco = caja_texto(diapositiva, Inches(1.1), Inches(2.35), Inches(11), Inches(1.0))
    escribir(marco.paragraphs[0],
             'Si algo no funciona y no encuentra la respuesta en el manual, escriba por '
             'cualquiera de estos dos medios.', 18, SURFACE_ALT)

    tarjeta = rectangulo(diapositiva, Inches(1.1), Inches(3.3), Inches(5.2), Inches(1.5), SURFACE)
    marco = tarjeta.text_frame
    marco.word_wrap = True
    marco.margin_left = Inches(0.3)
    marco.vertical_anchor = MSO_ANCHOR.MIDDLE
    escribir(marco.paragraphs[0], 'WhatsApp', 16, MUTED)
    escribir(marco.add_paragraph(), soporte['whatsapp_numero'], 24, ACENTO,
             negrita=True, espacio_antes=6)
    escribir(marco.add_paragraph(), soporte['correo'], 15, FG, espacio_antes=10)

    marco = caja_texto(diapositiva, Inches(6.9), Inches(3.3), Inches(5.3), Inches(2.6))
    escribir(marco.paragraphs[0], 'Qué incluir en el mensaje', 18, BLANCO, negrita=True)
    for detalle in [
        'Con qué usuario había iniciado sesión.',
        'La hora aproximada en que ocurrió.',
        'La placa o la cédula del registro, si aplica.',
        'En qué pantalla estaba.',
        'El texto exacto del error, o una foto de la pantalla.',
    ]:
        escribir(marco.add_paragraph(), f'•  {detalle}', 14, SURFACE_ALT, espacio_antes=8)


def main():
    soporte = obtener_soporte()

    prs = Presentation()
    prs.slide_width = ANCHO
    prs.slide_height = ALTO

    diapositiva_portada(prs)
    diapositiva_indice(prs)
    for entrada in DIAPOSITIVAS:
        diapositiva_contenido(prs, entrada)
    diapositiva_soporte(prs, soporte)

    prs.save(str(SALIDA))

    faltantes = [e['captura']['archivo'] for e in DIAPOSITIVAS
                 if not (CAPTURAS_DIR / e['captura']['archivo']).exists()]
    print(f'Presentacion generada: {SALIDA}')
    print(f'Diapositivas: {len(prs.slides)}')
    if faltantes:
        print('Sin captura (salen con marcador):')
        for archivo in faltantes:
            print(f'  - {archivo}')
    return 1 if faltantes else 0


if __name__ == '__main__':
    sys.exit(main())
