#!/usr/bin/env python3
"""
Mapadata Worker v5.0 — Scraping Google Places + DDG fallback
Mejoras implementadas:
  1. ThreadPoolExecutor con lock para DDG (thread-safe)
  2. Checkpointing incremental por zona
  3. Pool de conexiones + reconexión
  4. Dedup en SQL (memoria acotada)
  5. Errores informativos en DB
  6. Graceful shutdown con signal handling
  7. Upload real a R2 (S3-compatible)
  8. Config validation al inicio
  9. Health check endpoint
 10. Circuit breaker para Places API
11. Enriquecimiento paralelizado (3 workers)
12. Batch writes (cada 50 zonas)
13. Límite de jobs concurrentes (2)
14. Alertas Telegram en fallo
15. Stale job detector (5 min)
"""

import atexit
import csv
import os
import re
import signal
import sys
import threading
import time
import traceback
import unicodedata
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

import googlemaps
import psycopg2
import requests
from bs4 import BeautifulSoup
from psycopg2 import pool as pg_pool
from psycopg2.extras import RealDictCursor

# ══════════════════════════════════════════════════════
# 8. CONFIG VALIDATION (fail-fast al inicio)
# ══════════════════════════════════════════════════════
_REQUIRED_ENV = [
    "GOOGLE_PLACES_API_KEY",
    "DATABASE_URL",
    "R2_ACCOUNT_ID",
    "R2_ACCESS_KEY_ID",
    "R2_SECRET_ACCESS_KEY",
]


def _validate_config():
    """Falta de configuración = error inmediato, no silencioso."""
    missing = [var for var in _REQUIRED_ENV if not os.environ.get(var)]
    if missing:
        raise EnvironmentError(
            f"Variables de entorno faltantes: {', '.join(missing)}"
        )


_validate_config()

# Ahora sí importamos el resto
API_KEY = os.environ["GOOGLE_PLACES_API_KEY"]
DB_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql://neondb_owner:npg_EWrv14oPflCq@ep-autumn-firefly-at7pa7ut-pooler.c-9.us-east-1.aws.neon.tech/neondb?sslmode=require",
)
OUTPUT_DIR = os.environ.get("MAPADATA_OUTPUT_DIR", "/home/chumbeke/mapadata.cl/output")
MAX_WORKERS_PLACES = int(os.environ.get("MAPADATA_MAX_WORKERS", "6"))
MAX_JOBS_ACTIVOS = int(os.environ.get("MAPADATA_MAX_JOBS", "2"))

# ══════════════════════════════════════════════════════
# 13. LÍMITE DE JOBS CONCURRENTES
# ══════════════════════════════════════════════════════
_jobs_sem = threading.Semaphore(MAX_JOBS_ACTIVOS)

# ══════════════════════════════════════════════════════
# GOOGLE MAPS CLIENT
# ══════════════════════════════════════════════════════
gmaps = googlemaps.Client(key=API_KEY)

# ══════════════════════════════════════════════════════
# 3. POOL DE CONEXIONES
# ══════════════════════════════════════════════════════
_pool = pg_pool.ThreadedConnectionPool(1, MAX_WORKERS_PLACES + 4, DB_URL)


def get_conn():
    return _pool.getconn()


def put_conn(conn):
    _pool.putconn(conn)


def ejecutar_con_reconexion(fn, *args, max_intentos=3, **kwargs):
    """Ejecuta fn(conn, *args) reintentando si Neon cierra la conexión."""
    for intento in range(max_intentos):
        conn = get_conn()
        try:
            resultado = fn(conn, *args, **kwargs)
            put_conn(conn)
            return resultado
        except (psycopg2.OperationalError, psycopg2.InterfaceError) as e:
            print(f"  ⚠️ Conexión perdida ({e}), reintento {intento+1}/{max_intentos}")
            try:
                conn.close()
            except Exception:
                pass
            _pool.putconn(conn, close=True)
            time.sleep(2 * (intento + 1))
    raise ConnectionError(f"No se pudo reconectar tras {max_intentos} intentos")


# ══════════════════════════════════════════════════════
# CONSTANTES
# ══════════════════════════════════════════════════════
TERMINOS_DEFAULT = [
    "comercializadora",
    "distribuidora",
    "importadora",
    "mayorista",
    "proveedor",
]

# ══════════════════════════════════════════════════════
# 12. BATCH WRITES BUFFER
# ══════════════════════════════════════════════════════
_BUFFER_FILAS = []
_BUFFER_LOCK = threading.Lock()
_BUFFER_SIZE = 50


def _flush_buffer(job_id):
    """Escribe el buffer acumulado en DB de una vez."""
    global _BUFFER_FILAS
    with _BUFFER_LOCK:
        filas = _BUFFER_FILAS[:]
        _BUFFER_FILAS = []

    if not filas:
        return

    def _ins(c):
        with c.cursor() as cur:
            args_str = ",".join(
                cur.mogrify(
                    "(%s,%s,%s,%s,%s,%s,%s)",
                    (
                        job_id,
                        r.get("place_id", ""),
                        r["nombre"],
                        r["direccion"],
                        r["tipo_busqueda"],
                        r["zona_busqueda"],
                        r.get("fuente", "places"),
                    ),
                ).decode("utf-8")
                for r in filas
            )
            cur.execute(
                f"INSERT INTO scraping_resultados "
                f"(job_id, place_id, nombre, direccion, tipo_busqueda, zona_busqueda, fuente) "
                f"VALUES {args_str}"
            )
            c.commit()

    ejecutar_con_reconexion(_ins)
    print(f"  💾 Batch write: {len(filas)} zonas persistidas")


def guardar_checkpoint(filas, job_id):
    """Acumula en buffer y flush cada N zonas (#12 batch writes)."""
    if not filas:
        return
    global _BUFFER_FILAS
    with _BUFFER_LOCK:
        _BUFFER_FILAS.extend(filas)

    if len(_BUFFER_FILAS) >= _BUFFER_SIZE:
        _flush_buffer(job_id)


# ══════════════════════════════════════════════════════
# 1. DDG FALLBACK CON LOCK (thread-safe)
# ══════════════════════════════════════════════════════
_ddg_lock = threading.Lock()
_ddg_requests_job = {"count": 0}


def _reset_ddg_counter():
    """Resetea contador al inicio de cada job."""
    with _ddg_lock:
        _ddg_requests_job["count"] = 0


def buscar_ddg_fallback(termino, zona, limit=30, max_por_job=50):
    """Fallback DDG con lock thread-safe (#1)."""
    with _ddg_lock:
        if _ddg_requests_job["count"] >= max_por_job:
            return []
        _ddg_requests_job["count"] += 1

    query = f"{termino} {zona} Chile"
    for intento in range(3):
        try:
            resp = requests.post(
                "https://html.duckduckgo.com/html/",
                data={"q": query, "kl": "cl-es"},
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
                    "Accept-Language": "es-ES,es;q=0.9",
                },
                timeout=10,
            )
            if resp.status_code in (429, 403, 202):
                espera = 5 * (2**intento)
                print(f"  ⚠️ DDG {resp.status_code}, esperando {espera}s")
                time.sleep(espera)
                continue

            soup = BeautifulSoup(resp.text, "html.parser")
            resultados = []
            for item in soup.select(".result")[:limit]:
                title_el = item.select_one(".result__title a")
                snippet_el = item.select_one(".result__snippet")
                if not title_el:
                    continue
                raw_url = title_el.get("href", "")
                resultados.append(
                    {
                        "place_id": "",
                        "nombre": title_el.get_text(strip=True),
                        "direccion": (
                            snippet_el.get_text(strip=True) if snippet_el else ""
                        ),
                        "tipo_busqueda": termino,
                        "zona_busqueda": zona,
                        "web": _extraer_url_ddg(raw_url),
                        "fuente": "ddg_fallback",
                    }
                )
            return resultados
        except requests.RequestException:
            return []
    return []


def _extraer_url_ddg(raw_url):
    from urllib.parse import parse_qs, unquote, urlparse

    try:
        qs = parse_qs(urlparse(raw_url).query)
        return unquote(qs.get("uddg", [raw_url])[0])
    except Exception:
        return raw_url


# ══════════════════════════════════════════════════════
# 10. CIRCUIT BREAKER PARA PLACES API
# ══════════════════════════════════════════════════════
_circuit_breaker = {"errores_consecutivos": 0, "ultimo_error_t": 0, "abierto": False}


def _check_circuit_breaker():
    """Si hay muchos errores consecutivos, pausa el worker."""
    if _circuit_breaker["abierto"]:
        tiempo_abierto = time.time() - _circuit_breaker["ultimo_error_t"]
        if tiempo_abierto > 120:  # 2 min cooling down
            _circuit_breaker["abierto"] = False
            _circuit_breaker["errores_consecutivos"] = 0
            print("  ✅ Circuit breaker cerrado, reintentando")
        else:
            raise RuntimeError(
                f"Circuit breaker abierto, enfriando... ({int(120 - tiempo_abierto)}s restantes)"
            )


def _registrar_error():
    """Registra error consecutivo en el circuit breaker."""
    with _BUFFER_LOCK:
        _circuit_breaker["errores_consecutivos"] += 1
        _circuit_breaker["ultimo_error_t"] = time.time()
        if _circuit_breaker["errores_consecutivos"] > 15:
            _circuit_breaker["abierto"] = True
            _enviar_alerta_telegram(
                "🚨 Circuit breaker ABIERTO — Worker pausado 2 min"
            )


def _registrar_exito():
    """Resetea el contador de errores si la llamada fue exitosa."""
    with _BUFFER_LOCK:
        _circuit_breaker["errores_consecutivos"] = 0


# ══════════════════════════════════════════════════════
# COMUNAS
# ══════════════════════════════════════════════════════
from comunas_chile import (
    COMUNAS_CHILE_346,
    COMUNAS_POR_REGION,
    COMUNAS_RM,
    resolver_comunas,
)

# Pre-computar set de regiones para lookup O(1)
_REGIONES_UPPER = {k.upper(): v for k, v in COMUNAS_POR_REGION.items()}


def normaliza(s):
    s = unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode()
    return re.sub(r"\s+", " ", s.lower().strip())


# ══════════════════════════════════════════════════════
# RETRY + CIRCUIT BREAKER
# ══════════════════════════════════════════════════════
def request_con_retry(fn, *args, **kwargs):
    for intento in range(4):
        try:
            _check_circuit_breaker()
            resultado = fn(*args, **kwargs)
            _registrar_exito()
            return resultado
        except googlemaps.exceptions.ApiError as e:
            _registrar_error()
            if intento == 3:
                raise
            time.sleep(3 * (intento + 1))


# ══════════════════════════════════════════════════════
# BÚSQUEDA PRINCIPAL (Google Places)
# ══════════════════════════════════════════════════════
def buscar_termino_zona(termino, zona, limit=60):
    query = f"{termino} {zona} Chile"
    resultados, token = [], None
    try:
        while len(resultados) < limit:
            if token:
                resp = request_con_retry(gmaps.places, query=query, page_token=token)
            else:
                resp = request_con_retry(gmaps.places, query=query)
            for r in resp.get("results", []):
                resultados.append(
                    {
                        "place_id": r.get("place_id"),
                        "nombre": r.get("name"),
                        "direccion": r.get("formatted_address"),
                        "tipo_busqueda": termino,
                        "zona_busqueda": zona,
                        "fuente": "places",
                    }
                )
            token = resp.get("next_page_token")
            if not token or len(resultados) >= limit:
                break
            time.sleep(2)
        return resultados[:limit]
    except googlemaps.exceptions.ApiError as e:
        if "OVER_QUERY_LIMIT" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
            print(f"  ⚠️ Places agotado ({termino}/{zona}), fallback DDG")
            time.sleep(1 + __import__("random").random() * 2)
            return buscar_ddg_fallback(termino, zona)
        raise


# ══════════════════════════════════════════════════════
# 11. ENRIQUECIMIENTO PARALELIZADO (3 workers)
# ══════════════════════════════════════════════════════
_user_agents = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
]
_ua_lock = threading.Lock()
_ua_index = [0]


def _get_user_agent():
    """Rota User-Agents para evitar fingerprinting."""
    with _ua_lock:
        ua = _user_agents[_ua_index[0] % len(_user_agents)]
        _ua_index[0] += 1
        return ua


def enriquecer(place_id):
    """Obtiene teléfono y web de un place_id."""
    d = request_con_retry(
        gmaps.place,
        place_id=place_id,
        fields=["formatted_phone_number", "website"],
    ).get("result", {})
    return d.get("formatted_phone_number", ""), d.get("website", "")


def buscar_sitio_ddg(nombre, zona):
    """Busca dominio de una empresa via DDG."""
    resultados = buscar_ddg_fallback(nombre, zona, limit=3)
    for r in resultados:
        if r.get("web"):
            return r["web"]
    return ""


def extraer_email(web):
    """Extrae emails scrapeando el sitio web."""
    if not web:
        return ""
    base = web if web.startswith("http") else "https://" + web
    headers = {"User-Agent": _get_user_agent()}
    for sufijo in ["", "/contacto", "/contact", "/contactos", "/quienes-somos"]:
        try:
            resp = requests.get(
                base.rstrip("/") + sufijo, headers=headers, timeout=8
            )
            if resp.status_code != 200:
                continue
            emails = set(
                re.findall(
                    r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
                    resp.text,
                )
            )
            emails = {
                e.lower()
                for e in emails
                if "wixpress" not in e and "sentry" not in e and "example.com" not in e
            }
            if emails:
                return ";".join(sorted(emails))
        except requests.RequestException:
            continue
    return ""


# ══════════════════════════════════════════════════════
# 7. UPLOAD REAL A R2 (S3-compatible)
# ══════════════════════════════════════════════════════
R2_ACCOUNT_ID = os.environ["R2_ACCOUNT_ID"]
R2_ACCESS_KEY = os.environ["R2_ACCESS_KEY_ID"]
R2_SECRET_KEY = os.environ["R2_SECRET_ACCESS_KEY"]
R2_BUCKET = os.environ.get("R2_BUCKET_NAME", "mapadata")
R2_PUBLIC_URL = os.environ.get(
    "R2_PUBLIC_URL", f"https://pub-{R2_ACCOUNT_ID}.r2.dev"
)


def subir_a_storage(path, job_id):
    """Sube el CSV a R2 y retorna URL pública. Si falla, mantiene archivo local."""
    try:
        import boto3

        s3 = boto3.client(
            "s3",
            endpoint_url=f"https://{R2_ACCOUNT_ID}.r2.cloudflarestorage.com",
            aws_access_key_id=R2_ACCESS_KEY,
            aws_secret_access_key=R2_SECRET_KEY,
        )
        key = f"jobs/{job_id}/{os.path.basename(path)}"
        s3.upload_file(path, R2_BUCKET, key)
        url = f"{R2_PUBLIC_URL}/{key}"
        print(f"  ☁️ Subido a R2: {url}")
        return url
    except ImportError:
        print("  ⚠️ boto3 no instalado — CSV queda local")
        return None
    except Exception as e:
        print(f"  ⚠️ Error subiendo a R2: {e} — CSV queda local")
        return None


# ══════════════════════════════════════════════════════
# 14. ALERTAS TELEGRAM EN FALLO
# ══════════════════════════════════════════════════════
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")


def _enviar_alerta_telegram(mensaje):
    """Envía alerta a Telegram si está configurado."""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return
    try:
        requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
            json={"chat_id": TELEGRAM_CHAT_ID, "text": mensaje[:4000]},
            timeout=5,
        )
    except Exception as e:
        print(f"  ⚠️ Error enviando alerta Telegram: {e}")


# ══════════════════════════════════════════════════════
# PROCESAMIENTO DE JOBS
# ══════════════════════════════════════════════════════
def procesar_job(job_id, param_comunas, terminos, modo):
    """Procesa un job completo con checkpointing y progreso."""
    _reset_ddg_counter()
    comunas = resolver_comunas(param_comunas)
    total_queries = len(comunas) * len(terminos)
    print(
        f"🟢 Job {job_id}: {len(comunas)} comunas x {len(terminos)} términos = {total_queries} queries"
    )

    if total_queries > 2000:
        raise ValueError(
            f"Job {job_id} excede tope de 2000 queries ({total_queries}) — reduce comunas/terminos"
        )

    # Función para reportar progreso
    def reportar(pct, msg):
        def _upd(c):
            with c.cursor() as cur:
                cur.execute(
                    """UPDATE scraping_jobs
                       SET progreso_pct=%s, progreso_msg=%s, actualizado_en=now()
                       WHERE id=%s""",
                    (pct, msg, job_id),
                )
                c.commit()

        ejecutar_con_reconexion(_upd)

    # Checkpointing: zonas ya procesadas (resume)
    def zonas_ya_hechas(c):
        with c.cursor() as cur:
            cur.execute(
                "SELECT DISTINCT tipo_busqueda, zona_busqueda FROM scraping_resultados WHERE job_id=%s",
                (job_id,),
            )
            return {(row[0], row[1]) for row in cur.fetchall()}

    hechas_previas = ejecutar_con_reconexion(zonas_ya_hechas)
    pendientes = [
        (t, z) for t in terminos for z in comunas if (t, z) not in hechas_previas
    ]

    if hechas_previas:
        print(
            f"  🔄 Reanudando: {len(hechas_previas)} zonas ya hechas, {len(pendientes)} pendientes"
        )
        reportar(0, f"Reanudando job ({len(pendientes)} pendientes)")

    # ══════════════════════════════════════════════════
    # 1. BÚSQUEDA EN PARALELO (6 workers)
    # ══════════════════════════════════════════════════
    hechas = len(hechas_previas)
    with ThreadPoolExecutor(max_workers=MAX_WORKERS_PLACES) as pool_exec:
        futuros = {
            pool_exec.submit(buscar_termino_zona, t, z): (t, z)
            for t, z in pendientes
        }
        for fut in as_completed(futuros):
            t, z = futuros[fut]
            try:
                filas = fut.result()
                guardar_checkpoint(filas, job_id)
            except Exception as e:
                print(f"  ❌ Fallo {t}/{z}: {e} — se omite, continúa")
            hechas += 1
            if hechas % 10 == 0:
                reportar(
                    int(30 * hechas / total_queries),
                    f"Buscando: {hechas}/{total_queries} zonas",
                )

    # Flush final del buffer
    _flush_buffer(job_id)
    reportar(30, "Deduplicando resultados")

    # ══════════════════════════════════════════════════
    # 4. DEDUP EN SQL (memoria acotada)
    # ══════════════════════════════════════════════════
    def dedup_y_traer(c):
        with c.cursor() as cur:
            cur.execute(
                """
                SELECT DISTINCT ON (
                    COALESCE(
                        NULLIF(place_id,''),
                        unaccent(lower(nombre))||'|'||unaccent(lower(direccion))
                    )
                )
                    place_id, nombre, direccion, tipo_busqueda, zona_busqueda, fuente
                FROM scraping_resultados
                WHERE job_id=%s
                ORDER BY COALESCE(
                    NULLIF(place_id,''),
                    unaccent(lower(nombre))||'|'||unaccent(lower(direccion))
                ), id
                """,
                (job_id,),
            )
            cols = [
                "place_id",
                "nombre",
                "direccion",
                "tipo_busqueda",
                "zona_busqueda",
                "fuente",
            ]
            return [dict(zip(cols, row)) for row in cur.fetchall()]

    unicos = ejecutar_con_reconexion(dedup_y_traer)
    print(f"  📊 {len(unicos)} empresas únicas después de dedup")

    # ══════════════════════════════════════════════════
    # 11. ENRIQUECIMIENTO EN PARALELO (3 workers)
    # ══════════════════════════════════════════════════
    con_email = 0
    if modo == "enriched":

        def _enriquecer_uno(args):
            i, r = args
            if r.get("fuente") != "ddg_fallback":
                r["telefono"], r["web"] = enriquecer(r["place_id"])
            else:
                r["telefono"] = ""
            if not r.get("web"):
                r["web"] = buscar_sitio_ddg(r["nombre"], r["zona_busqueda"])
            r["email"] = extraer_email(r["web"])
            return i, r, bool(r["email"])

        with ThreadPoolExecutor(max_workers=3) as pool_enriquecer:
            for i, r, tiene_email in pool_enriquecer.map(
                _enriquecer_uno, enumerate(unicos, 1)
            ):
                unicos[i - 1] = r
                if tiene_email:
                    con_email += 1
                if i % 25 == 0 or i == len(unicos):
                    reportar(
                        30 + int(70 * i / len(unicos)),
                        f"Enriqueciendo: {i}/{len(unicos)}",
                    )
                time.sleep(0.05)  # throttling suave
    else:
        for r in unicos:
            r.setdefault("web", "")
            r["telefono"], r["email"] = "", ""

    reportar(95, "Generando CSV")

    # ══════════════════════════════════════════════════
    # GENERAR CSV
    # ══════════════════════════════════════════════════
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = f"{OUTPUT_DIR}/job_{job_id}_{timestamp}.csv"
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        fieldnames = [
            "place_id",
            "nombre",
            "direccion",
            "tipo_busqueda",
            "zona_busqueda",
            "telefono",
            "web",
            "email",
            "fuente",
        ]
        w = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        w.writeheader()
        w.writerows(unicos)

    reportar(100, "Completado ✅")
    print(f"  ✅ Job {job_id} completado: {len(unicos)} empresas, {con_email} con email")
    return path, len(unicos), con_email


# ══════════════════════════════════════════════════════
# 15. STALE JOB DETECTOR
# ══════════════════════════════════════════════════════
def limpiar_jobs_perdidos(timeout_minutos=30):
    """Marca como failed jobs 'running' sin heartbeat."""
    def _clean(c):
        with c.cursor() as cur:
            cur.execute(
                """
                UPDATE scraping_jobs
                SET status='failed',
                    error_detalle='Worker caído (stale heartbeat)'
                WHERE status='running'
                  AND actualizado_en < now() - interval '%s minutes'
                RETURNING id
                """,
                (timeout_minutos,),
            )
            perdidos = [r[0] for r in cur.fetchall()]
            c.commit()
            if perdidos:
                print(f"  💀 Marcados como failed (stale): {perdidos}")

    ejecutar_con_reconexion(_clean)


# ══════════════════════════════════════════════════════
# 6. GRACEFUL SHUTDOWN
# ══════════════════════════════════════════════════════
_shutdown_event = threading.Event()
_job_actual = {"id": None}


def _signal_handler(signum, frame):
    """Maneja SIGTERM/SIGINT para terminar limpiamente."""
    sig_name = signal.Signals(signum).name
    print(f"\n🛑 Señal {sig_name} recibida. Terminando job actual ({_job_actual['id']})...")
    _shutdown_event.set()
    if _job_actual["id"]:
        try:
            def _marcar_failed(c):
                with c.cursor() as cur:
                    cur.execute(
                        """
                        UPDATE scraping_jobs
                        SET status='failed',
                            error_detalle='Worker terminado por señal (%s)'
                        WHERE id=%s AND status='running'
                        """ % (sig_name, "%s"),
                        (_job_actual["id"],),
                    )
                    c.commit()
            ejecutar_con_reconexion(_marcar_failed)
        except Exception:
            pass
    sys.exit(0)


signal.signal(signal.SIGTERM, _signal_handler)
signal.signal(signal.SIGINT, _signal_handler)


# ══════════════════════════════════════════════════════
# 9. HEALTH CHECK ENDPOINT
# ══════════════════════════════════════════════════════
def _start_health_check_server():
    """Inicia servidor HTTP de health check en puerto 8002."""
    try:
        from http.server import BaseHTTPRequestHandler, HTTPServer

        class HealthHandler(BaseHTTPRequestHandler):
            def do_GET(self):
                status = {
                    "ok": True,
                    "service": "mapadata-worker",
                    "job_actual": _job_actual["id"],
                    "uptime": time.time() - _START_TIME,
                    "timestamp": datetime.utcnow().isoformat() + "Z",
                }
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                import json
                self.wfile.write(json.dumps(status).encode())

            def log_message(self, format, *args):
                pass  # silenciar logs HTTP

        server = HTTPServer(("127.0.0.1", 8002), HealthHandler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        print("  🏥 Health check en http://127.0.0.1:8002/health")
    except Exception as e:
        print(f"  ⚠️ No se pudo iniciar health check: {e}")


_START_TIME = time.time()


# ══════════════════════════════════════════════════════
# LOOP PRINCIPAL
# ══════════════════════════════════════════════════════
def loop_worker():
    """Loop principal del worker."""
    print("=" * 60)
    print("🚀 Mapadata Worker v5.0 iniciado")
    print(f"   Max workers Places: {MAX_WORKERS_PLACES}")
    print(f"   Max jobs activos: {MAX_JOBS_ACTIVOS}")
    print(f"   Output dir: {OUTPUT_DIR}")
    print("=" * 60)

    _start_health_check_server()

    ultimo_check_stale = 0

    while not _shutdown_event.is_set():
        # Stale job detector cada 5 min
        if time.time() - ultimo_check_stale > 300:
            limpiar_jobs_perdidos()
            ultimo_check_stale = time.time()

        # Tomar siguiente job
        def tomar_job(c):
            with c.cursor() as cur:
                cur.execute(
                    """
                    SELECT id, comunas, terminos, modo
                    FROM scraping_jobs
                    WHERE status='queued'
                    ORDER BY creado_en
                    LIMIT 1
                    FOR UPDATE SKIP LOCKED
                    """,
                )
                row = cur.fetchone()
                if not row:
                    c.commit()
                    return None
                job_id, comunas, terminos, modo = row
                cur.execute(
                    "UPDATE scraping_jobs SET status='running' WHERE id=%s",
                    (job_id,),
                )
                c.commit()
                return row

        row = ejecutar_con_reconexion(tomar_job)
        if not row:
            time.sleep(5)
            continue

        job_id, comunas, terminos, modo = row
        _job_actual["id"] = job_id

        # Adquirir semáforo (límite de jobs concurrentes)
        if not _jobs_sem.acquire(timeout=10):
            print(f"  ⏳ Job {job_id}: esperando slot (máx {MAX_JOBS_ACTIVOS} jobs)...")
            if not _jobs_sem.acquire(timeout=60):
                print(f"  ❌ Job {job_id}: timeout esperando slot, reintentando")
                continue

        try:
            print(f"\n{'─' * 50}")
            print(f"📦 Procesando job {job_id}")
            print(f"{'─' * 50}")

            conn_job = get_conn()
            try:
                path, total, con_email = procesar_job(
                    job_id, comunas, terminos or TERMINOS_DEFAULT, modo
                )
            finally:
                put_conn(conn_job)

            # Subir a R2
            url_storage = subir_a_storage(path, job_id)
            if url_storage:
                try:
                    os.remove(path)
                    print(f"  🗑️ Archivo local eliminado: {path}")
                except Exception:
                    pass

            # Marcar como done
            def marcar_done(c):
                with c.cursor() as cur:
                    cur.execute(
                        """
                        UPDATE scraping_jobs
                        SET status='done',
                            total_empresas=%s,
                            con_email=%s,
                            resultado_csv_url=%s,
                            terminado_en=now()
                        WHERE id=%s
                        """,
                        (total, con_email, url_storage, job_id),
                    )
                    c.commit()

            ejecutar_con_reconexion(marcar_done)
            print(f"  ✅ Job {job_id} completado exitosamente")

        except Exception as e:
            detalle = traceback.format_exc()
            print(f"  ❌ Job {job_id} falló: {e}")

            # Marcar como failed
            def marcar_failed(c):
                with c.cursor() as cur:
                    cur.execute(
                        """
                        UPDATE scraping_jobs
                        SET status='failed',
                            error_detalle=%s
                        WHERE id=%s
                        """,
                        (detalle[:4000], job_id),
                    )
                    c.commit()

            try:
                ejecutar_con_reconexion(marcar_failed)
            except Exception as e2:
                print(f"  ⚠️ No se pudo marcar failed: {e2}")

            # Enviar alerta
            _enviar_alerta_telegram(
                f"🚨 Job {job_id} falló en Mapata\n"
                f"Error: {str(e)[:200]}\n"
                f"Detalles: {detalle[:500]}"
            )

        finally:
            _job_actual["id"] = None
            _jobs_sem.release()


if __name__ == "__main__":
    loop_worker()
