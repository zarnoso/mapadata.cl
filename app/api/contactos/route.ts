export async function GET(req: Request) {
  const { searchParams } = new URL(req.url);
  const rut = searchParams.get("rut");

  if (!rut) {
    return Response.json({ ok: false, error: "Falta rut" });
  }

  return Response.json({
    ok: true,
    data: [
      { nombre: "Juan", apellido: "Pérez", cargo: "Gerente General" },
      { nombre: "María", apellido: "González", cargo: "Directora Comercial" }
    ]
  });
}