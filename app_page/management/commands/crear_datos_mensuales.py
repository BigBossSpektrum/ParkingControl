"""Genera datos de demostracion repartidos por mes.

A diferencia de crear_datos_prueba, que concentra un lote en los ultimos dias,
este comando distribuye los registros a lo largo de varios meses para poder ver
como se comportan los listados, los contadores y el historial de recaudacion.

Todo lo que crea queda marcado (cedulas con prefijo PRB- y una marca en las
observaciones del corte), asi que --limpiar borra los datos de prueba sin tocar
los registros reales.
"""

import calendar
import random
from datetime import datetime, timedelta
from decimal import Decimal

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from app_page.models import Cliente, Recaudacion, Visitante

PREFIJO_CEDULA = 'PRB-'
MARCA_OBSERVACIONES = '[datos-de-prueba]'

NOMBRES = [
    'Ana Torres', 'Carlos Rueda', 'Marta Diaz', 'Luis Rojas', 'Sofia Marin',
    'Jorge Pineda', 'Elena Castro', 'Diego Herrera', 'Paula Nieto', 'Ivan Salas',
]
LETRAS_PLACA = ['ABC', 'DEF', 'GHJ', 'KLM', 'NPQ', 'RST', 'UVW', 'XYZ', 'BCD', 'FGH']
TIPOS = ['Auto', 'Moto', 'Otro']


class Command(BaseCommand):
    help = 'Crea datos de demostracion repartidos por mes (clientes, visitantes y cortes)'

    def add_arguments(self, parser):
        parser.add_argument('--meses', type=int, default=3,
                            help='Cuantos meses hacia atras generar, incluido el actual (por defecto 3)')
        parser.add_argument('--por-mes', type=int, default=10,
                            help='Registros de cada tipo por mes (por defecto 10)')
        parser.add_argument('--limpiar', action='store_true',
                            help='Borra unicamente los datos de prueba y termina')
        parser.add_argument('--semilla', type=int, default=2026,
                            help='Semilla del generador, para que las corridas sean reproducibles')

    def handle(self, *args, **options):
        if options['limpiar']:
            self._limpiar()
            return

        meses = options['meses']
        por_mes = options['por_mes']
        if meses < 1 or por_mes < 1:
            self.stderr.write(self.style.ERROR('--meses y --por-mes deben ser mayores que cero.'))
            return

        azar = random.Random(options['semilla'])
        usuario = self._usuario_para_cortes()
        if usuario is None:
            self.stderr.write(self.style.ERROR(
                'No hay ningun usuario en la base de datos; cree uno antes de generar cortes.'
            ))
            return

        # Se borra lo anterior para poder reejecutar el comando sin acumular.
        self._limpiar(silencioso=True)

        with transaction.atomic():
            total_clientes = total_visitantes = total_cortes = 0
            for anio, mes in self._meses_hacia_atras(meses):
                clientes = self._crear_clientes(anio, mes, por_mes, azar)
                visitantes = self._crear_visitantes(anio, mes, por_mes, azar)
                corte = self._crear_corte(anio, mes, clientes, usuario)

                total_clientes += len(clientes)
                total_visitantes += len(visitantes)
                total_cortes += 1 if corte else 0

                activos = sum(1 for c in clientes if c.fecha_salida is None)
                self.stdout.write(
                    f'{anio}-{mes:02d}: {len(clientes)} clientes ({activos} aun en parking), '
                    f'{len(visitantes)} visitantes'
                    + (f', corte de ${corte.monto_recaudado:,.2f}' if corte else ', sin corte')
                )

        self.stdout.write(self.style.SUCCESS(
            f'\nDatos de demostracion creados: {total_clientes} clientes, '
            f'{total_visitantes} visitantes y {total_cortes} cortes en {meses} mes(es).\n'
            f'Para eliminarlos: python manage.py crear_datos_mensuales --limpiar'
        ))

    # --- Utilidades ---------------------------------------------------------

    def _usuario_para_cortes(self):
        return User.objects.filter(is_superuser=True).first() or User.objects.first()

    def _meses_hacia_atras(self, cantidad):
        """Devuelve (anio, mes) del mas antiguo al mas reciente, incluido el actual."""
        hoy = timezone.localdate()
        for atras in range(cantidad - 1, -1, -1):
            mes = hoy.month - atras
            anio = hoy.year
            while mes <= 0:
                mes += 12
                anio -= 1
            yield anio, mes

    def _ultimo_dia_util(self, anio, mes):
        """Ultimo dia que se puede usar: en el mes en curso no se inventa futuro."""
        hoy = timezone.localdate()
        if (anio, mes) == (hoy.year, hoy.month):
            return hoy.day
        return calendar.monthrange(anio, mes)[1]

    def _momento(self, anio, mes, dia, azar):
        ingenuo = datetime(anio, mes, dia, azar.randint(6, 21), azar.randint(0, 59))
        return timezone.make_aware(ingenuo)

    def _cierre_de_mes(self, anio, mes):
        """Instante del corte: fin del mes, o ahora si el mes sigue en curso.

        No sirve usar la ultima salida del mes: una entrada del dia 31 por la
        noche sale ya en el mes siguiente y dos cortes acabarian en el mismo mes.
        """
        hoy = timezone.localdate()
        if (anio, mes) == (hoy.year, hoy.month):
            return timezone.now()
        ultimo_dia = calendar.monthrange(anio, mes)[1]
        return timezone.make_aware(datetime(anio, mes, ultimo_dia, 23, 59))

    # --- Generacion ---------------------------------------------------------

    def _crear_clientes(self, anio, mes, cantidad, azar):
        tope = self._ultimo_dia_util(anio, mes)
        hoy = timezone.localdate()
        es_mes_actual = (anio, mes) == (hoy.year, hoy.month)
        creados = []

        for i in range(cantidad):
            dia = 1 + (i * (tope - 1)) // max(1, cantidad - 1) if tope > 1 else 1
            entrada = self._momento(anio, mes, dia, azar)

            # En el mes en curso se dejan los dos ultimos sin salida, para que el
            # contador de "en parking" y la tabla de ingresos tengan algo activo.
            sigue_dentro = es_mes_actual and i >= cantidad - 2
            salida = None if sigue_dentro else entrada + timedelta(minutes=azar.randint(20, 600))

            creados.append(Cliente.objects.create(
                cedula=f'{PREFIJO_CEDULA}C{anio % 100:02d}{mes:02d}{i:02d}',
                nombre=NOMBRES[i % len(NOMBRES)],
                telefono=f'30{azar.randint(10000000, 99999999)}',
                torre=azar.choice(['A', 'B', 'C', '1', '2']),
                apartamento=str(azar.randint(101, 905)),
                matricula=f'{LETRAS_PLACA[i % len(LETRAS_PLACA)]}-{azar.randint(100, 999)}',
                tipo_vehiculo=TIPOS[i % len(TIPOS)],
                fecha_entrada=entrada,
                fecha_salida=salida,
            ))
        return creados

    def _crear_visitantes(self, anio, mes, cantidad, azar):
        tope = self._ultimo_dia_util(anio, mes)
        creados = []

        for i in range(cantidad):
            dia = 1 + (i * (tope - 1)) // max(1, cantidad - 1) if tope > 1 else 1
            visitante = Visitante.objects.create(
                cedula=f'{PREFIJO_CEDULA}V{anio % 100:02d}{mes:02d}{i:02d}',
                nombre=NOMBRES[(i + 3) % len(NOMBRES)],
                telefono=f'31{azar.randint(10000000, 99999999)}',
                torre=azar.choice(['A', 'B', 'C', '1', '2']),
                apartamento=str(azar.randint(101, 905)),
            )
            # fecha_registro es auto_now_add: solo se puede fijar con update().
            Visitante.objects.filter(pk=visitante.pk).update(
                fecha_registro=self._momento(anio, mes, dia, azar)
            )
            creados.append(visitante)
        return creados

    def _crear_corte(self, anio, mes, clientes, usuario):
        cerrados = [c for c in clientes if c.fecha_salida]
        if not cerrados:
            return None

        monto = Decimal(str(round(sum(c.calcular_costo() for c in cerrados), 2)))
        corte = Recaudacion.objects.create(
            usuario=usuario,
            monto_recaudado=monto,
            fecha_inicio=min(c.fecha_entrada for c in cerrados),
            fecha_fin=max(c.fecha_salida for c in cerrados),
            numero_clientes=len(cerrados),
            observaciones=f'Corte de {anio}-{mes:02d}. {MARCA_OBSERVACIONES}',
        )
        # fecha_corte es auto_now_add y es el campo de ordenamiento del historial:
        # sin esto los cortes de todos los meses saldrian con la fecha de hoy.
        Recaudacion.objects.filter(pk=corte.pk).update(fecha_corte=self._cierre_de_mes(anio, mes))
        corte.refresh_from_db()
        return corte

    # --- Limpieza -----------------------------------------------------------

    def _limpiar(self, silencioso=False):
        clientes, _ = Cliente.objects.filter(cedula__startswith=PREFIJO_CEDULA).delete()
        visitantes, _ = Visitante.objects.filter(cedula__startswith=PREFIJO_CEDULA).delete()
        cortes, _ = Recaudacion.objects.filter(
            observaciones__contains=MARCA_OBSERVACIONES
        ).delete()

        if not silencioso:
            self.stdout.write(self.style.SUCCESS(
                f'Datos de prueba eliminados: {clientes} clientes, '
                f'{visitantes} visitantes, {cortes} cortes. '
                f'Los registros reales no se tocaron.'
            ))
