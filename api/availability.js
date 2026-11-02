export default async function handler(req, res) {
  res.setHeader("Cache-Control", "s-maxage=900, stale-while-revalidate=1800");
  res.setHeader("Access-Control-Allow-Origin", "*");
  if (req.method !== "GET") return res.status(405).json({ error: "Método não permitido" });
  const id = String(req.query.id || "").trim();
  const type = req.query.type === "tv" ? "show" : "movie";
  if (!/^\\d{1,12}$/.test(id)) return res.status(400).json({ error: "ID TMDB inválido." });
  const token = process.env.JUSTWATCH_PARTNER_TOKEN;
  if (!token) return res.status(200).json({ configured: false, provider: "JustWatch", offers: [], message: "A consulta de disponibilidade exige contrato e token de parceiro JustWatch." });
  try {
    const url = new URL("https://apis.justwatch.com/contentpartner/v2/content/offers/object_type/" + type + "/id_type/tmdb/id/" + encodeURIComponent(id) + "/locale/pt_BR");
    url.searchParams.set("token", token);
    const response = await fetch(url, { headers: { Accept: "application/json" } });
    if (!response.ok) return res.status(502).json({ error: "JustWatch respondeu com erro.", providerStatus: response.status });
    const data = await response.json();
    const offers = Array.isArray(data) ? data : (data.offers || []);
    return res.status(200).json({ configured: true, provider: "JustWatch", fullPath: data.full_path || data.fullPath || null, offers });
  } catch {
    return res.status(502).json({ error: "Falha ao consultar disponibilidade no JustWatch." });
  }
}
