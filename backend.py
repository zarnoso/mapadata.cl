#!/usr/bin/env python3
"""
Mapadata Backend API - FastAPI

Canonical API for mapadata.cl.
This file should be the single source of truth for the public backend.
"""

import logging
import os
from contextlib import contextmanager
from datetime import datetime
from typing import List, Optional

import psycopg2
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from psycopg2.extras import RealDictCursor

DB_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://neondb_owner:REDACTED_DB_PASS@ep-dark-sunset-ah922o3v-pooler.c-3.us-east-1.aws.neon.tech/neondb?sslmode=require",
)
ALLOWED_ORIGINS = [
    origin.strip()
    for origin in os.getenv(
        "CORS_ORIGINS",
        "https://www.mapadata.cl,https://mapadata.cl,http://localhost:3000,http://localhost:3001",
    ).split(",")
    if origin.strip()
]
DEFAULT_TERMINOS = [
    "comercializadora",
    "distribuidora",
    "importadora",
    "mayorista",
    "proveedor",
]

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("mapadata-api")

app = FastAPI(title="Mapadata API", version="2.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class JobCreate(BaseModel):
    comunas: List[str]
    terminos: Optional[List[str]] = None
    modo: Optional[str] = "enriched"
    cliente_id: int = 1


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
    service: str
    db: str
    ts: str


@contextmanager
def get_db():
    conn = psycopg2.connect(DB_URL, sslmode="require", cursor_factory=RealDictCursor)
    try:
        yield conn
    finally:
        conn.close()


@app.get("/")
async def root():
    return {"ok": True, "service": "mapadata-api", "version": "2.0.0"}


@app.get("/health", response_model=HealthResponse)
@app.get("/api/health", response_model=HealthResponse)
async def health():
    try:
        with get_db() as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()
        return HealthResponse(
            ok=True,
            service="mapadata-api",
            db="ok",
            ts=datetime.utcnow().isoformat() + "Z",
        )
    except Exception as exc:
        logger.exception("healthcheck_failed")
        return HealthResponse(
            ok=False,
            service="mapadata-api",
            db=f"error: {exc}",
            ts=datetime.utcnow().isoformat() + "Z",
        )


@app.get("/api/comunas", response_model=List[Comuna])
async def listar_comunas(region: Optional[str] = None):
    with get_db() as conn:
        with conn.cursor() as cursor:
            if region:
                cursor.execute(
                    """
                    SELECT id, nombre, region, region_number
                    FROM comunas_chile
                    WHERE region ILIKE %s
                    ORDER BY region, nombre
                    """,
                    (f"%{region}%",),
                )
            else:
                cursor.execute(
                    "SELECT id, nombre, region, region_number FROM comunas_chile ORDER BY region, nombre"
                )
            return cursor.fetchall()


@app.get("/api/regiones")
async def listar_regiones():
    with get_db() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT DISTINCT region, region_number FROM comunas_chile ORDER BY region"
            )
            return cursor.fetchall()


@app.post("/api/jobs", response_model=JobResponse)
async def crear_job(job: JobCreate):
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
                    cursor.execute(
                        "SELECT nombre FROM comunas_chile WHERE nombre ILIKE %s LIMIT 1",
                        (comuna,),
                    )
                    result = cursor.fetchone()
                    if not result:
                        raise HTTPException(
                            status_code=400, detail=f"Comuna no encontrada: {comuna}"
                        )
                    comunas_normalizadas.append(result["nombre"])

            if not comunas_normalizadas:
                raise HTTPException(
                    status_code=400, detail="No se encontraron comunas válidas"
                )

            terminos = job.terminos or DEFAULT_TERMINOS

            cursor.execute(
                """
                INSERT INTO scraping_jobs (comunas, terminos, modo, cliente_id, status)
                VALUES (%s, %s, %s, %s, 'queued')
                RETURNING id, status, comunas, terminos, modo, creado_en
                """,
                (comunas_normalizadas, terminos, job.modo, job.cliente_id),
            )
            new_job = cursor.fetchone()
            conn.commit()

    logger.info("job_created", extra={"job_id": new_job["id"], "comunas": len(comunas_normalizadas)})
    return {
        "id": new_job["id"],
        "status": new_job["status"],
        "comunas": new_job["comunas"],
        "terminos": new_job["terminos"],
        "modo": new_job["modo"],
        "total_empresas": None,
        "con_email": None,
        "resultado_csv_url": None,
        "creado_en": new_job["creado_en"],
        "terminado_en": None,
        "error_message": None,
    }


@app.get("/api/jobs/{job_id}", response_model=JobResponse)
async def obtener_job(job_id: int):
    with get_db() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT id, status, comunas, terminos, modo, total_empresas, con_email,
                       resultado_csv_url, creado_en, terminado_en, error_message
                FROM scraping_jobs
                WHERE id = %s
                """,
                (job_id,),
            )
            job = cursor.fetchone()
            if not job:
                raise HTTPException(status_code=404, detail="Job no encontrado")
            return job


@app.get("/api/jobs", response_model=List[JobResponse])
async def listar_jobs(cliente_id: Optional[int] = None, status: Optional[str] = None):
    with get_db() as conn:
        with conn.cursor() as cursor:
            query = """
                SELECT id, status, comunas, terminos, modo, total_empresas, con_email,
                       resultado_csv_url, creado_en, terminado_en, error_message
                FROM scraping_jobs
            """
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

            query += " ORDER BY creado_en DESC LIMIT 100"
            cursor.execute(query, params)
            return cursor.fetchall()


@app.delete("/api/jobs/{job_id}")
async def cancelar_job(job_id: int):
    with get_db() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                UPDATE scraping_jobs
                SET status = 'cancelled', terminado_en = now()
                WHERE id = %s AND status IN ('queued', 'running')
                RETURNING id, status
                """,
                (job_id,),
            )
            result = cursor.fetchone()
            conn.commit()

            if not result:
                raise HTTPException(
                    status_code=400,
                    detail="Job no encontrado o ya completado/cancelado",
                )

            return {"id": result["id"], "status": result["status"]}


@app.get("/api/stats")
async def estadisticas():
    with get_db() as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) AS total FROM comunas_chile")
            total_comunas = cursor.fetchone()["total"]

            cursor.execute("SELECT COUNT(*) AS total FROM scraping_jobs")
            total_jobs = cursor.fetchone()["total"]

            cursor.execute(
                "SELECT status, COUNT(*) AS total FROM scraping_jobs GROUP BY status"
            )
            jobs_por_estado = {
                row["status"]: row["total"] for row in cursor.fetchall()
            }

            cursor.execute(
                "SELECT COALESCE(SUM(total_empresas), 0) AS total FROM scraping_jobs WHERE status = 'done'"
            )
            total_empresas = cursor.fetchone()["total"]

            return {
                "comunas_chile": total_comunas,
                "total_jobs": total_jobs,
                "jobs_por_estado": jobs_por_estado,
                "total_empresas_extraidas": total_empresas,
            }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", "8001")))
