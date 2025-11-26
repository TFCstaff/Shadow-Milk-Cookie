import discord
from discord.ext import commands
import aiosqlite
import random
import time

XP_MIN = 10
XP_MAX = 20
BASE_COOLDOWN = 30  # seconds per user default

DB = "python-bot/data/levels.db"

class LevelingCore(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # cooldowns: {guild_id: {user_id: last_ts}}
        self.cooldowns = {}

    async def cog_load(self):
        # ensure tables exist (if not created by config cog)
        async with aiosqlite.connect(DB) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS leveling (
                    guild_id INTEGER,
                    user_id INTEGER,
                    xp INTEGER,
                    level INTEGER,
                    PRIMARY KEY (guild_id, user_id)
                )
            """)
            await db.execute("""
                CREATE TABLE IF NOT EXISTS level_config (
                    guild_id INTEGER PRIMARY KEY,
                    message TEXT,
                    attachment_url TEXT,
                    xp_multiplier REAL DEFAULT 1.0,
                    level_channel_id INTEGER
                    embed_color INTEGER DEFAULT 0x3498db
                )
            """)
            await db.execute("""
                CREATE TABLE IF NOT EXISTS level_roles (
                    guild_id INTEGER,
                    level INTEGER,
                    role_id INTEGER,
                    PRIMARY KEY (guild_id, level)
                )
            """)
            await db.execute("""
                CREATE TABLE IF NOT EXISTS level_block_channels (
                    guild_id INTEGER,
                    channel_id INTEGER,
                    PRIMARY KEY (guild_id, channel_id)
                )
            """)
            await db.commit()

    def get_user_last(self, guild_id, user_id):
        return self.cooldowns.get(guild_id, {}).get(user_id, 0)

    def set_user_last(self, guild_id, user_id, ts):
        self.cooldowns.setdefault(guild_id, {})[user_id] = ts

    async def is_channel_blocked(self, guild_id, channel_id):
        async with aiosqlite.connect(DB) as db:
            cursor = await db.execute("SELECT 1 FROM level_block_channels WHERE guild_id=? AND channel_id=?", (guild_id, channel_id))
            r = await cursor.fetchone()
            return bool(r)

    async def get_multiplier(self, guild_id):
        async with aiosqlite.connect(DB) as db:
            cursor = await db.execute("SELECT xp_multiplier FROM level_config WHERE guild_id=?", (guild_id,))
            row = await cursor.fetchone()
            return row[0] if row and row[0] is not None else 1.0

    async def get_level_role(self, guild_id, level):
        async with aiosqlite.connect(DB) as db:
            cursor = await db.execute("SELECT role_id FROM level_roles WHERE guild_id=? AND level=?", (guild_id, level))
            row = await cursor.fetchone()
            return int(row[0]) if row else None

    async def get_level_message(self, guild_id):
        async with aiosqlite.connect(DB) as db:
            cursor = await db.execute("SELECT message, attachment_url FROM level_config WHERE guild_id=?", (guild_id,))
            row = await cursor.fetchone()
            if row:
                return {"message": row[0] or "{user} leveled up to **Level {level}**!", "attachment": row[1]}
            else:
                return {"message": "{user} leveled up to **Level {level}**!", "attachment": None}
            
    async def get_embed_color(self, guild_id):
        async with aiosqlite.connect(DB) as db:
            cursor = await db.execute("SELECT embed_color FROM level_config WHERE guild_id=?", (guild_id,))
            row = await cursor.fetchone()
            return row[0] if row and row[0] is not None else 0x3498db


    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        # core guard
        if message.author.bot or not message.guild:
            return

        guild_id = message.guild.id
        user_id = message.author.id
        channel_id = message.channel.id

        # check blocked channel
        if await self.is_channel_blocked(guild_id, channel_id):
            return

        # cooldown per user (can be adjusted per-guild later)
        last = self.get_user_last(guild_id, user_id)
        now = time.time()
        if now - last < BASE_COOLDOWN:
            return

        self.set_user_last(guild_id, user_id, now)

        # xp with multiplier
        multiplier = await self.get_multiplier(guild_id)
        xp_gain = int(random.randint(XP_MIN, XP_MAX) * multiplier)

        async with aiosqlite.connect(DB) as db:
            # upsert
            cursor = await db.execute("SELECT xp, level FROM leveling WHERE guild_id=? AND user_id=?", (guild_id, user_id))
            row = await cursor.fetchone()
            if row is None:
                xp, level = xp_gain, 1
                await db.execute("INSERT INTO leveling (guild_id, user_id, xp, level) VALUES (?, ?, ?, ?)", (guild_id, user_id, xp, level))
            else:
                xp, level = row
                xp += xp_gain
                await db.execute("UPDATE leveling SET xp=? WHERE guild_id=? AND user_id=?", (xp, guild_id, user_id))

            # check level up threshold (simple formula: level * 100)
            required = level * 100
            if xp >= required:
                new_level = level + 1
                xp -= required
                await db.execute("UPDATE leveling SET level=?, xp=? WHERE guild_id=? AND user_id=?", (new_level, xp, guild_id, user_id))
                await db.commit()

                # send level up embed and reward role
                await self.handle_levelup(message, new_level)
            else:
                await db.commit()

    async def handle_levelup(self, message: discord.Message, new_level: int):
        guild = message.guild
        member = message.author

        # get level config from LevelConfig cog
        config_cog = self.bot.get_cog("LevelConfig")
        if config_cog:
            cfg = await config_cog.get_config(guild.id)
        else:
            cfg = {"message": "{user} leveled up to **Level {level}**!", "attachment": None, "channel": None}

        text = cfg["message"].replace("{user}", member.mention)\
                             .replace("{username}", member.name)\
                             .replace("{level}", str(new_level))\
                             .replace("{avatar}", member.display_avatar.url)

        color = cfg.get("color", 0x3498db)  # pulled from LevelConfig
        embed = discord.Embed(
            title="<a:SMC_SPARKLES:1435957094598578246> Level Up!",
            description=text,
            color=color
        )
        if cfg.get("attachment"):
            embed.set_image(url=cfg["attachment"])
        embed.set_thumbnail(url=member.display_avatar.url)

        # send to custom channel if set
        level_channel_id = cfg.get("channel")
        if level_channel_id:
            channel = guild.get_channel(level_channel_id)
            if channel:
                await channel.send(embed=embed)
                return

        # fallback → same channel
        await message.channel.send(embed=embed)

        # give role reward if exists
        role_id = await self.get_level_role(guild.id, new_level)
        if role_id:
            role = guild.get_role(role_id)
            if role:
                try:
                    await member.add_roles(role, reason="Level role reward")
                except discord.Forbidden:
                    try:
                        await message.channel.send("⚠️ I couldn't add the level role (missing permissions).", delete_after=8)
                    except:
                        pass


async def setup(bot):
    await bot.add_cog(LevelingCore(bot))
