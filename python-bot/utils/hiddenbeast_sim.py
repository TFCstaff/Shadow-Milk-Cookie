import discord
import random
import asyncio
import aiosqlite
from typing import List, Dict, Optional

CURRENCY = "<:LoD:1411031656055177276>"
SPECIAL_ROLES = ["Detective", "Healer", "Trickster", "Guardian", "Beast"]

CHOICE_TIMEOUT = 180       # 3 minutes
DISCUSSION_DURATION = 90  # 1 minute and 30 seconds
VOTE_DURATION = 60         # 1 minutes
DB_PATH = "python-bot/data/economy.db"


# ---------------------------
# Database helper
# ---------------------------
async def add_balance(user_id: int, amount: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("INSERT OR IGNORE INTO users (user_id, balance) VALUES (?, 0)", (user_id,))
        await db.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (amount, user_id))
        await db.commit()


# ---------------------------
# Dropdown option builder
# ---------------------------
def build_select_options(members: List[discord.Member]) -> List[discord.SelectOption]:
    opts = []
    for m in members:
        label = m.display_name if len(m.display_name) <= 100 else m.display_name[:97] + "..."
        opts.append(discord.SelectOption(label=label, value=str(m.id)))
    return opts


# ---------------------------
# Generic DM select views
# ---------------------------
class DMSelectView(discord.ui.View):
    def __init__(self, target_member: discord.Member, choices: List[discord.Member], prompt: str, timeout=CHOICE_TIMEOUT):
        super().__init__(timeout=timeout)
        self.chosen: Optional[int] = None
        self.target_member = target_member
        self.prompt = prompt
        self.add_item(DMSelect(choices))

    async def on_timeout(self):
        pass


class DMSelect(discord.ui.Select):
    def __init__(self, choices: List[discord.Member]):
        super().__init__(placeholder="Select a player...", min_values=1, max_values=1, options=build_select_options(choices))

    async def callback(self, interaction: discord.Interaction):
        self.view.chosen = int(self.values[0])
        await interaction.response.send_message("Selection received.", ephemeral=True)
        self.view.stop()


# ---------------------------
# Voting UI with live scoreboard
# ---------------------------
class VoteSelect(discord.ui.Select):
    def __init__(self, alive_members: List[discord.Member], view_ref):
        # Build options for live players, then add a SKIP option
        options = build_select_options(alive_members)
        options.append(discord.SelectOption(label="Skip Vote", value="SKIP"))
        super().__init__(placeholder="Vote who to eliminate...", min_values=1, max_values=1, options=options)
        self.view_ref = view_ref
        self.allowed_voters = {m.id for m in alive_members}

    async def callback(self, interaction: discord.Interaction):
        # Restrict voting to alive players only
        if interaction.user.id not in self.allowed_voters:
            await interaction.response.send_message("❌ You are not allowed to vote.", ephemeral=True)
            return

        voter_id = interaction.user.id
        chosen_value = self.values[0]

        if chosen_value == "SKIP":
            # Record skip as None
            self.view_ref.votes[voter_id] = None
            await interaction.response.send_message("Skip vote recorded.", ephemeral=True)
        else:
            chosen_id = int(chosen_value)
            self.view_ref.votes[voter_id] = chosen_id
            await interaction.response.send_message(
                f"Vote recorded for {self.view_ref.alive_dict[chosen_id].display_name}.",
                ephemeral=True
            )
        await self.view_ref.update_scoreboard()


class VoteView(discord.ui.View):
    def __init__(self, alive_members: List[discord.Member], channel: discord.TextChannel, timeout=VOTE_DURATION):
        super().__init__(timeout=timeout)
        self.votes: Dict[int, Optional[int]] = {}
        self.alive_dict = {m.id: m for m in alive_members}
        self.channel = channel
        self.embed_message: Optional[discord.Message] = None
        self.add_item(VoteSelect(alive_members, self))

    async def make_embed(self, remaining: int = None):
        """Creates the live vote scoreboard embed."""
        vote_counts: Dict[int, int] = {mid: 0 for mid in self.alive_dict}
        skip_count = 0
        for target_id in self.votes.values():
            if target_id is None:
                skip_count += 1
            elif target_id in vote_counts:
                vote_counts[target_id] += 1

        desc_lines = []
        for mid, count in vote_counts.items():
            desc_lines.append(f"{self.alive_dict[mid].display_name} — **{count} vote{'s' if count != 1 else ''}**")
        desc_lines.append(f"Skip — **{skip_count} vote{'s' if skip_count != 1 else ''}**")

        desc = "\n".join(desc_lines)
        embed = discord.Embed(
            title="🗳️ Voting in Progress",
            description=desc,
            color=discord.Color.orange()
        )
        if remaining is not None:
            embed.set_footer(text=f"⏳ Voting ends in {remaining}s...")
        return embed

    async def start_scoreboard(self):
        """Starts the scoreboard message + auto updater."""
        embed = await self.make_embed(VOTE_DURATION)
        self.embed_message = await self.channel.send(embed=embed, view=self)
        asyncio.create_task(self.auto_updater())

    async def auto_updater(self):
        """Automatically updates the scoreboard every 1s."""
        remaining = VOTE_DURATION
        while remaining > 0:
            await asyncio.sleep(1)
            remaining -= 1
            await self.update_scoreboard(remaining)
        # Voting ended, remove the view immediately
        await self.update_scoreboard(0, ended=True)
        self.stop()

    async def update_scoreboard(self, remaining: Optional[int] = None, ended: bool = False):
        """Updates the scoreboard embed live."""
        if not self.embed_message:
            return
        embed = await self.make_embed(remaining if remaining is not None else VOTE_DURATION)
        if ended:
            embed.set_footer(text="Voting has ended!")
        try:
            await self.embed_message.edit(embed=embed, view=self if not ended else None)
        except Exception:
            pass


# ---------------------------
# Detective clue generator
# ---------------------------
def generate_clue(target_role: str) -> str:
    riddles = {
        "Cookie": [
            "Only crumbs and whispers remain — too plain to hide secrets.",
            "Their aura is sweet, yet ordinary; sugar masks no shadow.",
            "Nothing but dough and innocence — or is it truly so?"
        ],
        "Medic": [
            "You sense the faint scent of herbs and healing — mercy clings to them.",
            "Soft hands stitched fate once before; perhaps they'll mend again.",
            "They walk with the calm of someone who has seen too much pain."
        ],
        "Guardian": [
            "A shimmer like invisible armor surrounds them — unseen yet strong.",
            "The wind bends away from them, as if guarding their heart.",
            "They stand firm, a silent watcher cloaked in quiet vows."
        ],
        "Vengeful": [
            "The air hums with resentment — laughter hiding sharp edges.",
            "A trickster’s grin flickers behind polite words.",
            "They smile as if knowing how this story ends."
        ],
        "Beast": [
            "Something moves where no shadow should — claws hidden by charm.",
            "A heartbeat heavier than most — hunger dressed as calm.",
            "The moon seems to favor them. You dare not meet their eyes."
        ]
    }
    options = riddles.get(target_role, ["The clue slips through your fingers like mist."])
    return random.choice(options)


# ---------------------------
# Scoreboard embed
# ---------------------------
def make_scoreboard_embed(round_number: int, alive: Dict[int, discord.Member], dead: Dict[int, Dict], role_map: Dict[int, str]):
    alive_list = "\n".join(f"🟢 {m.display_name}" for m in alive.values()) or "None"
    dead_list = "\n".join(f"🔴 {d['member'].display_name} ({d['role']})" for d in dead.values()) or "None"
    return discord.Embed(
        title=f"📊 Game Status — Round {round_number}",
        description=f"**Alive Players:**\n{alive_list}\n\n**Fallen Cookies:**\n{dead_list}",
        color=discord.Color.gold()
    )


# ---------------------------
# Countdown updater
# ---------------------------
async def run_countdown_embed(message: discord.Message, base_embed: discord.Embed, duration: int, phase: str):
    remaining = duration
    while remaining > 0:
        base_embed.set_footer(text=f"{phase} — {remaining}s remaining")
        try:
            await message.edit(embed=base_embed)
        except Exception:
            pass
        await asyncio.sleep(10)
        remaining -= 10
    base_embed.set_footer(text=f"{phase} — Time's up!")
    try:
        await message.edit(embed=base_embed)
    except Exception:
        pass


# ---------------------------
# Main simulation
# ---------------------------
async def run_simulation(bot: discord.Client, channel: discord.TextChannel, player_list: List[discord.Member], host: discord.Member):
    if len(player_list) < 5:
        await channel.send("Need at least 5 players to start.")
        return

    players = player_list.copy()
    random.shuffle(players)

    # Assign special roles randomly
    role_map: Dict[int, str] = {}
    for m, role in zip(players[:5], SPECIAL_ROLES):
        role_map[m.id] = role
    for m in players[5:]:
        role_map[m.id] = "Cookie"

    # DM roles
    for m in players:
        role = role_map[m.id]
        try:
            dm = await m.create_dm()
            await dm.send(f"🍪 **Your Role:** {role}\nKeep it secret and follow the rules. . . little cookie. <:SMC_Glare:1429184295179784354>")
        except Exception:
            await channel.send(f"Couldn't DM {m.mention} their role.")

    # Rules embed + wait before start
    rules_embed = discord.Embed(
        title="📜 Hidden Beast — Rules",
        description=(
            "• Do **not** reveal your role.\n"
            "• If you third-impostor, you'll be **blacklisted**.\n"
            "• Fallen cookies cannot chat (their messages will get deleted).\n"
            "• No alliances or info-sharing. **ELSE I WILL BLACKLIST YOU.**\n\n"
            "Winners:\n"
            f"• **Innocents** — {CURRENCY}100 each if Beast is eliminated.\n"
            f"• **Beast** — {CURRENCY}1000 if they survive.\n"
            f"• **Trickster** (Vengeful) — {CURRENCY}1000 if voted out."
        ),
        color=discord.Color.blue()
    )
    await channel.send(embed=rules_embed)
    await asyncio.sleep(10)  # Wait before game actually begins

    alive = {m.id: m for m in players}
    dead: Dict[int, Dict] = {}
    detective_scans: Dict[int, Dict[int, int]] = {}
    round_number = 1

    def living(): return list(alive.values())
    def find_alive(role):
        for i, m in alive.items():
            if role_map[i] == role:
                return m
        return None

    # Persistent on_message listener to delete any messages from dead players immediately
    async def on_msg(msg):
        if msg.author.bot:
            return
        if msg.channel.id != channel.id:
            return
        if msg.author.id in dead:
            try:
                await msg.delete()
            except:
                pass

    bot.add_listener(on_msg, "on_message")

    try:
        # --- Main game loop ---
        while True:
            # Win checks, roles, etc. (same as before)
            beasts = [mid for mid in alive if role_map[mid] == "Beast"]
            innocents = [mid for mid in alive if role_map[mid] != "Beast"]
            if not beasts:
                for mid, m in alive.items():
                    if role_map[mid] != "Beast":
                        await add_balance(mid, 100)
                for d in dead.values():
                    if d["role"] != "Beast":
                        await add_balance(d["member"].id, 100)
                await channel.send(embed=discord.Embed(
                    title="<:PV_Baby:1376949201879175220> Innocents Win!",
                    description=f"The winners have been given {CURRENCY}100 Light of Deceit!",
                    color=discord.Color.yellow()))
                return
            if len(beasts) >= len(innocents):
                for b in beasts:
                    await add_balance(b, 1000)
                await channel.send(embed=discord.Embed(
                    title="<:SMC_motivated:1429184202410033322> Beast Wins!",
                    description=f"The Beast has been given {CURRENCY}1000 Light of Deceit!",
                    color=discord.Color.blue()))
                return

            # === Start new day immediately ===
            await channel.send(embed=discord.Embed(title=f"☀️ Day {round_number}", description="The cookies awaken.", color=discord.Color.orange()))
            await asyncio.sleep(2)

            # Guardian phase
            guardian = find_alive("Guardian")
            protected_id = None
            if guardian:
                await channel.send("The guardian has visited the spire...")
                opts = [m for m in living() if m.id != guardian.id]
                if opts:
                    view = DMSelectView(guardian, opts, "Protect someone")
                    dm = await guardian.create_dm()
                    await dm.send("Choose someone to protect (3 minutes).", view=view)
                    await view.wait()
                    if view.chosen:
                        protected_id = view.chosen
                        await channel.send("The protection was given to one of the lucky cookies!")
                    else:
                        await channel.send("The guardian hasn't chosen... what a waste.")

            # Detective phase
            detective = find_alive("Detective")
            if detective:
                await channel.send("The detective passed by to check the spire...")
                opts = [m for m in living() if m.id != detective.id]
                if opts:
                    detective_scans.setdefault(detective.id, {})
                    view = DMSelectView(detective, opts, "Scan someone")
                    dm = await detective.create_dm()
                    await dm.send("Choose a player to scan (3 minutes).", view=view)
                    await view.wait()
                    if view.chosen:
                        tid = view.chosen
                        count = detective_scans[detective.id].get(tid, 0)
                        if count >= 2:
                            await dm.send("You already scanned them twice!")
                        else:
                            detective_scans[detective.id][tid] = count + 1
                            tr = role_map.get(tid, "Cookie")
                            clue = generate_clue(tr)
                            await dm.send(f"Clue about {alive.get(tid, dead.get(tid, {}).get('member')).display_name}:\n> {clue}")
                            await channel.send("The detective has scanned someone.")
                    else:
                        await channel.send("The detective hasn't scanned anyone.")

            # Medic phase
            medic = find_alive("Healer")
            if medic:
                if round_number == 1:
                    await channel.send("The healer didn't find any fallen cookies... they stayed for safety!")
                else:
                    await channel.send("The healer has graced us with their presence...")
                    if dead:
                        opts = [d["member"] for d in dead.values()]
                        view = DMSelectView(medic, opts, "Revive someone")
                        dm = await medic.create_dm()
                        await dm.send("Choose someone to revive (3 minutes).", view=view)
                        await view.wait()
                        if view.chosen:
                            rid = view.chosen
                            revived = dead[rid]["member"]
                            alive[rid] = revived
                            role_map[rid] = "Cookie"
                            del dead[rid]
                            await channel.send(f"The healer has revived {revived.display_name}! Welcome back!")
                        else:
                            await channel.send("The healer chose no one...")
                    else:
                        await channel.send("No one to revive.")

            # Beast phase
            beast = find_alive("Beast")
            if beast:
                await channel.send("The Beast has immerged...")
                opts = [m for m in living() if m.id != beast.id]
                if opts:
                    view = DMSelectView(beast, opts, "Choose your victim")
                    dm = await beast.create_dm()
                    await dm.send("Choose your victim (3 minutes).", view=view)
                    await view.wait()
                    if view.chosen:
                        vid = view.chosen
                        if protected_id == vid:
                            await channel.send(f"The Beast tried to hunt {alive[vid].display_name}, but the guardian has fended the attack!")
                        else:
                            victim = alive.pop(vid)
                            dead[vid] = {"member": victim, "role": role_map[vid]}
                            await channel.send(f"The beast has hunted down {victim.display_name}...")
                    else:
                        await channel.send("The cookies were spared... for now.")

            # Discussion
            emb = discord.Embed(title="<:chatting:1433000350566055989> Discussion Time", description="Fallen cookies, remain **silent**!", color=discord.Color.blurple())
            msg = await channel.send(embed=emb)
            # persistent on_msg listener will delete messages from dead automatically
            asyncio.create_task(run_countdown_embed(msg, emb, DISCUSSION_DURATION, "Discussion"))
            await asyncio.sleep(DISCUSSION_DURATION)

            # Voting
            await channel.send("🗳️ The time to vote has come...")
            vote_view = VoteView(living(), channel)
            await vote_view.start_scoreboard()
            await vote_view.wait()

            votes = vote_view.votes
            if not votes:
                await channel.send("No votes cast.")
                await channel.send(embed=make_scoreboard_embed(round_number, alive, dead, role_map))
                round_number += 1
                continue

            # Count votes (skip votes are stored as None)
            tally = {}
            for v in votes.values():
                if v is None:
                    continue
                tally[v] = tally.get(v, 0) + 1
            skip_count = sum(1 for v in votes.values() if v is None)

            if not tally and skip_count > 0:
                # Everyone skipped
                await channel.send("Most players chose to skip — no one was eliminated this round.")
                await channel.send(embed=make_scoreboard_embed(round_number, alive, dead, role_map))
                round_number += 1
                continue

            # Determine top non-skip candidate
            max_votes = max(tally.values()) if tally else 0
            # If skip strictly beats the top candidate, no elimination
            if skip_count > max_votes:
                await channel.send("Skip votes outnumbered candidate votes — no one was eliminated this round.")
                await channel.send(embed=make_scoreboard_embed(round_number, alive, dead, role_map))
                round_number += 1
                continue

            # Otherwise pick among top candidates (tie => random)
            top = [k for k, v in tally.items() if v == max_votes]
            eliminated_id = random.choice(top)
            eliminated = alive.pop(eliminated_id)
            role = role_map[eliminated_id]
            dead[eliminated_id] = {"member": eliminated, "role": role}
            await channel.send(embed=discord.Embed(title="⚰️ Elimination", description=f"{eliminated.display_name} was voted out! They were the **{role}**.", color=discord.Color.dark_red()))

            if role == "Trickster":
                await add_balance(eliminated_id, 1000)
                await channel.send(embed=discord.Embed(title="🎭 Trickster Victory", description=f"{eliminated.display_name} was the Trickster and wins {CURRENCY}1000 Light of Deceit!", color=discord.Color.blue()))
                return

            # Immediately show scoreboard and begin next round
            await channel.send(embed=make_scoreboard_embed(round_number, alive, dead, role_map))
            round_number += 1

    finally:
        # Remove persistent listener when game ends / function exits
        try:
            bot.remove_listener(on_msg, "on_message")
        except:
            pass
