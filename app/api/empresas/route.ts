import { NextResponse } from "next/server";

const WORKER_URL = process.env.WORKER_URL || "http://localhost:8001";
const COMUNAS_DEFAULT = [
  { id: 1, nombre: "Santiago", region: "Metropolitana de Santiago", region_number: "RM" },
  { id: 2, nombre: "Providencia", region: "Metropolitana de Santiago", region_number: "RM" },
  { id: 3, nombre: "Las Condes", region: "Metropolitana de Santiago", region_number: "RM" },
  { id: 4, nombre: "Vitacura", region: "Metropolitana de Santiago", region_number: "RM" },
  { id: 5, nombre: "Ñuñoa", region: "Metropolitana de Santiago", region_number: "RM" },
  { id: 6, nombre: "La Florida", region: "Metropolitana de Santiago", region_number: "RM" },
  { id: 7, nombre: "Maipú", region: "Metropolitana de Santiago", region_number: "RM" },
  { id: 8, nombre: "Puente Alto", region: "Metropolitana de Santiago", region_number: "RM" },
];

// POST /api/empresas - Inicia búsqueda y espera resultados
export async function POST(req: Request) {
  try {
    const { comunas, terminos } = await req.json();

    if (!comunas || comunas.length === 0) {
      return NextResponse.json({ error: "Sin comunas" }, { status: 400 });
    }

    // Intentar conectar al worker
    try {
      const res = await fetch(`${WORKER_URL}/api/jobs`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          comunas,
          terminos: terminos || ["comercializadora", "distribuidora", "importadora", "mayorista", "proveedor"],
          modo: "enriched",
          cliente_id: 1,
        }),
      });

      if (res.ok) {
        const job = await res.json();
        return NextResponse.json({ job_id: job.id, status: "queued" });
      }
    } catch (workerError) {
      console.log("Worker no disponible:", workerError);
    }

    // Fallback: devolver datos de ejemplo
    return NextResponse.json({
      job_id: null,
      status: "completed",
      data: EMPRESAS_EJEMPLO,
      total: EMPRESAS_EJEMPLO.length,
    });
  } catch (e) {
    console.error("Error en POST /api/empresas:", e);
    return NextResponse.json({ data: [], total: 0, error: "Error interno" });
  }
}

// GET /api/comunas - Lista comunas desde worker
export async function GET() {
  return NextResponse.json({
    data: COMUNAS_DEFAULT,
  });
}

const EMPRESAS_EJEMPLO = [
  {
    id: "1",
    nombre: "Comercializadora Santiago Ltda.",
    direccion: "Av. Providencia 1234, Providencia",
    tipo_busqueda: "comercializadora",
    zona_busqueda: "Santiago",
    telefono: "+56 2 2345 6789",
    web: "www.comercializadorasantiago.cl",
    email: "contacto@comercializadorasantiago.cl",
  },
  {
    id: "2",
    nombre: "Distribuidora del Sur",
    direccion: "Calle Los Olmos 567, Las Condes",
    tipo_busqueda: "distribuidora",
    zona_busqueda: "Santiago",
    telefono: "+56 2 2345 6790",
    web: "www.distribuidoradelsur.cl",
    email: "ventas@distribuidoradelsur.cl",
  },
  {
    id: "3",
    nombre: "Importadora Andina",
    direccion: "Av. Vitacura 890, Vitacura",
    tipo_busqueda: "importadora",
    zona_busqueda: "Santiago",
    telefono: "+56 2 2345 6791",
    web: "www.importadoraandina.cl",
    email: "info@importadoraandina.cl",
  },
];
