import nextcord
from nextcord.ext import commands
import sqlite3
import asyncio

intents = nextcord.Intents.default()
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

# Connect to the same database your dashboard uses
db = sqlite3.connect("applications.sqlite")
cursor = db.cursor()

# ---- Slash Command to List Templates ----
@bot.slash_command(name="templates", description="List your server's application templates")
async def templates(interaction: nextcord.Interaction):
    guild_id = str(interaction.guild.id)
    cursor.execute("SELECT id, name FROM templates WHERE guild_id=?", (guild_id,))
    templates = cursor.fetchall()
    if not templates:
        await interaction.response.send_message("No templates found for this server.")
        return
    msg = "\n".join([f"{t[0]}: {t[1]}" for t in templates])
    await interaction.response.send_message(f"Templates:\n{msg}")

# ---- Slash Command to Send Application to User ----
@bot.slash_command(name="sendapp", description="Send an application to a member")
async def sendapp(interaction: nextcord.Interaction, template_id: int, member: nextcord.Member):
    guild_id = str(interaction.guild.id)
    cursor.execute("SELECT name FROM templates WHERE id=? AND guild_id=?", (template_id, guild_id))
    template = cursor.fetchone()
    if not template:
        await interaction.response.send_message("Template not found.", ephemeral=True)
        return

    # Create Discord embed + button
    embed = nextcord.Embed(
        title=f"Shadow Milk Application: {template[0]}",
        description="Click the button below to start your application!",
        color=0x1E90FF
    )
    view = nextcord.ui.View()
    url = f"https://shadowmilk.com/apply/{guild_id}/{template_id}"
    view.add_item(nextcord.ui.Button(label="Start Application", url=url))
    await member.send(embed=embed, view=view)
    await interaction.response.send_message(f"Application sent to {member.display_name}", ephemeral=True)

# ---- Background Task to Forward Submissions to Staff ----
async def check_submissions():
    await bot.wait_until_ready()
    while not bot.is_closed():
        cursor.execute("SELECT * FROM submissions WHERE status='pending'")
        new_apps = cursor.fetchall()
        for app in new_apps:
            guild = bot.get_guild(int(app[1]))
            if not guild: continue
            staff_channel = guild.system_channel  # or your specific staff channel ID
            if not staff_channel: continue
            embed = nextcord.Embed(title="New Application Submitted", description=f"User ID: {app[2]}\nAnswers:\n{app[3]}", color=0x1E90FF)
            await staff_channel.send(embed=embed)
            cursor.execute("UPDATE submissions SET status='delivered' WHERE id=?", (app[0],))
            db.commit()
        await asyncio.sleep(5)  # check every 5 seconds

bot.loop.create_task(check_submissions())

# ---- Auto-DM New Member Verification ----
@bot.event
async def on_member_join(member):
    guild_id = str(member.guild.id)
    cursor.execute("SELECT auto_dm, default_template FROM guild_settings WHERE guild_id=?", (guild_id,))
    result = cursor.fetchone()
    if result and result[0] == 1:  # auto_dm ON
        default_template_id = result[1]
        if not default_template_id:
            return  # No template selected

        # Fetch template info
        cursor.execute("SELECT id, name FROM templates WHERE id=? AND guild_id=?", (default_template_id, guild_id))
        template = cursor.fetchone()
        if not template:
            return

        template_id, template_name = template
        embed = nextcord.Embed(
            title=f"Shadow Milk Verification: {template_name}",
            description="Click the button below to start your application!",
            color=0x1E90FF
        )
        view = nextcord.ui.View()
        url = f"https://shadow-milk-cookie.vercel.app/apply/{guild_id}/{template_id}"  # Replace with your dashboard URL
        view.add_item(nextcord.ui.Button(label="Start Application", url=url))
        try:
            await member.send(embed=embed, view=view)
        except:
            pass  # Member DMs might be closed

bot.run("DISCORD_BOT_TOKEN")
