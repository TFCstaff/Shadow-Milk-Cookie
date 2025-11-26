import random
import asyncio
import discord
import aiosqlite

DATABASE_PATH = "python-bot/data/economy.db"

class ParticipantStatus:
    def __init__(self, member: discord.Member):
        self.member = member
        self.health = 100
        self.injuries = []
        self.alive = True

# -----------------------------
#        INJURY POOLS
# -----------------------------
LIGHT_INJURIES = [
    "small cut on the cheek",
    "scratched arm",
    "lightly bruised ribs",
    "tiny burn mark",
    "mild rope burn",
    "strained fingers",
    "dust in their eyes",
    "stubbed toe",
    "minor elbow scrape",
    "pulled muscle"
]

MODERATE_INJURIES = [
    "twisted ankle",
    "badly bruised ribs",
    "deep forearm scratch",
    "sprained wrist",
    "bitten hand",
    "shoulder bruise",
    "cut along the thigh",
    "back strain",
    "swollen knee",
    "gashed palm"
]

SEVERE_INJURIES = [
    "shattered knee",
    "deep laceration on the side",
    "broken ribs",
    "dislocated shoulder",
    "major concussion",
    "deep puncture wound",
    "severely twisted leg",
    "fractured arm",
    "large bleeding cut",
    "severe burn on the torso"
]

ALL_INJURIES = [LIGHT_INJURIES, MODERATE_INJURIES, SEVERE_INJURIES]

# ============================================================
#          MESSAGE POOLS — Add as many as you want!
# ============================================================

ATTACK_MESSAGES = [
    "<a:blueexclamation:1432655175360708653> Shadow Milk hums delightfully as {a} ambushes {b}, carving in {dmg} damage.",
    "<a:blueexclamation:1432655175360708653> {a} lunges at {b} — Shadow Milk snickers, enjoying the {dmg} damage dealt.",
    "<a:blueexclamation:1432655175360708653> ‘Oh, how deliciously brutal,’ Shadow Milk whispers as {a} ruthlessly strikes {b} for {dmg}.",
    "<a:blueexclamation:1432655175360708653> {a} charges at {b} with reckless hunger — Shadow Milk applauds the {dmg} damage.",
    "<a:blueexclamation:1432655175360708653> Shadow Milk leans forward, amused, as {a} slams into {b}, inflicting {dmg} damage.",
    "<a:blueexclamation:1432655175360708653> ‘Yes… yes, fight harder,’ Shadow Milk purrs as {a} tears into {b} for {dmg}.",
    "<a:blueexclamation:1432655175360708653> The host watches eagerly as {a} crushes into {b}, leaving them with {dmg} damage.",
    "<a:blueexclamation:1432655175360708653> ‘How disappointing, {b}…’ Shadow Milk chuckles as {a} wounds them for {dmg}.",
    "<a:blueexclamation:1432655175360708653> {a} violently collides with {b} — Shadow Milk’s laughter echoes with the {dmg} damage dealt.",
    "<a:blueexclamation:1432655175360708653> ‘Oh, I *love* this part,’ Shadow Milk murmurs as {a} punishes {b} for {dmg} damage.",
    "<a:blueexclamation:1432655175360708653> {a} traps {b} in a brutal strike — Shadow Milk watches every second of the {dmg} damage.",
    "<a:blueexclamation:1432655175360708653> Shadow Milk twirls his staff lazily as {a} slashes {b} for {dmg}, thoroughly entertained.",
    "<a:blueexclamation:1432655175360708653> ‘Don’t fall yet, {b}…’ Shadow Milk taunts as {a} lands a vicious blow worth {dmg}.",
    "<a:blueexclamation:1432655175360708653> {a} grabs {b} and smashes them down — Shadow Milk smirks at the {dmg} damage caused.",
    "<a:blueexclamation:1432655175360708653> Shadow Milk softly applauds as {a} overwhelms {b} with an attack dealing {dmg} damage."
]


HEAL_MESSAGES = [
    "<:SMC_StaffLove:1355200034328678721> Shadow Milk watches with a soft, mocking smile as {a} tends their wounds, recovering {heal} health.",
    "<:SMC_StaffLove:1355200034328678721> ‘How adorable,’ Shadow Milk murmurs as {a} uses improvised medicine to regain {heal} health.",
    "<:SMC_StaffLove:1355200034328678721> {a} hides beneath a shattered pillar to recover — Shadow Milk allows them {heal} health… for now.",
    "<:SMC_StaffLove:1355200034328678721> Shadow Milk tilts his head, amused, as {a} patches themselves up and restores {heal} health.",
    "<:SMC_StaffLove:1355200034328678721> ‘Don’t crumble yet,’ Shadow Milk whispers as {a} gathers strength and heals {heal} health.",
    "<:SMC_StaffLove:1355200034328678721> Shadow Milk’s cape brushes past {a}, granting them a reluctant {heal} health.",
    "<:SMC_StaffLove:1355200034328678721> {a} steals a moment of peace — Shadow Milk allows the luxury, restoring {heal} health.",
    "<:SMC_StaffLove:1355200034328678721> ‘Mend yourself quickly,’ Shadow Milk sighs as {a} recovers {heal} health.",
    "<:SMC_StaffLove:1355200034328678721> Shadow Milk taps his staff lightly, and {a} feels a strange warmth healing {heal} health.",
    "<:SMC_StaffLove:1355200034328678721> ‘Still fighting, I see…’ Shadow Milk smirks as {a} regenerates {heal} health.",
    "<:SMC_StaffLove:1355200034328678721> {a} wraps their wounds — Shadow Milk looms above, granting them {heal} health with a teasing nod.",
    "<:SMC_StaffLove:1355200034328678721> Shadow Milk’s shadow curls around {a}, mending them for {heal} health.",
    "<:SMC_StaffLove:1355200034328678721> {a} breathes deeply and regains {heal} health under Shadow Milk’s watchful gaze.",
    "<:SMC_StaffLove:1355200034328678721> ‘Pathetic… but persistent,’ Shadow Milk hums as {a} restores {heal} health.",
    "<:SMC_StaffLove:1355200034328678721> A faint, eerie glow surrounds {a} — Shadow Milk’s silent mercy grants them {heal} health."
]

SELF_INJURY_MESSAGES = [
    "<a:swirl:1376843704429445170> Shadow Milk laughs softly as {a} slips on broken debris and earns a {injury}, losing {dmg} health.",
    "<a:swirl:1376843704429445170> {a} fumbles with equipment — Shadow Milk is delighted by the {injury} that costs them {dmg} health.",
    "<a:swirl:1376843704429445170> ‘How pitiful,’ Shadow Milk murmurs as {a} stumbles in the dark and suffers a {injury}.",
    "<a:swirl:1376843704429445170> Shadow Milk watches with amusement as {a} injures themselves with a careless move — {injury}, losing {dmg} HP.",
    "<a:swirl:1376843704429445170> ‘I didn’t even touch you…’ Shadow Milk teases as {a} trips and gains a {injury}, losing {dmg} health.",
    "<a:swirl:1376843704429445170> {a} panics, slips, and ends up with a {injury}. Shadow Milk finds this far funnier than he should.",
    "<a:swirl:1376843704429445170> Shadow Milk snorts softly as {a} walks into danger all by themselves, receiving a {injury} and {dmg} damage.",
    "<a:swirl:1376843704429445170> {a} underestimates the terrain, earning a clumsy {injury}. Shadow Milk calls it ‘entertainment.’",
    "<a:swirl:1376843704429445170> ‘Graceful as ever,’ Shadow Milk mocks as {a} manages to self-inflict a {injury}, losing {dmg} health.",
    "<a:swirl:1376843704429445170> Shadow Milk smirks as {a} bumps into something they *should’ve* seen, resulting in a {injury} (-{dmg} HP).",
    "<a:swirl:1376843704429445170> {a} tries to look tough and instead injures themselves with a {injury}. Shadow Milk applauds their failure.",
    "<a:swirl:1376843704429445170> ‘A tragedy… or a comedy?’ Shadow Milk muses as {a} earns a {injury}, losing {dmg} health.",
    "<a:swirl:1376843704429445170> {a} missteps, twists, and immediately regrets it — {injury}. Shadow Milk finds it ‘deliciously stupid.’",
    "<a:swirl:1376843704429445170> Shadow Milk watches {a} try to recover their balance, only to end up dealing {dmg} to themselves via {injury}.",
    "<a:swirl:1376843704429445170> ‘Oh do continue,’ Shadow Milk purrs as {a} manages to self-sabotage with a {injury}, losing {dmg} health."
]


KILL_MESSAGES = [
    "<:SoulJam:1341385834003169341> Shadow Milk watches with cold interest as {a} collapses from their injuries… their journey ends here.",
    "<:SoulJam:1341385834003169341> ‘How disappointing,’ Shadow Milk murmurs as {a} finally falls to their wounds.",
    "<:SoulJam:1341385834003169341> A low chuckle escapes Shadow Milk as {a} succumbs to their fatal injuries and goes still.",
    "<:SoulJam:1341385834003169341> ‘Another one claimed,’ Shadow Milk whispers as {a} takes their final breath.",
    "<:SoulJam:1341385834003169341> Shadow Milk tilts his head as {a} collapses—‘Pathetic. . . but entertaining.’",
    "<:SoulJam:1341385834003169341> {a} dies where they stand, and Shadow Milk steps over the body without hesitation.",
    "<:SoulJam:1341385834003169341> A dark smile forms as {a} fades… ‘You were never going to survive.’",
    "<:SoulJam:1341385834003169341> ‘Struggle all you like,’ Shadow Milk sighs as {a} finally stops moving.",
    "<:SoulJam:1341385834003169341> {a} falls limp, and Shadow Milk hums softly, as if pleased by the silence.",
    "<:SoulJam:1341385834003169341> With a dismissive glance, Shadow Milk watches {a} meet their end.",
    "<:SoulJam:1341385834003169341> {a} collapses, and Shadow Milk chuckles—‘I barely had to try.’",
    "<:SoulJam:1341385834003169341> ‘Your story ends here,’ Shadow Milk purrs as {a} dies at his feet.",
    "<:SoulJam:1341385834003169341> Shadow Milk kneels beside {a}’s fallen form, whispering, ‘Did you really think you’d win?’",
    "<:SoulJam:1341385834003169341> {a} expires with a weak gasp, and Shadow Milk’s grin widens at the sight.",
    "<:SoulJam:1341385834003169341> ‘How fragile…’ Shadow Milk observes as {a}’s life flickers out."
]


ALLY_MESSAGES = [
    "<:SMCmod:1433000635283935292> Shadow Milk snickers as {a} and {b} reluctantly form an alliance for the {phase}. Trust? Barely.",
    "<:SMCmod:1433000635283935292> ‘Temporary safety,’ Shadow Milk mocks as {a} teams up with {b} for the {phase}.",
    "<:SMCmod:1433000635283935292> Shadow Milk watches with mild amusement as {a} and {b} guard each other's backs through the {phase}.",
    "<:SMCmod:1433000635283935292> ‘How cute,’ he hums as {a} and {b} agree to avoid conflict this {phase}.",
    "<:SMCmod:1433000635283935292> Shadow Milk observes {a} and {b} joining forces for the {phase}, clearly desperate to survive.",
    "<:SMCmod:1433000635283935292> ‘An alliance? How fragile,’ Shadow Milk notes as {a} and {b} stand together in the {phase}.",
    "<:SMCmod:1433000635283935292> {a} and {b} exchange uneasy glances as they unite for the {phase}… Shadow Milk finds it laughable.",
    "<:SMCmod:1433000635283935292> Shadow Milk tilts his head as {a} and {b} whisper plans during the {phase}. ‘They won’t last.’",
    "<:SMCmod:1433000635283935292> {a} and {b} step into a shaky alliance for the {phase}, much to Shadow Milk’s amusement.",
    "<:SMCmod:1433000635283935292> ‘How long until betrayal?’ Shadow Milk muses as {a} and {b} pair up for the {phase}.",
    "<:SMCmod:1433000635283935292> Shadow Milk watches {a} cling to {b} for support during the {phase}. ‘Pathetic cooperation.’",
    "<:SMCmod:1433000635283935292> {a} and {b} huddle together in a tense alliance… Shadow Milk enjoys the tension.",
    "<:SMCmod:1433000635283935292> ‘Survival makes odd companions,’ Shadow Milk remarks as {a} and {b} join forces for the {phase}.",
    "<:SMCmod:1433000635283935292> {a} and {b} unite in the {phase}, and Shadow Milk quietly wonders who will break first.",
    "<:SMCmod:1433000635283935292> Shadow Milk smirks as {a} and {b} forge a fragile pact for the {phase} — doomed from the start."
]


HIDE_MESSAGES = [
    "<:SMC_peek:1365612850344624271> Shadow Milk chuckles as {a} melts into the shadows during the {phase}, hoping danger forgets them.",
    "<:SMC_peek:1365612850344624271> ‘Avoiding conflict, are we?’ Shadow Milk hums as {a} stays low throughout the {phase}.",
    "<:SMC_peek:1365612850344624271> {a} tries to hide quietly during the {phase}… Shadow Milk sees them anyway.",
    "<:SMC_peek:1365612850344624271> Shadow Milk watches {a} vanish from sight, avoiding trouble through the {phase}. Pathetic.",
    "<:SMC_peek:1365612850344624271> {a} thinks they’re unseen during the {phase} — Shadow Milk is simply entertained.",
    "<:SMC_peek:1365612850344624271> Shadow Milk smirks as {a} presses themselves against a wall for the {phase}, trembling slightly.",
    "<:SMC_peek:1365612850344624271> ‘Run, hide, scurry…’ Shadow Milk murmurs as {a} avoids all confrontation this {phase}.",
    "<:SMC_peek:1365612850344624271> {a} curls into the darkest corner they can find during the {phase}. Shadow Milk notes the cowardice.",
    "<:SMC_peek:1365612850344624271> Shadow Milk peers into the shadows where {a} hides for the {phase}… and lets them live.",
    "<:SMC_peek:1365612850344624271> {a} slips beneath a broken structure, hiding through the {phase}. Shadow Milk pretends not to see.",
    "<:SMC_peek:1365612850344624271> ‘Again with the hiding,’ Shadow Milk sighs as {a} avoids danger for the entire {phase}.",
    "<:SMC_peek:1365612850344624271> {a} shields themselves behind debris during the {phase}. Shadow Milk watches like it’s entertainment.",
    "<:SMC_peek:1365612850344624271> Shadow Milk’s eyes glow faintly as he notices {a} lurking quietly during the {phase}.",
    "<:SMC_peek:1365612850344624271> {a} scrambles into a shadowy nook for the {phase}. Shadow Milk wonders how long they can stay quiet.",
    "<:SMC_peek:1365612850344624271> Shadow Milk hums in amusement while {a} hides desperately through the {phase}, hoping to be ignored."
]


# -----------------------------
#       MAIN SIMULATION
# -----------------------------
async def run_massacre_simulation(channel, participants):
    statuses = {p.id: ParticipantStatus(p) for p in participants}
    survivors = list(statuses.values())
    max_days = 30
    day = 1

    while len([p for p in survivors if p.alive]) > 1 and day <= max_days:
        # ---- DAY PHASE ----
        await announce_phase(channel, f"☀️ Day {day} in the Spire — The Massacre Continues")

        if random.random() < 0.10:
            # Replace entire day with special event
            await trigger_special_event(channel, survivors)
        else:
            await run_regular_events(channel, survivors, phase="day")

        await show_scoreboard(channel, survivors, day, "Day")
        if len([p for p in survivors if p.alive]) <= 1:
            break

        await channel.send("<:chatting:1433000350566055989> Survivors may now discuss for **30 seconds**...")
        await asyncio.sleep(30)

        # ---- NIGHT PHASE ----
        if len([p for p in survivors if p.alive]) <= 1:
            break

        await announce_phase(channel, f"🌙 Night {day} in the Spire — The Shadows Whisper")

        if random.random() < 0.10:
            # Replace entire night with special event
            await trigger_special_event(channel, survivors)
        else:
            await run_regular_events(channel, survivors, phase="night")

        await show_scoreboard(channel, survivors, day, "Night")
        if len([p for p in survivors if p.alive]) <= 1:
            break

        await channel.send("<:chatting:1433000350566055989> The survivors whisper in fear... you have **30 seconds** to talk before dawn.")
        await asyncio.sleep(30)

        day += 1

    final_survivors = [p for p in survivors if p.alive]
    if final_survivors:
        winner = final_survivors[0]
    else:
        winner = max(survivors, key=lambda p: p.health)

    await announce_winner(channel, winner)
    
async def announce_phase(channel, title): 
    embed = discord.Embed(
        title=title,                   
        description="The air thickens with tension...", 
        color=0x0082e4
    ) 
    await channel.send(embed=embed) 
    await asyncio.sleep(2)
    
    
# -----------------------------
#        REGULAR EVENTS
# -----------------------------
async def run_regular_events(channel, survivors, phase="day"):
    alive = [p for p in survivors if p.alive]
    random.shuffle(alive)

    for actor in alive:
        if not actor.alive:
            continue

        await asyncio.sleep(2)
        roll = random.random()
        potential_targets = [x for x in alive if x != actor and x.alive]

        # ----- ATTACK EVENT -----
        if roll < 0.35 and potential_targets:
            target = random.choice(potential_targets)
            dmg = random.randint(15, 40) if phase == "day" else random.randint(25, 50)
            target.health -= dmg

            msg = random.choice(ATTACK_MESSAGES).format(
                a=actor.member.display_name,
                b=target.member.display_name,
                dmg=dmg
            )
            await channel.send(msg)

            # DM target
            try:
                await target.member.send(
                    f"You were attacked by {actor.member.display_name}! You lost {dmg} health. Current health: {max(target.health, 0)}"
                )
            except:
                pass

            if target.health <= 0:
                target.alive = False
                msg = random.choice(KILL_MESSAGES).format(a=target.member.display_name)
                await channel.send(msg)

        # ----- HEAL EVENT -----
        elif roll < 0.45:
            heal = random.randint(10, 25)
            actor.health = min(actor.health + heal, 100)

            msg = random.choice(HEAL_MESSAGES).format(
                a=actor.member.display_name,
                heal=heal
            )
            await channel.send(msg)

        # ----- SELF-INJURY EVENT -----
        elif roll < 0.65:
            dmg = random.randint(5, 15)
            actor.health -= dmg
            injury = random.choice(["scratched arm", "twisted ankle", "bruised ribs", "sprained wrist", "bitten hand"])
            actor.injuries.append(injury)

            if actor.health <= 0:
                actor.alive = False
                msg = random.choice(KILL_MESSAGES).format(a=actor.member.display_name)
                await channel.send(msg)
            else:
                msg = random.choice(SELF_INJURY_MESSAGES).format(
                    a=actor.member.display_name,
                    injury=injury,
                    dmg=dmg
                )
                await channel.send(msg)

        # ----- ALLIANCE EVENT -----
        elif roll < 0.65 and potential_targets:
            partner = random.choice(potential_targets)
            msg = random.choice(ALLY_MESSAGES).format(
                a=actor.member.display_name,
                b=partner.member.display_name,
                phase=phase
            )
            await channel.send(msg)

        # ----- HIDING EVENT -----
        else:
            msg = random.choice(HIDE_MESSAGES).format(
                a=actor.member.display_name,
                phase=phase
            )
            await channel.send(msg)



# -----------------------------
#       SPECIAL EVENTS
# -----------------------------

async def trigger_special_event(channel, alive_participants):
    alive_only = [p for p in alive_participants if p.alive]
    if not alive_only:
        return

    event_type = random.choice([
        "halloween_night",
        "blood_rain",
        "mad_feast",
        "shadow_storm",
        "void_reckoning"
    ])
    affected = alive_only

    # --- Send intro embed once ---
    if event_type == "halloween_night":
        embed = discord.Embed(
            title="🎃 Halloween Night — Shadow Milk’s Horror!",
            description="The arena twists into a nightmare of shrieks and laughter. The shadows awaken...",
            color=0xFF6600
        )
        await channel.send(embed=embed)

    elif event_type == "blood_rain":
        embed = discord.Embed(
            title="🌧️ Blood Rain!",
            description="A crimson storm pours over the spire — sticky, burning, alive...",
            color=0x990000
        )
        await channel.send(embed=embed)

    elif event_type == "mad_feast":
        embed = discord.Embed(
            title="🍖 Mad Feast!",
            description="Shadow Milk lures the survivors to a cursed banquet. Few will leave unscathed...",
            color=0xFF3300
        )
        await channel.send(embed=embed)

    elif event_type == "shadow_storm":
        embed = discord.Embed(
            title="🌪️ Shadow Storm!",
            description="Dark winds tear through the spire — screams vanish in the storm’s howl.",
            color=0x222244
        )
        await channel.send(embed=embed)

    elif event_type == "void_reckoning":
        embed = discord.Embed(
            title="⚫ The Void Reckoning!",
            description="The ground cracks open to nothingness. The void calls for sacrifices...",
            color=0x000000
        )
        await channel.send(embed=embed)

    # --- Helper for HP changes ---
    def apply_damage(p, amount):
        p.health = max(p.health - amount, 0)
        if p.health <= 0:
            p.alive = False


    # --- Apply effects to each player ---
    for p in affected:
        selected_message = None

        if event_type == "halloween_night":

            # Damage or heal ranges
            dmg = random.randint(10, 30)
            heal = random.randint(10, 30)

            # Death messages
            death_msgs = [
                f"🎃 {p.member.display_name} wandered too deep into the laughing shadows… Shadow Milk whispered *hush*, and they vanished.",
                f"<a:SMCfire:1433000197340008510> {p.member.display_name} got embraced by an elongated shadow figure… its grin was the last thing they saw.",
                f"<:Beacon:1434580085779857470> {p.member.display_name} opened a cursed beacon of light. Shadows poured out and swallowed them whole.",
                f"<a:Ghosty:1433000809196552262> {p.member.display_name} was caught by a ghost laughing in Shadow Milk's voice… their life drained instantly.",
                f"🎭 {p.member.display_name} tried to run, but the blue strings puppeteered their dough into silence."
            ]

            # Survival - damage
            dmg_msgs = [
                f"👁️‍🗨️ {p.member.display_name} felt a shadow claw scrape their back—Shadow Milk snickered—losing {dmg} health.",
                f"🦇 {p.member.display_name} ran past a swarm of shadow bats, losing {dmg} health.",
                f"🎃 {p.member.display_name} dodged a shadow trap—barely. Shadow Milk applauded mockingly. Lost {dmg}.",
                f"🩸 {p.member.display_name} tripped over a cursed pumpkin and got scratched by creeping roots, losing {dmg} health.",
                f"😨 {p.member.display_name} felt something breathe behind them. They escaped—barely. Lost {dmg}."
            ]

            # Survival - heal
            heal_msgs = [
                f"🎃 {p.member.display_name} found a quiet corner where the shadows purred around them. Shadow Milk granted {heal} health.",
                f"🕯️ {p.member.display_name} uncovered a blessed candle—its warmth restored {heal} health.",
                f"👻 Shadow Milk took pity on {p.member.display_name} for being amusingly terrified. Granted {heal} health.",
                f"🦇 {p.member.display_name} was carried to safety by friendly shadow bats, gaining {heal} health.",
                f"🎭 Shadow Milk flicked their forehead affectionately, restoring {heal} health."
            ]

            apply_damage(p, dmg)
            if not p.alive:
                selected_message = random.choice(death_msgs)
            else:
                # 50/50 random choice between heal or dmg message
                if random.choice([True, False]):
                    selected_message = random.choice(dmg_msgs)
                else:
                    p.health = min(p.health + heal, 100)
                    selected_message = random.choice(heal_msgs)

        elif event_type == "blood_rain":
            
            dmg = random.randint(10, 30)
            heal = random.randint(10, 30)

            death_msgs = [
                f"🩸 {p.member.display_name} melted under the acidic jam as Shadow Milk whispered 'Pathetic.'",
                f"{p.member.display_name} tried to hide—Shadow Milk dragged them back into the rain personally.",
                f"☠️ {p.member.display_name} slipped in the jam flood and drowned in its burning sweetness.",
                f"🔪 A jam-coated hand grabbed {p.member.display_name} from below… and pulled them under.",
                f"🌧️ {p.member.display_name} begged for shelter—Shadow Milk rolled his eyes and let the rain finish them."
            ]

            dmg_msgs = [
                f"☂️ {p.member.display_name} found half a roof, but the jam burned through it, costing {dmg} health.",
                f"🩸 The jam singed {p.member.display_name}'s skin—Shadow Milk laughed—losing {dmg} health.",
                f"{p.member.display_name} stumbled through the storm, losing {dmg} health.",
                f"🌧️ A jam surge slammed into {p.member.display_name}, costing {dmg} health.",
                f"🧱 {p.member.display_name} hid behind a wall, only for it to dissolve. Lost {dmg}."
            ]

            heal_msgs = [
                f"🌧️ Shadow Milk shielded {p.member.display_name} with his wings—for his own amusement. Gained {heal} health.",
                f"☂️ {p.member.display_name} found a blessed umbrella, restoring {heal} health.",
                f"🍬 A sweet drop landed perfectly on {p.member.display_name}, healing {heal}.",
                f"{p.member.display_name} found dry ground—Shadow Milk allowed them a moment of peace. +{heal}.",
                f"🩹 Shadow Milk patched up {p.member.display_name} with jam-soaked bandages, healing {heal}."
            ]

            apply_damage(p, dmg)
            if not p.alive:
                selected_message = random.choice(death_msgs)
            else:
                if random.choice([True, False]):
                    selected_message = random.choice(dmg_msgs)
                else:
                    p.health = min(p.health + heal, 100)
                    selected_message = random.choice(heal_msgs)

        elif event_type == "mad_feast":

            dmg = random.randint(10, 30)
            heal = random.randint(10, 30)

            death_msgs = [
                f"🍗 {p.member.display_name} ate something wriggling… Shadow Milk watched in delight as they collapsed.",
                f"{p.member.display_name} swallowed a cursed grape and instantly perished.",
                f"🔥 Shadow Milk snapped his fingers—{p.member.display_name}'s plate exploded.",
                f"🍽️ {p.member.display_name} choked on a living sausage that wrapped around their throat.",
                f"🍷 {p.member.display_name} drank the wrong wine… their soul was consumed."
            ]

            dmg_msgs = [
                f"🍖 {p.member.display_name} tasted a spicy cursed dish—lost {dmg} health.",
                f"🥄 A flying spoon attacked {p.member.display_name}, costing {dmg} health.",
                f"🍽️ The feast table tried to bite {p.member.display_name}, losing {dmg} health.",
                f"🩸 {p.member.display_name} bit into a spiked pastry—lost {dmg}.",
                f"🤢 {p.member.display_name} felt sick from a cursed snack, losing {dmg}."
            ]

            heal_msgs = [
                f"🍰 {p.member.display_name} found a harmless dessert—Shadow Milk looked offended. +{heal}.",
                f"🍷 Shadow Milk poured {p.member.display_name} a safe drink (rare). +{heal}.",
                f"🍇 {p.member.display_name} picked a blessed fruit, gaining {heal} health.",
                f"🍞 A warm loaf revived {p.member.display_name}, healing {heal}.",
                f"🍯 Sweet enchanted honey restored {heal} health to {p.member.display_name}."
            ]

            apply_damage(p, dmg)
            if not p.alive:
                selected_message = random.choice(death_msgs)
            else:
                if random.choice([True, False]):
                    selected_message = random.choice(dmg_msgs)
                else:
                    p.health = min(p.health + heal, 100)
                    selected_message = random.choice(heal_msgs)
        
        elif event_type == "shadow_storm":

            dmg = random.randint(10, 30)
            heal = random.randint(10, 30)

            death_msgs = [
                f"🌑 {p.member.display_name} was lifted into the storm—Shadow Milk waved goodbye.",
                f"{p.member.display_name} clung to debris, but the shadows peeled them away.",
                f"❌ A shadow tornado shredded {p.member.display_name}.",
                f"💨 {p.member.display_name} was blown into the abyss.",
                f"🌪️ The winds whispered {p.member.display_name}'s name… and took them."
            ]

            dmg_msgs = [
                f"💨 {p.member.display_name} was slammed into a wall by the wind, losing {dmg}.",
                f"🌪️ Shadows clawed at {p.member.display_name}, costing {dmg} health.",
                f"🌀 A flying crate hit {p.member.display_name}, losing {dmg}.",
                f"🌫️ Dust blinded {p.member.display_name}, injuring them for {dmg}.",
                f"🌪️ A whirlpool of shadows dragged {p.member.display_name}, losing {dmg}."
            ]

            heal_msgs = [
                f"🌫️ Shadow Milk shielded {p.member.display_name} with his cape. +{heal}.",
                f"💨 A gentle pocket of calm restored {heal} health to {p.member.display_name}.",
                f"🌪️ A whisper of mercy from Shadow Milk healed {heal}.",
                f"{p.member.display_name} found a magical shelter, gaining {heal} health.",
                f"🖤 Shadow winds stitched {p.member.display_name}'s wounds, granting {heal}."
            ]

            apply_damage(p, dmg)
            if not p.alive:
                selected_message = random.choice(death_msgs)
            else:
                if random.choice([True, False]):
                    selected_message = random.choice(dmg_msgs)
                else:
                    p.health = min(p.health + heal, 100)
                    selected_message = random.choice(heal_msgs)

        elif event_type == "void_reckoning":

            dmg = random.randint(10, 30)
            heal = random.randint(10, 30)

            death_msgs = [
                f"🕳️ {p.member.display_name} was pulled screaming into the void.",
                f"{p.member.display_name} stared too long into the abyss… and it claimed them.",
                f"⚫ A black tendril dragged {p.member.display_name} downward.",
                f"🚫 The void swallowed {p.member.display_name} without hesitation.",
                f"📉 {p.member.display_name}'s existence flickered… then vanished."
            ]

            dmg_msgs = [
                f"⚫ The void tugged at {p.member.display_name}'s soul, costing {dmg} health.",
                f"{p.member.display_name} resisted the pull, but shadows tore at them. Lost {dmg}.",
                f"🕳️ Reality bent around {p.member.display_name}, injuring them for {dmg}.",
                f"😨 {p.member.display_name} nearly fell in, losing {dmg}.",
                f"⚠️ A rift snapped shut on {p.member.display_name}, causing {dmg} damage."
            ]

            heal_msgs = [
                f"🖤 Shadow Milk grasped {p.member.display_name}'s hand, pulling them back and healing {heal}.",
                f"{p.member.display_name} found stability in the darkness—gaining {heal}.",
                f"🕳️ A gentle void breeze mended {p.member.display_name}'s wounds. +{heal}.",
                f"⚫ Shadow Milk placed a calming hand on {p.member.display_name}'s shoulder, healing {heal}.",
                f"{p.member.display_name} stepped away from the void and felt relief restore {heal} health."
            ]

            apply_damage(p, dmg)
            if not p.alive:
                selected_message = random.choice(death_msgs)
            else:
                if random.choice([True, False]):
                    selected_message = random.choice(dmg_msgs)
                else:
                    p.health = min(p.health + heal, 100)
                    selected_message = random.choice(heal_msgs)

        if selected_message:
            await channel.send(selected_message)
            await asyncio.sleep(3)

async def announce_winner(channel, winner):
    """Announce and reward the winner"""
    embed = discord.Embed(
        title="<a:Fount_crown:1422991318296166430> A Winner Emerges",
        description=f"**{winner.member.display_name}** survives the Massacre! Shadow Milk applauds your cunning. "
                    f"You are awarded **10,000 <:LoD:1411031656055177276> Light of Deceit!**",
        color=0x0082e4
    )
    await channel.send(embed=embed)

    # Reward 10,000 LoD to winner
    try:
        async with aiosqlite.connect(DATABASE_PATH) as db:
            await db.execute("INSERT OR IGNORE INTO users (user_id, balance) VALUES (?, 0)", (winner.member.id,))
            await db.execute("UPDATE users SET balance = balance + 10000 WHERE user_id = ?", (winner.member.id,))
            await db.commit()
    except Exception as e:
        await channel.send(f"⚠️ Could not update {winner.member.display_name}'s balance: {e}")

    try:
        await winner.member.send(
            "<a:Fount_crown:1422991318296166430> Congratulations! You survived the Massacre.\n"
            "Shadow Milk acknowledges your cunning and grants you **10,000 <:LoD:1411031656055177276> Light of Deceit!**"
        )
    except:
        pass


async def show_scoreboard(channel, survivors, day, phase):
    embed = discord.Embed(
        title=f"<a:FLOATING_HEART:1435956991838130227> Health Board — {phase} {day}",
        color=0x0082e4
    )
    for p in survivors:
        status = "<a:DEAD:1435957173396963421> Dead" if not p.alive else f"{p.health} <a:HP:1435957197610811432>"
        embed.add_field(name=p.member.display_name, value=status, inline=True)
    await channel.send(embed=embed)
