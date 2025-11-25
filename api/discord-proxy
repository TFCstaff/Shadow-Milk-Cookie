export default async function handler(req, res) {
  try {
    const userAgent = req.headers["user-agent"] || "ShadowMilkProxy";

    const response = await fetch("https://discord.com/api/v10/users/@me", {
      headers: {
        Authorization: `Bearer ${req.headers["authorization"]}`,
        "User-Agent": userAgent,
      },
    });

    const data = await response.json();
    res.status(response.status).json(data);
  } catch (error) {
    res.status(500).json({ error: "Proxy error", details: error.message });
  }
}
