import discord
from discord.ext import commands
import aiosqlite
import random
from datetime import datetime, timedelta

CURRENCY = "<:LoD:1411031656055177276>"

# Unified cooldowns in seconds
COOLDOWNS = {
    "work": 3600,
    "crime": 15,
    "pay": 15,
    "steal": 300,
    "daily": 86400,
}


async def safe_send(ctx, *args, **kwargs):
    """
    Send a message handling:
      - commands.Context (ctx.send)
      - interactions (interaction.response.send_message / followup)
      - FakeInteraction (has .send or .response.send_message)
      - fallback to channel.send
    Tries reasonable fallbacks to avoid "Unknown interaction" errors.
    """
    # If ctx is a Context from commands (hybrid), ctx.send should work and is preferred.
    try:
        # 1) commands.Context or similar that implements send
        if hasattr(ctx, "send") and not (hasattr(ctx, "interaction") and ctx.interaction is None):
            try:
                return await ctx.send(*args, **kwargs)
            except Exception as e:
                # often this fails due to expired interaction -> try followup if exists
                try:
                    if hasattr(ctx, "interaction") and hasattr(ctx.interaction, "followup"):
                        return await ctx.interaction.followup.send(*args, **kwargs)
                except Exception:
                    pass

        # 2) raw Interaction-like object (has response)
        if hasattr(ctx, "response") and hasattr(ctx, "channel"):
            try:
                # common for fake Interaction with response.send_message
                if hasattr(ctx.response, "send_message"):
                    return await ctx.response.send_message(*args, **kwargs)
            except Exception:
                # fallback: send to channel
                try:
                    return await ctx.channel.send(*args, **kwargs)
                except Exception:
                    pass

        # 3) FakeInteraction with .send
        if hasattr(ctx, "send") and not callable(getattr(ctx, "send")):
            # corner case but attempt to use channel
            pass

        # 4) direct channel send fallback
        if hasattr(ctx, "channel") and hasattr(ctx.channel, "send"):
            return await ctx.channel.send(*args, **kwargs)

    except Exception:
        # final fallback: attempt channel send if possible
        try:
            if hasattr(ctx, "channel") and hasattr(ctx.channel, "send"):
                return await ctx.channel.send(*args, **kwargs)
        except Exception:
            pass

    return None


class Economy(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # start DB init/migration in background
        bot.loop.create_task(self.setup_db())

    # ---------------- DB setup & migration ----------------
    async def setup_db(self):
        """
        Creates tables if missing and migrates missing columns.
        This preserves existing data and adds columns when needed.
        """
        async with aiosqlite.connect("python-bot/data/economy.db") as db:
            # create base tables if they don't exist (safe)
            await db.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    balance INTEGER DEFAULT 0,
                    last_daily TEXT DEFAULT '1970-01-01'
                    -- work_streak may be added by migration below
                )
            """)
            await db.execute("""
                CREATE TABLE IF NOT EXISTS protections (
                    user_id INTEGER PRIMARY KEY,
                    type TEXT,
                    expires_at INTEGER
                )
            """)
            await db.execute("""
                CREATE TABLE IF NOT EXISTS cooldowns (
                    user_id INTEGER,
                    command_name TEXT,
                    last_used INTEGER,
                    PRIMARY KEY(user_id, command_name)
                )
            """)
            await db.commit()

            # migrate users table to ensure columns exist (safe ALTER ADD)
            async with db.execute("PRAGMA table_info(users)") as cur:
                rows = await cur.fetchall()
                cols = [r[1] for r in rows]

            # If work_streak missing -> add it
            if "work_streak" not in cols:
                try:
                    await db.execute("ALTER TABLE users ADD COLUMN work_streak INTEGER DEFAULT 0")
                    await db.commit()
                    print("✅ Migrated DB: added 'work_streak' column to users")
                except Exception as e:
                    print(f"⚠️ Could not add work_streak column: {e}")

            # If last_daily missing for some reason, add it
            if "last_daily" not in cols:
                try:
                    await db.execute("ALTER TABLE users ADD COLUMN last_daily TEXT DEFAULT '1970-01-01'")
                    await db.commit()
                    print("✅ Migrated DB: added 'last_daily' column to users")
                except Exception as e:
                    print(f"⚠️ Could not add last_daily column: {e}")

        print("✅ Economy database initialized / migrated.")

    # ---------------- Helper functions ----------------
    async def get_balance(self, user_id: int):
        async with aiosqlite.connect("python-bot/data/economy.db") as db:
            async with db.execute("SELECT balance FROM users WHERE user_id = ?", (user_id,)) as cursor:
                row = await cursor.fetchone()
                return int(row[0]) if row else 0

    async def add_balance(self, user_id: int, amount: int):
        async with aiosqlite.connect("python-bot/data/economy.db") as db:
            # ensure user exists
            await db.execute("INSERT OR IGNORE INTO users (user_id, balance) VALUES (?, ?)", (user_id, 0))
            await db.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (amount, user_id))
            await db.commit()

    async def set_balance(self, user_id: int, amount: int):
        async with aiosqlite.connect("python-bot/data/economy.db") as db:
            await db.execute("INSERT OR IGNORE INTO users (user_id, balance) VALUES (?, ?)", (user_id, 0))
            await db.execute("UPDATE users SET balance = ? WHERE user_id = ?", (amount, user_id))
            await db.commit()

    # ---------------- Cooldown handling ----------------
    async def check_cooldown(self, user_id: int, command_name: str):
        """
        Returns None if allowed; otherwise returns a human-readable remaining time string.
        Note: this function only updates last_used when the command is allowed (prevents resetting cooldown on failed attempts).
        """
        now = int(datetime.utcnow().timestamp())
        cooldown_time = COOLDOWNS.get(command_name, 0)

        async with aiosqlite.connect("python-bot/data/economy.db") as db:
            async with db.execute("SELECT last_used FROM cooldowns WHERE user_id = ? AND command_name = ?", (user_id, command_name)) as cursor:
                row = await cursor.fetchone()
                if row:
                    last_used = int(row[0])
                    remaining = cooldown_time - (now - last_used)
                    if remaining > 0:
                        minutes, seconds = divmod(remaining, 60)
                        if minutes > 0:
                            return f"{minutes}m {seconds}s"
                        return f"{seconds}s"

            # allowed -> set last_used to now
            await db.execute("INSERT OR REPLACE INTO cooldowns (user_id, command_name, last_used) VALUES (?, ?, ?)", (user_id, command_name, now))
            await db.commit()

        return None

    # ---------------- Commands ----------------

    @commands.hybrid_command(name="balance", description="Check your Light of Deceit balance.")
    async def balance(self, ctx, member: discord.Member = None):
        member = member or ctx.author
        bal = await self.get_balance(member.id)
        bal_display = "∞" if member.id == 970301958835540049 else f"{bal}"
        embed = discord.Embed(
            title=f"{member.display_name}'s Balance",
            description=f"{CURRENCY} **{bal_display} Light of Deceit**",
            color=0x0082e4
        )
        await safe_send(ctx, embed=embed)

    @commands.hybrid_command(name="work", description="Work to earn Light of Deceit.")
    async def work(self, ctx):
        # check cooldown
        remaining = await self.check_cooldown(ctx.author.id, "work")
        if remaining:
            return await safe_send(ctx, f"⏳ **Cooldown!** You can use this command again in **{remaining}**.")

        # ensure user exists and has work_streak column (migration may have added it)
        async with aiosqlite.connect("python-bot/data/economy.db") as db:
            await db.execute("INSERT OR IGNORE INTO users (user_id, balance, work_streak, last_daily) VALUES (?, ?, ?, ?)",
                             (ctx.author.id, 0, 0, "1970-01-01"))
            await db.commit()
            async with db.execute("SELECT work_streak FROM users WHERE user_id = ?", (ctx.author.id,)) as cursor:
                row = await cursor.fetchone()
                streak = int(row[0]) if row and row[0] is not None else 0

        earnings = 300 + random.randint(500, 1200)
        streak += 1
        await self.add_balance(ctx.author.id, earnings)
        async with aiosqlite.connect("python-bot/data/economy.db") as db:
            await db.execute("UPDATE users SET work_streak = ? WHERE user_id = ?", (streak, ctx.author.id))
            await db.commit()

        embed = discord.Embed(
            title="<:SMCparkles:1402273494758199347> Work Complete",
            description=f"Shadow Milk noticed your dedication and gave you a raise! You earned {CURRENCY}**{earnings}**!",
            color=0x00AEEF
        )
        embed.set_footer(text=f"Work streak: {streak}")
        await safe_send(ctx, embed=embed)

        profile_cog = self.bot.get_cog("Profile")
        if profile_cog and hasattr(profile_cog, "add_xp"):
            await profile_cog.add_xp(ctx.author.id, 5)

    # ---------------- Expanded crime with themed outcomes ----------------
    SUCCESS_CRIME_MSGS = [
        "**Shadow Milk** slipped through the sewers and emptied a secret vault — you pocketed {amt}!",
        "You performed Shadow Milk's signature 'sublime swindle' and gained {amt}.",
        "A crooked jester tipped you a sack of coins. +{amt} to your hoard.",
        "You sold a Fake Purity amulet to a noble — profit {amt}.",
        "Pure Vanilla's ledger had a hole big enough for your hand. Stole {amt}.",
        "You charmed a guard with unsettling giggles and walked out richer by {amt}.",
        "A shipment labeled 'tea' was actually treasure. You grabbed {amt}.",
        "You convinced a merchant to 'lend' you his drawer. +{amt}.",
        "An old pact with a trickster paid off — you scored {amt}.",
        "You found a forgotten bribe pouch under the throne. It held {amt}.",
        "The Lamp blinked and spat out coins. You caught {amt}.",
        "A bitter fortune teller mistook you for royalty — tip: {amt}.",
        "You used a shadow-market coupon. The checkout returned {amt} more than expected.",
    ]

    FAIL_CRIME_MSGS = [
        "Pure Vanilla's patrols are relentless — they caught you and fined {amt}.",
        "You tripped over a vase before even reaching Pure Vanilla's vault and got fined {amt} by a maid",
        "You got lost and stumbled into Pure Vanilla's dungeons. What a waste of {amt}.",
        "Your mask fell off at the worst moment. Guards took {amt} as punishment.",
        "You tripped over your own lies and lost {amt} to a thieving rival.",
        "A snitch sold your location; you were lighter by {amt}.",
        "The Lamp of Deceit burned your plans — repair fees: {amt}.",
        "A ritual backfired; you owe a certain cruel baker {amt}.",
        "Your pickpocket partner ran with the bag. You paid a penalty of **{amt}**.",
        "You were cursed by a petty noble — their fine: {amt}.",
        "A loyal guard recognized you. They took {amt} before you could blink.",
        "An ill-fated gamble lost you {amt} to the alley's bookie.",
        "A trapdoor closed on your coinpurse. What a shame — {amt} gone.",
        "Someone snitched to Pure Vanilla — you paid {amt} in hush money.",
        "Your disguise was embroidered with the wrong crest; you paid {amt} in bribes.",
    ]

    @commands.hybrid_command(name="crime", description="Commit a risky crime for possible profit.")
    async def crime(self, ctx):
        remaining = await self.check_cooldown(ctx.author.id, "crime")
        if remaining:
            return await safe_send(ctx, f"⏳ **Cooldown!** You can use this command again in **{remaining}**.")

        # decide success/fail with more variety
        success_chance = 0.5
        if random.random() < success_chance:
            gain = random.randint(1000, 4000)
            await self.add_balance(ctx.author.id, gain)
            template = random.choice(self.SUCCESS_CRIME_MSGS)
            msg = template.format(amt=f"{CURRENCY}**{gain}**")
            color = 0x22BB33
        else:
            # lose some money, limited by balance
            loss = random.randint(300, 700)
            bal = await self.get_balance(ctx.author.id)
            loss = min(loss, bal)
            if loss > 0:
                await self.add_balance(ctx.author.id, -loss)
            template = random.choice(self.FAIL_CRIME_MSGS)
            msg = template.format(amt=f"{CURRENCY}**{loss}**")
            color = 0xBB2222

        embed = discord.Embed(title="<:victory_coin:1435301919940808794> Crime Result", description=msg, color=color)
        await safe_send(ctx, embed=embed)

        profile_cog = self.bot.get_cog("Profile")
        if profile_cog and hasattr(profile_cog, "add_xp"):
            await profile_cog.add_xp(ctx.author.id, 2)

    # ---------------- Daily ----------------
    @commands.hybrid_command(name="daily", description="Claim your daily Light of Deceit reward.")
    async def daily(self, ctx):
        remaining = await self.check_cooldown(ctx.author.id, "daily")
        if remaining:
            return await safe_send(ctx, f"⏳ **Cooldown!** You can use this command again in **{remaining}**.")

        user_id = ctx.author.id
        today = datetime.utcnow().date()
        async with aiosqlite.connect("python-bot/data/economy.db") as db:
            await db.execute("INSERT OR IGNORE INTO users (user_id, balance, last_daily) VALUES (?, ?, ?)",
                             (user_id, 0, "1970-01-01"))
            await db.commit()
            async with db.execute("SELECT last_daily FROM users WHERE user_id = ?", (user_id,)) as cursor:
                row = await cursor.fetchone()
                last_claim = datetime.strptime(row[0], "%Y-%m-%d").date() if row and row[0] else datetime(1970, 1, 1).date()

        if last_claim == today:
            return await safe_send(ctx, "You’ve already claimed your daily reward today!")

        reward = random.randint(200, 400)
        await self.add_balance(user_id, reward)
        async with aiosqlite.connect("python-bot/data/economy.db") as db:
            await db.execute("UPDATE users SET last_daily = ? WHERE user_id = ?", (today.isoformat(), user_id))
            await db.commit()

        await safe_send(ctx, f"You claimed your daily reward of {CURRENCY}**{reward}**! Come back tomorrow!")
        profile_cog = self.bot.get_cog("Profile")
        if profile_cog and hasattr(profile_cog, "add_xp"):
            await profile_cog.add_xp(ctx.author.id, 10)

    # ---------------- Pay ----------------
    @commands.hybrid_command(name="pay", description="Give Light of Deceit to another user.")
    async def pay(self, ctx, member: discord.Member, amount: int):
        remaining = await self.check_cooldown(ctx.author.id, "pay")
        if remaining:
            return await safe_send(ctx, f"⏳ **Cooldown!** You can use this command again in **{remaining}**.")

        if amount <= 0:
            return await safe_send(ctx, "You can’t pay negative amounts!")

        if ctx.author.id == 970301958835540049:
            await self.add_balance(member.id, amount)
            return await safe_send(ctx, f"✨ {ctx.author.display_name} gifted {member.display_name} {CURRENCY}**{amount}**!")

        bal = await self.get_balance(ctx.author.id)
        if bal < amount:
            return await safe_send(ctx, "You don’t have enough Light of Deceit!")

        await self.add_balance(ctx.author.id, -amount)
        await self.add_balance(member.id, amount)
        await safe_send(ctx, f"{ctx.author.display_name} paid {member.display_name} {CURRENCY}**{amount}**!")

    # ---------------- Steal ----------------
    @commands.hybrid_command(name="steal", description="Try to steal Light of Deceit from another player.")
    async def steal(self, ctx, target: discord.Member):
        remaining = await self.check_cooldown(ctx.author.id, "steal")
        if remaining:
            return await safe_send(ctx, f"⏳ **Cooldown!** You can use this command again in **{remaining}**.")

        if target.id == ctx.author.id:
            return await safe_send(ctx, "You can’t steal from yourself!")
        if target.bot:
            return await safe_send(ctx, "You can’t steal from a bot!")

        target_balance = await self.get_balance(target.id)
        if target_balance < 50:
            return await safe_send(ctx, "That user is too poor to steal from!")

        # Lamp protection
        async with aiosqlite.connect("python-bot/data/economy.db") as db:
            async with db.execute(
                "SELECT type FROM protections WHERE user_id = ? AND type = 'lamp' AND expires_at > strftime('%s','now')",
                (target.id,)
            ) as cur:
                protected = await cur.fetchone()

        if protected:
            gif = "https://cdn.discordapp.com/attachments/1286016432538386587/1435287997246472364/M40215-m40215-skill1.gif"
            embed = discord.Embed(title="<:LampOfDeceit:1434966495812653187> The Lamp of Deceit activates!",
                                  description=f"You are fined {CURRENCY}**1000**!",
                                  color=0xFF0000)
            embed.set_image(url=gif)
            await safe_send(ctx, embed=embed)
            await self.add_balance(ctx.author.id, -1000)
            async with aiosqlite.connect("python-bot/data/economy.db") as db:
                await db.execute("DELETE FROM protections WHERE user_id = ?", (target.id,))
                await db.commit()
            return

        if random.random() < 0.5:
            stolen = random.randint(20, min(150, target_balance))
            await self.add_balance(ctx.author.id, stolen)
            await self.add_balance(target.id, -stolen)
            await safe_send(ctx, f"You successfully stole {CURRENCY}**{stolen}** from {target.display_name}!")
        else:
            fine = random.randint(30, 100)
            await self.add_balance(ctx.author.id, -fine)
            await safe_send(ctx, f"You got caught trying to steal from {target.display_name} and lost {CURRENCY}**{fine}**!")

    # ---------------- Leaderboard ----------------
    @commands.hybrid_command(name="leaderboard", description="View the richest users.")
    async def leaderboard(self, ctx):
        async with aiosqlite.connect("python-bot/data/economy.db") as db:
            async with db.execute("SELECT user_id, balance FROM users ORDER BY balance DESC LIMIT 10") as cursor:
                rows = await cursor.fetchall()

        if not rows:
            return await safe_send(ctx, "No data found yet. Go earn some Light of Deceit first!")

        embed = discord.Embed(title="<a:cyanstars:1433000579566665798> Shadow Milk’s Richest Souls", color=0xFFD700)
        for rank, (user_id, balance) in enumerate(rows, start=1):
            try:
                user = await self.bot.fetch_user(user_id)
                name = user.display_name if user else f"User {user_id}"
            except Exception:
                name = f"User {user_id}"
            embed.add_field(name=f"#{rank} — {name}", value=f"{CURRENCY} **{balance}**", inline=False)
        await safe_send(ctx, embed=embed)


async def setup(bot):
    await bot.add_cog(Economy(bot))
