#!/usr/bin/env bash
set -o errexit

pip install -r requirements.txt
python manage.py collectstatic --no-input
python manage.py migrate --no-input

python manage.py create_admin

if [ "$CARGAR_DATOS" = "true" ]; then
    python manage.py cargar_datos_prueba
fi
#python cargar_datos_prueba.py
#python fix_alternativas.py