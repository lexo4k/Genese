export default async function handler(req, res) {
  res.setHeader("Cache-Control", "s-maxage=300, stale-while-revalidate=600");
  res.setHeader("Access-Control-Allow-Origin", "*");
  if (req.method !== "GET") return res.status(405).json({ error: "Método não permitido" });
  const query = String(req.query.q || "").trim().slice(0, 100);
  if (query.length < 2) return res.status(400).json({ error: "Digite pelo menos 2 caracteres." });
  const token = process.env.TMDB_READ_ACCESS_TOKEN;
  if (!token) return res.status(200).json({ configured: false, provider: "TMDB", results: [], message: "A integração de metadados ainda precisa de uma credencial TMDB válida e autorização de uso adequada." });
  try {
    const url = new URL("https://api.themoviedb.org/3/search/multi");
    url.searchParams.set("query", query);
    url.searchParams.set("include_adult", "false");
    url.searchParams.set("language", "pt-BR");
    url.searchParams.set("page", "1");
    const response = await fetch(url, { headers: { Authorization: "Bearer " + token, Accept: "application/json" } });
    if (!response.ok) return res.status(502).json({ error: "O catálogo TMDB respondeu com erro.", providerStatus: response.status });
    const data = await response.json();
    const results = (data.results || []).filter(x => ["movie", "tv"].includes(x.media_type) && x.adult !== true).slice(0, 20).map(x => ({
      id: String(x.id), tmdbId: x.id, mediaType: x.media_type,
      title: x.title || x.name || "Título sem nome",
      year: (x.release_date || x.first_air_date || "").slice(0, 4),
      description: x.overview || "Sinopse não informada.",
      poster: x.poster_path ? "https://image.tmdb.org/t/p/w500" + x.poster_path : "",
      backdrop: x.backdrop_path ? "https://image.tmdb.org/t/p/w780" + x.backdrop_path : "",
      rating: typeof x.vote_average === "number" ? x.vote_average : null,
      source: "TMDB", metadataOnly: true
    }));
    return res.status(200).json({ configured: true, provider: "TMDB", results });
  } catch {
    return res.status(502).json({ error: "Falha ao consultar o catálogo de metadados." });
  }
}
