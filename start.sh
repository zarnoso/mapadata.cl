#!/bin/bash
cd /home/chumbeke/mapadata.cl
source .venv/bin/activate
python backend.py > /tmp/mapadata_backend.log 2>&1 &
python worker.py > /tmp/mapadata_worker.log 2>&1 &
