import discord
from discord.ext import commands
from discord import app_commands
import json
import os

CONFIG_FILE = "python-bot/data/restore_roles_config.json"
DATA_FILE = "python-bot/data/restore_roles_data.json"


def load_json(file):
    if not os.path.exists(file):
        with open(file, "w") as f:
            json.dump({}, f)
    with open(file, "r") as f:
        return json.load(f)


def save_json(file, data):
    with open(file, "w") as f:
        json.dump(data, f, indent=4)


class RestoreRoles(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = load_json(CONFIG_FILE)  # server enable/disable
        self.data = load_json(DATA_FILE)      # user role backup

    # --------------------
    # Helper functions
    # --------------------
    def is_enabled(self, guild_id: int):
        return str(guild_id) in self.config and self.config[str(guild_id)]["enabled"]

    def save_all(self):
        save_json(CONFIG_FILE, self.config)
        save_json(DATA_FILE, self.data)

    # --------------------
    # Admin command
    # --------------------
    @app_commands.command(name="restore_roles", description="Enable or disable automatic role restoration.")
    @app_commands.describe(action="Choose whether to enable or disable this feature.")
    @app_commands.choices(action=[
        app_commands.Choice(name="Enable", value="enable"),
        app_commands.Choice(name="Disable", value="disable")
    ])
    async def restore_roles_slash(self, interaction: discord.Interaction, action: app_commands.Choice[str]):
        if not interaction.user.guild_permissions.manage_guild:
            await interaction.response.send_message("<:SMCx:1432661563470254172> You need **Manage Server** permission to use this command.", ephemeral=True)
            return

        guild_id = str(interaction.guild.id)
        enabled = (action.value == "enable")

        self.config[guild_id] = {"enabled": enabled}
        self.save_all()

        await interaction.response.send_message(
            f"<a:SMCcheck:1367520031914590269> Role restoration has been **{'enabled' if enabled else 'disabled'}** for this server."
        )

    # --------------------
    # Prefix command version (!sm restore roles)
    # --------------------
    @commands.command(name="restore", aliases=["restoreroles"])
    @commands.has_permissions(manage_guild=True)
    async def restore_roles_prefix(self, ctx, action: str = None):
        if not action or action.lower() not in ["enable", "disable"]:
            await ctx.send("Usage: `!sm restore enable` or `!sm restore disable`")
            return

        guild_id = str(ctx.guild.id)
        enabled = (action.lower() == "enable")

        self.config[guild_id] = {"enabled": enabled}
        self.save_all()

        await ctx.send(f"<a:SMCcheck:1367520031914590269> Role restoration has been **{'enabled' if enabled else 'disabled'}** for this server.")

    # --------------------
    # Save roles on leave
    # --------------------
    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        guild_id = str(member.guild.id)
        if not self.is_enabled(member.guild.id):
            return

        roles_to_save = [r.id for r in member.roles if not r.is_default() and not r.is_premium_subscriber()]
        if not roles_to_save:
            return

        self.data.setdefault(guild_id, {})
        self.data[guild_id][str(member.id)] = roles_to_save
        self.save_all()

    # --------------------
    # Restore roles on rejoin
    # --------------------
    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        guild_id = str(member.guild.id)
        if not self.is_enabled(member.guild.id):
            return

        user_data = self.data.get(guild_id, {}).get(str(member.id))
        if not user_data:
            return

        roles = [member.guild.get_role(rid) for rid in user_data if member.guild.get_role(rid)]
        try:
            await member.add_roles(*roles, reason="Restoring previously held roles")
            del self.data[guild_id][str(member.id)]
            self.save_all()
            print(f"Restored roles for {member.display_name} <a:SMCmusic:1433000825323520042>")
        except discord.Forbidden:
            print(f"<a:blueexclamation:1432655175360708653> Missing permissions to restore roles for {member.display_name}\n"
                 f"Please Remember to re-order my role to the top of all other bots. . . little cookie!\n\n"
                 "Now, now. if someone else joined, I won't miss the chance to do my duty. <a:SMCmusic:1433000825323520042>")
        except Exception as e:
            print(f"Error restoring roles: {e}")


async def setup(bot):
    await bot.add_cog(RestoreRoles(bot))
