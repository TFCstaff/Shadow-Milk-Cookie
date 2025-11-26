import discord
from discord.ext import commands
import json
import os

BLACKLIST_FILE = "blacklist.json"
OWNER_ID = 970301958835540049  # your Discord ID


def load_blacklist():
    if not os.path.exists(BLACKLIST_FILE):
        return []
    with open(BLACKLIST_FILE, "r") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return []


def save_blacklist(data):
    with open(BLACKLIST_FILE, "w") as f:
        json.dump(data, f, indent=2)


class Blacklist(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.blacklisted_users = load_blacklist()

    def is_owner(self, user_id):
        return user_id == OWNER_ID

    @commands.group(name="sm", invoke_without_command=True)
    async def sm(self, ctx):
        """Main command group for !sm commands."""
        await ctx.send(
            "**Usage Guide for `!sm blacklist`:**\n"
            "```\n"
            "!sm blacklist add @user   → Add someone to the blacklist\n"
            "!sm blacklist remove @user → Remove someone from the blacklist\n"
            "!sm blacklist view         → View all blacklisted users\n"
            "```\n"
            "⚠️ Only the bot owner can use these commands."
        )

    @sm.group(name="blacklist", invoke_without_command=True)
    async def blacklist(self, ctx):
        """Show guide if someone runs the wrong blacklist command."""
        await ctx.send(
            "**Blacklist Command Guide:**\n"
            "```\n"
            "!sm blacklist add @user   → Add someone to the blacklist\n"
            "!sm blacklist remove @user → Remove someone from the blacklist\n"
            "!sm blacklist view         → View all blacklisted users\n"
            "```\n"
            "⚠️ Only the bot owner can use these commands."
        )

    @blacklist.command(name="add")
    async def blacklist_add(self, ctx, user: discord.User):
        if not self.is_owner(ctx.author.id):
            return await ctx.send("🚫 You do not have permission to use this command.")

        if user.id in self.blacklisted_users:
            return await ctx.send(f"{user.mention} is already blacklisted.")

        self.blacklisted_users.append(user.id)
        save_blacklist(self.blacklisted_users)
        await ctx.send(f"✅ {user.mention} has been **blacklisted** from AI responses.")

    @blacklist.command(name="remove")
    async def blacklist_remove(self, ctx, user: discord.User):
        if not self.is_owner(ctx.author.id):
            return await ctx.send("🚫 You do not have permission to use this command.")

        if user.id not in self.blacklisted_users:
            return await ctx.send(f"{user.mention} is not blacklisted.")

        self.blacklisted_users.remove(user.id)
        save_blacklist(self.blacklisted_users)
        await ctx.send(f"✅ {user.mention} has been **removed** from the blacklist.")

    @blacklist.command(name="view")
    async def blacklist_view(self, ctx):
        if not self.is_owner(ctx.author.id):
            return await ctx.send("🚫 You do not have permission to use this command.")

        if not self.blacklisted_users:
            return await ctx.send("No one is currently blacklisted.")

        users_list = []
        for user_id in self.blacklisted_users:
            user = self.bot.get_user(user_id)
            users_list.append(user.mention if user else f"Unknown user ({user_id})")

        await ctx.send("🕳️ **Blacklisted Users:**\n" + "\n".join(users_list))


async def setup(bot):
    await bot.add_cog(Blacklist(bot))
