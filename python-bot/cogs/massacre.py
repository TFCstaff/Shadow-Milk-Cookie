import discord
from discord import app_commands
from discord.ext import commands
from discord.ui import View, Button
import asyncio
import random
from python-bot.utils.massacre_sim import run_massacre_simulation

class Massacre(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # store per-guild lobbies in-memory {guild_id: {...}}
        self.lobbies = {}

    @app_commands.command(name="massacre", description="Host a Massacre (Hunger Games) minigame.")
    async def massacre(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="The Shadow Realm",
            description="JOOOOOIN the Massacre! Let the show begin. . . <:SMCparkles:1402273494758199347>",
            color=0x0082e4,
        )
        embed.set_image(url="https://cdn.discordapp.com/attachments/1432658734441693214/1432663291754319965/Untitled2671_20250907131502.png?ex=6901df2a&is=69008daa&hm=a98cccea29beb5745f8cdf8886070d643805ff1908b45494c516c197dc796f55&")  # can be replaced
        embed.add_field(name="Instructions", value="Press **Join** to enter. The host (creator) can press **Start** to begin.")
        embed.set_footer(text="Max 25 participants.")

        view = MassacreLobbyView(self)
        view.host = interaction.user
        msg = await interaction.response.send_message(embed=embed, view=view)
        view.message = await interaction.original_response()  # store to edit later

class MassacreLobbyView(View):
    def __init__(self, cog):
        super().__init__(timeout=30 * 60)  # 30 minutes
        self.cog = cog
        self.participants = []
        self.host = None
        self.start_button = StartButton(self)
        self.add_item(JoinButton(self))
        self.add_item(LeaveButton(self))
        self.add_item(self.start_button)
        self.message = None

    async def on_timeout(self):
        # Optional cleanup
        if self.message:
            try:
                for item in self.children:
                    item.disabled = True
                await self.message.edit(view=self)
            except:
                pass

    async def update_embed(self):
        if not self.message:
            return
        embed = self.message.embeds[0]
        embed.clear_fields()
        embed.add_field(
            name="Instructions",
            value="Press **Join** to enter. The host (creator) can press **Start** to begin.",
            inline=False,
        )
        count_text = f"**{len(self.participants)} / 25** participants have joined.\n"
        if self.participants:
            count_text += ", ".join([m.display_name for m in self.participants])
        else:
            count_text += "No one has joined yet..."
        embed.add_field(name="Participants", value=count_text[:1024], inline=False)
        await self.message.edit(embed=embed, view=self)

class JoinButton(discord.ui.Button):
    def __init__(self, parent_view):
        super().__init__(label="Join", style=discord.ButtonStyle.success)
        self.parent_view = parent_view


    async def callback(self, interaction: discord.Interaction):
        member = interaction.user
        if member in self.parent_view.participants:
            await interaction.response.send_message("You already joined, wicked one.", ephemeral=True)
            return
        if len(self.parent_view.participants) >= 25:
            await interaction.response.send_message("The arena is full! 25 souls is enough for Shadow Milk’s delight.", ephemeral=True)
            return
        self.parent_view.participants.append(member)
        if not self.parent_view.host:
            self.parent_view.host = member
        await self.parent_view.update_embed()
        await interaction.response.send_message("You have entered the Massacre. . . The stage welcomes your chaos.", ephemeral=True)

class LeaveButton(discord.ui.Button):
    def __init__(self, parent_view):
        super().__init__(label="Leave", style=discord.ButtonStyle.danger)
        self.parent_view = parent_view


    async def callback(self, interaction: discord.Interaction):
        member = interaction.user
        if member not in self.parent_view.participants:
            await interaction.response.send_message("You were never part of my delightful chaos now, were you? <:SMC_WhatdyaSay:1346504541545300050>", ephemeral=True)
            return
        self.parent_view.participants.remove(member)
        await self.parent_view.update_embed()
        await interaction.response.send_message("You have left the Massacre. . . cowardly, but understandable.", ephemeral=True)

class StartButton(discord.ui.Button):
    def __init__(self, parent_view):
        super().__init__(label="Start", style=discord.ButtonStyle.primary)
        self.parent_view = parent_view

    async def callback(self, interaction: discord.Interaction):
        user = interaction.user
        # only host can start
        if self.parent_view.host and user != self.parent_view.host:
            await interaction.response.send_message("Only the host who birthed this chaos may start it.", ephemeral=True)
            return
        if len(self.parent_view.participants) < 2:
            await interaction.response.send_message("You need at least 2 participants to begin the slaughter.", ephemeral=True)
            return

        await interaction.response.send_message("The Massacre begins... may the odds be bitterly against you!", ephemeral=False)

        # Disable buttons once started
        for item in self.parent_view.children:
            item.disabled = True
        if self.parent_view.message:
            await self.parent_view.message.edit(view=self.parent_view)

        # Run the simulation
        await run_massacre_simulation(interaction.channel, self.parent_view.participants)
        p = self.parent_view.participants.copy()  # Make a local copy
        round_n = 1

        # Narration messages
        while len(p) > 1:
            await asyncio.sleep(random.uniform(1.0, 3.0))
            eliminated, p = run_massacre_round(p)
            if eliminated:
                action = dramatic_action()
                text = f"**Round {round_n}** — {eliminated.display_name} {action} by unknown horrors. . . Remaining: {len(p)}"
                await interaction.channel.send(embed=discord.Embed(description=text, color=0x0082e4))
                round_n += 1
            else:
                break

        # Final results
        endings = [
            "A dark laugh echoes... 'Survival is but a cruel joke.'",
            "Shadow Milk whispers, 'Another day, another corpse. Kehehehe~'",
            "The blood dries, but the screams remain... what a show!",
            "'Marvelous carnage!' cries Shadow Milk, clapping with delight.",
            "Only silence remains... and the winner’s trembling breath.",
        ]

        if p:
            winner = p[0]
            final_text = random.choice(endings)
            await channel.send(
                embed=discord.Embed(
                    title="A Winner Emerges",
                    description=f"**{winner.display_name}** survives the Massacre. {final_text} <a:Fount_crown:1422991318296166430>",
                    color=0x0082e4,
                )
            )
        else:
            await channel.send("All perished. . . Perfect. 🎶")

        return

async def setup(bot):
    await bot.add_cog(Massacre(bot))
