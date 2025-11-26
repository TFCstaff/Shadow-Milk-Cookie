import discord
from discord.ext import commands
import aiosqlite
import time
from typing import List, Tuple, Dict
from python-bot.utils.item_usage import ITEM_EFFECTS, remove_item  # existing effects and helper

CURRENCY = "<:LoD:1411031656055177276>"

# Categories for known items (clean_name -> category). Unknown items default to "Misc".
CATEGORY_MAP = {
    "Deceitful Cutter": "Consumables",
    "Energy Potion": "Consumables",
    "Starjelly": "Consumables",
    "Mysterious Portrait": "Consumables",
    "Lamp of Deceit": "Special",
    "Anon Letter": "Special",
    "Forbidden Chronicle": "Special",
    "Travelling Ticket": "Special",
    "Wizard Wand": "Buffs",
    "Orchid Locket": "Buffs",
    # add other known mappings as needed
}

# Items that can't be consumed
NON_CONSUMABLE_ITEMS = {
    "Forbidden Chronicle",
}

# Human-readable descriptions for preview (fallbacks accepted).
ITEM_DESCRIPTIONS = {
    "Deceitful Cutter": "Radiates with deceitful energy; it may be used to bring you new cookies...",
    "Lamp of Deceit": "A mysterious trinket of faint power. Activating it summons the Animatronic of Deceit to protect you from theft for a short time.",
    "Energy Potion": "A potion to restore you and your pet's health.",
    "Anon Letter": "Send an anonymous message to another user via the bot.",
    "Forbidden Chronicle": "A book containing confessions from other cookies.",
    "Wizard Wand": "Grants a random temporary buff (search luck, LoD multiplier, etc.).",
    "Orchid Locket": "Increases your odds in Blackjack for a limited time.",
    "Travelling Ticket": "Opens paths to other mysterious realms.",
    "Starjelly": "Sweet glowing jelly that restores your spirit.",
    "Wind Gem": "A gemstone that radiates refreshing energy.",
    "Mysterious Portrait": "An eerie portrait that hums with quiet power.",
}

# Per-item cooldowns in seconds (optional). 0 = no cooldown.
ITEM_COOLDOWNS = {
    "Lamp of Deceit": 600,
    "Wizard Wand": 600,
    "Orchid Locket": 1800,
}

PAGE_SIZE = 4  # items per page


class UseViewState:
    """Helper container representing the UI state shown to the user."""
    def __init__(self, items: List[Tuple[str, int]]):
        # items: list of (full_name, qty) where full_name is "<:emoji:id> Clean Name"
        self.all_items = items
        self.category = "All"  # All / Consumables / Buffs / Special / Misc
        self.page = 0

    def filtered_items(self) -> List[Tuple[str, int]]:
        if self.category == "All":
            return self.all_items
        else:
            out = []
            for full, qty in self.all_items:
                clean = parse_clean_name(full)
                cat = CATEGORY_MAP.get(clean, "Misc")
                if cat == self.category:
                    out.append((full, qty))
            return out

    def page_count(self) -> int:
        filtered = self.filtered_items()
        return max(1, (len(filtered) + PAGE_SIZE - 1) // PAGE_SIZE)


def parse_full_name(full_name: str) -> Tuple[str, str]:
    """Parse stored full name into (emoji, clean_name).
    Example: "<:Lamp:12345> Lamp of Deceit" -> ("<:Lamp:12345>", "Lamp of Deceit")
    If no emoji present, emoji returned as None and clean_name is the full string.
    """
    parts = full_name.split(" ", 1)
    if parts and parts[0].startswith("<:") and parts[0].endswith(">"):
        emoji = parts[0]
        clean = parts[1] if len(parts) > 1 else parts[0]
        return emoji, clean
    return None, full_name


def parse_clean_name(full_name: str) -> str:
    return parse_full_name(full_name)[1]


class UseCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # cooldowns: {(user_id, clean_name): expires_at_unix}
        self.item_cooldowns: Dict[Tuple[int, str], float] = {}

    async def get_inventory(self, user_id: int) -> List[Tuple[str, int]]:
        """Return list of (full_name, qty) for this user."""
        async with aiosqlite.connect("python-bot/data/economy.db") as db:
            async with db.execute(
                "SELECT item_name, quantity FROM inventory WHERE user_id = ?", (user_id,)
            ) as cur:
                rows = await cur.fetchall()
                return rows or []

    def _check_cooldown(self, user_id: int, clean_name: str) -> Tuple[bool, int]:
        """Return (is_on_cooldown, seconds_left)."""
        key = (user_id, clean_name)
        expires = self.item_cooldowns.get(key, 0)
        now = time.time()
        if now < expires:
            return True, int(expires - now)
        return False, 0

    def _set_cooldown(self, user_id: int, clean_name: str, seconds: int):
        if seconds <= 0:
            return
        key = (user_id, clean_name)
        self.item_cooldowns[key] = time.time() + seconds

    # ---------------- UI BUILDERS ----------------
    def _build_main_view(self, state: UseViewState, author_id: int):
        """Constructs the full view with category tabs, pagination, and item buttons for the current page."""
        view = discord.ui.View(timeout=120)

        # Category buttons row
        for cat in ["All", "Consumables", "Buffs", "Special", "Misc"]:
            style = discord.ButtonStyle.primary if cat == state.category else discord.ButtonStyle.secondary
            btn = discord.ui.Button(label=cat, style=style, custom_id=f"cat:{cat}")
            async def cat_cb(interaction: discord.Interaction, chosen=cat):
                # permission check
                if interaction.user.id != author_id:
                    return await interaction.response.send_message("This is not your inventory UI.", ephemeral=True)
                state.category = chosen
                state.page = 0
                await interaction.response.edit_message(embed=self._build_embed(state), view=self._build_main_view(state, author_id))
            btn.callback = cat_cb
            view.add_item(btn)

        # Get items for page
        filtered = state.filtered_items()
        start = state.page * PAGE_SIZE
        end = start + PAGE_SIZE
        page_slice = filtered[start:end]

        # create item buttons (one button per item)
        for full_name, qty in page_slice:
            emoji, clean = parse_full_name(full_name)
            # Button that opens the preview (preview includes Use button)
            label = f"{clean} (x{qty})"
            btn = discord.ui.Button(label=label, emoji=emoji if emoji else None, style=discord.ButtonStyle.secondary)
            async def item_cb(interaction: discord.Interaction, item_full=full_name):
                if interaction.user.id != author_id:
                    return await interaction.response.send_message("This is not your inventory UI.", ephemeral=True)
                # show preview panel
                await self._show_preview_panel(interaction, item_full)
            btn.callback = item_cb
            view.add_item(btn)

        # Pagination row: Prev / Page Info / Next
        prev_btn = discord.ui.Button(label="◀ Prev", style=discord.ButtonStyle.secondary)
        async def prev_cb(interaction: discord.Interaction):
            if interaction.user.id != author_id:
                return await interaction.response.send_message("This is not your inventory UI.", ephemeral=True)
            if state.page > 0:
                state.page -= 1
                await interaction.response.edit_message(embed=self._build_embed(state), view=self._build_main_view(state, author_id))
            else:
                await interaction.response.defer()
        prev_btn.callback = prev_cb
        view.add_item(prev_btn)

        # Page info as a disabled button
        page_info = f"Page {state.page+1}/{state.page_count()}"
        info_btn = discord.ui.Button(label=page_info, style=discord.ButtonStyle.grey, disabled=True)
        view.add_item(info_btn)

        next_btn = discord.ui.Button(label="Next ▶", style=discord.ButtonStyle.secondary)
        async def next_cb(interaction: discord.Interaction):
            if interaction.user.id != author_id:
                return await interaction.response.send_message("This is not your inventory UI.", ephemeral=True)
            if state.page < state.page_count() - 1:
                state.page += 1
                await interaction.response.edit_message(embed=self._build_embed(state), view=self._build_main_view(state, author_id))
            else:
                await interaction.response.defer()
        next_btn.callback = next_cb
        view.add_item(next_btn)

        return view

    def _build_embed(self, state: UseViewState) -> discord.Embed:
        """Creates the embed showing items for the current page and selected category."""
        embed = discord.Embed(title="🎒 Your Inventory", color=0x0082e4)
        embed.set_footer(text=f"Category: {state.category} • Use the item button to preview and use.")
        filtered = state.filtered_items()
        if not filtered:
            embed.description = "No items in this category."
            return embed

        start = state.page * PAGE_SIZE
        end = start + PAGE_SIZE
        page_slice = filtered[start:end]

        for full_name, qty in page_slice:
            emoji, clean = parse_full_name(full_name)
            desc = ITEM_DESCRIPTIONS.get(clean, "No description available.")
            embed.add_field(name=f"{emoji + ' ' if emoji else ''}{clean} (x{qty})", value=desc, inline=False)

        return embed

    async def _show_preview_panel(self, interaction: discord.Interaction, full_name: str):
        """Sends an ephemeral preview with Use / Close buttons for the selected item."""
        emoji, clean = parse_full_name(full_name)
        desc = ITEM_DESCRIPTIONS.get(clean, "No description available.")

        # Cooldown check
        on_cd, seconds_left = self._check_cooldown(interaction.user.id, clean)
        cd_text = f"\n\n⚠️ Cooldown: {seconds_left}s remaining." if on_cd else ""

        embed = discord.Embed(title=f"{emoji + ' ' if emoji else ''}{clean}", description=desc + cd_text, color=0x8A2BE2)
        view = discord.ui.View(timeout=90)

        # Use button
        use_btn = discord.ui.Button(label="Use Item", style=discord.ButtonStyle.success)
        async def use_cb(inner: discord.Interaction):
            # only invoker
            if inner.user.id != interaction.user.id:
                return await inner.response.send_message("You can't use items for another user!", ephemeral=True)

            # cooldown again
            on_cd2, secs = self._check_cooldown(inner.user.id, clean)
            if on_cd2:
                return await inner.response.send_message(f"Item is on cooldown: {secs}s left.", ephemeral=True)

            # run effect (ITEM_EFFECTS expects full stored name like "<:emoji:id> Clean Name")
            func = ITEM_EFFECTS.get(full_name)
            if not func:
                # Fallback for small item effects: try to handle common consumables that were not in ITEM_EFFECTS
                # (You can expand ITEM_EFFECTS to include them)
                await inner.response.send_message("This item cannot be used right now (no effect defined).", ephemeral=True)
                return

            # Call the effect; pass bot and the interaction so the effect can reply/DM etc.
            await func(self.bot, inner)

            # Remove item ONLY if it is a consumable
            if clean not in NON_CONSUMABLE_ITEMS:
                await remove_item(inner.user.id, full_name)
            cd_seconds = ITEM_COOLDOWNS.get(clean, 0)
            self._set_cooldown(inner.user.id, clean, cd_seconds)

            # Confirm used
            await inner.followup.send(f"<a:SMCcheck:1367520031914590269> You used {emoji}**{clean}**.", ephemeral=True)

            # Close the preview message (edit to show used)
            try:
                await interaction.message.delete()
            except Exception:
                pass

            view.stop()
        use_btn.callback = use_cb
        view.add_item(use_btn)

        # Close button
        close_btn = discord.ui.Button(label="Close", style=discord.ButtonStyle.secondary)
        async def close_cb(inner2: discord.Interaction):
            await inner2.response.defer()
            view.stop()
            try:
                await interaction.message.delete()
            except Exception:
                pass
        close_btn.callback = close_cb
        view.add_item(close_btn)

        # Send ephemeral preview (so only the user sees it)
        # If interaction is already responded to (it might be an ephemeral interaction from a button),
        # we use followup; otherwise respond.
        try:
            await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
        except Exception:
            await interaction.followup.send(embed=embed, view=view, ephemeral=True)

    # ---------------- Command ----------------
    @commands.hybrid_command(name="use", description="Open an interactive inventory UI to use items.")
    async def use(self, ctx):
        items = await self.get_inventory(ctx.author.id)
        if not items:
            return await ctx.send("You have no items in your inventory to use.")

        state = UseViewState(items)
        embed = self._build_embed(state)
        view = self._build_main_view(state, ctx.author.id)

        await ctx.send(embed=embed, view=view)


async def setup(bot):
    await bot.add_cog(UseCog(bot))
