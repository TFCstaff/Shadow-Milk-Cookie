import discord
from discord.ext import commands
from discord import app_commands
import aiosqlite
import io
import aiohttp
from PIL import Image, ImageDraw, ImageFont, ImageFilter

DB = "python-bot/data/levels.db"

# fonts - try to use a default system font if not provided
# You may change FONT_PATH to a .ttf you include in your project.
FONT_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

def draw_green_grid(base: Image.Image):
    """Draw a subtle green grid overlay on the image."""
    w, h = base.size
    overlay = Image.new("RGBA", base.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(overlay)
    spacing = 20
    line_color = (0, 255, 157, 30)  # translucent neon green
    for x in range(0, w, spacing):
        d.line([(x, 0), (x, h)], fill=line_color, width=1)
    for y in range(0, h, spacing):
        d.line([(0, y), (w, y)], fill=line_color, width=1)
    # subtle diagonal accents
    for i in range(-h, w, spacing):
        d.line([(i, 0), (i + h, h)], fill=(0, 255, 157, 10), width=1)
    return Image.alpha_composite(base.convert("RGBA"), overlay)

async def fetch_avatar_bytes(url: str, session: aiohttp.ClientSession):
    async with session.get(url) as resp:
        return await resp.read()

async def generate_rank_card(member: discord.Member, xp: int, level: int, required: int):
    # card size
    width, height = 900, 300
    base = Image.new("RGBA", (width, height), (2, 2, 2, 255))  # near-black background
    base = draw_green_grid(base)

    draw = ImageDraw.Draw(base)

    # load font
    try:
        title_font = ImageFont.truetype(FONT_PATH, 28)
        main_font = ImageFont.truetype(FONT_PATH, 40)
        small_font = ImageFont.truetype(FONT_PATH, 18)
    except Exception:
        title_font = ImageFont.load_default()
        main_font = ImageFont.load_default()
        small_font = ImageFont.load_default()

    # Avatar (circle with glow)
    avatar_size = 160
    avatar_x = 40
    avatar_y = (height - avatar_size) // 2

    async with aiohttp.ClientSession() as session:
        avatar_bytes = await fetch_avatar_bytes(str(member.display_avatar.replace(size=512)), session)

    avatar_img = Image.open(io.BytesIO(avatar_bytes)).convert("RGBA").resize((avatar_size, avatar_size))
    # mask to circle
    mask = Image.new("L", (avatar_size, avatar_size), 0)
    mask_draw = ImageDraw.Draw(mask)
    mask_draw.ellipse((0, 0, avatar_size, avatar_size), fill=255)
    # glow effect (neon green)
    glow = Image.new("RGBA", (avatar_size + 40, avatar_size + 40), (0, 0, 0, 0))
    glow_draw = ImageDraw.Draw(glow)
    gx, gy = 20, 20
    glow_draw.ellipse((gx, gy, gx + avatar_size, gy + avatar_size), fill=(0, 255, 157, 80))
    glow = glow.filter(ImageFilter.GaussianBlur(10))
    base.paste(glow, (avatar_x - 20, avatar_y - 20), glow)
    base.paste(avatar_img, (avatar_x, avatar_y), mask)

    # Text: Username and Discriminator
    name_x = avatar_x + avatar_size + 30
    name_y = avatar_y + 10
    display_name = member.display_name
    draw.text((name_x, name_y), display_name, font=main_font, fill=(255, 255, 255, 255))
    # small username
    subtext = f"Level {level} • {member.id}"
    draw.text((name_x, name_y + 48), subtext, font=small_font, fill=(180, 180, 180, 255))

    # XP bar
    bar_x = name_x
    bar_y = name_y + 90
    bar_w = width - bar_x - 60
    bar_h = 28

    # background bar
    draw.rounded_rectangle([bar_x, bar_y, bar_x + bar_w, bar_y + bar_h], radius=14, fill=(15, 15, 15, 220))
    # fill
    percent = min(1.0, xp / max(1, required))
    fill_w = int(bar_w * percent)
    if fill_w > 0:
        draw.rounded_rectangle([bar_x, bar_y, bar_x + fill_w, bar_y + bar_h], radius=14, fill=(0, 255, 157, 255))

    # xp text
    xp_text = f"XP: {xp} / {required}"
    tw, th = draw.textsize(xp_text, font=small_font)
    draw.text((bar_x + (bar_w - tw) // 2, bar_y + (bar_h - th) // 2), xp_text, font=small_font, fill=(255,255,255,255))

    # guild watermark (optional small)
    # draw.text((width - 200, height - 30), "White Lily", font=small_font, fill=(40,255,180,60))

    # export
    byte_io = io.BytesIO()
    base.save(byte_io, "PNG")
    byte_io.seek(0)
    return byte_io

class Ranking(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def cog_load(self):
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
            # add ensure embed_color exists for leaderboard
            await db.execute("""
                CREATE TABLE IF NOT EXISTS level_config (
                    guild_id INTEGER PRIMARY KEY,
                    message TEXT,
                    attachment_url TEXT,
                    xp_multiplier REAL DEFAULT 1.0,
                    level_channel_id INTEGER,
                    embed_color INTEGER DEFAULT 0x3498db
                )
            """)
            await db.commit()

    async def fetch_user_stats(self, guild_id: int, user_id: int):
        async with aiosqlite.connect(DB) as db:
            cursor = await db.execute("SELECT xp, level FROM leveling WHERE guild_id=? AND user_id=?", (guild_id, user_id))
            r = await cursor.fetchone()
            if r:
                return r[0], r[1]
            else:
                return 0, 1

    async def get_embed_color(self, guild_id: int):
        async with aiosqlite.connect(DB) as db:
            cursor = await db.execute("SELECT embed_color FROM level_config WHERE guild_id=?", (guild_id,))
            row = await cursor.fetchone()
            return row[0] if row and row[0] is not None else 0x3498db

    @app_commands.command(name="rank", description="Show your or another user's rank card")
    async def rank(self, interaction: discord.Interaction, member: discord.Member = None):
        await interaction.response.defer()
        if member is None:
            member = interaction.user
        xp, level = await self.fetch_user_stats(interaction.guild.id, member.id)
        required = level * 100
        img_bytes = await generate_rank_card(member, xp, level, required)
        file = discord.File(fp=img_bytes, filename="rank.png")
        await interaction.followup.send(file=file)

    @app_commands.command(name="rank-leaderboard", description="Show top users by level in this server")
    async def leaderboard(self, interaction: discord.Interaction, limit: int = 10):
        if limit < 1 or limit > 25:
            return await interaction.response.send_message("Limit must be between 1 and 25.", ephemeral=True)
        await interaction.response.defer()
        async with aiosqlite.connect(DB) as db:
            cursor = await db.execute("""
                SELECT user_id, level, xp FROM leveling
                WHERE guild_id=?
                ORDER BY level DESC, xp DESC
                LIMIT ?
            """, (interaction.guild.id, limit))
            rows = await cursor.fetchall()
        if not rows:
            return await interaction.followup.send("No leveling data yet in this server.")
        desc_lines = []
        pos = 1
        for user_id, level, xp in rows:
            member = interaction.guild.get_member(user_id)
            name = member.display_name if member else f"<@{user_id}>"
            desc_lines.append(f"**{pos}.** {name} — Level {level} ({xp} XP)")
            pos += 1

        # FIXED — leaderboard now uses server-level configured embed color
        color = await self.get_embed_color(interaction.guild.id)

        embed = discord.Embed(
            title=f"Leaderboard — Top {len(rows)}",
            description="\n".join(desc_lines),
            color=color
        )
        await interaction.followup.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Ranking(bot))
