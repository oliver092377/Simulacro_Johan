from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from simulacro.models import Area, Asignatura, MatrizPeso, Pregunta, Alternativa, PerfilEstudiante, Intento, RespuestaDetalle
from django_ckeditor_5.fields import CKEditor5Field
import random


class Command(BaseCommand):
    help = 'Carga datos de prueba para el simulador VILLTECC'

    def handle(self, *args, **options):
        self.stdout.write('Limpiando datos existentes...')
        RespuestaDetalle.objects.all().delete()
        Intento.objects.all().delete()
        Alternativa.objects.all().delete()
        Pregunta.objects.all().delete()
        MatrizPeso.objects.all().delete()
        Asignatura.objects.all().delete()
        Area.objects.all().delete()
        PerfilEstudiante.objects.all().delete()
        User.objects.filter(is_superuser=False).delete()

        # 1. CREAR ÁREAS
        self.stdout.write('Creando áreas...')
        areas_data = [
            ('ING', 'Ingenierías'),
            ('BIO', 'Biomédicas'),
            ('SOC', 'Sociales'),
            ('EXT', 'Extraordinario'),
        ]
        areas = {}
        for cod, nombre in areas_data:
            area, _ = Area.objects.get_or_create(nombre=cod, defaults={'nombre': cod})
            areas[cod] = area

        # 2. CREAR ASIGNATURAS POR ÁREA
        self.stdout.write('Creando asignaturas...')
        asignaturas_data = {
            'ING': [
                ('Algebra', 'Matemática'),
                ('Geometría Analítica', 'Matemática'),
                ('Física Mecánica', 'Física'),
                ('Física Eléctrica', 'Física'),
                ('Química General', 'Química'),
                ('Biología Celular', 'Biología'),
                ('Literatura', 'Lenguaje'),
                ('Historia Universal', 'Historia'),
            ],
            'BIO': [
                ('Algebra', 'Matemática'),
                ('Biología Celular', 'Biología'),
                ('Genética', 'Biología'),
                ('Fisiología Humana', 'Biología'),
                ('Química Orgánica', 'Química'),
                ('Física General', 'Física'),
                ('Literatura', 'Lenguaje'),
                ('Historia del Perú', 'Historia'),
            ],
            'SOC': [
                ('Algebra', 'Matemática'),
                ('Economía', 'Economía'),
                ('Filosofía', 'Filosofía'),
                ('Literatura', 'Lenguaje'),
                ('Historia Universal', 'Historia'),
                ('Geografía', 'Geografía'),
                ('Psicología', 'Psicología'),
                ('Sociología', 'Sociología'),
            ],
            'EXT': [
                ('Algebra', 'Matemática'),
                ('Biología', 'Biología'),
                ('Historia', 'Historia'),
                ('Literatura', 'Lenguaje'),
                ('Física', 'Física'),
                ('Química', 'Química'),
            ],
        }
        asignaturas = {}
        for area_cod, materias in asignaturas_data.items():
            area = areas[area_cod]
            asignaturas[area_cod] = []
            for nombre, eje in materias:
                asig, _ = Asignatura.objects.get_or_create(
                    nombre=nombre,
                    defaults={'nombre': nombre, 'eje_tematico': eje}
                )
                asignaturas[area_cod].append(asig)

        # 3. CREAR MATRIZ DE PESOS
        self.stdout.write('Creando matriz de pesos...')
        pesos_data = {
            'ING': {
                'Algebra': 0.1500000000,
                'Geometría Analítica': 0.1200000000,
                'Física Mecánica': 0.1000000000,
                'Física Eléctrica': 0.1000000000,
                'Química General': 0.0800000000,
                'Biología Celular': 0.0700000000,
                'Literatura': 0.0500000000,
                'Historia Universal': 0.0500000000,
            },
            'BIO': {
                'Algebra': 0.1000000000,
                'Biología Celular': 0.1500000000,
                'Genética': 0.1200000000,
                'Fisiología Humana': 0.1000000000,
                'Química Orgánica': 0.0800000000,
                'Física General': 0.0700000000,
                'Literatura': 0.0500000000,
                'Historia del Perú': 0.0500000000,
            },
            'SOC': {
                'Algebra': 0.1000000000,
                'Economía': 0.1200000000,
                'Filosofía': 0.1000000000,
                'Literatura': 0.1000000000,
                'Historia Universal': 0.1200000000,
                'Geografía': 0.1000000000,
                'Psicología': 0.0800000000,
                'Sociología': 0.0800000000,
            },
            'EXT': {
                'Algebra': 0.1200000000,
                'Biología': 0.1200000000,
                'Historia': 0.1200000000,
                'Literatura': 0.1200000000,
                'Física': 0.1200000000,
                'Química': 0.1200000000,
            },
        }
        cantidad_preguntas_data = {
            'ING': {
                'Algebra': 5, 'Geometría Analítica': 4, 'Física Mecánica': 4,
                'Física Eléctrica': 3, 'Química General': 3, 'Biología Celular': 3,
                'Literatura': 2, 'Historia Universal': 2,
            },
            'BIO': {
                'Algebra': 3, 'Biología Celular': 5, 'Genética': 4,
                'Fisiología Humana': 3, 'Química Orgánica': 3, 'Física General': 2,
                'Literatura': 2, 'Historia del Perú': 2,
            },
            'SOC': {
                'Algebra': 3, 'Economía': 4, 'Filosofía': 3,
                'Literatura': 3, 'Historia Universal': 4, 'Geografía': 3,
                'Psicología': 2, 'Sociología': 2,
            },
            'EXT': {
                'Algebra': 3, 'Biología': 3, 'Historia': 3,
                'Literatura': 3, 'Física': 3, 'Química': 3,
            },
        }

        for area_cod, pesos in pesos_data.items():
            area = areas[area_cod]
            for asig_nombre, peso in pesos.items():
                asig = None
                for a in asignaturas[area_cod]:
                    if a.nombre == asig_nombre:
                        asig = a
                        break
                if asig:
                    MatrizPeso.objects.get_or_create(
                        area=area,
                        asignatura=asig,
                        defaults={
                            'peso_pregunta': peso,
                            'cantidad_preguntas': cantidad_preguntas_data[area_cod].get(asig_nombre, 2),
                        }
                    )

        # 4. CREAR PREGUNTAS Y ALTERNATIVAS
        self.stdout.write('Creando preguntas y alternativas (mínimo 80)...')
        total_preguntas = 0
        temas = {
            'Algebra': [
                'Resuelve la ecuación: 2x + 5 = 17',
                '¿Cuál es la derivada de f(x) = 3x² + 2x - 1?',
                'Si a + b = 10 y a - b = 4, ¿cuánto vale a?',
                'Calcula el límite de (x² - 1)/(x - 1) cuando x tiende a 1',
                '¿Cuál es la suma de los primeros 50 números naturales?',
                'Resuelve el sistema: 3x + 2y = 12, x - y = 1',
                '¿Cuál es la factorización de x² - 9?',
                'Si log₂(x) = 5, ¿cuánto vale x?',
                'Calcula √(144) + √(25)',
                '¿Cuál es el valor de π redondeado a dos decimales?',
            ],
            'Geometría Analítica': [
                '¿Cuál es la distancia entre los puntos (1,2) y (4,6)?',
                'Encuentra la pendiente de la recta que pasa por (2,3) y (5,11)',
                '¿Cuál es la ecuación de la recta con pendiente 3 que pasa por (1,2)?',
                'Hallar el punto medio del segmento entre (-1,4) y (3,-2)',
                '¿Cuál es la ecuación del círculo con centro en (0,0) y radio 5?',
                'Calcula el área del triángulo con vértices (0,0), (4,0), (0,3)',
            ],
            'Física Mecánica': [
                'Un objeto de 5 kg acelera a 3 m/s². ¿Cuál es la fuerza aplicada?',
                '¿Cuál es la velocidad final de un objeto que parte del reposo con a = 4 m/s² en 3 segundos?',
                'Calcular la energía cinética de un objeto de 2 kg que se mueve a 6 m/s',
                '¿Cuánto trabajo se realiza al aplicar una fuerza de 10 N sobre 5 metros?',
                'Un carro viaja a 20 m/s y frena con deceleración de 4 m/s². ¿Cuánto tarda en detenerse?',
                '¿Cuál es la potencia desarrollada al subir 100 J en 5 segundos?',
            ],
            'Física Eléctrica': [
                'Calcular la corriente en un circuito con 12V y resistencia de 4Ω',
                '¿Cuál es la potencia consumida por un dispositivo de 220V con 0.5A?',
                'Si dos resistencias de 6Ω y 3Ω están en paralelo, ¿cuál es la resistencia equivalente?',
                '¿Cuánta carga pasa por un conductor si la corriente es 2A durante 5 minutos?',
                'Calcular la caída de tensión en una resistencia de 10Ω con 3A de corriente',
            ],
            'Química General': [
                '¿Cuál es la masa molar del agua (H₂O)?',
                'Balancear la ecuación: Fe + O₂ → Fe₂O₃',
                '¿Cuántos moles hay en 36g de agua?',
                '¿Cuál es el pH de una solución con [H⁺] = 0.001 M?',
                'Identificar el tipo de enlace en NaCl',
                '¿Cuál es la fórmula del sulfato de cobre(II)?',
            ],
            'Biología Celular': [
                '¿Cuál es la organela responsable de la producción de ATP?',
                '¿Qué tipo de membrana transporte requiere energía?',
                'Nombre la fase del ciclo celular donde ocurre la replicación del ADN',
                '¿Cuál es la función principal del ribosoma?',
                'Identificar la diferencia entre mitosis y meiosis',
                '¿Qué gas absorbe la clorofila durante la fotosíntesis?',
            ],
            'Literatura': [
                '¿Quién escribió "Cien años de soledad"?',
                '¿Qué movimiento literario caracterizó el siglo XIX en América Latina?',
                'Identificar el tipo de narrador en una novela en primera persona',
                '¿Qué es un soneto en poesía?',
                'Mencionar tres características del Romanticismo',
            ],
            'Historia Universal': [
                '¿En qué año comenzó la Primera Guerra Mundial?',
                '¿Qué tratado puso fin a la Segunda Guerra Mundial en Europa?',
                '¿Quién fue el primer presidente de la República Romana?',
                '¿Qué revolución comenzó en 1789 en Francia?',
                'Nombre la civilización que construyó las pirámides de Giza',
            ],
            'Geometría Analítica': [
                '¿Cuál es la distancia entre los puntos (0,0) y (3,4)?',
                'Encuentra la ecuación de la recta perpendicular a y = 2x + 1 que pasa por (1,5)',
                '¿Cuál es la pendiente de la recta 3x + 2y = 12?',
            ],
            'Física Mecánica': [
                '¿Cuál es la ley que establece que toda acción tiene una reacción igual y opuesta?',
                'Calcular la fuerza gravitacional entre dos masas de 100 kg separadas 1 metro',
                '¿Cuál es la unidad de trabajo en el Sistema Internacional?',
            ],
            'Química General': [
                '¿Cuál es el número atómico del carbono?',
                '¿Qué tipo de enlace se forma entre átomos de hidrógeno y oxígeno?',
                'Calcular la masa molecular del CO₂',
            ],
            'Biología Celular': [
                '¿Qué proceso celular divide el núcleo en dos células hijas?',
                '¿Cuál es la función de la membrana plasmática?',
                'Nombre los cuatro tipos de tejidos animales',
            ],
            'Literatura': [
                '¿Qué es un argumento literario?',
                'Identificar el recurso literario en: "El viento susurra entre los árboles"',
                '¿Quién escribió "La casa de los espíritus"?',
            ],
            'Historia Universal': [
                '¿Qué imperio fue gobernado por Napoleón Bonaparte?',
                '¿En qué año cayó el Muro de Berlín?',
                '¿Quién descubrió América en 1492?',
            ],
            'Economía': [
                '¿Qué es la ley de la oferta y la demanda?',
                'Definir el Producto Interno Bruto (PIB)',
                '¿Qué es la inflación y cuáles son sus causas?',
                'Diferenciar entre economía macro y micro',
            ],
            'Filosofía': [
                '¿Quién es considerado el padre de la filosofía occidental?',
                '¿Qué es el dualismo cartesiano?',
                'Definir el concepto de "cogito ergo sum"',
                'Mencionar tres ideas de Kant',
            ],
            'Economía': [
                '¿Qué es el modelo de oferta y demanda?',
                'Definir el concepto de costo de oportunidad',
                '¿Qué diferencia una economía de mercado de una planificada?',
            ],
            'Filosofía': [
                '¿Qué es la epistemología?',
                '¿Quién propuso la teoría del comunismo?',
                'Definir el existencialismo',
            ],
            'Geografía': [
                '¿Cuál es la capital de Perú?',
                'Nombre los cinco continentes',
                '¿Qué es la cordillera de los Andes?',
                'Definir el concepto de zona climática',
            ],
            'Psicología': [
                '¿Quién es considerado el padre del psicoanálisis?',
                '¿Qué es la teoría de la jerarquía de necesidades de Maslow?',
                'Definir el concepto de condicionamiento clásico',
            ],
            'Sociología': [
                '¿Quién acuñó el término "hecho social"?',
                '¿Qué es la movilidad social?',
                'Definir el concepto de capital social',
            ],
            'Genética': [
                '¿Quién descubrió la estructura del ADN?',
                '¿Qué es el código genético?',
                'Definir el concepto de mutación genética',
                '¿Cuál es la diferencia entre genotipo y fenotipo?',
            ],
            'Fisiología Humana': [
                '¿Cuál es la función principal del corazón?',
                '¿Cómo funciona el sistema respiratorio?',
                '¿Qué órgano produce la insulina?',
                'Nombre los huesos más grandes del cuerpo humano',
            ],
            'Química Orgánica': [
                '¿Qué es un hidrocarburo?',
                'Diferenciar entre alcanos, alquenos y alquinos',
                '¿Cuál es la fórmula general de los alcanos?',
                'Identificar el grupo funcional de un alcohol',
            ],
            'Física General': [
                '¿Cuáles son las tres leyes de Newton?',
                'Calcular la fuerza gravitatoria entre dos objetos',
                '¿Qué es la conservación de la energía?',
                'Definir la velocidad y la aceleración',
            ],
            'Historia del Perú': [
                '¿Quién fue el Inca Garcilaso de la Vega?',
                '¿En qué año se proclamó la independencia del Perú?',
                '¿Quién fue el primer presidente del Perú?',
                'Mencionar tres culturas preincaicas',
            ],
            'Biología': [
                '¿Cuál es la unidad básica de la vida?',
                '¿Qué proceso utilizan las plantas para producir alimento?',
                'Diferenciar entre mitosis y meiosis',
                '¿Cuál es la función del ADN?',
            ],
            'Historia': [
                '¿Cuáles fueron las causas de la Segunda Guerra Mundial?',
                '¿Qué fue la Revolución Francesa?',
                '¿Quién fue Simón Bolívar?',
            ],
            'Química': [
                '¿Qué es una reacción química?',
                'Definir el pH y su escala',
                '¿Cuál es la fórmula del ácido sulfúrico?',
            ],
        }

        # Map each area to its subjects
        area_asignaturas = {}
        for area_cod, materias in asignaturas_data.items():
            area_asignaturas[area_cod] = []
            for asig in asignaturas[area_cod]:
                area_asignaturas[area_cod].append(asig)

        # Create questions for each subject
        for area_cod, asigs in area_asignaturas.items():
            for asig in asigs:
                if asig.nombre in temas:
                    for i, enunciado in enumerate(temas[asig.nombre]):
                        if total_preguntas >= 100:
                            break
                        pregunta, _ = Pregunta.objects.get_or_create(
                            asignatura=asig,
                            tema_especifico=f'Tema {i+1}',
                            defaults={
                                'texto_pregunta': enunciado,
                                'etiqueta': 'SIMULACRO_4',
                            }
                        )
                        total_preguntas += 1

                        # Create 4 alternatives per question (A, B, C, D)
                        correct_idx = random.randint(0, 3)
                        opciones_texto = [
                            f'Alternativa A para: {enunciado[:50]}',
                            f'Alternativa B para: {enunciado[:50]}',
                            f'Alternativa C para: {enunciado[:50]}',
                            f'Alternativa D para: {enunciado[:50]}',
                        ]
                        for j, texto in enumerate(opciones_texto):
                            es_correcta = (j == correct_idx)
                            Alternativa.objects.get_or_create(
                                pregunta=pregunta,
                                defaults={
                                    'texto': texto,
                                    'es_correcta': es_correcta,
                                }
                            )
                if total_preguntas >= 100:
                    break
            if total_preguntas >= 100:
                break

        self.stdout.write(self.style.SUCCESS(f'Creadas {total_preguntas} preguntas con alternativas.'))

        # 5. CREAR USUARIOS DE PRUEBA
        self.stdout.write('Creando usuarios de prueba...')
        test_users = [
            ('76543210', 'Carlos', 'García López', '999111222', 'Ingeniería de Sistemas'),
            ('76543211', 'María', 'Rodríguez Pérez', '999111333', 'Medicina Humana'),
            ('76543212', 'José', 'Martínez Sánchez', '999111444', 'Derecho'),
            ('76543213', 'Ana', 'López Torres', '999111555', 'Arquitectura'),
            ('76543214', 'Pedro', 'Hernández Ruiz', '999111666', 'Administración'),
            ('76543215', 'Laura', 'González Mendoza', '999111777', 'Enfermería'),
            ('76543216', 'Miguel', 'Vásquez Castillo', '999111888', 'Economía'),
            ('76543217', 'Sofía', 'Ramírez Díaz', '999111999', 'Psicología'),
        ]
        for dni, first, last, tel, carrera in test_users:
            user, created = User.objects.get_or_create(
                username=dni,
                defaults={
                    'first_name': first,
                    'last_name': last,
                    'is_active': True,
                }
            )
            if created:
                user.set_password(dni)
                user.save()
            perfil, _ = PerfilEstudiante.objects.get_or_create(
                user=user,
                defaults={
                    'telefono': tel,
                    'carrera': carrera,
                    'examen_habilitado': False,
                }
            )

        # Habilitar examen para los primeros 3 usuarios
        for dni in ['76543210', '76543211', '76543212']:
            user = User.objects.get(username=dni)
            user.perfil.examen_habilitado = True
            user.perfil.save()

        self.stdout.write(self.style.SUCCESS('Usuarios de prueba creados. Habilitados: 76543210, 76543211, 76543212'))

        # 6. CREAR INTENTOS DE PRUEBA
        self.stdout.write('Creando intentos de prueba...')
        from django.utils import timezone
        from datetime import timedelta

        for dni in ['76543210', '76543211', '76543212']:
            user = User.objects.get(username=dni)
            area = random.choice(list(areas.values()))
            intento = Intento.objects.create(
                estudiante=user,
                area=area,
                fecha_inicio=timezone.now() - timedelta(days=random.randint(1, 30)),
                fecha_fin=timezone.now() - timedelta(days=random.randint(0, 29)),
                puntaje_final=round(random.uniform(5, 15), 7),
                nivel_acceso=random.choice([0, 1, 2]),
                pagado_reporte=random.choice([True, False]),
            )
            # Create some answer details
            preguntas = Pregunta.objects.order_by('?')[:random.randint(5, 15)]
            for preg in preguntas:
                alternativas = list(preg.alternativas.all())
                if alternativas:
                    marcada = random.choice(alternativas)
                    RespuestaDetalle.objects.create(
                        intento=intento,
                        pregunta=preg,
                        opcion_marcada=marcada.texto or 'Imagen',
                        es_correcta=marcada.es_correcta,
                    )

        self.stdout.write(self.style.SUCCESS('Intentos de prueba creados.'))

        # Summary
        self.stdout.write(self.style.SUCCESS('\n=== DATOS DE PRUEBA CARGADOS ==='))
        self.stdout.write(f'Áreas: {Area.objects.count()}')
        self.stdout.write(f'Asignaturas: {Asignatura.objects.count()}')
        self.stdout.write(f'Preguntas: {Pregunta.objects.count()}')
        self.stdout.write(f'Alternativas: {Alternativa.objects.count()}')
        self.stdout.write(f'Matriz de Pesos: {MatrizPeso.objects.count()}')
        self.stdout.write(f'Usuarios: {User.objects.filter(is_superuser=False).count()}')
        self.stdout.write(f'Perfiles: {PerfilEstudiante.objects.count()}')
        self.stdout.write(f'Intentos: {Intento.objects.count()}')
        self.stdout.write(f'Respuestas Detalle: {RespuestaDetalle.objects.count()}')