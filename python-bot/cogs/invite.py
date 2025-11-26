import discord
from discord import app_commands
from discord.ext import commands

class Invite(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="invite", description="Get an invite link for Shadow Milk Cookie")
    async def invite(self, interaction: discord.Interaction):
        client_id = interaction.client.application_id
        invite_url = f"https://discord.com/oauth2/authorize?client_id=1428029742740930772&scope=bot+applications.commands&permissions=116800"

        view = discord.ui.View()
        view.add_item(discord.ui.Button(emoji="<a:SMCquestion:1433000520842350602>", url=invite_url))

        await interaction.response.send_message(
            "You want to invite little ol' me to your server? WELL, CLICK THE BUTTON BELOW THEN, IF YOU DARE!!",
            view=view,
            ephemeral=True
        )

async def setup(bot):
    await bot.add_cog(Invite(bot))
