export async function GET() {
  try {
    const year = 2024;
    const month = 1;

    const url = `${process.env.CMF_BASE_URL}/uf/${year}/${month}?apikey=${process.env.CMF_API_KEY}&formato=json`;

    const res = await fetch(url);
    const text = await res.text();

    return Response.json({
      ok: res.ok,
      url,
      response: text,
    });

  } catch (error: any) {
    return Response.json({
      ok: false,
      error: error.message,
    });
  }
}