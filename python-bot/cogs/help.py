import discord
from discord.ext import commands
from discord import app_commands
from discord.ui import View, Button

LEFT_ARROW = "<:arrowleft:1433000307452940309>"
RIGHT_ARROW = "<:arrowright:1433000252306100294>"

class Help(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="help", description="Show Shadow Milk Cookie's help dashboard.")
    async def help(self, interaction: discord.Interaction):
        pages = self.build_pages()
        view = HelpPages(pages)
        await interaction.response.send_message(embed=pages[0], view=view, ephemeral=False)

    def build_pages(self):
        """Generate all help pages dynamically."""
        color = 0x0082e4

        pages = []

        # Page 1 — Games & Fun
        embed1 = discord.Embed(
            title="Shadow Milk Cookie — Help (1/6)",
            description="Entertainment, chaos, and play!",
            color=color
        )
        embed1.add_field(
            name="/massacre",
            value="Start a chaotic lobby of MASSACRE! Join with buttons and the host can start the simulation.",
            inline=False
        )
        embed1.add_field(
            name="/hangedcookie", 
            value="Start the Hanged Cookie game. Guess letters or the word before the cookie perishes!", 
            inline=False
        )
        embed1.add_field(
            name="/bingo", 
            value="Start a Bingo game with your server members. Bring the chaos!", 
            inline=False
        )
        embed1.add_field(
            name="/hiddenbeast", 
            value="Play the 'Hidden Beast' social deduction game, find the beast among the cookies!", 
            inline=False
        )
        embed1.add_field(
            name="**persona**", 
            value="Reply to Shadow Milk Cookie’s messages to trigger its personality and quotes!", 
            inline=False
        )
        embed1.set_footer(text="Page 1 — Minigames & fun")
        pages.append(embed1)

        # Page 2 — Economy & Currency
        embed2 = discord.Embed(
            title="Shadow Milk Cookie — Help (2/6)",
            description="Earn, gamble, and spend Light of Deceit!",
            color=color
        )
        embed2.add_field(
            name="/balance", 
            value="Check your Light of Deceit balance.", 
            inline=False
        )
        embed2.add_field(
            name="/daily", 
            value="Claim your daily Light of Deceit reward.", 
            inline=False
        )
        embed2.add_field(
            name="/work", 
            value="Earn Light of Deceit through work. (Work raises possible, depends on Shadow Milk Cookie!).", 
            inline=False
        )
        embed2.add_field(
            name="/crime", 
            value="Commit crimes for potential riches — or risk losing Light of Deceit. . . kehehehe.", 
            inline=False
        )
        embed2.add_field(
            name="/steal", 
            value="Steal from another player. Risky, but fun.", 
            inline=False
        )
        embed2.add_field(
            name="/pay", 
            value="Send Light of Deceit to another user.", 
            inline=False
        )
        embed2.add_field(
            name="/blackjack", 
            value="Gamble Light of Deceit in a tarot-styled blackjack game.", 
            inline=False
        )
        embed2.set_footer(text="Page 2 — Economy & Gambling")
        pages.append(embed2)

        # Page 3 — Shop & Items
        embed3 = discord.Embed(
            title="Shadow Milk Cookie — Help (3/6)",
            description="Buy, sell, and manage your items.",
            color=color
        )
        embed3.add_field(
            name="/shop", 
            value="Browse Shadow Milk’s shop of cursed goods.", 
            inline=False
        )
        embed3.add_field(
            name="/gacha", 
            value="You can use the gacha to pull for cookies now! You need to buy cutters from the shop for it.", 
            inline=False
        )
        embed3.add_field(
            name="/sell", 
            value="Sell an owned item back to the shop.", 
            inline=False
        )
        embed3.add_field(
            name="/inventory", 
            value="View your personal inventory.", 
            inline=False
        )
        embed3.add_field(
            name="/beg", 
            value="Beg Shadow Milk for LoD. Maybe he’ll pity you…", 
            inline=False
        )
        embed3.add_field(
            name="/search", 
            value="Search Earthbread for some hidden LoD.", 
            inline=False
        )
        embed3.add_field(
            name="/leaderboard", 
            value="See who’s the richest cookie. . . I wonder who is it!", 
            inline=False
        )
        embed3.set_footer(text="Page 3 — Shop & Items")
        pages.append(embed3)
        
        # Page 4 -- Shop & Items 2
        embed4 = discord.Embed(
            title="Shadow Milk Cookie — Help (4/6)",
            description="Gamble, ascend and manage your cookies.",
            color=color
        )
        embed4.add_field(
            name="/cookies", 
            value="You can view the pulled cookies you've got from gacha. There are 3 optional modes, and 5 sorts. The 'member' option is also optional. If you send the command, your own cookies will be viewed and sorted by rarity (from the rarest to the common.) while if you want to specify a sort, you can put any of the following: (rarity / alpha / stars / soulstones / recent). While in the modes option, you can input any of the following: (all / unlocked / locked).", 
            inline=False
        )
        embed4.add_field(
            name="/cookie", 
            value="You can view ONE cookie. View it's details, if you have unlocked it or not, and view how many stars it has.", 
            inline=False
        )
        embed4.add_field(
            name="/ascend", 
            value="You can ascend your cookies if you have extra soulstones. Make sure to input the exact cookie name, including 'cookie' beside it's name.", 
            inline=False
        )
        embed4.add_field(
            name="/profile", 
            value="View your profile, XP, full balance, badges. It's easy to view a summary of yourself here!", 
            inline=False
        )
        embed4.add_field(
            name="/confess", 
            value="You want to confess but. . . you don't want people to know it's you? The confessions go to my Forbidden Chronicle, dear! Buy the item from `/shop` to view your confession.", 
            inline=False
        )
        embed4.set_footer(text="Page 4 — Shop & Items #2")
        pages.append(embed4)

        # Page 5 — Utility & Server Tools
        embed5 = discord.Embed(
            title="Shadow Milk Cookie — Help (5/6)",
            description="Useful tools for server management and automation.",
            color=color
        )
        embed5.add_field(
            name="/restore_roles", 
            value="Restores previous roles to users who left, then rejoined, once enabled by mods.", 
            inline=False
        )
        embed5.add_field(
            name="/counting_setup", 
            value="Set up a counting channel for math chaos. Only Mods can configure this.", 
            inline=False
        )
        embed5.add_field(
            name="/invite", 
            value="You want to invite ME to your server? PSHH, easy! Just make sure the Guild piques my interest. . .", 
            inline=False
        )
        embed5.set_footer(text="Page 5 — Utilities & Admin Tools")
        pages.append(embed5)

        # Page 6 — Extra Info
        embed6 = discord.Embed(
            title="Shadow Milk Cookie — About (6/6)",
            description=(
                "Shadow Milk Cookie is a chaotic bot of fun, mischief, and Light of Deceit.\n\n"
                "Need help or found a bug? Contact `@_kobisan` or join the [testing server](https://discord.gg/Gz9SXRqC2M).\n"
                "Credits to `@seaofstars_.` for drawing the Check Mark emoji used in counting.\n"
                "Credits to `@pumpkein` for drawing the rest of the emojis used in massacre simulation.\n"
                "Credits to `@this.clown` for making the blackjack deck of cards emojis.\n\n"
                "Item Emojis are taken from the official CRK wiki.\n"
                "Use the arrow buttons below to navigate through all command categories."
            ),
            color=color
        )
        embed6.set_footer(text="Page 6 — About & Credits")
        pages.append(embed6)

        return pages


class HelpPages(View):
    def __init__(self, pages):
        super().__init__(timeout=300)
        self.pages = pages
        self.current_page = 0

        # Buttons
        self.left_button = Button(emoji=LEFT_ARROW, style=discord.ButtonStyle.secondary)
        self.right_button = Button(emoji=RIGHT_ARROW, style=discord.ButtonStyle.secondary)
        self.left_button.callback = self.go_left
        self.right_button.callback = self.go_right
        self.add_item(self.left_button)
        self.add_item(self.right_button)

    async def go_left(self, interaction: discord.Interaction):
        self.current_page = (self.current_page - 1) % len(self.pages)
        await interaction.response.edit_message(embed=self.pages[self.current_page], view=self)

    async def go_right(self, interaction: discord.Interaction):
        self.current_page = (self.current_page + 1) % len(self.pages)
        await interaction.response.edit_message(embed=self.pages[self.current_page], view=self)


async def setup(bot):
    await bot.add_cog(Help(bot))
