module.exports = function handler(req, res) {
  res.setHeader("Cache-Control", "no-store");
  if (req.method !== "GET") return res.status(405).json({ error: "Método não permitido" });
  return res.status(200).json({
    metadata: { name: "TMDB", configured: Boolean(process.env.TMDB_READ_ACCESS_TOKEN), purpose: "Metadados e imagens, não reprodução", credential: "TMDB_READ_ACCESS_TOKEN" },
    availability: { name: "JustWatch", configured: Boolean(process.env.JUSTWATCH_PARTNER_TOKEN), purpose: "Disponibilidade legal e links para provedores", credential: "JUSTWATCH_PARTNER_TOKEN" },
    playback: [
      { name: "Blender Video / PeerTube", configured: true, mode: "Player oficial incorporado para vídeos publicados e licenciados na plataforma" },
      { name: "YouTube IFrame Player", configured: true, mode: "Player oficial incorporado, sujeito a permissões de incorporação" },
      { name: "Plex", configured: false, mode: "Integração direta exige credenciais e acordo de parceiro Plex" },
      { name: "Prime Video", configured: false, mode: "APIs de conteúdo disponíveis apenas para parceiros gerenciados" }
    ]
  });
}
