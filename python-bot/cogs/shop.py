import discord
from discord.ext import commands
from discord.ui import View, Button
import aiosqlite

CURRENCY = "<:LoD:1411031656055177276>"

# CLEAN SHOP ITEMS — emoji separated from name
SHOP_ITEMS = [
    (
        "<:SMC_cutter:1411067252681211996>",
        "Deceitful Cutter",
        300,
        "Radiates with deceitful energy, it may be used to bring you new cookies. . ."
    ),
    (
        "<:LampOfDeceit:1434966495812653187>",
        "Lamp of Deceit",
        1000,
        "A mysterious trinket of faint power. Legends say it protects your light of deceit from getting stolen. . ."
    ),
    (
        "<:Energy_Potion:1434966305898893465>",
        "Energy Potion",
        1500,
        "This potion will cure you and your pet! If you stumbled upon one, you'd be just the luckiest!"
    ),
    (
        "<:Letter:1434580183595356250>",
        "Anon Letter",
        2000,
        "You want to send a letter to one random cookie without them knowing you? I've got just the right item for you!."
    ),
    (
        "<:Orchid_Locket:1434580197092491488>",
        "Orchid Locket",
        2500,
        "This Orchid Locket is pretty. . . peaceful. Once acquired, your blackjack chances increase to win."
    ),
    (
        "<:Wizard_Wand:1434966466809171988>",
        "Wizard Wand",
        3500,
        "Do not underestimate this wand, it will give you random magical boosts once used. . ."
    ),
    (
        "<:Travel_Ticket:1434580103081230498>",
        "Travelling Ticket",
        4000,
        "This Traveling Ticket will take you to other realms around Beast-Yeast!"
    ),
    (
        "<:Forbidden_Book:1434966390561050747>",
        "Forbidden Chronicle",
        5000,
        "Want in on a tiny little secret? This book includes. . . random confessions from all the cookies using the bot."
    ),
]

LEFT_ARROW = "<:arrowleft:1433000307452940309>"
RIGHT_ARROW = "<:arrowright:1433000252306100294>"

NON_REPEATABLE_ITEMS = {
    "Forbidden Chronicle",
}



class Shop(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # ---------- Database helpers ----------
    async def get_balance(self, user_id: int):
        async with aiosqlite.connect("python-bot/data/economy.db") as db:
            async with db.execute("SELECT balance FROM users WHERE user_id = ?", (user_id,)) as cursor:
                row = await cursor.fetchone()
                return row[0] if row else 0

    async def add_balance(self, user_id: int, amount: int):
        async with aiosqlite.connect("python-bot/data/economy.db") as db:
            await db.execute("INSERT OR IGNORE INTO users (user_id, balance) VALUES (?, 0)", (user_id,))
            await db.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (amount, user_id))
            await db.commit()

    async def add_item(self, user_id: int, item_name: str):
        async with aiosqlite.connect("python-bot/data/economy.db") as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS inventory (
                    user_id INTEGER,
                    item_name TEXT,
                    quantity INTEGER DEFAULT 1,
                    UNIQUE(user_id, item_name)
                )
            """)
            await db.execute("""
                INSERT INTO inventory (user_id, item_name, quantity)
                VALUES (?, ?, 1)
                ON CONFLICT(user_id, item_name)
                DO UPDATE SET quantity = quantity + 1
            """, (user_id, item_name))
            await db.commit()

    async def remove_item(self, user_id: int, item_name: str, qty: int = 1):
        async with aiosqlite.connect("python-bot/data/economy.db") as db:
            await db.execute("""
                UPDATE inventory
                SET quantity = quantity - ?
                WHERE user_id = ? AND item_name = ?
            """, (qty, user_id, item_name))
            await db.execute("DELETE FROM inventory WHERE quantity <= 0")
            await db.commit()

    async def get_inventory(self, user_id: int):
        async with aiosqlite.connect("python-bot/data/economy.db") as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS inventory (
                    user_id INTEGER,
                    item_name TEXT,
                    quantity INTEGER DEFAULT 1,
                    UNIQUE(user_id, item_name)
                )
            """)
            async with db.execute("SELECT item_name, quantity FROM inventory WHERE user_id = ?", (user_id,)) as cursor:
                rows = await cursor.fetchall()
                return rows or []

    # ---------- Commands ----------

    @commands.hybrid_command(name="shop", description="View Shadow Milk’s shop of cursed goods.")
    async def shop(self, ctx):
        pages = []
        items_per_page = 3
        total_pages = (len(SHOP_ITEMS) + items_per_page - 1) // items_per_page

        for i in range(total_pages):
            start = i * items_per_page
            end = start + items_per_page
            page_items = SHOP_ITEMS[start:end]

            embed = discord.Embed(
                title=f"🛍️ Shadow Milk’s Shop (Page {i+1}/{total_pages})",
                description="Browse the items below. Use `/buy <item>` to purchase, or `/sell <item>` to sell one you own.",
                color=0x5A189A
            )

            for idx, (emoji, name, price, desc) in enumerate(page_items, start=start + 1):
                embed.add_field(
                    name=f"{idx}. {emoji} **{name}** — {price} {CURRENCY}",
                    value=desc,
                    inline=False
                )

            embed.set_footer(text=f"Page {i+1}/{total_pages}")
            pages.append(embed)

        view = ShopPages(self.bot, pages, items_per_page, SHOP_ITEMS)
        view.owner_id = ctx.author.id
        await ctx.send(embed=pages[0], view=view)

    @commands.hybrid_command(name="sell", description="Sell an item back to the shop.")
    async def sell(self, ctx, *, item_name: str):
        item_name = item_name.title()

        match = next(
            (i for i in SHOP_ITEMS if i[1].lower() == item_name.lower()),
            None
        )

        if not match:
            return await ctx.send("You can’t sell that item here.")

        emoji, clean_name, price, _ = match

        # Stored item name = "emoji + space + name"
        stored_name = f"{emoji} {clean_name}"

        inventory = await self.get_inventory(ctx.author.id)
        owned = next((q for n, q in inventory if n == stored_name), 0)

        if owned <= 0:
            return await ctx.send("You don’t own that item!")

        sell_price = price // 2

        await self.remove_item(ctx.author.id, stored_name)
        await self.add_balance(ctx.author.id, sell_price)

        embed = discord.Embed(
            title="💰 Item Sold",
            description=f"You sold **{emoji} {clean_name}** for **{sell_price}** {CURRENCY}.",
            color=0x22BB33
        )
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="inventory", description="Check your item inventory.")
    async def inventory(self, ctx, member: discord.Member = None):
        member = member or ctx.author
        items = await self.get_inventory(member.id)

        if not items:
            return await ctx.send(f"{member.display_name} has no items yet.")

        embed = discord.Embed(
            title=f"🎒 {member.display_name}’s Inventory",
            color=0x0082e4
        )

        for full_name, qty in items:
            embed.add_field(name=full_name, value=f"Quantity: **{qty}**", inline=False)

        await ctx.send(embed=embed)

class QuantityModal(discord.ui.Modal, title="Enter Quantity"):
    def __init__(self, item_name, item_price, emoji, shop_cog):
        super().__init__()
        self.item_name = item_name
        self.item_price = item_price
        self.emoji = emoji
        self.shop_cog = shop_cog

        self.qty = discord.ui.TextInput(
            label="Quantity to buy",
            placeholder="Enter a number of how much quantity you want to purchase of the same item. (e.g. 5)",
            required=True
        )
        self.add_item(self.qty)

    async def on_submit(self, interaction: discord.Interaction):
        # Validate integer
        try:
            quantity = int(self.qty.value)
            if quantity <= 0:
                raise ValueError
        except ValueError:
            return await interaction.response.send_message(
                "Please enter a **valid positive number**.",
                ephemeral=True
            )

        total_cost = self.item_price * quantity
        bal = await self.shop_cog.get_balance(interaction.user.id)

        # build confirmation view
        conf_view = ConfirmPurchaseView(
            quantity, total_cost,
            self.item_name, self.emoji,
            self.item_price, self.shop_cog
        )

        embed = discord.Embed(
            title="🧾 Purchase Confirmation",
            description=(
                f"You are attempting to buy **{quantity}×** {self.emoji} **{self.item_name}**\n"
                f"Total Cost: **{total_cost} {CURRENCY}**\n"
                f"Your balance: **{bal} {CURRENCY}**"
            ),
            color=0xFFD700
        )

        if bal < total_cost:
            embed.color = 0xFF4444
            await interaction.response.send_message(
                "❌ You do not have enough balance for this purchase.",
                ephemeral=True
            )
            return

        await interaction.response.send_message(embed=embed, view=conf_view, ephemeral=True)
        
class ConfirmPurchaseView(discord.ui.View):
    def __init__(self, quantity, total_cost, item_name, emoji, item_price, shop_cog):
        super().__init__(timeout=60)
        self.quantity = quantity
        self.total_cost = total_cost
        self.item_name = item_name
        self.emoji = emoji
        self.item_price = item_price
        self.shop_cog = shop_cog

    @discord.ui.button(label="✅ Confirm", style=discord.ButtonStyle.success)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        bal = await self.shop_cog.get_balance(interaction.user.id)
        if bal < self.total_cost:
            return await interaction.response.send_message(
                "❌ Not enough balance anymore.",
                ephemeral=True
            )

        stored_name = f"{self.emoji} {self.item_name}"

        # charge money
        await self.shop_cog.add_balance(interaction.user.id, -self.total_cost)

        # add quantity
        async with aiosqlite.connect("python-bot/data/economy.db") as db:
            await db.execute("""
                INSERT INTO inventory (user_id, item_name, quantity)
                VALUES (?, ?, ?)
                ON CONFLICT(user_id, item_name)
                DO UPDATE SET quantity = quantity + ?
            """, (interaction.user.id, stored_name, self.quantity, self.quantity))
            await db.commit()

        await interaction.response.send_message(
            f"✅ Successfully purchased **{self.quantity}× {self.emoji} {self.item_name}** "
            f"for **{self.total_cost} {CURRENCY}**!",
            ephemeral=True
        )
        self.stop()

    @discord.ui.button(label="❌ Cancel", style=discord.ButtonStyle.danger)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Purchase cancelled.", ephemeral=True)
        self.stop()

# ---------- Pagination System with Buy Buttons ----------
class ShopPages(View):
    def __init__(self, bot, pages, items_per_page, shop_items):
        super().__init__(timeout=300)
        self.bot = bot
        self.pages = pages
        self.items_per_page = items_per_page
        self.shop_items = shop_items
        self.current = 0
        self.owner_id = None
        self.shop_cog = bot.get_cog("Shop")

        self.left_button = Button(emoji=LEFT_ARROW, style=discord.ButtonStyle.secondary)
        self.right_button = Button(emoji=RIGHT_ARROW, style=discord.ButtonStyle.secondary)

        self.left_button.callback = self.go_left
        self.right_button.callback = self.go_right

        self.refresh_buttons()

    def refresh_buttons(self):
        """Rebuilds buttons dynamically for the current page."""
        self.clear_items()
        self.add_item(self.left_button)

        start = self.current * self.items_per_page
        end = start + self.items_per_page
        page_items = self.shop_items[start:end]

        for emoji, name, price, _ in page_items:

            button = Button(
                label=f"Buy {name}",
                emoji=emoji,
                style=discord.ButtonStyle.success
            )

            async def buy_callback(
                interaction: discord.Interaction,
                item_emoji=emoji,
                item_name=name,
                item_price=price
            ):
                if interaction.user.id != self.owner_id:
                    return await interaction.response.send_message(
                        "This is not your shop window.",
                        ephemeral=True
                    )

                # one-time items
                already_owned = False
                if item_name in NON_REPEATABLE_ITEMS:
                    inv = await self.shop_cog.get_inventory(interaction.user.id)
                    already_owned = any(full.split(" ", 1)[1] == item_name for full, qty in inv)

                if already_owned:
                    return await interaction.response.send_message(
                        f"You may only own ONE {item_emoji} {item_name}.",
                        ephemeral=True
                    )
 
                # open quantity modal
                modal = QuantityModal(item_name, item_price, item_emoji, self.shop_cog)
                await interaction.response.send_modal(modal)

                
                # ----- Block buying items that can only be purchased once -----
                bal = await self.shop_cog.get_balance(interaction.user.id)
                if bal < item_price:
                    await interaction.response.send_message(
                        f"You don’t have enough {CURRENCY}! You need {item_price} but you only have {bal}.",
                        ephemeral=True
                    )
                    return

                stored_name = f"{item_emoji} {item_name}"

                await self.shop_cog.add_balance(interaction.user.id, -item_price)
                await self.shop_cog.add_item(interaction.user.id, stored_name)

                await interaction.response.send_message(
                    f"✅ You bought **{item_emoji} {item_name}** for **{item_price}** {CURRENCY}!",
                    ephemeral=True
                )

            button.callback = buy_callback
            self.add_item(button)

        self.add_item(self.right_button)

    async def go_left(self, interaction: discord.Interaction):
        if interaction.user.id != self.owner_id:
            return await interaction.response.send_message(
                "Only the person who opened this shop can use these buttons.",
                ephemeral=True
            )
        if self.current > 0:
            self.current -= 1
            self.refresh_buttons()
            await interaction.response.edit_message(
                embed=self.pages[self.current],
                view=self
            )
        else:
            await interaction.response.defer()

    async def go_right(self, interaction: discord.Interaction):
        if interaction.user.id != self.owner_id:
            return await interaction.response.send_message(
                "Only the person who opened this shop can use these buttons.",
                ephemeral=True
            )
        if self.current < len(self.pages) - 1:
            self.current += 1
            self.refresh_buttons()
            await interaction.response.edit_message(
                embed=self.pages[self.current],
                view=self
            )
        else:
            await interaction.response.defer()


async def setup(bot):
    await bot.add_cog(Shop(bot))
