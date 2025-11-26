import discord
from discord.ext import commands
import os
import inspect

# --- BOT SETUP ---
intents = discord.Intents.all()

bot = commands.Bot(
    command_prefix=["!", "sm ", "/"],  # Keep "!" for legacy commands if needed
    intents=intents,
    help_command=None
)

# --- Map text commands to slash command names ---
PREFIX_TO_SLASH = {
    "crime": "crime",
    "bj": "blackjack",
    "blackjack": "blackjack",
    "leader": "leaderboard",
    "work": "work",
    "beg": "beg",
    "bal": "balance",
    "balance": "balance",
    "hanged": "hangedcookie",
    "hangedcookie": "hangedcookie",
    "gacha": "gacha",
    "cookies": "cookies",
    "cookie": "cookie",
    "prof": "profile",
    "profile": "profile",
    "leaderboard": "leaderboard",
    "use": "use",
    "pay": "pay",
    "shop": "shop",
    "invite": "invite",
    "inv": "inventory",
    "inventory": "inventory",
    "search": "search",
    "scout": "search",
}

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} (ID: {bot.user.id})")
    print(f"Shadow Milk awakens in {len(bot.guilds)} realm(s)!")

    activity = discord.Activity(
        type=discord.ActivityType.watching,
        name="Pure Vanilla's Funeral."
    )
    await bot.change_presence(activity=activity)

    print("\n📦 Loading cogs...")
    for folder in os.listdir("python-bot/cogs"):
        if folder.endswith(".py") and not folder.startswith("__"):
            cog_name = folder[:-3]
            try:
                await bot.load_extension(f"cogs.{cog_name}")
                print(f"✅ Loaded {cog_name}")
            except Exception as e:
                print(f"❌ Failed to load {cog_name}: {e}")

    print("\n" + "=" * 50)
    print("✅ Bot is ONLINE and ready!")
    print("=" * 50)


@bot.command()
@commands.is_owner()
async def sync(ctx):
    """Manually sync slash commands (bot owner only)"""
    await ctx.send("<a:SMCloading:1433000133179736186> Syncing slash commands...")
    try:
        synced = await bot.tree.sync()
        await ctx.send(f"<a:SMCcheck:1367520031914590269> Synced {len(synced)} commands!")
        if synced:
            cmd_list = ", ".join([f"/{cmd.name}" for cmd in synced])
            await ctx.send(f"Commands: {cmd_list}")
    except Exception as e:
        await ctx.send(f"<:SMCx:1432661563470254172> Sync failed: {e}")


# --- FakeInteraction for text commands ---
class FakeInteraction:
    def __init__(self, message, bot=None):
        self.message = message
        self.user = message.author
        self.author = message.author  # alias
        self.channel = message.channel
        self.guild = message.guild
        self.bot = bot
        self.client = bot
        self.command = None
        self._sent_message = None
        self._deferred = False
        self._original_message = None  # store the "sent" message

    async def send(self, *args, **kwargs):
        # mimics ctx.send
        msg = await self.channel.send(*args, **kwargs)
        self._original_message = msg
        return msg

    @property
    def response(self):
        # mimics interaction.response.send_message
        class Resp:
            def __init__(self, outer):
                self.outer = outer

            async def send_message(inner_self, content=None, **kwargs):
                msg = await self.outer.channel.send(content=content, **kwargs)
                self.outer._original_message = msg
                return msg

        return Resp(self)

    async def original_response(self):
        # Returns the "sent" message (used by HangedCookie to edit embed)
        return self._original_message

    # -------------------------------
    # Discord-style response proxy
    # -------------------------------
    class ResponseProxy:
        def __init__(self, outer):
            self.outer = outer

        async def send_message(self, *args, **kwargs):
            """Behaves like interaction.response.send_message()"""
            self.outer._sent_message = await self.outer.channel.send(*args, **kwargs)
            return self.outer._sent_message

        async def defer(self, ephemeral=False):
            """Mimics defer() call for slash commands."""
            self.outer._deferred = True

        async def edit_message(self, *args, **kwargs):
            """Supports interaction.response.edit_message()."""
            if self.outer._sent_message:
                return await self.outer._sent_message.edit(*args, **kwargs)
            return None

    @property
    def response(self):
        return FakeInteraction.ResponseProxy(self)

    # --------------------------------
    # Slash command style helpers
    # --------------------------------
    async def defer(self, ephemeral=False):
        """Used by slash commands → ignored for prefix commands."""
        self._deferred = True

    async def followup(self, *args, **kwargs):
        """Supports interaction.followup.send()."""
        return await self.channel.send(*args, **kwargs)

    async def original_response(self):
        """Returns the first message sent by this FakeInteraction."""
        return self._sent_message

    async def edit_original_response(self, **kwargs):
        """Supports interaction.edit_original_response()."""
        if self._sent_message:
            return await self._sent_message.edit(**kwargs)
        return None

    # ---------------------------------
    # Compatibility helpers
    # ---------------------------------
    async def send(self, *args, **kwargs):
        """For code that uses interaction.send() directly."""
        return await self.channel.send(*args, **kwargs)


# --- Text "sm " prefix system ---
@bot.event
async def on_message(message: discord.Message):
    if message.author.bot:
        return

    content = message.content.lower()

    if content.startswith("sm "):
        parts = message.content.split()
        if len(parts) < 2:
            return

        cmd_name = parts[1].lower()
        args = parts[2:]

        slash_name = PREFIX_TO_SLASH.get(cmd_name)
        if not slash_name:
            return

        # ---- find command object inside cogs ----
        command_obj = None
        cog_instance = None

        for cog in bot.cogs.values():
            if hasattr(cog, slash_name):
                command_obj = getattr(cog, slash_name)
                cog_instance = cog
                break

        if command_obj is None:
            return await message.channel.send(
                f"❌ Command `{cmd_name}` is registered but has no slash command bound."
            )

        # ---- convert args to correct python types ----
        import inspect
        sig = inspect.signature(command_obj.callback)
        params = list(sig.parameters.values())[2:]  # skip (self, ctx)

        resolved_args = []
        for raw, param in zip(args, params):
            # Determine expected type
            expected = param.annotation if param.annotation != inspect._empty else str

            # Try to cast
            try:
                value = expected(raw)
            except:
                value = raw  # fallback

            resolved_args.append(value)

        # ---- resolve mentions to Member objects ----
        final_args = []
        for a in resolved_args:
            if isinstance(a, str):
                # <@123>
                if a.startswith("<@") and a.endswith(">"):
                    user_id = a.replace("<@", "").replace(">", "").replace("!", "")
                    member = message.guild.get_member(int(user_id))
                    final_args.append(member or a)
                # raw id
                elif a.isdigit():
                    member = message.guild.get_member(int(a))
                    final_args.append(member or a)
                else:
                    final_args.append(a)
            else:
                final_args.append(a)

        fake_interaction = FakeInteraction(message)

        # ---- attempt to call command callback ----
        try:
            await command_obj.callback(cog_instance, fake_interaction, *final_args)

        except TypeError as e:
            print(f"[Prefix->Slash ERROR] {slash_name}: {e}")
            # fallback: call without args
            try:
                await command_obj.callback(cog_instance, fake_interaction)
            except Exception as e2:
                print(f"[Fallback Fail] {e2}")

        return

    # allow normal prefix commands
    await bot.process_commands(message)


def main():
    token = os.getenv('DISCORD_BOT_TOKEN')
    if not token:
        print("❌ Error: DISCORD_BOT_TOKEN not found")
        return

    try:
        bot.run(token)
    except Exception as e:
        print("❌ Error: {e}")


if __name__ == "__main__":
    main()
