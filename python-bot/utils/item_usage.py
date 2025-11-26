import discord
import random
import asyncio
import aiosqlite

# --- This file handles what happens when an item is USED ---

CURRENCY = "<:LoD:1411031656055177276>"

# Helper to make sure inventory exists
async def remove_item(user_id: int, item_name: str, qty: int = 1):
    async with aiosqlite.connect("python-bot/data/economy.db") as db:
        await db.execute("""
            UPDATE inventory
            SET quantity = quantity - ?
            WHERE user_id = ? AND item_name = ?
        """, (qty, user_id, item_name))
        await db.execute("DELETE FROM inventory WHERE quantity <= 0")
        await db.commit()


# ---------------- Lamp of Deceit ----------------
async def use_lamp_of_deceit(bot, interaction: discord.Interaction):
    """Protects the user from one /steal attempt."""
    user_id = interaction.user.id
    await remove_item(user_id, "<:LampOfDeceit:1434966495812653187> Lamp of Deceit")

    async with aiosqlite.connect("python-bot/data/economy.db") as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS protections (
                user_id INTEGER PRIMARY KEY,
                type TEXT,
                expires_at REAL
            )
        """)
        await db.execute("""
            INSERT OR REPLACE INTO protections (user_id, type, expires_at)
            VALUES (?, ?, strftime('%s','now') + 9999999999999)
        """, (user_id, "lamp"))
        await db.commit()

    gif = "https://cdn.discordapp.com/attachments/1286016432538386587/1435295873864175616/M40215-m40215-battle_idle.gif?ex=690b72f2&is=690a2172&hm=ecd835e7bad537cec4182f8535a325da2c4e09cc966d6a177c5fff9594875802&"
    embed = discord.Embed(
        title="🔮 Lamp of Deceit Activated",
        description="You feel a strange warmth… The Lamp’s animatronic awaits in the shadows to protect your Light of Deceit.",
        color=0x8A2BE2
    )
    embed.set_image(url=gif)
    await interaction.response.send_message(embed=embed)


# ---------------- Anon Letter ----------------
async def use_anon_letter(bot, interaction: discord.Interaction):
    """Lets user send an anonymous message to another server member."""
    user = interaction.user
    await remove_item(user.id, "<:Letter:1434580183595356250> Anon Letter")

    # Ask for recipient through modal
    class RecipientModal(discord.ui.Modal, title="📨 Anonymous Letter - Step 1"):
        recipient_input = discord.ui.TextInput(
            label="Who do you want to send your anonymous letter to?",
            placeholder="Mention them or enter their user ID",
            required=True,
            max_length=64
        )

        async def on_submit(self, interaction2: discord.Interaction):
            content = str(self.recipient_input.value).strip()

            # Try to extract recipient
            target = None
            if len(interaction2.message.mentions) > 0:
                target = interaction2.message.mentions[0]
            elif content.isdigit():
                target = interaction.guild.get_member(int(content))
            elif content.startswith("<@") and content.endswith(">"):
                try:
                    uid = int(content.strip("<@!>"))
                    target = interaction.guild.get_member(uid)
                except Exception:
                    pass
            else:
                target = discord.utils.get(interaction.guild.members, name=content)

            if not target:
                return await interaction2.response.send_message(
                    "<:SMCx:1432661563470254172> I couldn’t find that user. Try again later.",
                    ephemeral=True
                )

            safe_name = target.display_name
            if len(safe_name) > 20:
                safe_name = safe_name[:20] + "…"  # truncate to avoid long titles
                
            # Message input modal
            class MessageModal(discord.ui.Modal, title=f"💌 Anonymous Letter to {safe_name}"):
                message_input = discord.ui.TextInput(
                    label="Write your anonymous message below:",
                    style=discord.TextStyle.paragraph,
                    placeholder="Type your message here...",
                    required=True,
                    max_length=2000
                )

                async def on_submit(self, interaction3: discord.Interaction):
                    content = str(self.message_input.value)
                    try:
                        embed = discord.Embed(
                            title="<:SMCLetter:1434966250014117989> Anonymous Message",
                            description=content,
                            color=0xFFC0CB
                        )
                        await target.send(embed=embed)
                        await interaction3.response.send_message(
                            f"<a:SMCcheck:1367520031914590269> Your anonymous letter was delivered to **{target.display_name}**!",
                            ephemeral=True
                        )
                    except discord.Forbidden:
                        await interaction3.response.send_message(
                            "<:SMCx:1432661563470254172> I couldn’t DM that user. They may have DMs disabled.",
                            ephemeral=True
                        )

            await interaction2.response.send_modal(MessageModal())

    await interaction.response.send_modal(RecipientModal())


# ---------------- Wizard Wand ----------------
async def use_wizard_wand(bot, interaction: discord.Interaction):
    """Applies a random temporary buff to the user."""
    user_id = interaction.user.id
    await remove_item(user_id, "<:Wizard_Wand:1434966466809171988> Wizard Wand")

    boosts = [
        ("lod_multiplier", 1.5, 600, "✨ Your Light of Deceit rewards are increased by **1.5x** for 10 minutes!"),
        ("search_luck", 0.25, 600, "🔍 You feel luckier when searching — item drop chance increased!"),
        ("beg_success", 0.2, 600, "🪙 Begging feels easier — success chance slightly higher!"),
    ]
    chosen = random.choice(boosts)
    boost_type, value, duration, desc = chosen

    async with aiosqlite.connect("python-bot/data/economy.db") as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS active_buffs (
                user_id INTEGER,
                type TEXT,
                value REAL,
                expires_at REAL,
                UNIQUE(user_id, type)
            )
        """)
        await db.execute("""
            INSERT OR REPLACE INTO active_buffs (user_id, type, value, expires_at)
            VALUES (?, ?, ?, strftime('%s','now') + ?)
        """, (user_id, boost_type, value, duration))
        await db.commit()

    embed = discord.Embed(
        title="🪄 Wizard Wand Used",
        description=desc,
        color=0x6A0DAD
    )
    await interaction.response.send_message(embed=embed)


# ---------------- Orchid Locket ----------------
async def use_orchid_locket(bot, interaction: discord.Interaction):
    """Increases Blackjack win chance temporarily."""
    user_id = interaction.user.id
    await remove_item(user_id, "<:Orchid_Locket:1434580197092491488> Orchid Locket")

    async with aiosqlite.connect("python-bot/data/economy.db") as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS active_buffs (
                user_id INTEGER,
                type TEXT,
                value REAL,
                expires_at REAL,
                UNIQUE(user_id, type)
            )
        """)
        await db.execute("""
            INSERT OR REPLACE INTO active_buffs (user_id, type, value, expires_at)
            VALUES (?, ?, ?, strftime('%s','now') + ?)
        """, (user_id, "blackjack_luck", 0.3, 1800))
        await db.commit()

    embed = discord.Embed(
        title="💠 Orchid Locket Activated",
        description="You feel serene... Your odds in Blackjack are increased for 30 minutes.",
        color=0x00BFFF
    )
    await interaction.response.send_message(embed=embed)

# ---------------- Forbidden Chronicle ----------------
async def use_forbidden_chronicle(bot, interaction: discord.Interaction):
    """Displays confessions from confessions.db in a paginated book view."""
    user_id = interaction.user.id

    async with aiosqlite.connect("python-bot/data/confessions.db") as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS confessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                confession TEXT,
                timestamp TEXT
            )
        """)
        async with db.execute("SELECT user_id, confession, timestamp FROM confessions ORDER BY id DESC") as cursor:
            confessions = await cursor.fetchall()

    if not confessions:
        return await interaction.response.send_message(
            "📖 The Forbidden Chronicle is empty... no confessions lie within.",
            ephemeral=True
        )

    pages = []
    for i, (uid, text, timestamp) in enumerate(confessions, start=1):
        embed = discord.Embed(
            title=f"📜 Forbidden Chronicle — Page {i}/{len(confessions)}",
            description=f"**Confession:** {text}",
            color=0x8B0000
        )
        embed.set_footer(text=f"Confessed anonymously • Date: {timestamp}")
        pages.append(embed)

    class ConfessionBook(discord.ui.View):
        def __init__(self):
            super().__init__(timeout=120)
            self.index = 0

        @discord.ui.button(emoji="<:arrowleft:1433000307452940309>", style=discord.ButtonStyle.secondary)
        async def left(self, interaction2: discord.Interaction, button: discord.ui.Button):
            if interaction2.user.id != user_id:
                return await interaction2.response.send_message("You can’t flip this book.", ephemeral=True)
            self.index = (self.index - 1) % len(pages)
            await interaction2.response.edit_message(embed=pages[self.index], view=self)

        @discord.ui.button(emoji="<:arrowright:1433000252306100294>", style=discord.ButtonStyle.secondary)
        async def right(self, interaction2: discord.Interaction, button: discord.ui.Button):
            if interaction2.user.id != user_id:
                return await interaction2.response.send_message("You can’t flip this book.", ephemeral=True)
            self.index = (self.index + 1) % len(pages)
            await interaction2.response.edit_message(embed=pages[self.index], view=self)

    view = ConfessionBook()
    await interaction.response.send_message(embed=pages[0], view=view)



# --- Item to function mapping ---
ITEM_EFFECTS = {
    "<:LampOfDeceit:1434966495812653187> Lamp of Deceit": use_lamp_of_deceit,
    "<:Letter:1434580183595356250> Anon Letter": use_anon_letter,
    "<:Wizard_Wand:1434966466809171988> Wizard Wand": use_wizard_wand,
    "<:Orchid_Locket:1434580197092491488> Orchid Locket": use_orchid_locket,
    "<:Forbidden_Book:1434966390561050747> Forbidden Chronicle": use_forbidden_chronicle,

}
