from django.conf import settings


def whatsapp_context(request):
    """Context processor que expone el numero de WhatsApp a todos los templates."""
    return {
        'WHATSAPP_NUMERO': settings.WHATSAPP_NUMERO,
    }
