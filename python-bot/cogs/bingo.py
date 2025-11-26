import discord
from discord import app_commands
from discord.ext import commands
from discord.ui import View, Button
import random
import asyncio
import aiosqlite
import io

from python-bot.utils.bingo_card import generate_bingo_card, generate_card_image

REWARD_LINE = 500
REWARD_FILL = 5000
DATABASE_PATH = "python-bot/data/economy.db"


class Bingo(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.lobbies = {}  # channel.id -> lobby dict

    @app_commands.command(name="bingo", description="Start a Bingo lobby where everyone can join!")
    async def bingo(self, interaction: discord.Interaction):
        channel = interaction.channel

        if channel.id in self.lobbies:
            return await interaction.response.send_message(
                "A Bingo game is already active in this channel!",
                ephemeral=True,
            )

        lobby = {
            "host": interaction.user,
            "participants": [],
            "participants_by_id": {},
            "cards": {},
            "drawn": set(),
            "message": None,
            "line_claimed": False,   # ✅ NEW
            "fill_claimed": False,   # ✅ NEW
        }

        view = BingoLobbyView(self, lobby)
        embed = discord.Embed(
            title="<:SMC_Dice:1435282878119547021> Bingo Lobby — Join the Game!",
            description="Press **Join** to participate!\nThe host can press **Start** when ready.\n\n<:discordbooster:1433000376151310377> **Rewards:**\n• Line win — <:LoD:1411031656055177276> 500 LoD\n• Full card — <:LoD:1411031656055177276> 5000 LoD",
            color=0x0082e4,
        )

        await interaction.response.send_message(embed=embed, view=view)
        lobby_msg = await interaction.original_response()
        lobby["message"] = lobby_msg
        self.lobbies[channel.id] = lobby

    # LISTENER FOR CHAT CALLS
    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return

        for lobby in self.lobbies.values():
            if message.channel.id != lobby["message"].channel.id:
                continue

            user_id = message.author.id
            content = message.content.strip().upper()

            # LINE CALL — only if NOT already claimed
            if (
                content == "BINGO"
                and not lobby["line_claimed"]          # ✅ NEW
                and user_id in lobby.get("line_ready", [])
            ):
                lobby["line_claimed"] = True          # ✅ NEW — lock further claims
                await award_loD(user_id, REWARD_LINE)
                await message.channel.send(
                    f"🏆 {message.author.mention} called **BINGO** and won <:LoD:1411031656055177276> {REWARD_LINE} Light of Deceit!"
                )
                lobby["line_ready"].clear()

            # FILL CALL — only if NOT already claimed
            elif (
                content == "FILL"
                and not lobby["fill_claimed"]         # ✅ NEW
                and user_id in lobby.get("fill_ready", [])
            ):
                lobby["fill_claimed"] = True          # ✅ NEW — prevent more fills
                await award_loD(user_id, REWARD_FILL)
                await message.channel.send(
                    f"🏆 {message.author.mention} called **FILL** and won <:LoD:1411031656055177276> {REWARD_FILL} Light of Deceit! 🎉"
                )
                lobby["fill_ready"].clear()

                # END GAME IMMEDIATELY AFTER FILL
                channel = lobby["message"].channel
                await channel.send("<a:Fount_crown:1422991318296166430> **The game has ended — a player got a FULL CARD!**")
                self.lobbies.pop(channel.id, None)
                return

    # DRAW LOOP
    async def run_draws(self, channel: discord.TextChannel):
        lobby = self.lobbies[channel.id]
        numbers = list(range(1, 76))
        random.shuffle(numbers)
        drawn = set()

        await channel.send("🎱 **The Bingo game has begun!**")

        called_numbers_by_letter = {letter: [] for letter in "BINGO"}

        call_count = 0

        while numbers:
            # STOP EARLY IF SOMEONE CALLED FILL
            if lobby["fill_claimed"]:
                return

            await asyncio.sleep(20)
            num = numbers.pop()
            drawn.add(num)
            lobby["drawn"] = drawn
            call_count += 1

            # Determine letter based on number
            if 1 <= num <= 15:
                letter = "B"
            elif 16 <= num <= 30:
                letter = "I"
            elif 31 <= num <= 45:
                letter = "N"
            elif 46 <= num <= 60:
                letter = "G"
            else:
                letter = "O"

            called_numbers_by_letter[letter].append(num)

            # Mark numbers in each player’s card
            for pid, data in lobby["cards"].items():
                card = data["matrix"]
                marked = data["marked"]

                for r in range(5):
                    for c in range(5):
                        if card[r][c] == num:
                            marked[r][c] = True

                # Add to ready lists, but rewards limited by flags
                if check_full(marked):
                    lobby.setdefault("fill_ready", set()).add(pid)
                elif check_line_bingo(marked):
                    lobby.setdefault("line_ready", set()).add(pid)

            header = "# ━━━━༺🃏༻━━━━\n"
            main = (
                "⠀⠀⠀**A number has been dealt...**\n\n"
                f"# ⠀⠀  ⠀CALL #{call_count}\n"
                f"# ⠀⠀⠀⠀      {letter}\n"
                f"# ⠀⠀⠀⠀     **{num}**\n"
                f"#  ⠀⠀⠀⠀     "
            )
            separator = "\n# ━━━━༺🃏༻━━━━"

            history_lines = []
            for col_letter in "BINGO":
                nums = sorted(called_numbers_by_letter[col_letter])
                if nums:
                    nums_str = ", ".join(str(n) for n in nums)
                    history_lines.append(f"{col_letter} — {nums_str}")
                else:
                    history_lines.append(f"{col_letter} — *None yet*")

            full_text = f"{header}{main}\n" + "\n".join(history_lines) + separator

            embed = discord.Embed(
                title="",
                description=full_text,
                color=0x0082e4
            )
            embed.set_footer(text="Type BINGO or FILL to claim your win when ready!")

            await channel.send(embed=embed)



class BingoLobbyView(View):
    def __init__(self, cog, lobby, timeout=1800):
        super().__init__(timeout=timeout)
        self.cog = cog
        self.lobby = lobby
        self.add_item(JoinButton(self))
        self.add_item(LeaveButton(self))
        self.start_button = StartButton(self)
        self.add_item(self.start_button)

    async def update_embed(self):
        msg = self.lobby["message"]
        if not msg:
            return

        embed = msg.embeds[0]
        embed.clear_fields()

        embed.add_field(name="Host", value=self.lobby["host"].mention, inline=False)
        if self.lobby["participants"]:
            embed.add_field(
                name="Players",
                value=", ".join([m.display_name for m in self.lobby["participants"]])[:1024],
                inline=False,
            )
        else:
            embed.add_field(name="Players", value="No players yet.", inline=False)

        await msg.edit(embed=embed, view=self)


class JoinButton(Button):
    def __init__(self, parent_view):
        super().__init__(label="Join", style=discord.ButtonStyle.success)
        self.parent_view = parent_view

    async def callback(self, interaction: discord.Interaction):
        member = interaction.user
        lobby = self.parent_view.lobby

        if member in lobby["participants"]:
            return await interaction.response.send_message("You already joined!", ephemeral=True)

        lobby["participants"].append(member)
        lobby["participants_by_id"][member.id] = member
        await self.parent_view.update_embed()
        await interaction.response.send_message("<a:SMCcheck:1367520031914590269> Welcome, welcome! You joined the Bingo lobby !", ephemeral=True)


class LeaveButton(Button):
    def __init__(self, parent_view):
        super().__init__(label="Leave", style=discord.ButtonStyle.danger)
        self.parent_view = parent_view

    async def callback(self, interaction: discord.Interaction):
        member = interaction.user
        lobby = self.parent_view.lobby

        if member not in lobby["participants"]:
            return await interaction.response.send_message("You are not in this lobby. . .", ephemeral=True)

        lobby["participants"].remove(member)
        lobby["participants_by_id"].pop(member.id, None)
        await self.parent_view.update_embed()
        await interaction.response.send_message("<:SMCx:1432661563470254172> Awww. . . You left the Bingo lobby.", ephemeral=True)


class StartButton(Button):
    def __init__(self, parent_view):
        super().__init__(label="Start", style=discord.ButtonStyle.primary)
        self.parent_view = parent_view

    async def callback(self, interaction: discord.Interaction):
        lobby = self.parent_view.lobby

        if interaction.user != lobby["host"]:
            return await interaction.response.send_message("Only the host can start the game. . .", ephemeral=True)

        if len(lobby["participants"]) == 0:
            return await interaction.response.send_message("No participants yet!", ephemeral=True)

        await interaction.response.send_message("<a:SMCloading:1433000133179736186> Starting Bingo! DMing cards...", ephemeral=False)

        for item in self.parent_view.children:
            item.disabled = True
        await lobby["message"].edit(view=self.parent_view)

        await self.prepare_and_send_cards(interaction)
        await self.parent_view.cog.run_draws(interaction.channel)

    async def prepare_and_send_cards(self, interaction: discord.Interaction):
        lobby = self.parent_view.lobby

        for member in lobby["participants"]:
            card = generate_bingo_card()
            lobby["cards"][member.id] = {
                "matrix": card,
                "marked": [[False] * 5 for _ in range(5)],
            }
            lobby["cards"][member.id]["marked"][2][2] = True  # Center free space

            img_bytes = generate_card_image(
                card,
                logo_url="https://cdn.discordapp.com/attachments/1434579783886307421/1434953736199077969/KwcshsE.png?ex=690a344e&is=6908e2ce&hm=cf8433077690f0aeaab95d7b1fcca0b570d8bba4e3215d00f2c6ddf0528e6cfd&"
            )

            try:
                if img_bytes:
                    file = discord.File(img_bytes, filename="bingo_card.png")
                    await member.send("<a:tarot_card:1376843676860547163> Here’s your Bingo card. Keep it safe! <:SMC_Glare:1429184295179784354>", file=file)
                else:
                    await member.send("<a:tarot_card:1376843676860547163> Here’s your Bingo card:\n" + card_to_text(card))
            except Exception:
                await interaction.channel.send(f"{member.mention} (DM failed): Here’s your Bingo card!")
                if img_bytes:
                    file = discord.File(img_bytes, filename="bingo_card.png")
                    await interaction.channel.send(file=file)
                else:
                    await interaction.channel.send(card_to_text(card))


# === Helper functions ===
def check_line_bingo(marked):
    for r in range(5):
        if all(marked[r][c] for c in range(5)):
            return True
    for c in range(5):
        if all(marked[r][c] for r in range(5)):
            return True
    if all(marked[i][i] for i in range(5)):
        return True
    if all(marked[i][4 - i] for i in range(5)):
        return True
    return False


def check_full(marked):
    return all(all(row) for row in marked)


async def award_loD(user_id: int, amount: int):
    try:
        async with aiosqlite.connect(DATABASE_PATH) as db:
            await db.execute(
                "INSERT OR IGNORE INTO users (user_id, balance) VALUES (?, 0)", (user_id,)
            )
            await db.execute(
                "UPDATE users SET balance = balance + ? WHERE user_id = ?", (amount, user_id)
            )
            await db.commit()
    except Exception as e:
        print("Failed to award Light of Deceit:", e)


async def setup(bot):
    await bot.add_cog(Bingo(bot))
