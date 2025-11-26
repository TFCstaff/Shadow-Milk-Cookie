import discord
from discord import app_commands
from discord.ext import commands
import random
import asyncio
import aiosqlite

PLACEHOLDER = "❒"

HANGMANPICS = [
    '''
  +---+
  |   |
      |
      |
      |
      |
=========''',
    '''
  +---+
  |   |
  O   |
      |
      |
      |
=========''',
    '''
  +---+
  |   |
  O   |
  |   |
      |
      |
=========''',
    '''
  +---+
  |   |
  O   |
 /|   |
      |
      |
=========''',
    r'''
  +---+
  |   |
  O   |
 /|\  |
      |
      |
=========''',
    r'''
  +---+
  |   |
  O   |
 /|\  |
 /    |
      |
=========''',
    r'''
  +---+
  |   |
  O   |
 /|\  |
 / \  |
      |
========='''
]

WORDS = [
    "cookie", "shadow", "pure vanilla", "jambound", "kingdom", "darkness", "battle",
    "realm", "arena", "slaughter", "void", "chaos", "chaotic", "meaningless", "deceitful",
    "sadness", "loneliness", "fear", "madness", "chaosborn", "crimson", "jester",
    "nightmare", "laughter", "torment", "corruption", "mask", "mirror", "abyss",
    "despair", "trickster", "vanilla", "purity", "betrayal", "voidheart", "frenzy",
    "lunacy", "eclipse", "darkness", "puppet", "stringless", "vengeance", "fangs",
    "whispers", "shadow realm", "milkshake", "foolishness", "sanity", "insanity",
    "grin", "riddle", "storm", "wrath", "silence", "emptiness", "scarlet", "illusion",
    "wickedness", "paranoia", "fearless", "devotion", "sinister", "temptation",
    "fate", "bloodlust", "melancholy", "tragedy", "revelation", "chaotic laughter",
    "archie", "green bean", "greenskie", "silly vanilly", "truthless recluse",
    "shadow milk", "eternal sugar", "i am coming", "your ip address", "candy apple",
    "black sapphire", "spire", "knowledge", "fountain", "sarcasm", "senseless",
    "forbidden truth", "false prophet", "dark scholar", "deceiver", "truthless",
    "cursed wisdom", "inkheart", "mindbreaker", "fool’s crown", "midnight tea",
    "raven glass", "whispering tome", "blighted verse", "shadowkeeper", "liar’s smile",
    "cracked halo", "pale grin", "forgotten vow", "sinbound", "illusionist", "oracle",
    "empty throne", "mirrorfall", "sweet poison", "book of deceit", "black quill",
    "truth eater", "milk of sin", "frozen mirth", "eyeless", "velvet dusk",
    "hollow laughter", "tainted purity", "vanilla dusk", "mimicry", "chaos ink",
    "endless jest", "unraveled", "false light", "echoing silence", "clever fiend",
    "twisted grin", "jester’s crown", "scripted madness", "serpent tongue", "gilded lie",
    "sweet despair", "milk of void", "crimson echo", "sinister glee", "honest liar",
    "cunning", "truthweaver", "blackened joy", "lunatic sage", "velvet chain",
    "fatebinder", "glass smile", "sugarbane", "the masquerade", "unspoken oath",
    "mockery"
]

REWARD = 1000  # Light of Deceit reward for winning

class HangedCookie(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.active_games = {}

    @app_commands.command(name="hangedcookie", description="Do you want to get hanged? I have just the game for you!")
    async def hangedcookie(self, interaction: discord.Interaction):
        if interaction.channel.id in self.active_games:
            await interaction.response.send_message(
                "A game is already running in this channel! Wait for it to finish.",
                ephemeral=True
            )
            return

        word = random.choice(WORDS).upper()
        display = [PLACEHOLDER if c.isalpha() else c for c in word]
        guessed_letters = set()
        lives = len(HANGMANPICS) - 1

        embed = discord.Embed(
            title="<:SMC_cutter:1411067252681211996> The Hanged Cookie!",
            description=f"```{HANGMANPICS[0]}```\nWord: {self.format_display(display)}\n\nOnly **{interaction.user.display_name}** can guess here!",
            color=0x0082e4
        )
        await interaction.response.send_message(embed=embed)
        message = await interaction.original_response()

        self.active_games[interaction.channel.id] = {
            "user_id": interaction.user.id,
            "word": word,
            "display": display,
            "guessed": guessed_letters,
            "lives": lives,
            "message": message,
            "embed": embed,
        }

        await self.run_game(interaction.channel)


    async def run_game(self, channel: discord.TextChannel):
        game = self.active_games[channel.id]
        word = game["word"]
        display = game["display"]
        reward_given = False

        # ✅ Fixed check: allow ANY messages from the original player id, works for fake interactions
        def check(m):
            return m.channel.id == channel.id and m.author.id == game["user_id"] and not m.author.bot

        while game["lives"] > 0 and PLACEHOLDER in display:
            try:
                msg = await self.bot.wait_for("message", timeout=90.0, check=check)
            except asyncio.TimeoutError:
                await channel.send("⏰ Time ran out... Pure Vanilla hangs lifeless. <:SAGE_sip:1429186997418987571>")
                break

            guess = msg.content.strip().upper()

            if len(guess) == 1 and guess.isalpha():
                if guess in game["guessed"]:
                    await channel.send(f"{msg.author.mention}, you already guessed that letter!")
                    continue
                game["guessed"].add(guess)

                if guess in word:
                    for i, letter in enumerate(word):
                        if letter == guess:
                            display[i] = guess
                    await channel.send(f"<a:SMCcheck:1367520031914590269> {guess} was correct!")
                else:
                    game["lives"] -= 1
                    await channel.send(f"<:SMCx:1432661563470254172> {guess} was wrong! The cookie trembles...")

            elif guess == word:
                for i, ch in enumerate(word):
                    display[i] = ch
                await channel.send(f"🎉 {msg.author.mention} guessed the word **{word}**! Pure Vanilla lives for another day...")
                await self.give_reward(msg.author.id, REWARD)
                await channel.send(f"💰 {msg.author.mention} earned **{REWARD:,} <:LoD:1411031656055177276> Light of Deceit!**")
                reward_given = True
                break
            else:
                await channel.send("That’s not quite the right word...")

            stage_index = len(HANGMANPICS) - 1 - game["lives"]
            game["embed"].description = (
                f"```{HANGMANPICS[stage_index]}```\n"
                f"Word: {self.format_display(display)}\n"
                f"Guessed: {', '.join(sorted(game['guessed'])) or 'None'}"
            )
            await game["message"].edit(embed=game["embed"])

            if PLACEHOLDER not in display:
                await channel.send(f"✨ The word was **{word}** — You’ve saved Pure Vanilla for today! Kyehehehe~")
                await self.give_reward(game["user_id"], REWARD)
                await channel.send(f"💰 <@{game['user_id']}> earned **{REWARD:,} <:LoD:1411031656055177276> Light of Deceit!**")
                reward_given = True
                break

        if not reward_given and game["lives"] <= 0:
            await channel.send(f"<:SMC_motivated:1429184202410033322> Pure Vanilla has fallen. The word was **{word}**.")

        self.active_games.pop(channel.id, None)

    async def give_reward(self, user_id: int, amount: int):
        async with aiosqlite.connect("python-bot/data/economy.db") as db:
            await db.execute("INSERT OR IGNORE INTO users (user_id, balance) VALUES (?, 0)", (user_id,))
            await db.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (amount, user_id))
            await db.commit()

    @staticmethod
    def format_display(display):
        return " ".join(c if c != " " else "   " for c in display)

async def setup(bot):
    await bot.add_cog(HangedCookie(bot))
