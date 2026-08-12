from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import PerfilEstudiante

CARRERAS_UNSA = [
    ('Biomedicas', (
        ('Medicina Humana', 'Medicina Humana'),
        ('Enfermeria', 'Enfermeria'),
        ('Biologia', 'Biologia'),
        ('Ciencias de la Nutricion', 'Ciencias de la Nutricion'),
        ('Agronomia', 'Agronomia'),
        ('Ingenieria Pesquera', 'Ingenieria Pesquera'),
    )),
    ('Ingenierias', (
        ('Arquitectura', 'Arquitectura'),
        ('Ingenieria Civil', 'Ingenieria Civil'),
        ('Ingenieria Ambiental', 'Ingenieria Ambiental'),
        ('Ingenieria Sanitaria', 'Ingenieria Sanitaria'),
        ('Ingenieria de Sistemas', 'Ingenieria de Sistemas'),
        ('Ciencia de la Computacion', 'Ciencia de la Computacion'),
        ('Ingenieria Industrial', 'Ingenieria Industrial'),
        ('Ingenieria Mecanica', 'Ingenieria Mecanica'),
        ('Ingenieria Metalurgica', 'Ingenieria Metalurgica'),
        ('Ingenieria Electronica', 'Ingenieria Electronica'),
        ('Ingenieria de Telecomunicaciones', 'Ingenieria de Telecomunicaciones'),
        ('Ingenieria de Minas', 'Ingenieria de Minas'),
        ('Ingenieria Geologica', 'Ingenieria Geologica'),
        ('Ingenieria Geofisica', 'Ingenieria Geofisica'),
        ('Ingenieria de Materiales', 'Ingenieria de Materiales'),
        ('Ingenieria Quimica', 'Ingenieria Quimica'),
        ('Ingenieria de Industrias Alimentarias', 'Ingenieria de Industrias Alimentarias'),
        ('Matematicas', 'Matematicas'),
        ('Fisica', 'Fisica'),
        ('Quimica', 'Quimica'),
    )),
    ('Sociales', (
        ('Derecho', 'Derecho'),
        ('Administracion', 'Administracion'),
        ('Contabilidad', 'Contabilidad'),
        ('Psicologia', 'Psicologia'),
        ('Educacion', 'Educacion'),
        ('Turismo y Hoteleria', 'Turismo y Hoteleria'),
        ('Antropologia', 'Antropologia'),
        ('Trabajo Social', 'Trabajo Social'),
        ('Sociologia', 'Sociologia'),
        ('Historia', 'Historia'),
        ('Artes', 'Artes'),
        ('Relaciones Industriales', 'Relaciones Industriales'),
        ('Gestion', 'Gestion'),
        ('Ciencias de la Comunicacion', 'Ciencias de la Comunicacion'),
        ('Literatura y Linguistica', 'Literatura y Linguistica'),
        ('Filosofia', 'Filosofia'),
        ('Economia', 'Economia'),
        ('Finanzas', 'Finanzas'),
        ('Banca y Seguros', 'Banca y Seguros'),
        ('Marketing', 'Marketing'),
    ))
]


class RegistroUsuarioForm(UserCreationForm):
    username = forms.CharField(
        max_length=8,
        min_length=8,
        required=True,
        label="DNI (Sera tu usuario unico)",
        widget=forms.TextInput(attrs={
            'pattern': '[0-9]{8}',
            'title': 'Debe ingresar exactamente los 8 numeros de su DNI',
            'placeholder': 'Ej: 76543210'
        })
    )
    first_name = forms.CharField(max_length=30, required=True, label="Nombres")
    last_name = forms.CharField(max_length=30, required=True, label="Apellidos")
    email = forms.EmailField(required=True, label="Correo Electronico",
                             help_text="Enviaremos un enlace de verificacion a este correo.")
    telefono = forms.CharField(max_length=15, required=True, label="Numero de Celular")
    carrera = forms.ChoiceField(choices=CARRERAS_UNSA, required=True, label="Carrera a la que postulas")

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username', 'first_name', 'last_name', 'email')

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if not username.isdigit():
            raise forms.ValidationError("El DNI debe contener unicamente numeros.")
        return username

    def clean_first_name(self):
        return self.cleaned_data.get('first_name', '').strip().upper()

    def clean_last_name(self):
        return self.cleaned_data.get('last_name', '').strip().upper()

    def save(self, commit=True):
        user = super().save(commit=False)
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.email = self.cleaned_data['email']

        if commit:
            user.save()
            PerfilEstudiante.objects.update_or_create(
                user=user,
                defaults={
                    'telefono': self.cleaned_data['telefono'],
                    'carrera': self.cleaned_data['carrera']
                }
            )
        return user
