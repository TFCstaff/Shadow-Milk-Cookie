export default async function handler(req, res) {
    const token = req.query.token;

    if (!token) {
        return res.status(400).json({ error: "Missing token" });
    }

    try {
        const discordResponse = await fetch("https://discord.com/api/users/@me", {
            headers: {
                Authorization: `Bearer ${token}`
            }
        });

        if (!discordResponse.ok) {
            const errorText = await discordResponse.text();
            return res.status(500).json({ error: "Discord API error", message: errorText });
        }

        const user = await discordResponse.json();
        res.status(200).json(user);

    } catch (error) {
        res.status(500).json({ error: error.message });
    }
}
