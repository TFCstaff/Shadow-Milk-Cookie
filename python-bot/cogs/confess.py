import discord
from discord.ext import commands
import aiosqlite
from datetime import datetime

class Confess(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name="confess", description="Send an anonymous confession to the Forbidden Chronicle.")
    async def confess(self, ctx):

        class ConfessModal(discord.ui.Modal, title="Confession"):  # ✅ FIXED TITLE (must be 1–45 chars)
            confession = discord.ui.TextInput(
                label="Your Confession",
                style=discord.TextStyle.paragraph,
                placeholder="Write your confession here…",
                max_length=500
            )

            async def on_submit(self, interaction: discord.Interaction):
                confession_text = self.confession.value.strip()

                if not confession_text:
                    return await interaction.response.send_message(
                        "You must write something to confess.",
                        ephemeral=True
                    )

                async with aiosqlite.connect("python-bot/data/confessions.db") as db:
                    await db.execute("""
                        CREATE TABLE IF NOT EXISTS confessions (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            user_id INTEGER,
                            confession TEXT,
                            timestamp TEXT
                        )
                    """)
                    await db.execute(
                        "INSERT INTO confessions (user_id, confession, timestamp) VALUES (?, ?, ?)",
                        (
                            interaction.user.id,
                            confession_text,
                            datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
                        )
                    )
                    await db.commit()

                await interaction.response.send_message(
                    "<:Ancient_Scroll:1434580067651948657> Your confession has been etched into the Forbidden Chronicle.",
                    ephemeral=True
                )

        modal = ConfessModal()
        await ctx.interaction.response.send_modal(modal)


async def setup(bot):
    await bot.add_cog(Confess(bot))
