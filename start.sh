#!/bin/bash
# Mapadata.cl - Script de inicio
# Usa Python 3.11 para evitar problemas con psycopg2

cd /home/chumbeke/mapadata.cl

# Activar venv
source .venv/bin/activate

# Variables de entorno
export DATABASE_URL="postgresql://neondb_owner:REDACTED_DB_PASS@ep-dark-sunset-ah922o3v-pooler.c-3.us-east-1.aws.neon.tech/neondb?sslmode=require"
export GOOGLE_PLACES_API_KEY="${GOOGLE_PLACES_API_KEY:-}"
export R2_ACCOUNT_ID="7976da0811374c03128e815940af652a"
export R2_API_TOKEN="${R2_API_TOKEN:-}"
export R2_BUCKET_NAME="mapadata"
export R2_PUBLIC_URL="https://pub-7976da0811374c03128e815940af652a.r2.dev"

# Matar procesos anteriores
lsof -ti:8001 | xargs kill -9 2>/dev/null
lsof -ti:8002 | xargs kill -9 2>/dev/null

echo "=== Iniciando Mapadata Backend (puerto 8001) ==="
python backend.py > /tmp/mapadata_backend.log 2>&1 &
BACKEND_PID=$!

sleep 2

if curl -s http://localhost:8001 > /dev/null 2>&1; then
    echo "✅ Backend corriendo en http://localhost:8001"
else
    echo "❌ Error iniciando backend"
    cat /tmp/mapadata_backend.log
    exit 1
fi

echo ""
echo "=== Iniciando Mapadata Worker ==="
python worker.py > /tmp/mapadata_worker.log 2>&1 &
WORKER_PID=$!

sleep 2

if ps -p $WORKER_PID > /dev/null 2>&1; then
    echo "✅ Worker corriendo"
else
    echo "❌ Error iniciando worker"
    cat /tmp/mapadata_worker.log
fi

echo ""
echo "=== Estado ==="
echo "Backend PID: $BACKEND_PID"
echo "Worker PID: $WORKER_PID"
echo "Logs: /tmp/mapadata_backend.log, /tmp/mapadata_worker.log"
