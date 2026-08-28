import { NextResponse } from "next/server";

// GET /api/comunas - Lista todas las comunas
export async function GET() {
  return NextResponse.json({ data: COMUNAS_DEFAULT });
}

// POST /api/empresas - Buscar empresas
export async function POST(req: Request) {
  try {
    const body = await req.json();
    const { comunas, terminos } = body;

    if (!comunas || comunas.length === 0) {
      return NextResponse.json({ error: "Sin comunas" }, { status: 400 });
    }

    // Llamar al worker para procesar la búsqueda
    const workerUrl = process.env.WORKER_URL || "http://localhost:8001";
    
    const res = await fetch(`${workerUrl}/poll`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        comunas,
        terminos: terminos || ["comercializadora", "distribuidora", "importadora", "mayorista", "proveedor"],
        modo: "enriched",
      }),
    });

    if (!res.ok) {
      const errorText = await res.text();
      console.error("Worker error:", errorText);
      return NextResponse.json({ data: [], total: 0 });
    }

    const result = await res.json();
    return NextResponse.json({ data: result.empresas || [], total: result.total || 0 });
  } catch (e) {
    console.error("Error en POST /api/empresas:", e);
    return NextResponse.json({ data: [], total: 0 });
  }
}

const COMUNAS_DEFAULT = [
  { id: 1, nombre: "Santiago", region: "Metropolitana de Santiago", region_number: "RM" },
  { id: 2, nombre: "Providencia", region: "Metropolitana de Santiago", region_number: "RM" },
  { id: 3, nombre: "Las Condes", region: "Metropolitana de Santiago", region_number: "RM" },
  { id: 4, nombre: "Vitacura", region: "Metropolitana de Santiago", region_number: "RM" },
  { id: 5, nombre: "Ñuñoa", region: "Metropolitana de Santiago", region_number: "RM" },
  { id: 6, nombre: "La Florida", region: "Metropolitana de Santiago", region_number: "RM" },
  { id: 7, nombre: "Maipú", region: "Metropolitana de Santiago", region_number: "RM" },
  { id: 8, nombre: "Puente Alto", region: "Metropolitana de Santiago", region_number: "RM" },
  { id: 9, nombre: "Iquique", region: "Tarapacá", region_number: "I" },
  { id: 10, nombre: "Antofagasta", region: "Antofagasta", region_number: "II" },
  { id: 11, nombre: "La Serena", region: "Coquimbo", region_number: "IV" },
  { id: 12, nombre: "Valparaíso", region: "Valparaíso", region_number: "V" },
  { id: 13, nombre: "Viña del Mar", region: "Valparaíso", region_number: "V" },
  { id: 14, nombre: "Rancagua", region: "O'Higgins", region_number: "VI" },
  { id: 15, nombre: "Talca", region: "Maule", region_number: "VII" },
  { id: 16, nombre: "Concepción", region: "Biobío", region_number: "VIII" },
  { id: 17, nombre: "Temuco", region: "Araucanía", region_number: "IX" },
  { id: 18, nombre: "Valdivia", region: "Los Ríos", region_number: "XIV" },
  { id: 19, nombre: "Puerto Montt", region: "Los Lagos", region_number: "X" },
  { id: 20, nombre: "Coyhaique", region: "Aysén", region_number: "XI" },
  { id: 21, nombre: "Punta Arenas", region: "Magallanes", region_number: "XII" },
];
