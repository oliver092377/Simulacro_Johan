from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import strip_tags, format_html
from django.urls import reverse
from .models import Area, Asignatura, MatrizPeso, Pregunta, Alternativa, Intento, RespuestaDetalle, PerfilEstudiante

# 1. Configuración para Áreas (Simple)
admin.site.register(Area)

# 2. Configuración para Asignaturas
@admin.register(Asignatura)
class AsignaturaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'eje_tematico')
    list_filter = ('eje_tematico',)
    search_fields = ('nombre',)

# 3. Configuración para la Matriz de Pesos
@admin.register(MatrizPeso)
class MatrizPesoAdmin(admin.ModelAdmin):
    list_display = ('area', 'asignatura', 'peso_pregunta', 'cantidad_preguntas')
    list_filter = ('area', 'asignatura__eje_tematico')
    list_editable = ('peso_pregunta', 'cantidad_preguntas')

# --- CONFIGURACIÓN DE PREGUNTAS ---
class AlternativaInline(admin.TabularInline):
    model = Alternativa
    extra = 5
    fields = ('texto', 'imagen', 'es_correcta')

@admin.register(Pregunta)
class PreguntaAdmin(admin.ModelAdmin):
    inlines = [AlternativaInline]
    list_display = ('texto_corto', 'asignatura', 'etiqueta', 'tiene_imagen', 'tiene_solucion')
    list_filter = ('etiqueta', 'asignatura__eje_tematico', 'asignatura')
    list_editable = ('etiqueta',)
    search_fields = ('texto_pregunta', 'tema_especifico')

    def texto_corto(self, obj):
        return strip_tags(obj.texto_pregunta)[:50] + "..."
    texto_corto.short_description = "Enunciado"

    def tiene_imagen(self, obj):
        return "✅ Sí" if obj.imagen else "❌ No"
    tiene_imagen.short_description = "Img"

    def tiene_solucion(self, obj):
        if obj.solucion_texto or obj.solucion_imagen:
            return "💡 Lista"
        return "⚠️ Falta"
    tiene_solucion.short_description = "Solucionario"

# --- CONFIGURACIÓN DE INTENTOS (EXÁMENES Y COBROS) ---
class RespuestaInline(admin.TabularInline):
    model = RespuestaDetalle
    readonly_fields = ('pregunta', 'opcion_marcada', 'es_correcta')
    extra = 0
    can_delete = False

@admin.action(description='🟢 Activar Nivel 1: Diagnóstico PDF (S/ 10.00)')
def activar_nivel_1(modeladmin, request, queryset):
    updated_count = queryset.update(nivel_acceso=1, pagado_reporte=True)
    modeladmin.message_user(request, f"✅ {updated_count} alumno(s) actualizados a Nivel 1 (Diagnóstico PDF + Check activado).")

@admin.action(description='⭐ Activar Nivel 2: VIP Solucionario (S/ 25.00)')
def activar_nivel_2(modeladmin, request, queryset):
    updated_count = queryset.update(nivel_acceso=2, pagado_reporte=True)
    modeladmin.message_user(request, f"⭐ {updated_count} alumno(s) actualizados a Nivel 2 (VIP Solucionario + Check activado).")

@admin.register(Intento)
class IntentoAdmin(admin.ModelAdmin):
    list_display = ('estudiante', 'area', 'fecha_inicio', 'puntaje_final', 'nivel_acceso', 'pagado_reporte', 'ver_reporte_link')
    list_editable = ('nivel_acceso', 'pagado_reporte')
    list_filter = ('nivel_acceso', 'pagado_reporte', 'area', 'fecha_inicio')
    inlines = [RespuestaInline]
    actions = [activar_nivel_1, activar_nivel_2]
    search_fields = ('estudiante__username', 'estudiante__first_name', 'estudiante__last_name')

    def save_model(self, request, obj, form, change):
        if obj.nivel_acceso >= 1:
            obj.pagado_reporte = True
        elif obj.nivel_acceso == 0:
            obj.pagado_reporte = False
        super().save_model(request, obj, form, change)

    def ver_reporte_link(self, obj):
        url = reverse('descargar_pdf', args=[obj.id])
        return format_html('<a class="button" href="{}" target="_blank">🖨️ Ver PDF</a>', url)
    ver_reporte_link.short_description = "Reporte"

# --- CONFIGURACIÓN DE USUARIOS ---
class PerfilInline(admin.StackedInline):
    model = PerfilEstudiante
    can_delete = False
    verbose_name_plural = 'Datos de Contacto'

class UserAdmin(BaseUserAdmin):
    inlines = (PerfilInline,)
    list_display = ('username', 'first_name', 'last_name', 'get_carrera', 'get_telefono', 'ver_historial')
    list_filter = ('perfil__carrera', 'is_active')

    def get_telefono(self, obj):
        return obj.perfil.telefono if hasattr(obj, 'perfil') else "-"
    get_telefono.short_description = '📱 Celular'

    def get_carrera(self, obj):
        return obj.perfil.carrera if hasattr(obj, 'perfil') else "-"
    get_carrera.short_description = '🎓 Carrera'

    def ver_historial(self, obj):
        url = reverse('admin:simulacro_intento_changelist') + f'?estudiante__id__exact={obj.id}'
        return format_html('<a class="button" href="{}">📂 Ver Reportes</a>', url)
    ver_historial.short_description = 'Acciones'

admin.site.unregister(User)
admin.site.register(User, UserAdmin)

# --- ADMIN DE PERFIL ESTUDIANTE ---
@admin.register(PerfilEstudiante)
class PerfilEstudianteAdmin(admin.ModelAdmin):
    list_display = ('user', 'carrera', 'telefono', 'examen_habilitado', 'email_verificado', 'puede_rendir')
    list_filter = ('examen_habilitado', 'email_verificado', 'puede_rendir', 'carrera')
    search_fields = ('user__username', 'user__first_name', 'user__last_name')
    list_editable = ('examen_habilitado', 'puede_rendir')

@admin.action(description='✅ Habilitar examen para usuarios seleccionados')
def habilitar_examen(modeladmin, request, queryset):
    updated_count = queryset.update(examen_habilitado=True)
    modeladmin.message_user(request, f"✅ {updated_count} usuario(s) habilitado(s) para rendir el examen.")

@admin.action(description='🔄 Habilitar reintento de examen')
def habilitar_reintento(modeladmin, request, queryset):
    updated_count = queryset.update(puede_rendir=True)
    modeladmin.message_user(request, f"🔄 {updated_count} estudiante(s) habilitado(s) para rendir nuevamente.")

PerfilEstudianteAdmin.actions = [habilitar_examen, habilitar_reintento]