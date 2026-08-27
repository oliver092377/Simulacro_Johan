"""Herramientas protegidas para usuarios administradores."""
import io
import logging

from django.contrib.admin.views.decorators import staff_member_required
from django.http import FileResponse, HttpResponse
from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string

from ..models import Area
from ..services import seleccionar_preguntas_examen

logger = logging.getLogger('simulacro')


@staff_member_required
def descargar_examen_pdf(request, area_id):
    """Renderiza el examen con MathJax en Chromium y lo descarga como PDF."""
    area = get_object_or_404(Area, id=area_id)
    preguntas = seleccionar_preguntas_examen(area)

    html = render_to_string(
        'simulacro/examen_pdf.html',
        {
            'area': area,
            'preguntas': preguntas,
            'base_url': request.build_absolute_uri('/'),
        },
        request=request,
    )

    try:
        from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
        from playwright.sync_api import sync_playwright

        with sync_playwright() as playwright:
            browser = playwright.chromium.launch()
            try:
                page = browser.new_page()
                page.set_content(html, wait_until='networkidle')
                page.wait_for_function(
                    """() => window.MathJax && MathJax.startup && MathJax.startup.promise""",
                    timeout=15000,
                )
                page.evaluate("() => MathJax.startup.promise")
                page.evaluate("() => MathJax.typesetPromise()")
                page.wait_for_timeout(250)
                pdf_bytes = page.pdf(
                    format='Letter',
                    print_background=True,
                    prefer_css_page_size=True,
                    margin={
                        'top': '14mm',
                        'right': '12mm',
                        'bottom': '14mm',
                        'left': '12mm',
                    },
                )
            finally:
                browser.close()
    except ImportError:
        logger.exception('Playwright no esta instalado')
        return HttpResponse(
            'El generador PDF requiere Playwright. Ejecute: playwright install chromium',
            status=503,
        )
    except PlaywrightTimeoutError:
        logger.exception('MathJax no termino de renderizar el examen')
        return HttpResponse(
            'MathJax no pudo terminar de renderizar el examen.',
            status=503,
        )
    except Exception:
        logger.exception('Error generando el PDF administrativo')
        return HttpResponse(
            'No se pudo generar el PDF del examen.',
            status=503,
        )

    nombre = f'examen_{area.nombre.lower()}_villtecc.pdf'
    return FileResponse(
        io.BytesIO(pdf_bytes),
        as_attachment=True,
        filename=nombre,
        content_type='application/pdf',
    )
