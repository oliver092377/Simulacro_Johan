"""
Vistas de pagos: procesar pago, generar PDF, QR de pago.
"""
import io
import logging

from django.contrib.auth.decorators import login_required
from django.core.files.base import ContentFile
from django.http import HttpResponse, FileResponse
from django.shortcuts import render, redirect, get_object_or_404

from ..models import Intento
from ..services import generar_qr_whatsapp_pago
from ..utils import generar_pdf_diagnostico

logger = logging.getLogger('simulacro')


@login_required
def procesar_pago(request, intento_id):
    """Muestra la pagina de pago con QR."""
    intento = get_object_or_404(Intento, id=intento_id, estudiante=request.user)
    return render(request, 'simulacro/pagar.html', {'intento': intento})


@login_required
def generar_reporte_pdf(request, intento_id):
    """Genera o entrega el reporte PDF del diagnostico."""
    intento_actual = get_object_or_404(Intento, id=intento_id)

    if intento_actual.estudiante != request.user and not request.user.is_superuser:
        return redirect('inicio')

    if not intento_actual.pagado_reporte and not request.user.is_superuser:
        return redirect('procesar_pago', intento_id=intento_actual.id)

    if intento_actual.reporte_pdf:
        return FileResponse(
            intento_actual.reporte_pdf.open('rb'),
            as_attachment=True,
            filename=f"Reporte_VILLTECC_{intento_actual.id}.pdf",
        )

    buffer = generar_pdf_diagnostico(intento_actual)
    nombre_archivo = f"Reporte_VILLTECC_{intento_actual.id}.pdf"
    intento_actual.reporte_pdf.save(nombre_archivo, ContentFile(buffer.getvalue()))
    intento_actual.save()

    return FileResponse(buffer, as_attachment=True, filename=nombre_archivo)


@login_required
def generar_qr_whatsapp(request, intento_id):
    """Genera imagen QR con link de WhatsApp para comprobante de pago."""
    intento = get_object_or_404(Intento, id=intento_id)
    buffer = generar_qr_whatsapp_pago(intento.estudiante.username)
    return HttpResponse(buffer.getvalue(), content_type="image/png")
