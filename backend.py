#!/usr/bin/env python3
import logging
import os
import re
from contextlib import contextmanager
from datetime import datetime
from typing import List, Optional

import psycopg2
from fastapi import FastAPI, HTTPException, Security, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from psycopg2.extras import RealDictCursor
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

DB_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql://neondb_owner:npg_EWrv14oPflCq@ep-autumn-firefly-at7pa7ut-pooler.c-9.us-east-1.aws.neon.tech/neondb?sslmode=require",
)
ALLOWED_ORIGINS = [
    origin.strip()
    for origin in os.environ.get(
        "CORS_ORIGINS",
        "https://www.mapadata.cl,https://mapadata.cl",
    ).split(",")
    if origin.strip()
]

API_KEY = os.environ.get("MAPADATA_API_KEY", "")

DEFAULT_TERMINOS = ["comercializadora", "distribuidora", "importadora", "mayorista", "proveedor"]

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("mapadata-api")

app = FastAPI(title="Mapadata API", version="2.1.0")

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request, exc):
    return JSONResponse(
        status_code=429,
        content={"detail": "Demadasadas requests. Intentá de nuevo en un minuto."}
    )

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS or ["https://www.mapadata.cl"],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

app.add_middleware(TrustedHostMiddleware, allowed_hosts=["api.mapadata.cl", "localhost", "127.0.0.1"])


@app.middleware("http")
async def add_security_headers(request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    return response


async def verify_api_key(request: Request):
    if not API_KEY:
        return True
    x_api_key = request.headers.get("X-API-Key", "")
    if x_api_key != API_KEY:
        raise HTTPException(status_code=403, detail="API Key inválida")
    return True


def sanitize_comuna(comuna: str) -> str:
    if not comuna or len(comuna) > 100:
        raise ValueError("Comuna inválida")
    if not re.match(r'^[a-zA-ZáéíóúÁÉÍÓÚñÑüÜ\s\-]+$', comuna):
        raise ValueError("Comuna contiene caracteres inválidos")
    return comuna.strip()


def sanitize_job_id(job_id: str) -> int:
    try:
        jid = int(job_id)
        if jid <= 0 or jid > 999999:
            raise ValueError
        return jid
    except (ValueError, TypeError):
        raise HTTPException(status_code=400, detail="Job ID inválido")


class JobCreate(BaseModel):
    comunas: List[str] = Field(..., min_items=1, max_items=347)
    terminos: Optional[List[str]] = None
    modo: Optional[str] = Field("enriched", pattern="^(enriched|basic)$")
    cliente_id: int = Field(1, ge=1, le=9999)


class JobResponse(BaseModel):
    id: int
    status: str
    comunas: List[str]
    terminos: List[str]
    modo: str
    total_empresas: Optional[int] = None
    con_email: Optional[int] = None
    resultado_csv_url: Optional[str] = None
    creado_en: Optional[datetime] = None
    terminado_en: Optional[datetime] = None
    error_message: Optional[str] = None


class Comuna(BaseModel):
    id: int
    nombre: str
    region: str
    region_number: str


class HealthResponse(BaseModel):
    ok: bool
    ts: str


@contextmanager
def get_db():
    if not DB_URL:
        raise HTTPException(status_code=503, detail="Base de datos no configurada")
    conn = psycopg2.connect(DB_URL, sslmode="require", cursor_factory=RealDictCursor)
    try:
        yield conn
    finally:
        conn.close()


@app.get("/")
async def root():
    return {"ok": True, "service": "mapadata-api"}


@app.get("/health", response_model=HealthResponse)
@app.get("/api/health", response_model=HealthResponse)
@limiter.limit("10/minute")
async def health(request: Request):
    return HealthResponse(ok=True, ts=datetime.utcnow().isoformat() + "Z")


@app.get("/api/comunas", response_model=List[Comuna])
@limiter.limit("60/minute")
async def listar_comunas(request: Request, region: Optional[str] = None):
    with get_db() as conn:
        with conn.cursor() as cursor:
            if region:
                region_clean = sanitize_comuna(region)
                cursor.execute(
                    "SELECT id, nombre, region, region_number FROM comunas_chile WHERE region ILIKE %s ORDER BY region, nombre",
                    (f"%{region_clean}%",),
                )
            else:
                cursor.execute("SELECT id, nombre, region, region_number FROM comunas_chile ORDER BY region, nombre")
            return cursor.fetchall()


@app.get("/api/regiones")
@limiter.limit("30/minute")
async def listar_regiones(request: Request):
    with get_db() as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT DISTINCT region, region_number FROM comunas_chile ORDER BY region")
            return cursor.fetchall()


@app.post("/api/jobs", response_model=JobResponse)
@limiter.limit("5/minute")
async def crear_job(request: Request, job: JobCreate, authorized: bool = Depends(verify_api_key)):
    if not job.comunas:
        raise HTTPException(status_code=400, detail="Debe seleccionar al menos una comuna")

    comunas_normalizadas: List[str] = []
    with get_db() as conn:
        with conn.cursor() as cursor:
            if "TODO_CHILE" in job.comunas:
                cursor.execute("SELECT nombre FROM comunas_chile ORDER BY region, nombre")
                comunas_normalizadas = [row["nombre"] for row in cursor.fetchall()]
            else:
                for comuna in job.comunas:
                    try:
                        comuna_clean = sanitize_comuna(comuna)
                    except ValueError as e:
                        raise HTTPException(status_code=400, detail=str(e))
                    cursor.execute("SELECT nombre FROM comunas_chile WHERE nombre ILIKE %s LIMIT 1", (comuna_clean,))
                    result = cursor.fetchone()
                    if not result:
                        raise HTTPException(status_code=400, detail=f"Comuna no encontrada: {comuna}")
                    comunas_normalizadas.append(result["nombre"])

            if not comunas_normalizadas:
                raise HTTPException(status_code=400, detail="No se encontraron comunas válidas")

            terminos = job.terminos or DEFAULT_TERMINOS
            cursor.execute(
                """INSERT INTO scraping_jobs (comunas, terminos, modo, cliente_id, status)
                   VALUES (%s, %s, %s, %s, 'queued')
                   RETURNING id, status, comunas, terminos, modo, creado_en""",
                (comunas_normalizadas, terminos, job.modo, job.cliente_id),
            )
            new_job = cursor.fetchone()
            conn.commit()

    logger.info(f"job_created: id={new_job['id']}, comunas={len(comunas_normalizadas)}")
    return {
        "id": new_job["id"], "status": new_job["status"],
        "comunas": new_job["comunas"], "terminos": new_job["terminos"],
        "modo": new_job["modo"], "total_empresas": None,
        "con_email": None, "resultado_csv_url": None,
        "creado_en": new_job["creado_en"], "terminado_en": None,
        "error_message": None,
    }


@app.get("/api/jobs/{job_id}", response_model=JobResponse)
@limiter.limit("30/minute")
async def obtener_job(request: Request, job_id: str, authorized: bool = Depends(verify_api_key)):
    jid = sanitize_job_id(job_id)
    with get_db() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """SELECT id, status, comunas, terminos, modo, total_empresas, con_email,
                          resultado_csv_url, creado_en, terminado_en, error_message
                   FROM scraping_jobs WHERE id = %s""",
                (jid,),
            )
            job = cursor.fetchone()
            if not job:
                raise HTTPException(status_code=404, detail="Job no encontrado")
            return job


@app.get("/api/jobs", response_model=List[JobResponse])
@limiter.limit("20/minute")
async def listar_jobs(request: Request, cliente_id: Optional[int] = None, status: Optional[str] = None, authorized: bool = Depends(verify_api_key)):
    with get_db() as conn:
        with conn.cursor() as cursor:
            query = """SELECT id, status, comunas, terminos, modo, total_empresas, con_email,
                              resultado_csv_url, creado_en, terminado_en, error_message
                       FROM scraping_jobs"""
            params = []
            conditions = []
            if cliente_id is not None:
                conditions.append("cliente_id = %s")
                params.append(cliente_id)
            if status:
                conditions.append("status = %s")
                params.append(status)
            if conditions:
                query += " WHERE " + " AND ".join(conditions)
            query += " ORDER BY creado_en DESC LIMIT 50"
            cursor.execute(query, params)
            return cursor.fetchall()


@app.delete("/api/jobs/{job_id}")
@limiter.limit("10/minute")
async def cancelar_job(request: Request, job_id: str, authorized: bool = Depends(verify_api_key)):
    jid = sanitize_job_id(job_id)
    with get_db() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """UPDATE scraping_jobs SET status = 'cancelled', terminado_en = now()
                   WHERE id = %s AND status IN ('queued', 'running')
                   RETURNING id, status""",
                (jid,),
            )
            result = cursor.fetchone()
            conn.commit()
            if not result:
                raise HTTPException(status_code=400, detail="Job no encontrado o ya completado/cancelado")
            return {"id": result["id"], "status": result["status"]}


@app.get("/api/stats")
@limiter.limit("10/minute")
async def estadisticas(request: Request, authorized: bool = Depends(verify_api_key)):
    with get_db() as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) AS total FROM comunas_chile")
            total_comunas = cursor.fetchone()["total"]
            cursor.execute("SELECT COUNT(*) AS total FROM scraping_jobs")
            total_jobs = cursor.fetchone()["total"]
            cursor.execute("SELECT status, COUNT(*) AS total FROM scraping_jobs GROUP BY status")
            jobs_por_estado = {row["status"]: row["total"] for row in cursor.fetchall()}
            cursor.execute("SELECT COALESCE(SUM(total_empresas), 0) AS total FROM scraping_jobs WHERE status = 'done'")
            total_empresas = cursor.fetchone()["total"]
            return {
                "comunas_chile": total_comunas, "total_jobs": total_jobs,
                "jobs_por_estado": jobs_por_estado, "total_empresas_extraidas": total_empresas,
            }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=int(os.environ.get("PORT", "8001")))
