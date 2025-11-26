import discord
from discord.ext import commands
from discord import app_commands
import json
import os
import random
import math
import re

DATA_FILE = "python-bot/data/counting_data.json"

# ========== SAVE / LOAD SYSTEM ==========
def load_data():
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

# ========== SAFE EVALUATION WITH FACTORIAL + ^ SUPPORT ==========
def safe_eval(expr: str):
    try:
        expr = expr.strip()

        # Extract number/math expression from the *start* of the message
        match = re.match(r"^[0-9+\-*/().!^ ]+", expr)
        if not match:
            return None
        expr = match.group(0)

        # Replace ^ with **
        expr = expr.replace("^", "**")

        # Whitelist allowed characters
        allowed = set("0123456789+-*/().!^ ")
        if not set(expr).issubset(allowed):
            return None

        # Factorial replacement
        def factorial_replace(match):
            inner = match.group(1)
            return f"math.factorial({inner})"

        expr = re.sub(r"(\d+|\([^()]+\))!", factorial_replace, expr)

        result = eval(expr, {"__builtins__": None}, {"math": math})
        if isinstance(result, (int, float)):
            return result
    except Exception:
        return None
    return None

# ========== COUNTING COG ==========
class Counting(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.data = load_data()

    async def cog_unload(self):
        save_data(self.data)

    @app_commands.command(name="counting_setup", description="Set a counting channel (mods only).")
    @app_commands.checks.has_permissions(manage_channels=True)
    async def counting_setup(self, interaction: discord.Interaction, channel: discord.TextChannel):
        guild_id = str(interaction.guild_id)
        if guild_id not in self.data:
            self.data[guild_id] = {"channel_id": None, "count": 0, "last_user": None, "warned_users": []}

        self.data[guild_id]["channel_id"] = channel.id
        self.data[guild_id]["count"] = 0
        self.data[guild_id]["last_user"] = None
        self.data[guild_id]["warned_users"] = []
        save_data(self.data)

        await interaction.response.send_message(
            f"Counting channel set to {channel.mention}! Shadow Milk shall now oversee your mathematical chaos.",
            ephemeral=True
        )

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or not message.guild:
            return

        guild_id = str(message.guild.id)
        if guild_id not in self.data or not self.data[guild_id]["channel_id"]:
            return

        channel_id = self.data[guild_id]["channel_id"]
        if message.channel.id != channel_id:
            return

        content = message.content.strip()
        num = safe_eval(content)
        if num is None:
            return

        if isinstance(num, float):
            num = round(num, 6)

        current = self.data[guild_id]["count"]
        expected = current + 1
        last_user = self.data[guild_id]["last_user"]

        # No double counting
        if message.author.id == last_user:
            await message.add_reaction("<:SMCx:1432661563470254172>")
            await message.channel.send(
                f"Kehehehe! {message.author.mention}, trying to count twice in a row? Naughty cookie! The chaos resets!",
                delete_after=8,
            )
            self.data[guild_id]["count"] = 0
            self.data[guild_id]["last_user"] = None
            save_data(self.data)
            return

        # ---------- CORRECT COUNT ----------
        if num == expected:
            self.data[guild_id]["count"] = expected
            self.data[guild_id]["last_user"] = message.author.id
            save_data(self.data)
            try:
                await message.add_reaction("<:SMCheck:1434999970733363250>")

                # SPECIAL EMOJIS 67, 69, 100
                if expected == 67:
                    for emoji in ["<:SMCsix:1436019629175865514>", "<:SMCseven:1436019674675679473>", "<:SMC_freaky:1435957230943080458>"]:
                        try: await message.add_reaction(emoji)
                        except: pass

                if expected == 69:
                    for emoji in ["<:SMCsix:1436019629175865514>", "<:SMCnine:1436020874888347798>", "<:SMC_Unhinged:1346501979861418084>"]:
                        try: await message.add_reaction(emoji)
                        except: pass

                if expected == 100:
                    for emoji in ["<:SMCone:1435963007942266971>", "<:SMCzero:1435963022651687034>", "<:zerooo:1435963228181237770>", "<:SMCparkles:1402273494758199347>"]:
                        try: await message.add_reaction(emoji)
                        except: pass

            except discord.HTTPException:
                pass
            return

        # ---------- INCORRECT COUNT ----------
        warned_users = self.data[guild_id].get("warned_users", [])
        if message.author.id not in warned_users:
            self.data[guild_id]["warned_users"].append(message.author.id)
            save_data(self.data)
            warnings = [
                f"{message.author.mention}, your arithmetic offends the dark gods. Try again, little cookie.",
                f"First mistake, {message.author.mention}? Shadow Milk forgives you... barely.",
                f"Kehehehe~ You stumble, {message.author.mention}. Tread carefully next time.",
            ]
            await message.channel.send(random.choice(warnings), delete_after=8)
            try: await message.add_reaction("<:Abyss:1341389646772305930>")
            except: pass
            return

        mocks = [
            f"<a:blueexclamation:1432655175360708653> {message.author.mention} ruined it all! Kehehehe! Back to 1 you go! <:SMC_motivated:1429184202410033322>",
            f"<a:blueexclamation:1432655175360708653> The count falls to dust thanks to {message.author.mention}! Math dies today!",
            f"<a:blueexclamation:1432655175360708653> Shadow Milk rejoices in your failure, {message.author.mention}. Reset time~",
            f"<a:blueexclamation:1432655175360708653> Oops! {message.author.mention} summoned chaos! All numbers vanish!",
            f"<a:blueexclamation:1432655175360708653> The dark powers frown upon {message.author.mention}. Count resets!",
            f"<a:blueexclamation:1432655175360708653> {message.author.mention} stepped on a forbidden number. Back to zero!",
            f"<a:blueexclamation:1432655175360708653> Shadow Milk smirks: {message.author.mention}, your math fails me. Reset!",
            f"<a:blueexclamation:1432655175360708653> {message.author.mention}, the Spire laughs at your mistake. Count erased!",
            f"<a:blueexclamation:1432655175360708653> Chaos reigns! {message.author.mention} disturbs the order. Start over!",
            f"<a:blueexclamation:1432655175360708653> Numbers tremble before {message.author.mention}'s blunder. Count collapses!",
            f"<a:blueexclamation:1432655175360708653> {message.author.mention} has unleashed pandemonium. Count reset!",
            f"<a:blueexclamation:1432655175360708653> The Spire engulfs the count! {message.author.mention} is the culprit!",
            f"<a:blueexclamation:1432655175360708653> Math dies screaming! {message.author.mention}, reset time!",
        ]
        await message.add_reaction("<:SMCx:1432661563470254172>")
        await message.channel.send(random.choice(mocks), delete_after=8)
        self.data[guild_id]["count"] = 0
        self.data[guild_id]["last_user"] = None
        save_data(self.data)

async def setup(bot):
    await bot.add_cog(Counting(bot))
