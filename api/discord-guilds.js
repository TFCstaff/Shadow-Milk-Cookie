// api/discord-guilds.js
export default async function handler(req, res) {
  try {
    const PROXY_SECRET = process.env.PROXY_SECRET || "";
    const secret = req.query.secret || req.headers["x-proxy-secret"];
    if (!PROXY_SECRET || secret !== PROXY_SECRET) {
      return res.status(401).json({ error: "Unauthorized (missing or invalid secret)" });
    }

    const token = req.query.token;
    if (!token) return res.status(400).json({ error: "Missing token query parameter" });

    const discordRes = await fetch("https://discord.com/api/users/@me/guilds", {
      headers: { Authorization: `Bearer ${token}` }
    });

    const json = await discordRes.json();
    return res.status(discordRes.status).json(json);
  } catch (err) {
    console.error("discord-guilds proxy error:", err);
    return res.status(500).json({ error: "Internal proxy error", details: String(err) });
  }
}
