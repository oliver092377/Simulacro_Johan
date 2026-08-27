#!/usr/bin/env bash
set -o errexit

pip install -r requirements.txt
python -m playwright install chromium #recien incluido para que funcione en el contenedor de docker
python manage.py collectstatic --no-input
python manage.py migrate --no-input

python manage.py create_admin

if [ "$CARGAR_DATOS" = "true" ]; then
    #python manage.py cargar_datos_prueba
    python manage.py fix_alternativas
fi
#python cargar_datos_prueba.py
#python fix_alternativas.py
