import discord
from discord import app_commands
from discord.ext import commands
from discord.ui import View, Button
import aiosqlite
import math
import time
from utils.gacha_sim import RARITY_POOLS, COOKIE_EMOJIS

# User-provided emojis
LOCKED_EMOJI = "<:sm_lock:1439610863911829627>"
UNLOCKED_EMOJI = "<:sm_unlock:1439610901912354906>"

LEFT_ARROW = "<:arrowleft:1433000307452940309>"
RIGHT_ARROW = "<:arrowright:1433000252306100294>"

# Rarity order rarest -> common
RARITY_ORDER = [
    "Ancient",
    "Beast",
    "Legendary",
    "SuperEpic",
    "Epic",
    "Rare",
    "Common"
]

ITEMS_PER_PAGE = 9  # 3x3 grid


class _CookiesPaginator(View):
    def __init__(self, bot, pages, author_id):
        super().__init__(timeout=180)
        self.bot = bot
        self.pages = pages
        self.author_id = author_id
        self.current = 0

        self.left = Button(style=discord.ButtonStyle.secondary, emoji=LEFT_ARROW)
        self.left.callback = self.on_left
        self.add_item(self.left)

        self.right = Button(style=discord.ButtonStyle.secondary, emoji=RIGHT_ARROW)
        self.right.callback = self.on_right
        self.add_item(self.right)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.author_id:
            await interaction.response.send_message(
                "Only the command invoker may use these buttons.",
                ephemeral=True
            )
            return False
        return True

    async def on_left(self, interaction: discord.Interaction):
        self.current = (self.current - 1) % len(self.pages)
        await interaction.response.edit_message(embed=self.pages[self.current], view=self)

    async def on_right(self, interaction: discord.Interaction):
        self.current = (self.current + 1) % len(self.pages)
        await interaction.response.edit_message(embed=self.pages[self.current], view=self)


class Cookies(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def _build_all_cookie_list(self):
        all_cookies = []
        for rarity in RARITY_ORDER:
            pool = RARITY_POOLS.get(rarity, [])
            for name in sorted(pool, key=lambda s: s.lower()):
                all_cookies.append((rarity, name))
        return all_cookies

    async def _fetch_user_cookies(self, user_id: int):
        user_cookie_map = {}
        async with aiosqlite.connect("python-bot/data/economy.db") as db:
            async with db.execute("""
                SELECT cookie_name, soulstones, stars, ascension_level, unlocked
                FROM cookies WHERE user_id = ?
            """, (user_id,)) as cursor:
                rows = await cursor.fetchall()
                for name, soulstones, stars, asc, unlocked in rows:
                    user_cookie_map[name] = {
                        "soulstones": soulstones,
                        "stars": stars,
                        "ascension": asc,
                        "unlocked": bool(unlocked)
                    }
        return user_cookie_map

    async def _get_recent_score(self, user_id: int, cookie_name: str):
        async with aiosqlite.connect("python-bot/data/economy.db") as db:
            async with db.execute("""
                SELECT MAX(timestamp)
                FROM recent_pulls
                WHERE user_id = ? AND cookie_name = ?
            """, (user_id, cookie_name)) as cursor:
                row = await cursor.fetchone()
                return row[0] or 0

    async def cookie_autocomplete(self, interaction: discord.Interaction, current: str):
        current = current.lower()
        suggestions = []

        for rarity, pool in RARITY_POOLS.items():
            for name in pool:
                if current in name.lower():
                    suggestions.append(name)

        return [
            app_commands.Choice(name=name, value=name)
            for name in suggestions[:25]
        ]

    # FIXED — cookie_name removed (unused & broke sync)
    @commands.hybrid_command(name="cookies", description="View a member's cookie details.")
    @app_commands.autocomplete()
    async def cookies(self, ctx, member: discord.Member = None, mode: str = "all", sort: str = "rarity"):
        member = member or ctx.author
        mode = mode.lower()
        sort = sort.lower()

        valid_modes = ("all", "unlocked", "locked")
        valid_sorts = ("rarity", "alpha", "stars", "soulstones", "recent")

        if mode not in valid_modes:
            return await ctx.send("Mode must be `all`, `unlocked`, or `locked`.")
        if sort not in valid_sorts:
            return await ctx.send("Sort must be: rarity, alpha, stars, soulstones, recent")

        await ctx.defer()

        all_cookies = self._build_all_cookie_list()
        user_map = await self._fetch_user_cookies(member.id)

        entries = []
        for rarity, cname in all_cookies:
            data = user_map.get(cname, {"soulstones": 0, "stars": 0, "ascension": 0, "unlocked": False})
            unlocked = data["unlocked"]

            if mode == "unlocked" and not unlocked:
                continue
            if mode == "locked" and unlocked:
                continue

            recent_ts = 0
            if sort == "recent":
                recent_ts = await self._get_recent_score(member.id, cname)

            entries.append({
                "rarity": rarity,
                "name": cname,
                "emoji": COOKIE_EMOJIS.get(cname, "🍪"),
                "soulstones": data["soulstones"],
                "stars": data["stars"],
                "ascension": data["ascension"],
                "unlocked": unlocked,
                "recent_ts": recent_ts
            })

        if not entries:
            return await ctx.send(f"{member.display_name} has no cookies matching that view.")

        # sorting
        order_index = {r: i for i, r in enumerate(RARITY_ORDER)}
        if sort == "rarity":
            entries.sort(key=lambda e: (order_index[e["rarity"]], e["name"].lower()))
        elif sort == "alpha":
            entries.sort(key=lambda e: e["name"].lower())
        elif sort == "stars":
            entries.sort(key=lambda e: (-e["stars"], e["name"].lower()))
        elif sort == "soulstones":
            entries.sort(key=lambda e: (-e["soulstones"], e["name"].lower()))
        elif sort == "recent":
            entries.sort(key=lambda e: (-e["recent_ts"], e["name"].lower()))

        # pagination
        pages = []
        total_pages = math.ceil(len(entries) / ITEMS_PER_PAGE)

        for p in range(total_pages):
            slice = entries[p * ITEMS_PER_PAGE:(p + 1) * ITEMS_PER_PAGE]

            emojis = [
                f"{item['emoji']}{UNLOCKED_EMOJI if item['unlocked'] else LOCKED_EMOJI}"
                for item in slice
            ]

            while len(emojis) < 9:
                emojis.append("⬜")

            rows = []
            for i in range(3):
                rows.append("  ".join(emojis[i*3:(i+1)*3]))

            grid = "\n".join(rows)

            stats = []
            for i in slice:
                text = f"{i['stars']}⭐"
                if i['ascension'] > 0:
                    text += f" A{i['ascension']}"
                stats.append(
                    f"{i['emoji']} **{i['name']}** — {i['rarity']} | {text} | {i['soulstones']} SS"
                )

            embed = discord.Embed(
                title=f"🍪 {member.display_name}'s Cookies ({mode.title()})",
                description=f"{grid}\n\n" + ("\n".join(stats)),
                color=0x0082e4
            )
            embed.set_footer(text=f"Page {p+1}/{total_pages} • Total: {len(entries)} • Sort: {sort}")
            pages.append(embed)

        view = _CookiesPaginator(self.bot, pages, ctx.author.id)
        await ctx.send(embed=pages[0], view=view)

    # FIXED — proper command name & fixed member reference
    @commands.hybrid_command(name="cookie", description="View a single cookie's details.")
    @app_commands.autocomplete(cookie_name=cookie_autocomplete)
    async def cookie(self, ctx, *, cookie_name: str):
        member = ctx.author

        if not cookie_name:
            return await ctx.send("You must select a cookie name.")

        await ctx.defer()

        # normalize cookie name
        rarity_found = None
        for r, pool in RARITY_POOLS.items():
            for n in pool:
                if n.lower() == cookie_name.lower():
                    cookie_name = n
                    rarity_found = r
                    break
            if rarity_found:
                break

        if not rarity_found:
            return await ctx.send(f"Cookie `{cookie_name}` does not exist.")

        user_id = member.id

        async with aiosqlite.connect("python-bot/data/economy.db") as db:
            async with db.execute("""
                SELECT soulstones, stars, ascension_level, unlocked
                FROM cookies
                WHERE user_id = ? AND cookie_name = ?
            """, (user_id, cookie_name)) as c:
                row = await c.fetchone()

                if row:
                    soulstones, stars, asc, unlocked = row
                    unlocked = bool(unlocked)
                else:
                    soulstones = stars = asc = 0
                    unlocked = False

            async with db.execute("""
                SELECT MAX(timestamp) FROM recent_pulls
                WHERE user_id = ? AND cookie_name = ?
            """, (user_id, cookie_name)) as c2:
                r2 = await c2.fetchone()
                last_ts = r2[0] if r2 and r2[0] else None

        emoji = COOKIE_EMOJIS.get(cookie_name, "🍪")
        asc_text = f"{stars}⭐"
        if asc > 0:
            asc_text += f" A{asc}"

        embed = discord.Embed(
            title=f"{emoji} {cookie_name}",
            description=(
                f"**Rarity:** {rarity_found}\n"
                f"**Status:** {'Unlocked' if unlocked else 'Locked'}\n"
                f"**Soulstones:** {soulstones}\n"
                f"**Stars:** {asc_text}\n"
                f"**Last Pulled:** "
                f"{time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(last_ts)) if last_ts else 'Never'}\n"
            ),
            color=0x00C2A8
        )

        embed.set_footer(text=f"Viewing data for {member.display_name}")
        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(Cookies(bot))
