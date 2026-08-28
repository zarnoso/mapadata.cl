#!/usr/bin/env python3
"""
Mapadata Worker - Sistema de Logging
Configuración centralizada para logging del worker
"""

import logging
from datetime import datetime

def get_logger():
    """Retorna logger configurado para el worker"""
    
    logger = logging.getLogger('mapata-worker')
    
    # Si ya tiene handlers, retornar
    if logger.handlers:
        return logger
    
    logger.setLevel(logging.INFO)
    
    # Handler para archivo
    file_handler = logging.FileHandler('/tmp/mapadata_worker.log', encoding='utf-8')
    file_handler.setLevel(logging.INFO)
    file_format = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s')
    file_handler.setFormatter(file_format)
    
    # Handler para consola
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_format = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s')
    console_handler.setFormatter(console_format)
    
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

# Ejemplo de uso
if __name__ == "__main__":
    logger = get_logger()
    logger.info("Worker iniciado")
    logger.info(f"Log guardado en /tmp/mapadata_worker.log")
    logger.info("Logs rotan cada 24h")
