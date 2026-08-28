#!/usr/bin/env python3
import csv
import logging
import os
import re
import time
import unicodedata
from datetime import datetime

import psycopg2
import requests
from bs4 import BeautifulSoup
from psycopg2.extras import RealDictCursor

DB_URL = os.getenv("DATABASE_URL", "")
GOOGLE_PLACES_API_KEY = os.getenv("GOOGLE_PLACES_API_KEY", "")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.FileHandler("/tmp/mapadata_worker.log"), logging.StreamHandler()],
)
logger = logging.getLogger("mapadata-worker")

TERMINOS_DEFAULT = ["comercializadora", "distribuidora", "importadora", "mayorista", "proveedor"]
MAX_RESULTS_PER_QUERY = 60
EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")
IGNORAR_EMAILS = ["wixpress.com", "sentry.io", "example.com", ".png", ".jpg", ".webp"]


def normaliza(s):
    s = unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode()
    return re.sub(r"\s+", " ", s.lower().strip())


def buscar_termino_zona(termino, zona, limite=MAX_RESULTS_PER_QUERY):
    if not GOOGLE_PLACES_API_KEY:
        logger.error("GOOGLE_PLACES_API_KEY no configurada")
        return []

    query = f"{termino} {zona} Chile"
    resultados = []
    token = None
    while len(resultados) < limite:
        try:
            url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
            params = {"query": query, "key": GOOGLE_PLACES_API_KEY, "language": "es"}
            if token:
                params["pagetoken"] = token
            resp = requests.get(url, params=params, timeout=30)
            data = resp.json()
            if data.get("status") != "OK":
                logger.warning("API error: %s - %s", data.get("status"), data.get("error_message", ""))
                break
            for r in data.get("results", []):
                resultados.append(
                    {
                        "place_id": r.get("place_id"),
                        "nombre": r.get("name"),
                        "direccion": r.get("formatted_address"),
                        "tipo_busqueda": termino,
                        "zona_busqueda": zona,
                    }
                )
            token = data.get("next_page_token")
            if not token or len(resultados) >= limite:
                break
            time.sleep(2)
        except Exception as e:
            logger.error("Error buscando %s: %s", query, e)
            break
    return resultados[:limite]


def enriquecer_place(place_id):
    if not GOOGLE_PLACES_API_KEY:
        return "", ""
    try:
        url = "https://maps.googleapis.com/maps/api/place/details/json"
        params = {
            "place_id": place_id,
            "key": GOOGLE_PLACES_API_KEY,
            "fields": "formatted_phone_number,website",
            "language": "es",
        }
        resp = requests.get(url, params=params, timeout=30)
        data = resp.json()
        if data.get("status") == "OK":
            result = data.get("result", {})
            return result.get("formatted_phone_number", ""), result.get("website", "")
        return "", ""
    except Exception as e:
        logger.error("Error enriqueciendo %s: %s", place_id, e)
        return "", ""


def extraer_email(web):
    if not web:
        return ""
    base = web if web.startswith("http") else "https://" + web
    headers = {"User-Agent": "Mozilla/5.0"}
    for sufijo in ["", "/contacto", "/contact", "/contactos", "/quienes-somos", "/sobre-nosotros"]:
        try:
            resp = requests.get(base.rstrip("/") + sufijo, headers=headers, timeout=8)
            if resp.status_code != 200:
                continue
            emails = set(EMAIL_RE.findall(resp.text))
            emails = {e.lower() for e in emails if not any(ig in e.lower() for ig in IGNORAR_EMAILS)}
            if emails:
                return ";".join(sorted(emails))
            soup = BeautifulSoup(resp.text, "html.parser")
            mailto = [a["href"].replace("mailto:", "").split("?")[0] for a in soup.select('a[href^="mailto:"]')]
            if mailto:
                return ";".join(sorted(set(mailto)))
        except requests.RequestException:
            continue
    return ""


def procesar_job(job_id, comunas, terminos, modo):
    logger.info("Procesando job %s: %s comunas, %s términos", job_id, len(comunas), len(terminos))
    todos = []
    for t in terminos:
        for zona in comunas:
            resultados = buscar_termino_zona(t, zona)
            todos.extend(resultados)
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
    con_email = 0
    if modo == "enriched":
        for r in unicos:
            r["telefono"], r["web"] = enriquecer_place(r["place_id"])
            r["email"] = extraer_email(r["web"])
            if r["email"]:
                con_email += 1
            time.sleep(0.1)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = f"/tmp/job_{job_id}_{timestamp}.csv"
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        fieldnames = ["place_id", "nombre", "direccion", "tipo_busqueda", "zona_busqueda", "telefono", "web", "email"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(unicos)
    return path, len(unicos), con_email


def loop_worker():
    logger.info("Worker iniciado. Esperando jobs...")
    while True:
        conn = psycopg2.connect(DB_URL, sslmode="require", cursor_factory=RealDictCursor)
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT id, comunas, terminos, modo FROM scraping_jobs
                    WHERE status = 'queued'
                    ORDER BY creado_en
                    LIMIT 1
                    FOR UPDATE SKIP LOCKED
                    """
                )
                row = cur.fetchone()
                if not row:
                    conn.commit()
                    time.sleep(5)
                    continue
                job_id = row["id"]
                comunas = row["comunas"]
                terminos = row["terminos"] or TERMINOS_DEFAULT
                modo = row["modo"]
                cur.execute("UPDATE scraping_jobs SET status = 'running' WHERE id = %s", (job_id,))
                conn.commit()
            path, total, con_email = procesar_job(job_id, comunas, terminos, modo)
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE scraping_jobs
                    SET status = 'done', total_empresas = %s, con_email = %s, resultado_csv_url = %s, terminado_en = now()
                    WHERE id = %s
                    """,
                    (total, con_email, path, job_id),
                )
                conn.commit()
        except Exception as e:
            logger.error("Error en worker: %s", e)
            conn.rollback()
            time.sleep(5)
        finally:
            conn.close()


if __name__ == "__main__":
    loop_worker()
