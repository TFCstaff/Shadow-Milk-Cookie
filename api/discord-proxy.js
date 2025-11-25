// api/discord-proxy.js
import fetch from "node-fetch";

export default async function handler(req, res) {
  try {
    // Forward request to Katabump server
    const katabumpURL = `http://145.239.65.118:20319${req.url}`;

    const response = await fetch(katabumpURL, {
      method: req.method,
      headers: {
        "Content-Type": "application/json",
        "Authorization": req.headers.authorization || ""
      },
      body: req.method === "POST" ? JSON.stringify(req.body) : undefined
    });

    // Forward response back
    const text = await response.text();
    res.status(response.status).send(text);
  } catch (err) {
    console.error("Proxy error:", err);
    res.status(500).json({ error: "Proxy failed" });
  }
}
