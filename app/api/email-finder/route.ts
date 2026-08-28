import { NextResponse } from "next/server";

function normalizar(texto: string) {
  return texto
    .toLowerCase()
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .replace(/ñ/g, "n")
    .replace(/\s+/g, "");
}

function generarDominios(base: string) {
  // si ya viene con dominio completo, usarlo como base
  const limpio = base.replace(/https?:\/\//, "").replace("www.", "");

  const nombre = limpio.split(".")[0];

  return [
    `${nombre}.cl`,
    `${nombre}.com`,
  ];
}

function generarEmails(nombre: string, apellido: string, dominio: string) {
  const n = normalizar(nombre);
  const a = normalizar(apellido);

  return [
    `${n}.${a}@${dominio}`,
    `${n[0]}.${a}@${dominio}`,
    `${n}${a}@${dominio}`,
    `${n}@${dominio}`,
    `${a}.${n}@${dominio}`,
    `${n}_${a}@${dominio}`,
  ];
}

export async function GET(req: Request) {
  const { searchParams } = new URL(req.url);

  const nombre = searchParams.get("nombre");
  const apellido = searchParams.get("apellido");
  const dominioInput = searchParams.get("dominio");

  if (!nombre || !apellido || !dominioInput) {
    return NextResponse.json({
      ok: false,
      error: "Faltan parámetros",
    });
  }

  const dominios = generarDominios(dominioInput);

  let resultados: any[] = [];

  dominios.forEach((dominio) => {
    const emails = generarEmails(nombre, apellido, dominio);

    emails.forEach((email, i) => {
      resultados.push({
        email,
        dominio,
        score: 90 - i * 10,
      });
    });
  });

  // ordenar por score
  resultados = resultados.sort((a, b) => b.score - a.score);

  // devolver top 5
  return NextResponse.json({
    ok: true,
    data: resultados.slice(0, 5),
  });
}