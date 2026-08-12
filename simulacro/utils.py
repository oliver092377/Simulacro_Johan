# simulacro/utils.py
import io
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.utils import ImageReader
from django.utils.timezone import localtime
from .models import Intento, RespuestaDetalle
import os
from django.conf import settings

def generar_pdf_diagnostico(intento_actual):
    """
    Genera el PDF del reporte y devuelve el buffer (el archivo en memoria).
    El gráfico de evolución se coloca al final del documento.
    """
    alumno = intento_actual.estudiante

    # --- 1. PREPARAR DATOS ---
    nota = round(intento_actual.puntaje_final, 4) if intento_actual.puntaje_final else 0
    respuestas = RespuestaDetalle.objects.filter(intento=intento_actual)
    asignaturas_vistas = set([r.pregunta.asignatura for r in respuestas])

    # --- 2. GENERAR GRÁFICO DE EVOLUCIÓN ---
    historial = Intento.objects.filter(
        estudiante=alumno,
        area=intento_actual.area
    ).order_by('fecha_inicio')[:10]

    fechas = [localtime(i.fecha_inicio).strftime('%d/%m') for i in historial]
    puntajes = [i.puntaje_final for i in historial]

    plt.figure(figsize=(7, 3.5))
    plt.plot(fechas, puntajes, marker='o', linestyle='-', color='#2c3e50', linewidth=2, markersize=8)
    plt.title(f'Tu Evolución en {intento_actual.area.get_nombre_display()}', fontsize=13, fontweight='bold')
    plt.xlabel('Intentos', fontsize=11)
    plt.ylabel('Puntaje', fontsize=11)
    plt.grid(True, linestyle='--', alpha=0.5)
    plt.tight_layout()

    buffer_img = io.BytesIO()
    plt.savefig(buffer_img, format='png', dpi=150, bbox_inches='tight')
    plt.close()
    buffer_img.seek(0)

    # --- 3. CREAR PDF ---
    buffer_pdf = io.BytesIO()
    p = canvas.Canvas(buffer_pdf, pagesize=letter)
    p.setTitle(f"Reporte_{alumno.username}")
    # ==========================================
    # NUEVO: AGREGAR LOGO (Membrete Superior)
    # ==========================================
    # Construimos la ruta. Asume que 'Logo.png' está directo en tu carpeta /static/
    # Si está en /static/img/, cambia a: os.path.join(settings.BASE_DIR, 'static', 'img', 'Logo.png')
    ruta_logo = os.path.join(settings.BASE_DIR, 'static', 'img', 'Logo.png')

    if os.path.exists(ruta_logo):
        try:
            # drawImage(archivo, x, y, width, height, ...)
            # x=450, y=730 coloca el logo a la derecha del título
            # Ajusta 'width' y 'height' según el tamaño real de tu imagen
            p.drawImage(ruta_logo, 440, 725, width=120, height=60, preserveAspectRatio=True, mask='auto')
        except Exception as e:
            print(f"Error cargando logo: {e}")
    else:
        # Opción: Imprimir en consola si no encuentra el logo para depurar
        print(f"No se encontró el logo en: {ruta_logo}")

    y = 750

    # ENCABEZADO
    p.setFont("Helvetica-Bold", 20)
    p.drawString(50, y, "REPORTE DE DIAGNÓSTICO - UNSA 2026")
    y -= 30

    p.setFont("Helvetica", 12)
    p.drawString(50, y, f"Estudiante: {alumno.username}")
    y -= 18
    p.drawString(50, y, f"Área: {intento_actual.area.get_nombre_display()}")
    y -= 18
    p.drawString(50, y, f"Fecha: {intento_actual.fecha_inicio.strftime('%d/%m/%Y %H:%M')}")
    y -= 35

    # PUNTAJE DESTACADO
    p.setFillColor(colors.HexColor('#2c3e50'))
    p.rect(380, y-5, 170, 35, fill=True, stroke=False)
    p.setFillColor(colors.white)
    p.setFont("Helvetica-Bold", 16)
    p.drawString(400, y+5, f"Puntaje: {nota}")
    p.setFillColor(colors.black)
    y -= 50

    # LÍNEA SEPARADORA
    p.setStrokeColor(colors.grey)
    p.setLineWidth(1)
    p.line(50, y, 550, y)
    y -= 30

    # ANÁLISIS DE DEBILIDADES
    p.setFont("Helvetica-Bold", 15)
    p.drawString(50, y, "Análisis de Debilidades por Curso")
    y -= 25

    p.setFont("Helvetica", 11)

    for asignatura in sorted(asignaturas_vistas, key=lambda x: x.nombre):
        total = respuestas.filter(pregunta__asignatura=asignatura).count()
        correctas = respuestas.filter(pregunta__asignatura=asignatura, es_correcta=True).count()
        incorrectas = total - correctas
        porcentaje = (correctas / total * 100) if total > 0 else 0

        # Nombre de la asignatura
        p.setFont("Helvetica-Bold", 12)
        p.setFillColor(colors.HexColor('#34495e'))
        p.drawString(60, y, f"{asignatura.nombre}")
        y -= 16

        # Estadísticas
        p.setFont("Helvetica", 10)
        p.setFillColor(colors.black)
        texto_stats = f"Correctas: {correctas}/{total}  •  Errores: {incorrectas}  •  Rendimiento: {porcentaje:.1f}%"
        p.drawString(70, y, texto_stats)
        y -= 14

        # Temas a repasar (si hay errores)
        if incorrectas > 0:
            errores = respuestas.filter(pregunta__asignatura=asignatura, es_correcta=False)
            temas_fallados = set([e.pregunta.tema_especifico for e in errores if e.pregunta.tema_especifico])

            if temas_fallados:
                p.setFillColor(colors.HexColor('#e74c3c'))
                p.setFont("Helvetica-Oblique", 9)
                temas_texto = ", ".join(sorted(temas_fallados))

                # Manejar textos largos
                max_width = 480
                if p.stringWidth(f"⚠ Repasar: {temas_texto}", "Helvetica-Oblique", 9) > max_width:
                    palabras = temas_texto.split(", ")
                    linea_actual = "⚠ Repasar: "

                    for palabra in palabras:
                        if p.stringWidth(linea_actual + palabra + ", ", "Helvetica-Oblique", 9) < max_width:
                            linea_actual += palabra + ", "
                        else:
                            p.drawString(80, y, linea_actual.rstrip(", "))
                            y -= 12
                            linea_actual = "           " + palabra + ", "

                    if linea_actual.strip():
                        p.drawString(80, y, linea_actual.rstrip(", "))
                        y -= 12
                else:
                    p.drawString(80, y, f"⚠ Repasar: {temas_texto}")
                    y -= 12

        y -= 18

        # Control de página
        if y < 280:
            p.showPage()
            y = 750

    # --- 4. GRÁFICO AL FINAL ---
    # Asegurar que estamos en una posición adecuada
    if y < 300:
        p.showPage()
        y = 750

    # Línea separadora antes del gráfico
    y -= 20
    p.setStrokeColor(colors.grey)
    p.setLineWidth(1)
    p.line(50, y, 550, y)
    y -= 40

    # Título del gráfico
    p.setFont("Helvetica-Bold", 15)
    p.setFillColor(colors.black)
    p.drawString(50, y, "Gráfico de Evolución")
    y -= 240  # Espacio para el gráfico

    # Insertar gráfico
    imagen_grafico = ImageReader(buffer_img)
    p.drawImage(imagen_grafico, 50, y, width=500, height=220, preserveAspectRatio=True)

    # PIE DE PÁGINA
    p.setFont("Helvetica-Oblique", 8)
    p.setFillColor(colors.grey)
    p.drawString(50, 30, f"Generado el {localtime(intento_actual.fecha_inicio).strftime('%d/%m/%Y a las %H:%M')}")
    p.drawString(450, 30, "UNSA 2026")

    # --- 5. FINALIZAR Y RETORNAR ---
    p.showPage()
    p.save()

    buffer_pdf.seek(0)
    return buffer_pdf