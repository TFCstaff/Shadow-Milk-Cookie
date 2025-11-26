import discord
from discord.ext import commands
import asyncio
import aiosqlite
import time
from utils.gacha_sim import simulate_gacha, RARITY_COLORS, RARITY_POOLS, ASCENSION_COSTS, MAX_STARS

CUTTER_NAME = "<:SMC_cutter:1411067252681211996> Deceitful Cutter"
LOADING_EMOJI = "<a:SMCloading:1433000133179736186>"

class Gacha(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.bot.loop.create_task(self.ensure_tables())

    async def ensure_tables(self):
        """Create tables and run safe migrations (add unlocked column if missing)."""
        async with aiosqlite.connect("python-bot/data/economy.db") as db:
            # Create base tables if they don't exist
            await db.execute("""
                CREATE TABLE IF NOT EXISTS cookies (
                    user_id INTEGER,
                    cookie_name TEXT,
                    soulstones INTEGER DEFAULT 0,
                    stars INTEGER DEFAULT 0,
                    ascension_level INTEGER DEFAULT 0,
                    UNIQUE(user_id, cookie_name)
                )
            """)
            await db.execute("""
                CREATE TABLE IF NOT EXISTS inventory (
                    user_id INTEGER,
                    item_name TEXT,
                    quantity INTEGER DEFAULT 1,
                    UNIQUE(user_id, item_name)
                )
            """)
            await db.execute("""
                CREATE TABLE IF NOT EXISTS recent_pulls (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    cookie_name TEXT,
                    rarity TEXT,
                    soulstones INTEGER,
                    timestamp INTEGER
                )
            """)
            await db.commit()

            # Migration: add unlocked column if missing
            async with db.execute("PRAGMA table_info(cookies)") as cur:
                cols = await cur.fetchall()
                col_names = [c[1] for c in cols]
                if "unlocked" not in col_names:
                    await db.execute("ALTER TABLE cookies ADD COLUMN unlocked INTEGER DEFAULT 0")
                    await db.commit()

    # --------- DB Helpers ----------
    async def get_item(self, user_id: int, item_name: str):
        async with aiosqlite.connect("python-bot/data/economy.db") as db:
            async with db.execute(
                "SELECT quantity FROM inventory WHERE user_id = ? AND item_name = ?",
                (user_id, item_name),
            ) as cursor:
                row = await cursor.fetchone()
                return row[0] if row else 0

    async def remove_item(self, user_id: int, item_name: str, qty: int = 1):
        async with aiosqlite.connect("python-bot/data/economy.db") as db:
            await db.execute("""
                UPDATE inventory
                SET quantity = quantity - ?
                WHERE user_id = ? AND item_name = ?
            """, (qty, user_id, item_name))
            await db.execute("DELETE FROM inventory WHERE quantity <= 0")
            await db.commit()

    async def add_soulstones(self, user_id: int, cookie_name: str, amount: int):
        """
        Adds soulstones for a user cookie. Ensures row exists. If cookie is locked and
        total soulstones >= 20 -> unlock and subtract 20 leaving remainder.
        """
        async with aiosqlite.connect("python-bot/data/economy.db") as db:
            # ensure row exists
            await db.execute("""
                INSERT INTO cookies (user_id, cookie_name, soulstones, stars, ascension_level, unlocked)
                VALUES (?, ?, 0, 0, 0, 0)
                ON CONFLICT(user_id, cookie_name) DO NOTHING
            """, (user_id, cookie_name))

            # add soulstones
            await db.execute("""
                UPDATE cookies
                SET soulstones = soulstones + ?
                WHERE user_id = ? AND cookie_name = ?
            """, (amount, user_id, cookie_name))

            # check total and unlock if needed
            async with db.execute("""
                SELECT soulstones, unlocked FROM cookies WHERE user_id = ? AND cookie_name = ?
            """, (user_id, cookie_name)) as cursor:
                row = await cursor.fetchone()
                total = row[0] if row else 0
                unlocked = row[1] if row else 0

            if not unlocked and total >= 20:
                remaining = total - 20
                await db.execute("""
                    UPDATE cookies
                    SET soulstones = ?, unlocked = 1
                    WHERE user_id = ? AND cookie_name = ?
                """, (remaining, user_id, cookie_name))

            await db.commit()

    async def update_cookie(self, user_id: int, cookie_name: str, stars=None, ascension=None, soulstones=None, unlocked=None):
        async with aiosqlite.connect("python-bot/data/economy.db") as db:
            updates, params = [], []
            if stars is not None:
                updates.append("stars = ?")
                params.append(stars)
            if ascension is not None:
                updates.append("ascension_level = ?")
                params.append(ascension)
            if soulstones is not None:
                updates.append("soulstones = ?")
                params.append(soulstones)
            if unlocked is not None:
                updates.append("unlocked = ?")
                params.append(1 if unlocked else 0)
            if not updates:
                return
            params.extend([user_id, cookie_name])
            await db.execute(f"""
                UPDATE cookies SET {', '.join(updates)}
                WHERE user_id = ? AND cookie_name = ?
            """, tuple(params))
            await db.commit()

    async def get_cookie(self, user_id: int, cookie_name: str):
        async with aiosqlite.connect("python-bot/data/economy.db") as db:
            async with db.execute("""
                SELECT soulstones, stars, ascension_level, unlocked
                FROM cookies WHERE user_id = ? AND cookie_name = ?
            """, (user_id, cookie_name)) as cursor:
                row = await cursor.fetchone()
                if row:
                    return {"soulstones": row[0], "stars": row[1], "ascension": row[2], "unlocked": bool(row[3])}
                return {"soulstones": 0, "stars": 0, "ascension": 0, "unlocked": False}

    # --------- Gacha Command ----------
    @commands.hybrid_command(name="gacha", description="Pull cookies using your Deceitful Cutters!")
    async def gacha(self, ctx, draws: int = 1):
        await ctx.defer()

        if draws not in [1, 10]:
            return await ctx.send("You can only draw **1** or **10** times!")

        user_id = ctx.author.id
        cutters = await self.get_item(user_id, CUTTER_NAME)
        if cutters < draws:
            return await ctx.send(f"❌ You don’t have enough {CUTTER_NAME}! You need {draws}.")

        # Remove cutters first
        await self.remove_item(user_id, CUTTER_NAME, draws)

        # Send loading animation
        loading_msg = await ctx.send(f"{LOADING_EMOJI} Drawing cookies... Please wait!")

        try:
            # Simulate suspense delay
            await asyncio.sleep(2.5)

            # Perform gacha draws
            pulls = simulate_gacha(draws)
            desc_lines = []
            rarity_counts = {}

            for result in pulls:
                rarity_counts[result["rarity"]] = rarity_counts.get(result["rarity"], 0) + 1
                # add soulstones (may unlock)
                await self.add_soulstones(user_id, result["cookie"], result["soulstones"])
                # record recent pull
                async with aiosqlite.connect("python-bot/data/economy.db") as db:
                    await db.execute("""
                        INSERT INTO recent_pulls (user_id, cookie_name, rarity, soulstones, timestamp)
                        VALUES (?, ?, ?, ?, ?)
                    """, (user_id, result["cookie"], result["rarity"], result["soulstones"], int(time.time())))
                    await db.commit()

                desc_lines.append(
                    f"{result['emoji']} **{result['cookie']}** — *{result['rarity']}* (+{result['soulstones']} Soulstones)"
                )

            desc = "\n".join(desc_lines) or "No results?"
            if not rarity_counts:
                rarity_counts = {"Common": 1}
            dominant_rarity = max(rarity_counts, key=rarity_counts.get)

            embed = discord.Embed(
                title=f"🍪 {'10x Cookie Draw!' if draws == 10 else 'Cookie Draw!'}",
                description=desc,
                color=RARITY_COLORS.get(dominant_rarity, 0xFFFFFF),
            )
            embed.set_footer(text=f"Used {draws} Deceitful Cutters!")
            # Edit the loading message into the final embed
            await loading_msg.edit(content=None, embed=embed)

        except Exception as e:
            await loading_msg.edit(content=f"❌ An error occurred: `{e}`")
            raise  # Optional: keeps traceback visible in console

    # --------- Ascend Command ----------
    @commands.hybrid_command(name="ascend", description="Ascend a cookie using soulstones!")
    async def ascend(self, ctx, *, cookie_name: str):
        await ctx.defer()

        user_id = ctx.author.id
        cookie_name = cookie_name.title()
        cookie_data = await self.get_cookie(user_id, cookie_name)
        if not cookie_data:
            return await ctx.send(f"❌ You do not own **{cookie_name}**.")

        stars = cookie_data["stars"]
        asc = cookie_data["ascension"]
        soulstones = cookie_data["soulstones"]

        cookie_type = "Beast" if cookie_name in RARITY_POOLS.get("Beast", []) else "Default"
        max_level = MAX_STARS.get(cookie_type, "A5")

        if stars < 5:
            next_cost = ASCENSION_COSTS.get(stars + 1)
        else:
            key_map = ["A1", "A2", "A3", "A4", "A5"]
            next_cost = ASCENSION_COSTS.get(key_map[asc]) if asc < 5 else None

        if next_cost is None:
            return await ctx.send(f"✅ **{cookie_name}** has reached max ascension!")

        if soulstones < next_cost:
            return await ctx.send(f"❌ You need {next_cost} soulstones to ascend **{cookie_name}**. You currently have {soulstones}.")

        soulstones -= next_cost
        if stars < 5:
            stars += 1
        else:
            asc += 1

        await self.update_cookie(user_id, cookie_name, stars=stars, ascension=asc, soulstones=soulstones)
        await ctx.send(
            f"✨ **{cookie_name}** has been ascended!\nNow: {stars}⭐ A{asc if asc > 0 else 0}\nRemaining Soulstones: {soulstones}"
        )


async def setup(bot):
    await bot.add_cog(Gacha(bot))
