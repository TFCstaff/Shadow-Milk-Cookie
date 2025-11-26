import discord
from discord.ext import commands
import aiosqlite
import math

CURRENCY = "<:LoD:1411031656055177276>"
BETA_BADGE = "<:Powder_Scale:1434580329829634048> Early Beta Tester"

class Profile(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        bot.loop.create_task(self.setup_db())

    async def setup_db(self):
        """Initialize user levels & badges table."""
        async with aiosqlite.connect("python-bot/data/economy.db") as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS levels (
                    user_id INTEGER PRIMARY KEY,
                    xp INTEGER DEFAULT 0,
                    level INTEGER DEFAULT 1
                )
            """)
            await db.execute("""
                CREATE TABLE IF NOT EXISTS badges (
                    user_id INTEGER,
                    badge TEXT,
                    UNIQUE(user_id, badge)
                )
            """)
            await db.commit()
        print("✅ Profile system initialized.")

    # ───────────────────────────
    # XP + LEVEL SYSTEM
    # ───────────────────────────
    async def add_xp(self, user_id: int, amount: int):
        """Adds XP to a user, levels them up if threshold reached."""
        async with aiosqlite.connect("python-bot/data/economy.db") as db:
            await db.execute("INSERT OR IGNORE INTO levels (user_id, xp, level) VALUES (?, 0, 1)", (user_id,))
            await db.commit()

            async with db.execute("SELECT xp, level FROM levels WHERE user_id = ?", (user_id,)) as cursor:
                row = await cursor.fetchone()
                if not row:
                    xp, level = 0, 1
                else:
                    xp, level = row

            xp += amount

            # XP needed for next level (simple curve)
            xp_needed = 1000 * level
            leveled_up = False

            while xp >= xp_needed and level < 100:
                xp -= xp_needed
                level += 1
                xp_needed = 1000 * level
                leveled_up = True

                # Award 10k LoD per level up
                async with aiosqlite.connect("python-bot/data/economy.db") as db2:
                    await db2.execute(
                        "UPDATE users SET balance = balance + ? WHERE user_id = ?",
                        (10000, user_id)
                    )
                    await db2.commit()

            await db.execute("UPDATE levels SET xp = ?, level = ? WHERE user_id = ?", (xp, level, user_id))
            await db.commit()
        return leveled_up

    async def get_level_data(self, user_id: int):
        async with aiosqlite.connect("python-bot/data/economy.db") as db:
            async with db.execute("SELECT xp, level FROM levels WHERE user_id = ?", (user_id,)) as cursor:
                row = await cursor.fetchone()
                if not row:
                    return 0, 1
                return row[0], row[1]

    async def get_balance(self, user_id: int):
        async with aiosqlite.connect("python-bot/data/economy.db") as db:
            async with db.execute("SELECT balance FROM users WHERE user_id = ?", (user_id,)) as cursor:
                row = await cursor.fetchone()
                return row[0] if row else 0

    async def get_badges(self, user_id: int):
        async with aiosqlite.connect("python-bot/data/economy.db") as db:
            async with db.execute("SELECT badge FROM badges WHERE user_id = ?", (user_id,)) as cursor:
                rows = await cursor.fetchall()
                if not rows:
                    # Give beta tester badge if they’re new
                    await db.execute("INSERT OR IGNORE INTO badges (user_id, badge) VALUES (?, ?)", (user_id, BETA_BADGE))
                    await db.commit()
                    return [BETA_BADGE]
                return [r[0] for r in rows]

    # ───────────────────────────
    # PROFILE COMMAND
    # ───────────────────────────
    @commands.hybrid_command(name="profile", description="View your Shadow Milk profile.")
    async def profile(self, ctx, member: discord.Member = None):
        member = member or ctx.author

        xp, level = await self.get_level_data(member.id)
        balance = await self.get_balance(member.id)
        badges = await self.get_badges(member.id)

        # XP Progress
        xp_needed = 1000 * level
        progress = xp / xp_needed
        filled = int(progress * 15)
        bar = "█" * filled + "░" * (15 - filled)

        embed = discord.Embed(
            title=f"🍶 {member.display_name}'s Shadow Profile",
            color=0x0082e4
        )
        embed.add_field(name="Level", value=f"**{level}** / 100", inline=True)
        embed.add_field(name="XP", value=f"{xp}/{xp_needed}", inline=True)
        embed.add_field(name="Balance", value=f"{CURRENCY} **{balance}**", inline=False)
        embed.add_field(name="Progress", value=f"`{bar}` {progress*100:.1f}%", inline=False)

        embed.add_field(
            name="Badges",
            value=" ".join(badges) if badges else "No badges yet.",
            inline=False
        )

        embed.set_thumbnail(url=member.display_avatar.url)
        embed.set_footer(text="Use economy commands to gain XP and level up!")

        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Profile(bot))
