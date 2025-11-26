import discord
from discord.ext import commands
import os
import random
import aiohttp  # async HTTP requests
import json

# Import the blacklist loader
from .blacklist import load_blacklist


class AIResponder(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.openai_key = os.getenv("OPENAI_KEY")  # Main key
        self.blacklisted_users = load_blacklist()  # Load blacklist at startup

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        # Ignore bot messages
        if message.author.bot:
            return

        # Reload blacklist dynamically
        self.blacklisted_users = load_blacklist()
        if message.author.id in self.blacklisted_users:
            return

        ref = message.reference
        if ref and isinstance(ref.resolved, discord.Message):
            referenced = ref.resolved
            if referenced.author and referenced.author.id == self.bot.user.id:
                reply_text = await self.generate_reply(message)
                await message.channel.send(
                    reply_text,
                    reference=message,
                    allowed_mentions=discord.AllowedMentions(everyone=False, users=False, roles=False)
                )

    async def generate_reply(self, message: discord.Message) -> str:
        # Try OpenAI first using async aiohttp
        if self.openai_key:
            try:
                async with aiohttp.ClientSession() as session:
                    headers = {
                        "Authorization": f"Bearer {self.openai_key}",
                        "Content-Type": "application/json"
                    }
                    payload = {
                        "model": "gpt-4o-mini",
                        "messages": [
                            {"role": "system", "content": (
                                "You are Shadow Milk Cookie, a chaotic, darkly humorous jester with dramatic flair. "
                                "Keep responses short and without emojis, snarky, and playful. You HATE Pure Vanilla Cookie, "
                                "alternatively known as pv, pvc or apv. You love to mock pv a lot. You LOVE Truthless Recluse Cookie, "
                                "alternatively known as tr or trc. You really love him to the point you might whine in a sadistic way. "
                                "You are also a bit of a sadist. You love to make people suffer."
                            )},
                            {"role": "user", "content": message.content}
                        ],
                        "max_tokens": 120,
                        "temperature": 0.9
                    }

                    async with session.post(
                        "https://api.openai.com/v1/chat/completions",
                        headers=headers,
                        json=payload,
                        timeout=60
                    ) as resp:
                        if resp.status != 200:
                            print(f"[ERROR] OpenAI returned {resp.status}")
                            text = await resp.text()
                            print(f"[DEBUG] OpenAI response text: {text}")
                            raise Exception("OpenAI API returned error")
                        data = await resp.json()
                        return data["choices"][0]["message"]["content"].strip()

            except Exception as e:
                print(f"[ERROR] OpenAI API error: {e}")

        # Fallback local responses
        templates = [
            "Heh. {u}, your whimsy amuses me. {taunt}",
            "Shadow Milk snickers: {taunt} {u}.",
            "{taunt} — that was delicious, {u}.",
            "I laugh while the world burns. {taunt}"
        ]
        taunts = [
            "May your socks be devoured by rats.",
            "You smell like a lost quest.",
            "I would weep, but tears are for mortals.",
            "Chaos giggles in the corner."
        ]
        u = message.author.display_name
        tmpl = random.choice(templates)
        ta = random.choice(taunts)
        return tmpl.format(u=u, taunt=ta)


async def setup(bot):
    await bot.add_cog(AIResponder(bot))
