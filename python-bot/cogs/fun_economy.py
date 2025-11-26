import discord
from discord.ext import commands
import random
import aiosqlite
from datetime import datetime

CURRENCY = "<:LoD:1411031656055177276>"

# Unified cooldowns in seconds
COOLDOWNS = {
    "beg": 20,
    "search": 25,
}

class FunEconomy(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        bot.loop.create_task(self.setup_db())

    async def setup_db(self):
        async with aiosqlite.connect("python-bot/data/economy.db") as db:
            # Ensure users table exists
            await db.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    balance INTEGER DEFAULT 0
                )
            """)
            # Cooldowns table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS cooldowns (
                    user_id INTEGER,
                    command_name TEXT,
                    last_used INTEGER,
                    PRIMARY KEY(user_id, command_name)
                )
            """)
            # Inventory table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS inventory (
                    user_id INTEGER,
                    item_name TEXT,
                    quantity INTEGER DEFAULT 1,
                    UNIQUE(user_id, item_name)
                )
            """)
            await db.commit()
        print("✅ FunEconomy database initialized.")

    # --------- Helper functions ---------
    async def add_balance(self, user_id: int, amount: int):
        async with aiosqlite.connect("python-bot/data/economy.db") as db:
            await db.execute("INSERT OR IGNORE INTO users (user_id, balance) VALUES (?, 0)", (user_id,))
            await db.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (amount, user_id))
            await db.commit()

    async def add_item(self, user_id: int, item_name: str):
        async with aiosqlite.connect("python-bot/data/economy.db") as db:
            await db.execute("""
                INSERT INTO inventory (user_id, item_name, quantity)
                VALUES (?, ?, 1)
                ON CONFLICT(user_id, item_name)
                DO UPDATE SET quantity = quantity + 1
            """, (user_id, item_name))
            await db.commit()

    # --------- Cooldown checker ---------
    async def check_cooldown(self, user_id: int, command_name: str):
        now = int(datetime.utcnow().timestamp())
        cooldown_time = COOLDOWNS.get(command_name, 0)
        async with aiosqlite.connect("python-bot/data/economy.db") as db:
            async with db.execute("SELECT last_used FROM cooldowns WHERE user_id = ? AND command_name = ?", (user_id, command_name)) as cursor:
                row = await cursor.fetchone()
                if row:
                    last_used = row[0]
                    remaining = cooldown_time - (now - last_used)
                    if remaining > 0:
                        return remaining
            # Update last used time (this enforces cooldown immediately on command invocation)
            await db.execute("INSERT OR REPLACE INTO cooldowns (user_id, command_name, last_used) VALUES (?, ?, ?)", (user_id, command_name, now))
            await db.commit()
        return 0

    # --------- Commands ---------
    @commands.hybrid_command(name="beg", description="Beg for Light of Deceit… maybe Shadow Milk will show mercy.")
    async def beg(self, ctx):
        remaining = await self.check_cooldown(ctx.author.id, "beg")
        if remaining:
            return await ctx.send(f"⏳ **Cooldown!** You can use this command again in **{remaining:.0f} seconds**.")

        author = ctx.author
        success = random.random() < 0.55
        reward = random.randint(30, 120)
        responses_success = [
            "Shadow Milk rolls his eyes and throws you a few {c} crumbs.",
            "‘Tch… fine,’ he mutters, tossing some {c} your way.",
            "He sighs deeply as he gives you {c} — ‘Don’t tell anyone I did this.’",
            "‘I’m not a charity, cookie… but take {c} before I change my mind.’",
            "‘How pitiful,’ he says, handing you {c}.",
            "‘Don’t make a habit of this,’ Shadow Milk warns, giving you {c}.",
            "‘You again? Ugh… here.’ {c}",
            "‘You actually showed some persistence. Impressive.’ {c}",
            "‘Fine. You win. Take this {c} before I regret it.’",
            "‘Get out of my sight before I double it.’ {c}"
        ]
        responses_fail = [
            "‘You’re begging? How disappointing.’",
            "He looks down at you and simply walks away.",
            "‘Not today, cookie.’",
            "‘You think whining works on me?’",
            "‘I should fine you for wasting my time.’",
            "‘You got guts asking me that. Still no.’",
            "‘You look broke. I’d help… if I cared.’",
            "‘Keep begging. Maybe someone else will care.’",
            "‘I admire the audacity. The result’s still nothing.’",
            "‘No.’ (He didn’t even look at you.)"
        ]

        if success:
            msg = random.choice(responses_success).format(c=f"**{reward}** {CURRENCY}")
            await self.add_balance(author.id, reward)

            # Small chance of random item drop
            if random.random() < 0.1:
                item = "<:PV_coin:1351245204203634799> Old Coin"
                await self.add_item(author.id, item)
                msg += f"\nYou also managed to get an **{item}** while begging Shadow Milk!"
            color = 0x00AEEF
        else:
            msg = random.choice(responses_fail)
            color = 0xFF5555

        embed = discord.Embed(title="Let's see if your begging went anywhere. . .", description=msg, color=color)
        await ctx.send(embed=embed)
        
        profile_cog = self.bot.get_cog("Profile")
        if profile_cog:
            await profile_cog.add_xp(ctx.author.id, 2)


    @commands.hybrid_command(name="search", description="Search around for Light of Deceit.")
    async def search(self, ctx):
        # enforce cooldown immediately and update DB timestamp so buttons don't re-trigger cooldown
        remaining = await self.check_cooldown(ctx.author.id, "search")
        if remaining:
            return await ctx.send(f"⏳ **Cooldown!** You can use this command again in **{remaining:.0f} seconds**.")

        author = ctx.author
        locations = [
            "Vanilla Kingdom’s ruins", "Dark Cacao’s fortress", "The Spire of deceit", "Abandoned Mine",
            "Milk Arena", "Library of knowledge", "Forgotten Forest", "Cursed Village",
            "Ruined Silent Hall", "Shattered Apathy Bridge", "Fortress of The Almighty", "The Silver Tree",
            "Timeless Kingdom", "The Garden of Delights", "Golden Cheese's Tomb", "Secret Guest Passage",
            "Land of Silence", "The Faerie Palace Hall", "Grand Coral Reef", "Iridescent Gem Shoreline",
            "Confectionery Empire", "Lake of Truth", "Coconut Forest", "GreenSalad Jungle",
            "Truthless Recluse's Bedroom", "Shadow Milk's Closet", "Giant Chess Board", "Milkway Lake",
            "Space Train", "City of Wizards", "Yoghurt River", "Destroyed Golden Kingdom", "The Forgotten Academy"
        ]

        # pick 3 unique random locations for the buttons
        choices = random.sample(locations, k=3)

        # Build embed prompting user to choose a location
        prompt_embed = discord.Embed(
            title="🔍 Where will you search?",
            description="Choose one of the locations below to search. You have 25 seconds.",
            color=0x00AEEF
        )
        prompt_embed.set_footer(text="Only the command user can click these buttons. Buttons expire after 25 seconds.")

        # Create a view with 3 buttons
        view = discord.ui.View(timeout=25)

        # store a flag to ensure only the first click from the user is processed
        # We attach author id to the view for checks
        view.author_id = author.id

        # Helper to create a button callback for a given place
        def make_callback(place: str):
            async def callback(interaction: discord.Interaction):
                # Only the original command user may click
                if interaction.user.id != view.author_id:
                    return await interaction.response.send_message("This isn't your search session.", ephemeral=True)

                # Run the exact same search logic (success/fail/drop)
                success = random.random() < 0.55
                reward = random.randint(40, 200)

                success_msgs = [
                    f"You searched {place} and found {CURRENCY}**{reward}**!",
                    f"In {place}, you stumbled upon a hidden pouch of {CURRENCY}**{reward}**.",
                    f"You dug through {place} and discovered {CURRENCY}**{reward}**.",
                    f"Looks like luck was on your side at {place}! You earned {CURRENCY}**{reward}**.",
                    f"{place} held some forgotten {CURRENCY} — you pocketed {CURRENCY}**{reward}**."
                ]
                fail_msgs = [
                    f"You searched {place} but found nothing but dust.",
                    f"You nearly fell through a crack in {place} — no {CURRENCY} this time.",
                    f"{place} was empty… and kind of creepy.",
                    f"You got lost in {place} and came back empty-handed.",
                    f"You searched for hours in {place}… nothing."
                ]

                if success:
                    msg = random.choice(success_msgs)
                    # add the balance and maybe drop item
                    await self.add_balance(interaction.user.id, reward)

                    # Chance of random item
                    if random.random() < 0.01:
                        item = random.choice([
                            "<:Lost_Portrait:1434580123063029860> Mysterious Portrait",
                            "<:Gem:1434993304654581842> Wind Gem"
                        ])
                        await self.add_item(interaction.user.id, item)
                        msg += f"\nYou lucky little cookie. . . you also found a **{item}**!"
                    color = 0x00AEEF
                else:
                    msg = random.choice(fail_msgs)
                    color = 0xFF5555

                # Build result embed
                result_embed = discord.Embed(title="Let's see what you've searched. . .", description=msg, color=color)

                # Edit the original message to show the result and remove buttons
                try:
                    await interaction.response.edit_message(embed=result_embed, view=None)
                except Exception:
                    # fallback to sending a new message (shouldn't happen often)
                    await interaction.response.send_message(embed=result_embed)

                # stop the view so on_timeout won't try to edit again
                view.stop()
            return callback
        profile_cog = self.bot.get_cog("Profile")
        if profile_cog:
            await profile_cog.add_xp(ctx.author.id, 2)  

        # Add buttons to the view (label uses the location name)
        for place in choices:
            # Truncate label if too long (Discord button labels max 80 chars; our locations are short)
            label = place if len(place) <= 80 else place[:77] + "..."
            btn = discord.ui.Button(label=label, style=discord.ButtonStyle.primary)
            btn.callback = make_callback(place)
            view.add_item(btn)

        # on_timeout: disable buttons (edit message to remove view)
        async def on_timeout_callback():
            try:
                # If message exists and still has view, remove it
                if hasattr(view, "message") and view.message:
                    try:
                        await view.message.edit(content="⏳ Time's up — the search session expired.", embed=None, view=None)
                    except Exception:
                        pass
            finally:
                return

        # attach on_timeout to the view
        async def _on_timeout():
            await on_timeout_callback()
        view.on_timeout = _on_timeout  # assign custom timeout handler

        # send the prompt message and attach the view
        sent = await ctx.send(embed=prompt_embed, view=view)
        # keep a reference to the message on the view so on_timeout can edit it
        view.message = sent

    # If you want more commands copied from the other file, add them here.

async def setup(bot):
    await bot.add_cog(FunEconomy(bot))
