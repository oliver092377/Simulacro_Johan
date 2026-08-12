"""
Vistas de autenticacion: inicio, registro, verificacion de correo, password reset.
"""
import logging

from django.conf import settings
from django.contrib.auth import login
from django.contrib.auth.views import PasswordResetView, PasswordResetConfirmView
from django.contrib.auth.tokens import default_token_generator
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import send_mail
from django.shortcuts import render, redirect
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str

from ..forms import RegistroUsuarioForm
from ..models import Area
from ..tokens import email_verification_token

logger = logging.getLogger('simulacro')


def inicio(request):
    """Pantalla de inicio con seleccion de area."""
    areas = Area.objects.all()
    examen_habilitado = False
    if request.user.is_authenticated:
        perfil = getattr(request.user, 'perfil', None)
        if perfil:
            examen_habilitado = perfil.examen_habilitado
    return render(request, 'simulacro/inicio.html', {
        'areas': areas,
        'examen_habilitado': examen_habilitado,
    })


def registro(request):
    """Registro de nuevos postulantes con verificacion de correo."""
    if request.method == 'POST':
        form = RegistroUsuarioForm(request.POST)
        if form.is_valid():
            usuario = form.save(commit=False)
            usuario.is_active = False  # Inactivo hasta verificar email
            usuario.save()

            # Crear perfil si no existe
            from ..models import PerfilEstudiante
            PerfilEstudiante.objects.get_or_create(user=usuario)

            # Enviar email de verificacion
            _enviar_email_verificacion(request, usuario)

            return render(request, 'simulacro/email_sent.html', {
                'email': usuario.email or usuario.username,
            })
    else:
        form = RegistroUsuarioForm()
    return render(request, 'simulacro/registro.html', {'form': form})


def verificar_email(request, uidb64, token):
    """Verifica el email del usuario y activa su cuenta."""
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        from django.contrib.auth.models import User
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and email_verification_token.check_token(user, token):
        user.is_active = True
        user.save()

        # Actualizar perfil
        perfil, _ = user.perfil.__class__.objects.get_or_create(user=user)
        perfil.email_verificado = True
        perfil.save()

        login(request, user)
        return render(request, 'simulacro/email_verified.html')
    else:
        return render(request, 'simulacro/email_invalid.html')


def _enviar_email_verificacion(request, user):
    """Envia el email de verificacion al usuario."""
    current_site = get_current_site(request)
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = email_verification_token.make_token(user)

    verification_url = f"{request.scheme}://{current_site.domain}/verificar-email/{uid}/{token}/"

    subject = 'Verifica tu correo - VILLTECC'
    message = f"""
    Hola {user.first_name or user.username},

    Gracias por registrarte en VILLTECC.

    Para activar tu cuenta y acceder a los simulacros UNSA,
    haz clic en el siguiente enlace:

    {verification_url}

    Si no creaste esta cuenta, ignora este mensaje.

    Saludos,
    Equipo VILLTECC
    """

    email_destino = user.email
    if not email_destino:
        logger.warning("Usuario %s no tiene email configurado", user.username)
        return

    try:
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [email_destino],
            fail_silently=False,
        )
        logger.info("Email de verificacion enviado a %s", email_destino)
        # En desarrollo, loguear la URL para verificacion manual
        if settings.DEBUG:
            logger.info("URL de verificacion (copia y pega en el navegador): %s", verification_url)
    except Exception as e:
        logger.error("Error enviando email de verificacion a %s: %s", email_destino, e)
        # En desarrollo, loguear la URL aunque falle el envio
        if settings.DEBUG:
            logger.info("URL de verificacion (copia y pega en el navegador): %s", verification_url)


class VILLTECCPasswordResetView(PasswordResetView):
    """Vista personalizada de recuperacion de contrasena."""
    template_name = 'simulacro/password_reset.html'
    email_template_name = 'simulacro/password_reset_email.html'
    subject_template_name = 'simulacro/password_reset_subject.txt'
    success_url = '/password-reset/done/'


class VILLTECCPasswordResetConfirmView(PasswordResetConfirmView):
    """Vista personalizada de confirmacion de nueva contrasena."""
    template_name = 'simulacro/password_reset_confirm.html'
    success_url = '/accounts/login/'
