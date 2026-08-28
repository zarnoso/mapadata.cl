#!/usr/bin/env python3
"""
Mapadata Storage - Cloudflare R2
Sube archivos CSV a R2 y genera URLs firmadas
"""

import os
import logging
from datetime import datetime, timedelta

logger = logging.getLogger('mapadata-storage')

# Configuración R2
R2_ACCOUNT_ID = os.getenv('R2_ACCOUNT_ID', '')
R2_ACCESS_KEY_ID = os.getenv('R2_ACCESS_KEY_ID', '')
R2_SECRET_ACCESS_KEY = os.getenv('R2_SECRET_ACCESS_KEY', '')
R2_BUCKET_NAME = os.getenv('R2_BUCKET_NAME', 'mapadata')
R2_PUBLIC_URL = os.getenv('R2_PUBLIC_URL', '')

def subir_a_r2(ruta_local: str, nombre_archivo: str = None) -> str:
    """
    Sube un archivo a Cloudflare R2 y retorna la URL firmada.
    
    Args:
        ruta_local: Ruta local del archivo
        nombre_archivo: Nombre del archivo en R2 (opcional)
    
    Returns:
        URL firmada para descarga
    """
    try:
        import boto3
    except ImportError:
        logger.error("boto3 no instalado. Ejecuta: pip install boto3")
        return ""
    
    if not all([R2_ACCOUNT_ID, R2_ACCESS_KEY_ID, R2_SECRET_ACCESS_KEY, R2_BUCKET_NAME]):
        logger.error("Credenciales R2 no configuradas")
        return ""
    
    if not nombre_archivo:
        nombre_archivo = os.path.basename(ruta_local)
    
    # Endpoint de R2
    endpoint_url = f"https://{R2_ACCOUNT_ID}.r2.cloudflarestorage.com"
    
    # Cliente S3-compatible para R2
    s3_client = boto3.client(
        's3',
        endpoint_url=endpoint_url,
        aws_access_key_id=R2_ACCESS_KEY_ID,
        aws_secret_access_key=R2_SECRET_ACCESS_KEY,
        region_name='auto'
    )
    
    try:
        # Subir archivo
        with open(ruta_local, 'rb') as f:
            s3_client.upload_fileobj(f, R2_BUCKET_NAME, nombre_archivo)
        
        logger.info(f"Archivo subido a R2: {nombre_archivo}")
        
        # Generar URL firmada (válida por 7 días)
        url_firmada = s3_client.generate_presigned_url(
            'get_object',
            Params={'Bucket': R2_BUCKET_NAME, 'Key': nombre_archivo},
            ExpiresIn=604800  # 7 días
        )
        
        return url_firmada
        
    except Exception as e:
        logger.error(f"Error subiendo a R2: {e}")
        return ""

def eliminar_de_r2(nombre_archivo: str) -> bool:
    """Elimina un archivo de R2"""
    try:
        import boto3
    except ImportError:
        return False
    
    endpoint_url = f"https://{R2_ACCOUNT_ID}.r2.cloudflarestorage.com"
    
    s3_client = boto3.client(
        's3',
        endpoint_url=endpoint_url,
        aws_access_key_id=R2_ACCESS_KEY_ID,
        aws_secret_access_key=R2_SECRET_ACCESS_KEY,
        region_name='auto'
    )
    
    try:
        s3_client.delete_object(Bucket=R2_BUCKET_NAME, Key=nombre_archivo)
        logger.info(f"Archivo eliminado de R2: {nombre_archivo}")
        return True
    except Exception as e:
        logger.error(f"Error eliminando de R2: {e}")
        return False

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Uso: python r2_storage.py <archivo_local> [nombre_remoto]")
        sys.exit(1)
    
    ruta = sys.argv[1]
    nombre = sys.argv[2] if len(sys.argv) > 2 else None
    
    url = subir_a_r2(ruta, nombre)
    if url:
        print(f"URL: {url}")
    else:
        print("Error subiendo archivo")
