"""
Vistas de examen: realizar examen con auto-save y persistencia.
Timer basado en segundos_activos (solo avanza cuando pestaña visible).
"""
import json
import logging

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from ..models import Area, Intento, Pregunta, Alternativa, MatrizPeso
from ..services import (
    seleccionar_preguntas_examen,
    procesar_respuestas_examen,
    guardar_respuesta_auto_save,
    calcular_penalidad,
    DURACION_EXAMEN_MINUTOS,
)

logger = logging.getLogger('simulacro')
DURACION_TOTAL_SEGUNDOS = DURACION_EXAMEN_MINUTOS * 60


@login_required
def realizar_examen(request, area_id):
    """Vista principal del examen: crea/reanuda Intento, muestra preguntas, procesa envio."""
    area_seleccionada = get_object_or_404(Area, id=area_id)

    perfil = getattr(request.user, 'perfil', None)
    if not perfil or not perfil.examen_habilitado:
        return render(request, 'simulacro/inicio.html', {
            'areas': Area.objects.all(),
            'examen_habilitado': False,
            'mensaje_error': 'Tu examen aun no ha sido habilitado por el administrador.',
        })

    if not perfil.email_verificado:
        return render(request, 'simulacro/inicio.html', {
            'areas': Area.objects.all(),
            'examen_habilitado': False,
            'mensaje_error': 'Debes verificar tu correo electronico antes de rendir el examen.',
        })

    if not perfil.puede_rendir:
        return render(request, 'simulacro/inicio.html', {
            'areas': Area.objects.all(),
            'examen_habilitado': False,
            'mensaje_error': 'Ya rendiste tu examen. Si deseas rendirlo nuevamente, contacta al administrador.',
        })

    # Buscar si ya tiene un examen activo (en_curso) en CUALQUIER area
    intento_activo_global = Intento.objects.filter(
        estudiante=request.user,
        en_curso=True,
    ).select_related('area').first()

    if intento_activo_global:
        if intento_activo_global.area_id != area_id:
            return render(request, 'simulacro/inicio.html', {
                'areas': Area.objects.all(),
                'examen_habilitado': False,
                'mensaje_error': f'Ya tienes un examen activo de {intento_activo_global.area.nombre}. Debes finalizarlo primero.',
            })
        intento = intento_activo_global
    else:
        preguntas_examen = seleccionar_preguntas_examen(area_seleccionada)
        preguntas_ids = [p.id for p in preguntas_examen]
        intento = Intento.objects.create(
            estudiante=request.user,
            area=area_seleccionada,
            en_curso=True,
            segundos_activos=0,
            preguntas_orden=preguntas_ids,
        )

    # POST: envio final del examen (boton "Finalizar Examen")
    if request.method == 'POST':
        if not intento.en_curso:
            return redirect('ver_resultado', intento_id=intento.id)
        procesar_respuestas_examen(intento)
        perfil.puede_rendir = False
        perfil.save()
        return redirect('ver_resultado', intento_id=intento.id)

    # GET: mostrar examen
    if intento.preguntas_orden:
        preguntas_ids = intento.preguntas_orden
        preguntas_examen = list(
            Pregunta.objects.filter(id__in=preguntas_ids)
            .select_related('asignatura')
        )
        pregunta_map = {p.id: p for p in preguntas_examen}
        preguntas_examen = [pregunta_map[pid] for pid in preguntas_ids if pid in pregunta_map]
    else:
        preguntas_examen = seleccionar_preguntas_examen(area_seleccionada)

    # Calcular segundos restantes desde segundos_activos (timer congelable)
    segundos_restantes = max(DURACION_TOTAL_SEGUNDOS - intento.segundos_activos, 0)

    if segundos_restantes <= 0:
        procesar_respuestas_examen(intento)
        perfil.puede_rendir = False
        perfil.save()
        return redirect('ver_resultado', intento_id=intento.id)

    # Cargar respuestas ya guardadas para pre-seleccionar
    respuestas_existentes = {}
    from ..models import RespuestaDetalle
    respuestas_bd = RespuestaDetalle.objects.filter(intento=intento).values_list('pregunta_id', 'opcion_marcada')
    for pid, texto_opcion in respuestas_bd:
        if texto_opcion and texto_opcion != "Imagen" and texto_opcion != "Sin respuesta":
            alt = Alternativa.objects.filter(
                pregunta_id=pid, texto=texto_opcion
            ).values_list('id', flat=True).first()
            if alt:
                respuestas_existentes[str(pid)] = str(alt)
        elif texto_opcion == "Imagen":
            alt = Alternativa.objects.filter(
                pregunta_id=pid, texto__isnull=True, imagen__isnull=False
            ).values_list('id', flat=True).first()
            if alt:
                respuestas_existentes[str(pid)] = str(alt)

    return render(request, 'simulacro/examen.html', {
        'area': area_seleccionada,
        'intento': intento,
        'preguntas': preguntas_examen,
        'segundos_restantes': segundos_restantes,
        'respuestas_json': json.dumps(respuestas_existentes),
    })


@login_required
@require_POST
def guardar_respuesta_ajax(request, intento_id):
    """Guarda una respuesta individual via AJAX (auto-save)."""
    try:
        intento = Intento.objects.get(id=intento_id, estudiante=request.user, en_curso=True)
    except Intento.DoesNotExist:
        return JsonResponse({'ok': False, 'error': 'Examen no encontrado o ya finalizado'}, status=404)

    segundos_restantes = DURACION_TOTAL_SEGUNDOS - intento.segundos_activos
    if segundos_restantes <= 0:
        return JsonResponse({'ok': False, 'error': 'Tiempo expirado'}, status=400)

    try:
        data = json.loads(request.body)
        pregunta_id = int(data.get('pregunta_id', 0))
        alternativa_id = int(data.get('alternativa_id', 0))
    except (json.JSONDecodeError, ValueError, TypeError):
        return JsonResponse({'ok': False, 'error': 'Datos invalidos'}, status=400)

    exito = guardar_respuesta_auto_save(intento, pregunta_id, alternativa_id)
    if exito:
        return JsonResponse({'ok': True})
    return JsonResponse({'ok': False, 'error': 'No se pudo guardar'}, status=400)


@login_required
@csrf_exempt
@require_POST
def sincronizar_tiempo_ajax(request, intento_id):
    """Recibe un DELTA de segundos activos (nuevos desde la ultima sync) y lo suma al total."""
    try:
        intento = Intento.objects.get(id=intento_id, estudiante=request.user, en_curso=True)
    except Intento.DoesNotExist:
        return JsonResponse({'ok': False, 'error': 'Examen no encontrado'}, status=404)

    try:
        raw = request.body.decode('utf-8')
        data = json.loads(raw)
        segundos_activos = int(data.get('segundos_activos', 0))
    except (json.JSONDecodeError, ValueError, TypeError, UnicodeDecodeError):
        return JsonResponse({'ok': False, 'error': 'Datos invalidos'}, status=400)

    # Validar que no exceda el maximo; el cliente envia un DELTA (segundos nuevos desde ultima sync)
    delta = max(0, min(segundos_activos, DURACION_TOTAL_SEGUNDOS))
    nuevos_total = intento.segundos_activos + delta
    nuevos_total = min(nuevos_total, DURACION_TOTAL_SEGUNDOS)
    intento.segundos_activos = nuevos_total
    intento.save(update_fields=['segundos_activos'])

    segundos_restantes = max(DURACION_TOTAL_SEGUNDOS - intento.segundos_activos, 0)

    return JsonResponse({
        'ok': True,
        'segundos_restantes': segundos_restantes,
        'tiempo_agotado': segundos_restantes <= 0,
    })


@login_required
@require_POST
def finalizar_examen_ajax(request, intento_id):
    """Finaliza el examen cuando se agota el tiempo o por otro motivo."""
    try:
        intento = Intento.objects.get(id=intento_id, estudiante=request.user, en_curso=True)
    except Intento.DoesNotExist:
        return JsonResponse({'ok': False, 'error': 'Examen no encontrado'}, status=404)

    procesar_respuestas_examen(intento)

    perfil = getattr(request.user, 'perfil', None)
    if perfil:
        perfil.puede_rendir = False
        perfil.save()

    return JsonResponse({
        'ok': True,
        'redirect_url': f'/resultado/{intento.id}/',
    })
