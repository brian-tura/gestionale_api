#!/usr/bin/env bash
# exit on error
set -o errexit

pip install -r requirements.txt
python manage.py collectstatic --noinput
python manage.py migrate

# Carica i dati dell'apiario se presenti
if [ -f initial_data.json ]; then
    python manage.py loaddata initial_data.json || true
fi