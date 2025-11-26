import discord
from discord.ext import commands
import random
import asyncio

CURRENCY = "<:LoD:1411031656055177276>"
TAROT = "<a:tarot_card:1376843676860547163>"

class Blackjack(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name="blackjack", description="Play Blackjack for Light of Deceit!")
    @commands.cooldown(1, 60, commands.BucketType.user)
    async def blackjack(self, ctx, bet: int):
        """Simple emoji Blackjack game with tarot vibes."""
        from cogs.economy import Economy  # reuse balance system
        econ: Economy = ctx.bot.get_cog("Economy")

        balance = await econ.get_balance(ctx.author.id)
        if bet <= 0:
            return await ctx.send("Bet must be positive, little gambler.")
        if balance < bet:
            return await ctx.send("You don't have enough Light of Deceit to bet that much!")

        # cards + emoji symbols
        card_values = {
            "A": 11, "K": 10, "Q": 10, "J": 10,
            "10": 10, "9": 9, "8": 8, "7": 7,
            "6": 6, "5": 5, "4": 4, "3": 3, "2": 2
        }
        card_emojis = {
            "A": "<:TarotOne:1433139228853928036>", "K": "<:TarotKing:1433139188756250774>", "Q": "<:TarotQueen:1433145038858358946>", "J": "<:TarotJack:1433145107561054320>",
            "10": "<:TarotTen:1433147728061403207>", "9": "<:TarotNine:1433147692569071650>", "8": "<:TarotEight:1433147667613089993>", "7": "<:TarotSeven:1433147639611920545>",
            "6": "<:TarotSix:1433147619278065735>", "5": "<:TarotFive:1433147593348874290>", "4": "<:TarotFour:1433147560591364186>", "3": "<:TarotThree:1433145383370100876>", "2": "<:TarotTwo:1433145156244344923>"
        }
        deck = list(card_values.keys()) * 4
        random.shuffle(deck)

        def hand_value(hand):
            value = sum(card_values[c] for c in hand)
            # Aces count as 1 if over 21
            for c in hand:
                if c == "A" and value > 21:
                    value -= 10
            return value

        player = [deck.pop(), deck.pop()]
        dealer = [deck.pop(), deck.pop()]

        def display(hand):
            return " ".join(card_emojis[c] for c in hand)

        await ctx.send(f"{TAROT} **Your Hand:** {display(player)} (Total {hand_value(player)})\n"
                       f"Dealer shows: {card_emojis[dealer[0]]}")

        # Player turn (auto-simple logic)
        while hand_value(player) < 17 and random.random() < 0.5:
            await asyncio.sleep(2)
            card = deck.pop()
            player.append(card)
            await ctx.send(f"You drew {card_emojis[card]} (Total {hand_value(player)})")

        # Dealer turn
        while hand_value(dealer) < 17:
            await asyncio.sleep(2)
            dealer.append(deck.pop())

        player_val = hand_value(player)
        dealer_val = hand_value(dealer)

        await asyncio.sleep(2)
        result_msg = (
            f"{TAROT} **Dealer’s Hand:** {display(dealer)} (Total {dealer_val})\n\n"
        )

        if player_val > 21:
            await econ.add_balance(ctx.author.id, -bet)
            result_msg += f"You busted! Lost **{bet}** {CURRENCY}."
            color = 0xBB2222
        elif dealer_val > 21 or player_val > dealer_val:
            await econ.add_balance(ctx.author.id, bet)
            result_msg += f"You win! Gained **{bet}** {CURRENCY}!"
            color = 0x22BB33
        elif player_val == dealer_val:
            result_msg += f"It's a tie! Shadow Milk spares your balance... for now."
            color = 0xCCCC00
        else:
            await econ.add_balance(ctx.author.id, -bet)
            result_msg += f"Dealer wins. Lost **{bet}** {CURRENCY}."
            color = 0xBB2222

        embed = discord.Embed(
            title=f"{TAROT} Blackjack Results",
            description=result_msg,
            color=color
        )
        await ctx.send(embed=embed)
        
        # Check Orchid Locket buff
        async with aiosqlite.connect("economy.db") as db:
            async with db.execute("SELECT value FROM active_buffs WHERE user_id = ? AND type = 'blackjack_luck' AND expires_at > strftime('%s','now')", (ctx.author.id,)) as cur:
                row = await cur.fetchone()
                if row and random.random() < row[0]:
                    # Force a win
                    await econ.add_balance(ctx.author.id, bet)
                    embed = discord.Embed(title="🌸 Orchid Luck Shines", description=f"You won {CURRENCY}**{bet}** thanks to the Orchid Locket’s grace!", color=0x22BB33)
                    return await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(Blackjack(bot))
