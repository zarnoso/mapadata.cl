#!/bin/bash
# Inicio unificado de Mapata
# Se ejecuta automáticamente con systemd

cd /home/chumbeke/mapadata.cl

# Variables de entorno
export DATABASE_URL="postgresql://neondb_owner:npg_EWrv14oPflCq@ep-autumn-firefly-at7pa7ut-pooler.c-9.us-east-1.aws.neon.tech/neondb?sslmode=require"
export GOOGLE_PLACES_API_KEY="${GOOGLE_PLACES_API_KEY:-}"
export R2_ACCOUNT_ID="7976da0811374c03128e815940af652a"
export R2_ACCESS_KEY_ID="${R2_ACCESS_KEY_ID:-}"
export R2_SECRET_ACCESS_KEY="${R2_SECRET_ACCESS_KEY:-}"
export R2_BUCKET_NAME="mapadata"
export R2_PUBLIC_URL="https://pub-7976da0811374c03128e815940af652a.r2.dev"
export MAPADATA_OUTPUT_DIR="/home/chumbeke/mapadata.cl/output"
export MAPADATA_MAX_WORKERS="6"
export MAPADATA_MAX_JOBS="2"
export TELEGRAM_BOT_TOKEN="${TELEGRAM_BOT_TOKEN:-}"
export TELEGRAM_CHAT_ID="${TELEGRAM_CHAT_ID:-}"

# Matar procesos anteriores
lsof -ti:8001 | xargs kill -9 2>/dev/null
lsof -ti:8002 | xargs kill -9 2>/dev/null

echo "=== Iniciando Mapata Backend (puerto 8001) ==="
nohup /home/chumbeke/esphome-venv/bin/python backend.py > /tmp/mapadata_backend.log 2>&1 &
BACKEND_PID=$!

sleep 2

if curl -s http://localhost:8001 > /dev/null 2>&1; then
    echo "✅ Backend corriendo en http://localhost:8001"
else
    echo "❌ Error iniciando backend"
    cat /tmp/mapadata_backend.log
fi

echo ""
echo "=== Iniciando Mapata Worker v5.0 ==="
nohup /home/chumbeke/esphome-venv/bin/python worker_extraccion.py > /tmp/mapadata_worker.log 2>&1 &
WORKER_PID=$!

sleep 2

if ps -p $WORKER_PID > /dev/null 2>&1; then
    echo "✅ Worker corriendo"
else
    echo "❌ Error iniciando worker"
    cat /tmp/mapadata_worker.log
fi

echo ""
echo "=== Iniciando Cloudflare Tunnel ==="
nohup cloudflared tunnel run mapadata > /tmp/mapadata_tunnel.log 2>&1 &
TUNNEL_PID=$!

sleep 3

if ps -p $TUNNEL_PID > /dev/null 2>&1; then
    echo "✅ Tunnel corriendo"
else
    echo "❌ Error iniciando tunnel"
    cat /tmp/mapadata_tunnel.log
fi

echo ""
echo "=== Estado ==="
echo "Backend PID: $BACKEND_PID"
echo "Worker PID: $WORKER_PID"
echo "Tunnel PID: $TUNNEL_PID"
echo "Logs: /tmp/mapadata_backend.log, /tmp/mapadata_worker.log, /tmp/mapadata_tunnel.log"
