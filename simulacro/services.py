"""
Capa de servicios para el simulacro VILLTECC.
Contiene la logica de negocio pura, separada de las vistas.
"""
import io
import logging

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from decimal import Decimal

import qrcode
from django.conf import settings
from django.core.files.base import ContentFile
from django.utils import timezone
from django.utils.timezone import localtime

from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

from .models import (
    Area, Pregunta, MatrizPeso, Intento,
    RespuestaDetalle, Alternativa,
)

logger = logging.getLogger('simulacro')


# =============================================================================
# SCORING / CALIFICACION
# =============================================================================

PENALIDAD_DEFAULT = Decimal('0.102')
ETIQUETA_EXAMEN = 'SIMULACRO_4'
DURACION_EXAMEN_MINUTOS = 150


def calcular_penalidad(area: Area) -> Decimal:
    """Retorna la penalidad por respuesta incorrecta segun el area."""
    if area.nombre == 'EXT':
        return Decimal('0.00')
    return PENALIDAD_DEFAULT


def seleccionar_preguntas_examen(area: Area) -> list:
    """
    Selecciona las preguntas para un examen dado un area.
    Retorna una lista mezclada de objetos Pregunta.
    """
    configuraciones = MatrizPeso.objects.filter(area=area)
    preguntas_examen = []

    for config in configuraciones:
        preguntas = list(
            Pregunta.objects.filter(
                asignatura=config.asignatura,
                etiqueta=ETIQUETA_EXAMEN,
            ).select_related('asignatura').order_by('?')[:config.cantidad_preguntas]
        )
        preguntas_examen.extend(preguntas)

    import random
    random.shuffle(preguntas_examen)
    return preguntas_examen


def procesar_respuestas_examen(intento: Intento) -> Decimal:
    """
    Calcula el puntaje final desde las RespuestaDetalle ya guardadas en BD.
    Marca el Intento como finalizado.
    Retorna puntaje_total.
    """
    penalidad = calcular_penalidad(intento.area)
    puntaje_total = Decimal('0.0000000')

    respuestas = RespuestaDetalle.objects.filter(
        intento=intento
    ).select_related('pregunta__asignatura')

    for resp in respuestas:
        peso_obj = MatrizPeso.objects.filter(
            area=intento.area, asignatura=resp.pregunta.asignatura
        ).first()
        peso_pregunta = peso_obj.peso_pregunta if peso_obj else Decimal('0')

        if resp.es_correcta:
            puntaje_total += peso_pregunta
        else:
            puntaje_total -= penalidad

    intento.fecha_fin = timezone.now()
    intento.puntaje_final = puntaje_total
    intento.en_curso = False
    intento.save()

    return puntaje_total


def guardar_respuesta_auto_save(intento: Intento, pregunta_id: int, alternativa_id: int) -> bool:
    """
    Guarda o actualiza una respuesta individual (auto-save AJAX).
    Retorna True si se guardó correctamente.
    """
    if not intento.en_curso:
        return False

    pregunta = Pregunta.objects.filter(id=pregunta_id).first()
    if not pregunta:
        return False

    alternativa = Alternativa.objects.filter(id=alternativa_id).first()
    es_correcta = alternativa.es_correcta if alternativa else False
    texto_opcion = (alternativa.texto or "Imagen") if alternativa else "Sin respuesta"

    RespuestaDetalle.objects.update_or_create(
        intento=intento,
        pregunta=pregunta,
        defaults={
            'opcion_marcada': texto_opcion,
            'es_correcta': es_correcta,
        }
    )
    return True


# =============================================================================
# QR / WHATSAPP
# =============================================================================

def generar_qr_whatsapp_venta(puntaje, username: str) -> io.BytesIO:
    """Genera un QR con link de WhatsApp para venta de reporte."""
    numero = settings.WHATSAPP_NUMERO
    puntaje_rounded = round(puntaje, 4)
    mensaje = f"Hola, saqué {puntaje_rounded} en el simulacro y quiero informes sobre el descuento. Mi usuario es: {username}"
    url = f"https://wa.me/{numero}?text={mensaje}"

    qr = qrcode.QRCode(box_size=10, border=4)
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill='black', back_color='white')

    buffer = io.BytesIO()
    img.save(buffer, "PNG")
    buffer.seek(0)
    return buffer


def generar_qr_whatsapp_pago(username: str) -> io.BytesIO:
    """Genera un QR con link de WhatsApp para comprobante de pago."""
    numero = settings.WHATSAPP_NUMERO
    mensaje = f"Hola, ya realicé el pago del simulacro. Mi usuario es: {username}"
    url = f"https://wa.me/{numero}?text={mensaje}"

    qr = qrcode.QRCode(box_size=10, border=5)
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill='black', back_color='white')

    buffer = io.BytesIO()
    img.save(buffer, "PNG")
    buffer.seek(0)
    return buffer


# =============================================================================
# SEMAFORO DE RENDIMIENTO
# =============================================================================

def calcular_semaforo(intento: Intento) -> dict:
    """
    Calcula el semaforo de rendimiento por curso para un intento.
    Retorna dict con listas 'verdes', 'amarillos', 'rojos'.
    """
    semaforo = {'verdes': [], 'amarillos': [], 'rojos': []}

    if intento.nivel_acceso < 1 and not intento.pagado_reporte:
        return semaforo

    respuestas = RespuestaDetalle.objects.filter(
        intento=intento
    ).select_related('pregunta__asignatura')

    cursos_stats = {}
    for resp in respuestas:
        curso_nombre = resp.pregunta.asignatura.nombre
        if curso_nombre not in cursos_stats:
            cursos_stats[curso_nombre] = {'total': 0, 'correctas': 0}
        cursos_stats[curso_nombre]['total'] += 1
        if resp.es_correcta:
            cursos_stats[curso_nombre]['correctas'] += 1

    for curso, stats in cursos_stats.items():
        total = stats['total']
        correctas = stats['correctas']
        porcentaje = (correctas / total * 100) if total > 0 else 0
        item = {'nombre': curso, 'porcentaje': round(porcentaje, 1)}

        if porcentaje >= 70:
            semaforo['verdes'].append(item)
        elif porcentaje >= 40:
            semaforo['amarillos'].append(item)
        else:
            semaforo['rojos'].append(item)

    return semaforo


# =============================================================================
# CALCULO DE TIEMPO
# =============================================================================

def calcular_segundos_restantes(session, area_id: int) -> int:
    """
    Calcula los segundos restantes del examen basado en la sesion.
    Retorna 0 si el tiempo ya expiro.
    """
    hoy = timezone.localtime(timezone.now()).date()
    clave_inicio = f'inicio_examen_{area_id}_{hoy}'

    if clave_inicio not in session:
        session[clave_inicio] = timezone.now().isoformat()

    from django.utils.dateparse import parse_datetime
    from datetime import timedelta

    inicio_str = session[clave_inicio]
    hora_inicio = parse_datetime(inicio_str)

    if not hora_inicio:
        hora_inicio = timezone.now()

    duracion = timedelta(minutes=DURACION_EXAMEN_MINUTOS)
    hora_fin = hora_inicio + duracion
    tiempo_restante = hora_fin - timezone.now()
    segundos = int(tiempo_restante.total_seconds())

    return max(segundos, 0)


def limpiar_sesion_examen(session, area_id: int):
    """Limpia la clave de inicio del examen de la sesion."""
    hoy = timezone.localtime(timezone.now()).date()
    clave_inicio = f'inicio_examen_{area_id}_{hoy}'
    if clave_inicio in session:
        del session[clave_inicio]
