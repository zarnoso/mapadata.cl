#!/bin/bash

# Cargar variables de entorno
if [ -f .env.mapadata ]; then
    export $(cat .env.mapadata | grep -v '^#' | xargs)
fi

# Activar venv
source /home/chumbeke/esphome-venv/bin/activate

# Iniciar backend canónico
echo "Iniciando Mapadata Backend..."
python backend.py
