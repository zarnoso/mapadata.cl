export async function GET(request: Request) {
  try {
    const { searchParams } = new URL(request.url);
    const rut = searchParams.get("rut");

    if (!rut) {
      return Response.json({ ok: false, error: "Falta RUT" });
    }

    const url = `https://zeus.sii.cl/cvc/stc/stc.html?RUT=${rut}`;

    const res = await fetch(url, {
      headers: {
        "User-Agent":
          "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120 Safari/537.36",
        "Accept":
          "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "es-CL,es;q=0.9",
        "Connection": "keep-alive",
      },
    });

    const html = await res.text();

    return Response.json({
      ok: true,
      preview: html.substring(0, 500),
    });

  } catch (error: any) {
    return Response.json({
      ok: false,
      error: error.message,
    });
  }
}