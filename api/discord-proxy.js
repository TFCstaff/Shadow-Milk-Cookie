const fetch = require("node-fetch");

export default async function handler(req, res) {
  // Forward the request to your Katabump dashboard
  const url = `http://145.239.65.118:20319${req.url}`;

  try {
    const response = await fetch(url, {
      method: req.method,
      headers: {
        "Content-Type": "application/json",
        "Authorization": req.headers.authorization || ""
      },
      body: req.method === "POST" ? JSON.stringify(req.body) : undefined
    });

    const data = await response.text(); // forward raw text
    res.status(response.status).send(data);
  } catch (err) {
    console.error("Proxy error:", err);
    res.status(500).json({ error: "Proxy failed" });
  }
}
