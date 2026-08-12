from django.db import models
from django.contrib.auth.models import User
from django_ckeditor_5.fields import CKEditor5Field


class Area(models.Model):
    """Areas de postulacion a la UNSA."""
    NOMBRE_CHOICES = [
        ('ING', 'Ingenierias'),
        ('BIO', 'Biomedicas'),
        ('SOC', 'Sociales'),
        ('EXT', 'Extraordinario'),
    ]
    nombre = models.CharField(max_length=3, choices=NOMBRE_CHOICES, unique=True)

    class Meta:
        verbose_name = 'Area'
        verbose_name_plural = 'Areas'

    def __str__(self):
        return self.get_nombre_display()


class Asignatura(models.Model):
    """Cursos base (Algebra, Historia, etc.)."""
    nombre = models.CharField(max_length=100)
    eje_tematico = models.CharField(max_length=100)

    class Meta:
        verbose_name = 'Asignatura'
        verbose_name_plural = 'Asignaturas'

    def __str__(self):
        return f"{self.eje_tematico} - {self.nombre}"


class MatrizPeso(models.Model):
    """Matriz de pesos por area y asignatura (RCU N 0220-2024)."""
    area = models.ForeignKey(Area, on_delete=models.CASCADE)
    asignatura = models.ForeignKey(Asignatura, on_delete=models.CASCADE)
    peso_pregunta = models.DecimalField(max_digits=15, decimal_places=10)
    cantidad_preguntas = models.IntegerField(default=0)

    class Meta:
        unique_together = ('area', 'asignatura')
        verbose_name = 'Matriz de Peso'
        verbose_name_plural = 'Matriz de Pesos'

    def __str__(self):
        return f"{self.area} - {self.asignatura}: {self.peso_pregunta} pts"


class Pregunta(models.Model):
    """Pregunta del banco de examenes."""
    asignatura = models.ForeignKey(Asignatura, on_delete=models.CASCADE)
    tema_especifico = models.CharField(max_length=200, help_text="Ej: Ecuaciones Diferenciales")
    etiqueta = models.CharField(max_length=50, default='SIMULACRO_1')
    texto_pregunta = CKEditor5Field('Texto de la Pregunta', config_name='default')
    imagen = models.ImageField(upload_to='preguntas/', null=True, blank=True)
    solucion_texto = CKEditor5Field(
        'Explicacion / Solucionario',
        config_name='default',
        blank=True,
        null=True,
    )
    solucion_imagen = models.ImageField(
        upload_to='soluciones/',
        null=True,
        blank=True,
        verbose_name="Foto de resolucion a mano (Opcional)",
    )

    class Meta:
        verbose_name = 'Pregunta'
        verbose_name_plural = 'Preguntas'

    def __str__(self):
        return f"{self.asignatura} - {self.tema_especifico}"


class Alternativa(models.Model):
    """Alternativa de respuesta para una pregunta."""
    pregunta = models.ForeignKey(Pregunta, related_name='alternativas', on_delete=models.CASCADE)
    texto = models.CharField(max_length=500, blank=True, null=True, help_text="Puede incluir codigo LaTeX entre $")
    imagen = models.ImageField(upload_to='alternativas/', null=True, blank=True)
    es_correcta = models.BooleanField(default=False, verbose_name="Es la correcta?")

    class Meta:
        verbose_name = 'Alternativa'
        verbose_name_plural = 'Alternativas'

    def __str__(self):
        if self.texto:
            return f"Alternativa: {self.texto[:20]}..."
        return f"Alternativa {self.id} (Imagen)"


class Intento(models.Model):
    """Intento de examen de un estudiante."""
    estudiante = models.ForeignKey(User, on_delete=models.CASCADE)
    area = models.ForeignKey(Area, on_delete=models.CASCADE)
    fecha_inicio = models.DateTimeField(auto_now_add=True)
    fecha_fin = models.DateTimeField(null=True, blank=True)
    en_curso = models.BooleanField(default=False, verbose_name="Examen en curso")
    segundos_activos = models.IntegerField(default=0, verbose_name="Segundos activos acumulados")
    preguntas_orden = models.JSONField(null=True, blank=True, verbose_name="Orden de preguntas")
    reporte_pdf = models.FileField(upload_to='reportes_pdf/', null=True, blank=True)
    puntaje_final = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)
    pagado_reporte = models.BooleanField(default=False)
    NIVELES_ACCESO = [
        (0, 'Nivel 0: Gratis (Solo Nota Final)'),
        (1, 'Nivel 1: Diagnostico S/ 10 (Semaforo + Reporte PDF)'),
        (2, 'Nivel 2: VIP S/ 25 (Todo + Solucionario PDF)'),
    ]
    nivel_acceso = models.IntegerField(
        choices=NIVELES_ACCESO,
        default=0,
        verbose_name="Nivel de Desbloqueo",
    )

    class Meta:
        verbose_name = 'Intento'
        verbose_name_plural = 'Intentos'
        indexes = [
            models.Index(fields=['estudiante', 'area', 'fecha_inicio']),
            models.Index(fields=['estudiante', '-fecha_inicio']),
            models.Index(fields=['-puntaje_final']),
        ]

    def __str__(self):
        return f"{self.estudiante.username} - {self.area} - {self.fecha_inicio.date()}"


class RespuestaDetalle(models.Model):
    """Detalle de respuesta de una pregunta en un intento."""
    intento = models.ForeignKey(Intento, related_name='respuestas', on_delete=models.CASCADE)
    pregunta = models.ForeignKey(Pregunta, on_delete=models.CASCADE)
    opcion_marcada = models.CharField(max_length=200, blank=True, null=True)
    es_correcta = models.BooleanField(default=False)

    class Meta:
        verbose_name = 'Respuesta Detalle'
        verbose_name_plural = 'Respuestas Detalle'


class PerfilEstudiante(models.Model):
    """Perfil extendido del estudiante."""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='perfil')
    telefono = models.CharField(max_length=15, blank=True, null=True)
    carrera = models.CharField(max_length=100, help_text="Ej: Ingenieria de Sistemas")
    examen_habilitado = models.BooleanField(default=False, verbose_name="Examen habilitado")
    email_verificado = models.BooleanField(default=False, verbose_name="Email verificado")
    puede_rendir = models.BooleanField(default=True, verbose_name="Puede rendir examen")

    class Meta:
        verbose_name = 'Perfil Estudiante'
        verbose_name_plural = 'Perfiles Estudiantes'

    def __str__(self):
        return f"Perfil de {self.user.username}"
