"""
Views package para el simulacro VILLTECC.
Re-exporta todas las vistas para mantener compatibilidad con urls.py.
"""
from .auth import inicio, registro, verificar_email
from .auth import VILLTECCPasswordResetView, VILLTECCPasswordResetConfirmView
from .examen import realizar_examen, guardar_respuesta_ajax, sincronizar_tiempo_ajax, finalizar_examen_ajax
from .resultados import (
    ver_resultado, ver_ranking, mis_examenes,
    generar_qr_resultado, descargar_solucionario_pdf,
)
from .pagos import procesar_pago, generar_reporte_pdf, generar_qr_whatsapp

__all__ = [
    'inicio',
    'registro',
    'verificar_email',
    'VILLTECCPasswordResetView',
    'VILLTECCPasswordResetConfirmView',
    'realizar_examen',
    'guardar_respuesta_ajax',
    'sincronizar_tiempo_ajax',
    'finalizar_examen_ajax',
    'ver_resultado',
    'ver_ranking',
    'mis_examenes',
    'generar_qr_resultado',
    'descargar_solucionario_pdf',
    'procesar_pago',
    'generar_reporte_pdf',
    'generar_qr_whatsapp',
]
