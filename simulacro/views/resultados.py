"""
Vistas de resultados: ver resultado, ranking, mis examenes, QR, solucionario.
"""
import io
import logging

from django.contrib.auth.decorators import login_required
from django.core.files.base import ContentFile
from django.http import HttpResponse, FileResponse
from django.shortcuts import render, redirect, get_object_or_404

from ..models import Area, Intento, RespuestaDetalle
from ..services import (
    calcular_semaforo,
    generar_qr_whatsapp_venta,
)
from ..utils import generar_pdf_diagnostico

logger = logging.getLogger('simulacro')


@login_required
def ver_resultado(request, intento_id):
    """Muestra el resultado de un examen."""
    intento = get_object_or_404(Intento, id=intento_id, estudiante=request.user)
    if intento.estudiante != request.user and not request.user.is_superuser:
        return render(request, 'simulacro/acceso_denegado.html')
    return render(request, 'simulacro/resultado.html', {'intento': intento})


def ver_ranking(request):
    """Muestra el ranking de puntajes."""
    area_id = request.GET.get('area')

    ranking = Intento.objects.select_related(
        'estudiante',
        'estudiante__perfil',
        'area',
    ).order_by('-puntaje_final')

    if area_id:
        ranking = ranking.filter(area_id=area_id)

    areas = Area.objects.all()

    return render(request, 'simulacro/ranking.html', {
        'ranking': ranking,
        'areas': areas,
        'area_actual': int(area_id) if area_id else None,
    })


@login_required
def generar_qr_resultado(request, intento_id):
    """Genera imagen QR con link de WhatsApp para el resultado."""
    intento = get_object_or_404(Intento, id=intento_id)
    buffer = generar_qr_whatsapp_venta(intento.puntaje_final, intento.estudiante.username)
    return HttpResponse(buffer.getvalue(), content_type="image/png")


@login_required
def mis_examenes(request):
    """Historial de examenes del estudiante con semaforo."""
    intentos = Intento.objects.filter(
        estudiante=request.user
    ).order_by('-fecha_inicio')

    historial_procesado = []
    for intento in intentos:
        semaforo = calcular_semaforo(intento)
        historial_procesado.append({
            'intento': intento,
            'semaforo': semaforo,
        })

    return render(request, 'simulacro/mis_examenes.html', {'historial': historial_procesado})


@login_required
def descargar_solucionario_pdf(request, intento_id):
    """Descarga el solucionario VIP en HTML con MathJax."""
    intento = get_object_or_404(Intento, id=intento_id, estudiante=request.user)

    if intento.nivel_acceso < 2:
        return HttpResponse(
            "Acceso denegado. Debes adquirir el Paquete VIP (S/ 25.00).",
            status=403,
        )

    respuestas = RespuestaDetalle.objects.filter(
        intento=intento
    ).select_related('pregunta', 'pregunta__asignatura')

    return render(request, 'simulacro/solucionario_vip.html', {
        'intento': intento,
        'respuestas': respuestas,
    })
