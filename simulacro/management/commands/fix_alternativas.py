from django.core.management.base import BaseCommand
from simulacro.models import Pregunta, Alternativa
import random


class Command(BaseCommand):
    help = 'Corrige las alternativas: elimina las existentes y crea 4 por pregunta'

    def handle(self, *args, **options):
        total = Pregunta.objects.count()
        self.stdout.write(f'Eliminando {Alternativa.objects.count()} alternativas existentes...')
        Alternativa.objects.all().delete()

        self.stdout.write(f'Recreando 4 alternativas para cada una de las {total} preguntas...')
        count = 0
        preguntas = Pregunta.objects.all()
        for i, preg in enumerate(preguntas, 1):
            correct_idx = random.randint(0, 3)
            opciones = [
                f'A) {preg.texto_pregunta[:80]}',
                f'B) {preg.texto_pregunta[:80]}',
                f'C) {preg.texto_pregunta[:80]}',
                f'D) {preg.texto_pregunta[:80]}',
            ]
            for j, texto in enumerate(opciones):
                es_correcta = (j == correct_idx)
                Alternativa.objects.create(
                    pregunta=preg,
                    texto=texto,
                    es_correcta=es_correcta,
                )
                count += 1
            if i % 20 == 0:
                self.stdout.write(f'  Procesadas {i}/{total} preguntas...')

        self.stdout.write(self.style.SUCCESS(
            f'Done! {count} alternativas creadas ({count // total} por pregunta).'
        ))