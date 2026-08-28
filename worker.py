#!/usr/bin/env python3
"""
Mapadata Worker - Procesa jobs de scraping de Google Places
Se ejecuta en background, leyendo jobs de Neon con FOR UPDATE SKIP LOCKED
"""

import os
import csv
import time
import re
import unicodedata
import logging
from datetime import datetime

import psycopg2
from psycopg2.extras import RealDictCursor
import requests

# Configuración
DB_URL = os.getenv('DATABASE_URL', 'postgresql://neondb_owner:REDACTED_DB_PASS@ep-dark-sunset-ah922o3v-pooler.c-3.us-east-1.aws.neon.tech/neondb?sslmode=require')
GOOGLE_PLACES_API_KEY = os.getenv('GOOGLE_PLACES_API_KEY', '')

# Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler('/tmp/mapadata_worker.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('mapadata-worker')

# Constantes
TERMINOS_DEFAULT = ["comercializadora", "distribuidora", "importadora", "mayorista", "proveedor"]
MAX_RESULTS_PER_QUERY = 60
EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")
IGNORAR_EMAILS = ["wixpress.com", "sentry.io", "example.com", ".png", ".jpg", ".webp"]

def normaliza(s):
    """Normaliza texto para deduplicación"""
    s = unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode()
    return re.sub(r"\s+", " ", s.lower().strip())

def buscar_termino_zona(termino, zona, limite=MAX_RESULTS_PER_QUERY):
    """Busca lugares en Google Places por término y zona"""
    if not GOOGLE_PLACES_API_KEY:
        logger.error("GOOGLE_PLACES_API_KEY no configurada")
        return []
    
    query = f"{termino} {zona} Chile"
    resultados = []
    token = None
    
    while len(resultados) < limite:
        try:
            url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
            params = {
                "query": query,
                "key": GOOGLE_PLACES_API_KEY,
                "language": "es"
            }
            if token:
                params["pagetoken"] = token
            
            resp = requests.get(url, params=params, timeout=30)
            data = resp.json()
            
            if data.get("status") != "OK":
                logger.warning(f"API error: {data.get('status')} - {data.get('error_message', '')}")
                break
            
            for r in data.get("results", []):
                resultados.append({
                    "place_id": r.get("place_id"),
                    "nombre": r.get("name"),
                    "direccion": r.get("formatted_address"),
                    "tipo_busqueda": termino,
                    "zona_busqueda": zona,
                })
            
            token = data.get("next_page_token")
            if not token or len(resultados) >= limite:
                break
            
            time.sleep(2)  # Requerido por Google entre páginas
            
        except Exception as e:
            logger.error(f"Error buscando {query}: {e}")
            break
    
    return resultados[:limite]

def enriquecer_place(place_id):
    """Obtiene detalles adicionales de un lugar"""
    if not GOOGLE_PLACES_API_KEY:
        return "", ""
    
    try:
        url = "https://maps.googleapis.com/maps/api/place/details/json"
        params = {
            "place_id": place_id,
            "key": GOOGLE_PLACES_API_KEY,
            "fields": "formatted_phone_number,website",
            "language": "es"
        }
        
        resp = requests.get(url, params=params, timeout=30)
        data = resp.json()
        
        if data.get("status") == "OK":
            result = data.get("result", {})
            return result.get("formatted_phone_number", ""), result.get("website", "")
        
        logger.warning(f"Place details error: {data.get('status')}")
        return "", ""
        
    except Exception as e:
        logger.error(f"Error enriqueciendo {place_id}: {e}")
        return "", ""

def extraer_email(web):
    """Extrae emails de la web de una empresa"""
    if not web:
        return ""
    
    base = web if web.startswith("http") else "https://" + web
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    
    for sufijo in ["", "/contacto", "/contact", "/contactos", "/quienes-somos", "/sobre-nosotros"]:
        try:
            resp = requests.get(base.rstrip("/") + sufijo, headers=headers, timeout=8)
            if resp.status_code != 200:
                continue
            
            # Buscar emails en texto
            emails = set(EMAIL_RE.findall(resp.text))
            emails = {e.lower() for e in emails if not any(ig in e.lower() for ig in IGNORAR_EMAILS)}
            
            if emails:
                return ";".join(sorted(emails))
            
            # Buscar mailto links
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(resp.text, "html.parser")
            mailto = [a["href"].replace("mailto:", "").split("?")[0]
                      for a in soup.select('a[href^="mailto:"]')]
            if mailto:
                return ";".join(sorted(set(mailto)))
                
        except requests.RequestException:
            continue
    
    return ""

def procesar_job(job_id, comunas, terminos, modo):
    """Procesa un job de scraping"""
    logger.info(f"Procesando job {job_id}: {len(comunas)} comunas, {len(terminos)} términos")
    
    todos = []
    for t in terminos:
        for zona in comunas:
            logger.info(f"  Buscando '{t}' en '{zona}'...")
            resultados = buscar_termino_zona(t, zona)
            todos.extend(resultados)
            logger.info(f"    Encontrados: {len(resultados)}")
    
    # Deduplicar
    vistos_id, vistos_nd, unicos = set(), set(), []
    for r in todos:
        if r["place_id"] in vistos_id:
            continue
        clave = normaliza(r["nombre"]) + "|" + normaliza(r["direccion"])
        if clave in vistos_nd:
            continue
        vistos_id.add(r["place_id"])
        vistos_nd.add(clave)
        unicos.append(r)
    
    logger.info(f"Total únicos: {len(unicos)}")
    
    # Enriquecer y extraer emails
    con_email = 0
    if modo == "enriched":
        for i, r in enumerate(unicos):
            r["telefono"], r["web"] = enriquecer_place(r["place_id"])
            r["email"] = extraer_email(r["web"])
            if r["email"]:
                con_email += 1
            
            if (i + 1) % 10 == 0:
                logger.info(f"  Enriqueciendo {i+1}/{len(unicos)}...")
            
            time.sleep(0.1)
    
    # Generar CSV
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"job_{job_id}_{timestamp}.csv"
    path = f"/tmp/{filename}"
    
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        fieldnames = ["place_id", "nombre", "direccion", "tipo_busqueda", "zona_busqueda", "telefono", "web", "email"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(unicos)
    
    logger.info(f"CSV generado: {path} ({len(unicos)} registros, {con_email} con email)")
    
    return path, len(unicos), con_email

def loop_worker():
    """Loop principal del worker"""
    logger.info("Worker iniciado. Esperando jobs...")
    
    while True:
        conn = psycopg2.connect(DB_URL, sslmode='require', cursor_factory=RealDictCursor)
        try:
            conn.rollback()
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT id, comunas, terminos, modo FROM scraping_jobs
                    WHERE status = 'queued'
                    ORDER BY creado_en
                    LIMIT 1
                    FOR UPDATE SKIP LOCKED
                """)
                row = cur.fetchone()
                
                if not row:
                    conn.commit()
                    time.sleep(5)
                    continue
                
                job_id = row['id']
                comunas = row['comunas']
                terminos = row['terminos'] or TERMINOS_DEFAULT
                modo = row['modo']
                
                cur.execute("UPDATE scraping_jobs SET status = 'running' WHERE id = %s", (job_id,))
                conn.commit()
            
            logger.info(f"Job {job_id} iniciado")
            
            try:
                path, total, con_email = procesar_job(job_id, comunas, terminos, modo)
                
                # TODO: Subir a R2 y obtener URL firmada
                # Por ahora, guardamos la ruta local
                with conn.cursor() as cur:
                    cur.execute("""
                        UPDATE scraping_jobs
                        SET status = 'done',
                            total_empresas = %s,
                            con_email = %s,
                            resultado_csv_url = %s,
                            terminado_en = now()
                        WHERE id = %s
                    """, (total, con_email, path, job_id))
                    conn.commit()
                
                logger.info(f"Job {job_id} completado: {total} empresas, {con_email} con email")
                
            except Exception as e:
                logger.error(f"Job {job_id} falló: {e}")
                with conn.cursor() as cur:
                    cur.execute("""
                        UPDATE scraping_jobs
                        SET status = 'failed',
                            error_message = %s,
                            terminado_en = now()
                        WHERE id = %s
                    """, (str(e), job_id))
                    conn.commit()
        
        except Exception as e:
            logger.error(f"Error en loop: {e}")
            time.sleep(10)
        finally:
            conn.close()

if __name__ == "__main__":
    if not GOOGLE_PLACES_API_KEY:
        logger.error("❌ GOOGLE_PLACES_API_KEY no configurada")
        exit(1)
    
    loop_worker()
