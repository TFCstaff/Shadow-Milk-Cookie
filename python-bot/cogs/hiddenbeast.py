import discord
from discord.ext import commands
from discord import app_commands
from python-bot.utils import hiddenbeast_sim

MAX_PLAYERS = 15


class HiddenBeastLobby(discord.ui.View):
    def __init__(self, bot, starter: discord.Member):
        super().__init__(timeout=None)
        self.bot = bot
        self.starter = starter
        self.players = []
        self.message = None

    async def update_embed(self):
        embed = discord.Embed(
            title="<:SoulJam:1341385834003169341> Hidden Beast — Game Lobby",
            description=(
                "A social deduction minigame inspired by *Among Us*.\n"
                "Find the **Beast** hiding among the cookies.\n\n"
                f"<a:Fount_crown:1422991318296166430> Host: {self.starter.mention}\n"
                f"<:SMC_cutter:1411067252681211996> Players joined: **{len(self.players)}/{MAX_PLAYERS}**"
            ),
            color=discord.Color.dark_purple()
        )

        if self.players:
            embed.add_field(
                name="Players",
                value="\n".join(f"{i+1}. {p.display_name}" for i, p in enumerate(self.players)),
                inline=False
            )
        else:
            embed.add_field(name="Players", value="_No one yet!_", inline=False)

        embed.set_footer(text="Press 'Join' to play — Only the host can start the game.")
        return embed

    @discord.ui.button(label="Join", style=discord.ButtonStyle.success)
    async def join(self, interaction: discord.Interaction, button: discord.ui.Button):
        user = interaction.user
        if user in self.players:
            return await interaction.response.send_message("You already joined.", ephemeral=True)
        if len(self.players) >= MAX_PLAYERS:
            return await interaction.response.send_message("Lobby is full!", ephemeral=True)
        self.players.append(user)
        await interaction.response.edit_message(embed=await self.update_embed(), view=self)

    @discord.ui.button(label="Leave", style=discord.ButtonStyle.danger)
    async def leave(self, interaction: discord.Interaction, button: discord.ui.Button):
        user = interaction.user
        if user not in self.players:
            return await interaction.response.send_message("You aren't in the lobby.", ephemeral=True)
        self.players.remove(user)
        await interaction.response.edit_message(embed=await self.update_embed(), view=self)

    @discord.ui.button(label="Start", style=discord.ButtonStyle.primary)
    async def start(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.starter:
            return await interaction.response.send_message("Only the host can start!", ephemeral=True)
        if len(self.players) < 5:
            return await interaction.response.send_message("You need at least 5 players to start!", ephemeral=True)

        # Disable lobby controls
        for child in self.children:
            child.disabled = True
        await interaction.response.edit_message(embed=await self.update_embed(), view=self)

        await interaction.followup.send("Game starting...", ephemeral=False)
        # Delegate to the external simulation
        await hiddenbeast_sim.run_simulation(self.bot, interaction.channel, self.players, self.starter)


class HiddenBeast(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="hiddenbeast", description="Start a Hidden Beast lobby game.")
    async def hiddenbeast_slash(self, interaction: discord.Interaction):
        view = HiddenBeastLobby(self.bot, interaction.user)
        embed = await view.update_embed()
        msg = await interaction.channel.send(embed=embed, view=view)
        view.message = msg
        await interaction.response.send_message("Lobby created!", ephemeral=True)


async def setup(bot):
    await bot.add_cog(HiddenBeast(bot))
