import discord
from discord.ext import commands
from discord import app_commands
import aiosqlite

DEFAULT_MSG = "<a:SMC_SPARKLES:1435957094598578246> {user} leveled up to **Level {level}**!"

class LevelConfig(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = "python-bot/data/levels.db"

    async def cog_load(self):
        async with aiosqlite.connect(self.db) as db:
            # Table for leveling config
            await db.execute("""
                CREATE TABLE IF NOT EXISTS level_config (
                    guild_id INTEGER PRIMARY KEY,
                    message TEXT DEFAULT '{user} leveled up to {level}!',
                    attachment_url TEXT,
                    xp_multiplier REAL DEFAULT 1.0,
                    level_channel_id INTEGER,
                    embed_color INTEGER DEFAULT 0x3498db
                )
            """)


            # Table for level role rewards
            await db.execute("""
                CREATE TABLE IF NOT EXISTS level_roles (
                    guild_id INTEGER,
                    level INTEGER,
                    role_id INTEGER,
                    PRIMARY KEY (guild_id, level)
                )
            """)

            # Table for blocked channels
            await db.execute("""
                CREATE TABLE IF NOT EXISTS level_block_channels (
                    guild_id INTEGER,
                    channel_id INTEGER,
                    PRIMARY KEY (guild_id, channel_id)
                )
            """)

            await db.commit()

    # ---------- Helper to fetch config ----------
    async def get_config(self, guild_id):
        async with aiosqlite.connect(self.db) as db:
            cursor = await db.execute(
                "SELECT message, attachment_url, xp_multiplier, level_channel_id, embed_color "
                "FROM level_config WHERE guild_id=?",
                (guild_id,)
            )

            row = await cursor.fetchone()

            if row:
                return {
                    "message": row[0],
                    "attachment": row[1],
                    "multiplier": row[2],
                    "channel": row[3],
                    "color": row[4]
                }

            else:
                return {
                    "message": DEFAULT_MSG,
                    "attachment": None,
                    "multiplier": 1.0,
                    "channel": None,
                    "color": 0x3498db

                }

    # ---------- Slash group ----------
    group = app_commands.Group(name="level-up", description="Leveling configuration (guild mods only)")

    @group.command(name="preview", description="Show current level-up preview")
    @app_commands.default_permissions(manage_guild=True)
    async def preview(self, interaction: discord.Interaction):
        cfg = await self.get_config(interaction.guild.id)
        example = cfg["message"].replace("{user}", interaction.user.mention).replace("{level}", "5")
        embed = discord.Embed(
            title="Level-up Preview",
            description=example,
            color=cfg["color"]
        )
        if cfg["attachment"]:
            embed.set_image(url=cfg["attachment"])
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @group.command(name="set-message", description="Set the level-up message.")
    @app_commands.default_permissions(manage_guild=True)
    async def set_message(self, interaction: discord.Interaction, *, message: str):
        async with aiosqlite.connect(self.db) as db:
            await db.execute("""
                INSERT INTO level_config (guild_id, message)
                VALUES (?, ?)
                ON CONFLICT(guild_id) DO UPDATE SET message=excluded.message
            """, (interaction.guild.id, message))
            await db.commit()
        await interaction.response.send_message("<a:CheckMark:1440792005088120954> Saved!", ephemeral=True)

    @group.command(name="set-attachment", description="Set image/GIF for level-up embeds")
    @app_commands.default_permissions(manage_guild=True)
    async def set_attachment(self, interaction: discord.Interaction, url: str):
        async with aiosqlite.connect(self.db) as db:
            await db.execute("""
                INSERT INTO level_config (guild_id, attachment_url)
                VALUES (?, ?)
                ON CONFLICT(guild_id) DO UPDATE SET attachment_url=excluded.attachment_url
            """, (interaction.guild.id, url))
            await db.commit()
        await interaction.response.send_message("📎 Attachment set!", ephemeral=True)

    @group.command(name="set-multiplier", description="Set XP multiplier")
    @app_commands.default_permissions(manage_guild=True)
    async def set_multiplier(self, interaction: discord.Interaction, multiplier: float):
        if multiplier <= 0:
            return await interaction.response.send_message("Multiplier must be > 0.", ephemeral=True)
        async with aiosqlite.connect(self.db) as db:
            await db.execute("""
                INSERT INTO level_config (guild_id, xp_multiplier)
                VALUES (?, ?)
                ON CONFLICT(guild_id) DO UPDATE SET xp_multiplier=excluded.xp_multiplier
            """, (interaction.guild.id, multiplier))
            await db.commit()
        await interaction.response.send_message(f"Multiplier set to {multiplier}x!", ephemeral=True)

    @group.command(name="block-channel", description="Toggle XP in a channel")
    @app_commands.default_permissions(manage_guild=True)
    async def block_channel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        guild_id = interaction.guild.id
        chan_id = channel.id
        async with aiosqlite.connect(self.db) as db:
            cursor = await db.execute("SELECT 1 FROM level_block_channels WHERE guild_id=? AND channel_id=?", (guild_id, chan_id))
            found = await cursor.fetchone()
            if found:
                await db.execute("DELETE FROM level_block_channels WHERE guild_id=? AND channel_id=?", (guild_id, chan_id))
                await interaction.response.send_message(f"XP enabled in {channel.mention}.", ephemeral=True)
            else:
                await db.execute("INSERT INTO level_block_channels (guild_id, channel_id) VALUES (?, ?)", (guild_id, chan_id))
                await interaction.response.send_message(f"XP disabled in {channel.mention}.", ephemeral=True)
            await db.commit()

    @group.command(name="add-level-role", description="Give a role at a level")
    @app_commands.default_permissions(manage_guild=True)
    async def add_level_role(self, interaction: discord.Interaction, level: int, role: discord.Role):
        async with aiosqlite.connect(self.db) as db:
            await db.execute("""
                INSERT INTO level_roles (guild_id, level, role_id)
                VALUES (?, ?, ?)
                ON CONFLICT(guild_id, level) DO UPDATE SET role_id=excluded.role_id
            """, (interaction.guild.id, level, role.id))
            await db.commit()
        await interaction.response.send_message(f"Role added for level {level}.", ephemeral=True)

    @group.command(name="remove-level-role", description="Remove a reward role")
    @app_commands.default_permissions(manage_guild=True)
    async def remove_level_role(self, interaction: discord.Interaction, level: int):
        async with aiosqlite.connect(self.db) as db:
            await db.execute("DELETE FROM level_roles WHERE guild_id=? AND level=?", (interaction.guild.id, level))
            await db.commit()
        await interaction.response.send_message("Removed.", ephemeral=True)

    @group.command(name="set-channel", description="Set a channel for level-up messages")
    @app_commands.default_permissions(manage_guild=True)
    async def set_level_channel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        async with aiosqlite.connect(self.db) as db:
            await db.execute("""
                INSERT INTO level_config (guild_id, level_channel_id)
                VALUES (?, ?)
                ON CONFLICT(guild_id) DO UPDATE SET level_channel_id=excluded.level_channel_id
            """, (interaction.guild.id, channel.id))
            await db.commit()
        await interaction.response.send_message(f"Level-up messages → {channel.mention}", ephemeral=True)

    @group.command(name="clear-channel", description="Reset to sending in same channel")
    @app_commands.default_permissions(manage_guild=True)
    async def clear_level_channel(self, interaction: discord.Interaction):
        async with aiosqlite.connect(self.db) as db:
            await db.execute("UPDATE level_config SET level_channel_id=NULL WHERE guild_id=?", (interaction.guild.id,))
            await db.commit()
        await interaction.response.send_message("Now sending in same channel.", ephemeral=True)
    
    @group.command(name="set-color", description="Set the embed color (hex code).")
    @app_commands.default_permissions(manage_guild=True)
    async def set_color(self, interaction: discord.Interaction, hex_code: str):
        # Remove # if provided
        if hex_code.startswith("#"):
            hex_code = hex_code[1:]

        try:
            color_value = int(hex_code, 16)
        except ValueError:
            return await interaction.response.send_message("Invalid hex color! Example: `#3498db`", ephemeral=True)

        async with aiosqlite.connect(self.db) as db:
            await db.execute("""
                INSERT INTO level_config (guild_id, embed_color)
                VALUES (?, ?)
                ON CONFLICT(guild_id) DO UPDATE SET embed_color=excluded.embed_color
            """, (interaction.guild.id, color_value))
            await db.commit()

        await interaction.response.send_message(f"Embed color updated to `#{hex_code}`!", ephemeral=True)


async def setup(bot):
    await bot.add_cog(LevelConfig(bot))
