from django.urls import path, include
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    # Inicio y General
    path('', views.inicio, name='inicio'),
    path('ranking/', views.ver_ranking, name='ranking'),

    # Autenticacion
    path('registro/', views.registro, name='registro'),
    path('verificar-email/<str:uidb64>/<str:token>/', views.verificar_email, name='verificar_email'),
    path('accounts/login/', auth_views.LoginView.as_view(template_name='simulacro/login.html'), name='login'),
    path('accounts/', include('django.contrib.auth.urls')),

    # Recuperacion de contrasena
    path('password-reset/', views.VILLTECCPasswordResetView.as_view(), name='password_reset'),
    path('password-reset/done/', auth_views.PasswordResetDoneView.as_view(
        template_name='simulacro/email_sent.html'
    ), name='password_reset_done'),
    path('password-reset-confirm/<str:uidb64>/<str:token>/',
         views.VILLTECCPasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('password-reset-complete/', auth_views.PasswordResetCompleteView.as_view(
        template_name='simulacro/email_verified.html'
    ), name='password_reset_complete'),

    # Flujo de Examen
    path('examen/<int:area_id>/', views.realizar_examen, name='realizar_examen'),
    path('ajax/guardar-respuesta/<int:intento_id>/', views.guardar_respuesta_ajax, name='guardar_respuesta_ajax'),
    path('ajax/sincronizar-tiempo/<int:intento_id>/', views.sincronizar_tiempo_ajax, name='sincronizar_tiempo_ajax'),
    path('ajax/finalizar-examen/<int:intento_id>/', views.finalizar_examen_ajax, name='finalizar_examen_ajax'),
    path('resultado/<int:intento_id>/', views.ver_resultado, name='ver_resultado'),

    # Pagos y Servicios Externos
    path('pagar/<int:intento_id>/', views.procesar_pago, name='procesar_pago'),
    path('reporte/<int:intento_id>/', views.generar_reporte_pdf, name='generar_reporte_pdf'),

    # Recursos Dinamicos (QR)
    path('qr_whatsapp/<int:intento_id>/', views.generar_qr_whatsapp, name='generar_qr_whatsapp'),
    path('qr_resultado/<int:intento_id>/', views.generar_qr_resultado, name='generar_qr_resultado'),
    path('reporte_pdf/<int:intento_id>/', views.generar_reporte_pdf, name='descargar_pdf'),

    path('mis-examenes/', views.mis_examenes, name='mis_examenes'),
    path('descargar-solucionario/<int:intento_id>/', views.descargar_solucionario_pdf, name='descargar_solucionario_pdf'),

    # Descarga administrativa de exámenes
    path('herramientas-admin/descargar-examen/<int:area_id>/', views.descargar_examen_pdf, name='admin_descargar_examen_pdf'),
]
