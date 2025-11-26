import random

RARITY_POOLS = {
    "Common": [
        "GingerBrave", 
        "Beet Cookie", 
        "Strawberry Cookie", 
        "Ninja Cookie", 
        "Angel Cookie", 
        "Wizard Cookie", 
        "Muscle Cookie"
    ],
    "Rare": [
        "Devil Cookie", "Custard Cookie III", "Clover Cookie", "Carrot Cookie", "Avocado Cookie", "Pancake Cookie", "Onion Cookie", 
        "Gumball Cookie", "Blackberry Cookie", "Adventurer Cookie", "Alchemist Cookie", "Cherry Cookie", "Knight Cookie", "Princess Cookie"
    ],
    "Epic": [
        "Salt Cellar Cookie", "Charcoal Cookie", "Menthol Cookie", "Seltzer Cookie", "GrapeFruit Cookie", "Lime Cookie",
        "Manju Cookie", "Jagae Cookie", "Orange Cookie", "Lemon Cookie", "Cream Soda Cookie", "Sugarfly Cookie",
        "Pavlova Cookie", "Agar Agar Cookie", "Wedding Cake Cookie", "Black Forest Cookie", "Black Sapphire Cookie",
        "Candy Apple Cookie", "Cloud Haetae Cookie", "Okchun Cookie", "Green Tea Mousse Cookie", "Pudding a la Mode Cookie",
        "Choco Drizzle Cookie", "Red Osmanthus Cookie", "Golden Osmanthus Cookie", "Smoked Cheese Cookie", "Star Coral Cookie",
        "Nutmeg Tiger Cookie", "Peach Blossom Cookie", "Street Urachin Cookie", "Caramel Choux Cookie", "Silverbell Cookie",
        "Mercurial Knight Cookie", "Rebel Cookie", "Creme Brulee Cookie", "Linzer Cookie", "Olive Cookie", "Mozzarela Cookie",
        "Fettuccine Cookie", "Burnt Cheese Cookie", "Frilled Jellyfish Cookie", "Peppermint Cookie", "Black Lemonade Cookie",
        "Rockstar Cookie", "Tarte Tatin Cookie", "Royal Margarine Cookie", "Kouign-Amann Cookie", "Prune Juice Cookie",
        "Space Doughnut", "Blueberry Pie Cookie", "Prophet Cookie", "Milkyway Cookie", "Pinecone Cookie", "Carol Cookie", 
        "Macaron Cookie", "Schwarzwalder", "Candy Diver Cookie", "Captain Cavier Cookie", "Cream Unicorn Cookie",
        "Financier Cookie", "Crunchy Chip Cookie", "Wildberry Cookie", "Cherry Blossom Cookie", "Caramel Arrow Cookie",
        "Affogato Cookie", "Tea Knight Cookie", "Eclair Cookie", "Cocoa Cookie", "Cotton Cookie", "Pumpkin Pie Cookie",
        "Twizzly Gummy Cookie", "Mala Sauce Cookie", "Moon Rabbit Cookie", "Raspberry Cookie", "Sorbet Shark Cookie",
        "Parfait Cookie", "Squid Ink Cookie", "Lilac Cookie", "Mango Cookie", "Red Velvet Cookie", "Pastry Cookie",
        "Strawberry Crepe Cookie", "Pig Cookie", "Black Raisin Cookie", "Almond Cookie", "Cream Puff Cookie",
        "Latte Cookie", "Kumiho Cookie", "Rye Cookie", "Espresso Cookie", "Madeleine Cookie", "Milk Cookie",
        "Licorice Cookie", "Poison Mushroom Cookie", "Pomegranate Cookie", "Purple Yam Cookie", "Herb Cookie",
        "Chilli Pepper Cookie", "Sparkling Cookie", "Dark Choco Cookie", "Mint Choco Cookie", "Werewolf Cookie",
        "Tiger Lily Cookie", "Vampire Cookie", "Snow Sugar Cookie", "Matcha Cookie", "Kumiho Cookie"
    ],
    "SuperEpic": [
        "Doughael Cookie", "Elder Faerie Cookie", "Camellia Cookie", "Crimson Coral Cookie", "Shining Glitter Cookie",
        "Capsaicin Cookie", "Stardust Cookie", "Sherbet Cookie", "Oyster Cookie", "Clotted Cream Cookie"
    ],
    "Legendary": [
        "Frost Queen Cookie", "Sea Fairy Cookie", "Black Pearl Cookie", "Moonlight Cookie", "Wind Archer Cookie", 
        "Fire Spirit Cookie", "Stormbringer Cookie"
    ],
    "Dragon": [
        "Pitaya Dragon Cookie"
    ],
    "Ancient": [
        "Pure Vanilla Cookie", 
        "Hollyberry Cookie", 
        "Dark Cacao Cookie", 
        "Golden Cheese Cookie", 
        "White Lily Cookie"
    ],
    "Awakened": [
        "Awakened Pure Vanilla Cookie", 
        "Awakened Hollyberry Cookie", 
        "Awakened Golden Cheese Cookie", 
        "Awakened Dark Cacao Cookie",        
        "Awakened White Lily Cookie"
    ],
    "Beast": [
        "Shadow Milk Cookie", 
        "Eternal Sugar Cookie", 
        "Mystic Flour Cookie", 
        "Burning Spice Cookie", 
        "Silent Salt Cookie"
    ]
}

RARITY_WEIGHTS = {
    "Common": 55,
    "Rare": 25,
    "Epic": 15,
    "SuperEpic": 5,
    "Legendary": 3,
    "Dragon": 2,
    "Ancient": 1,
    "Awakened": 1,
    "Beast": 1
}

RARITY_COLORS = {
    "Common": 0xB0B0B0,      # brown
    "Rare": 0x4DB8FF,        # blue
    "Epic": 0xA64DFF,        # purple
    "SuperEpic": 0x4B0082,   # dark purple
    "Legendary": 0xFFD700,   # idk what color
    "Dragon": 0xFF0000,      # red
    "Ancient": 0xFF4500,     # forgot color
    "Awakened": 0xFF4500,    # forgotten color
    "Beast": 0xFF0000        # red
}

# Placeholder emoji map for later customization
COOKIE_EMOJIS = {
    "GingerBrave": "<:gingerbrave:1435318345074216980>",
    "Muscle Cookie": "<:musclecookie:1435318370000965743>",
    "Strawberry Cookie": "<:strawberrycookie:1435318405560406036>",
    "Wizard Cookie": "<:wizardcookie:1435318422719303710>",
    "Ninja Cookie": "<:ninjacookie:1435318387419906138>",
    "Beet Cookie": "<:beetcookie:1435318439278411786>",
    "Angel Cookie": "<:angelcookie:1435318454944141423>",
    "Custard Cookie III": "<:Soulstone_custard_iii:1435320323951169618>",
    "Princess Cookie": "<:Soulstone_princess:1435320417589133512>",
    "Knight Cookie": "<:Soulstone_knight:1435320370252218388>",
    "Avocado Cookie": "<:Soulstone_avocado:1435320212353319084>",
    "Adventurer Cookie": "<:Soulstone_adventurer:1435320171907645581>",
    "Clover Cookie": "<:Soulstone_clover:1435320308193296496>", 
    "Carrot Cookie": "<:Soulstone_carrot:1435320244913832166>",
    "Pancake Cookie": "<:Soulstone_pancake:1435320402992955393>",
    "Onion Cookie": "<:Soulstone_onion:1435320387947855984>",
    "Blackberry Cookie": "<:Soulstone_blackberry:1435320227897282733>",
    "Devil Cookie": "<:Soulstone_devil:1435320338354409646>",
    "Gumball Cookie": "<:Soulstone_gumball:1435320354770780251>",
    "Alchemist Cookie": "<:Soulstone_alchemist:1435320194837774346>", 
    "Cherry Cookie": "<:Soulstone_cherry:1435320294486315048>",
    "Salt Cellar Cookie": "<:Soulstone_salt_cellar:1435323805584330834>", 
    "Charcoal Cookie": "<:Soulstone_charcoal:1435323861523497000>", 
    "Menthol Cookie": "<:Soulstone_menthol:1435323844935286915>", 
    "Seltzer Cookie": "<:Soulstone_seltzer:1435323822352892025>", 
    "GrapeFruit Cookie": "<:Soulstone_grapefruit:1435323932541583511>", 
    "Lime Cookie": "<:Soulstone_lime:1435323878254579712>",
    "Manju Cookie": "<:Soulstone_manju:1435325017968738446>", 
    "Jagae Cookie": "<:Soulstone_jagae:1435325089817296976>", 
    "Orange Cookie": "<:Soulstone_orange:1435325044418154568>", 
    "Lemon Cookie": "<:Soulstone_lemon:1435325001523003512>", 
    "Cream Soda Cookie": "<:Soulstone_cream_soda:1435325070900727829>", 
    "Sugarfly Cookie": "<:Soulstone_sugarfly:1435325110918840505>",
    "Pavlova Cookie": "<:Soulstone_pavlova:1435326391469084743>", 
    "Agar Agar Cookie": "<:Soulstone_agar_agar:1435326320056733736>", 
    "Wedding Cake Cookie": "<:Soulstone_wedding_cake:1435326303170596864>", 
    "Black Forest Cookie": "<:Soulstone_black_forest:1435326237143990355>", 
    "Black Sapphire Cookie": "<:Soulstone_black_sapphire:1435326253254053939>", 
    "Candy Apple Cookie": "<:Soulstone_candy_apple:1435326274431225857>",
    "Cloud Haetae Cookie": "<:Soulstone_cloud_haetae:1435327354057527428>", 
    "Okchun Cookie": "<:Soulstone_okchun:1435327625563209800>",
    "Green Tea Mousse Cookie": "<:Soulstone_green_tea_mousse:1435327382637645895>", 
    "Pudding a la Mode Cookie": "<:Soulstone_pudding_3F_la_mode:1435327451285815317>",
    "Choco Drizzle Cookie": "<:Soulstone_choco_drizzle:1438787548439646371>", 
    "Red Osmanthus Cookie": "<:Soulstone_red_osmanthus:1438787597056082082>", 
    "Golden Osmanthus Cookie": "<:Soulstone_golden_osmanthus:1438787571353387109>", 
    "Smoked Cheese Cookie": "<:Soulstone_smoked_cheese:1438787849053933648>", 
    "Star Coral Cookie": "<:Soulstone_star_coral:1438788034542698516>",
    "Nutmeg Tiger Cookie": "<:Soulstone_nutmeg_tiger:1438787877335994400>", 
    "Peach Blossom Cookie": "<:Soulstone_peach_blossom:1438789560095215676>", 
    "Street Urachin Cookie": "<:Soulstone_street_urchin:1438789945866063934>", 
    "Caramel Choux Cookie": "<:Soulstone_caramel_choux:1438789892250402948>", 
    "Silverbell Cookie": "<:Soulstone_silverbell:1438789982520217610>",
    "Mercurial Knight Cookie": "<:Soulstone_mercurial_knight:1438790801886023863>", 
    "Rebel Cookie": "<:Soulstone_rebel:1438790878918610964>", 
    "Creme Brulee Cookie": "<:Soulstone_creme_brulee:1438790845980479600>", 
    "Linzer Cookie": "<:Soulstone_linzer:1438790825365737653>", 
    "Olive Cookie": "<:Soulstone_olive:1438790971553747014>", 
    "Mozzarela Cookie": "<:Soulstone_mozzarella:1438792918847590442>",
    "Matcha Cookie": "<:Soulstone_matcha:1438826654259609640>",
    "Fettuccine Cookie": "<:Soulstone_fettuccine:1439653554343379157>", 
    "Burnt Cheese Cookie": "<:Soulstone_burnt_cheese:1439651490309476392>", 
    "Frilled Jellyfish Cookie": "<:Soulstone_frilled_jellyfish:1439653602791784538>", 
    "Peppermint Cookie": "<:Soulstone_peppermint:1439653733192695818>", 
    "Black Lemonade Cookie": "<:Soulstone_black_lemonade:1439651449578717348>",
    "Rockstar Cookie": "<:Soulstone_rockstar:1439653861697655037>", 
    "Tarte Tatin Cookie": "<:Soulstone_tarte_tatin:1439653983802101862>", 
    "Royal Margarine Cookie": "<:Soulstone_royal_margarine:1439653884921643089>", 
    "Kouign-Amann Cookie": "<:Soulstone_kouignamann:1439653648211906790>", 
    "Prune Juice Cookie": "<:Soulstone_prune_juice:1439653809675698186>",
    "Space Doughnut": "<:Soulstone_space_doughnut:1439653958061916181>", 
    "Blueberry Pie Cookie": "<:Soulstone_blueberry_pie:1439651469551992833>", 
    "Prophet Cookie": "<:Soulstone_prophet:1439653783893446737>", 
    "Milkyway Cookie": "<:Soulstone_milky_way:1439653704063123557>", 
    "Pinecone Cookie": "<:Soulstone_pinecone:1439653757595029504>", 
    "Carol Cookie": "<:Soulstone_carol:1439653372616769676>", 
    "Macaron Cookie": "<:Soulstone_macaron:1439653677408194732>", 
    "Schwarzwalder": "<:Soulstone_schwarzwalder:1439653919037980672>", 
    "Candy Diver Cookie": "<:Soulstone_candy_diver:1439651511159361577>", 
    "Captain Cavier Cookie": "<:Soulstone_captain_caviar:1439651534639075538>", 
    "Cream Unicorn Cookie": "<:Soulstone_cream_unicorn:1439653483170103529>",    
    "Financier Cookie": "<:Soulstone_financier:1439653578498244790>", 
    "Crunchy Chip Cookie": "<:Soulstone_crunchy_chip:1439653507065188445>", 
    "Wildberry Cookie": "<:Soulstone_wildberry:1439654036528959708>", 
    "Cherry Blossom Cookie": "<:Soulstone_cherry_blossom:1439653400001380362>", 
    "Caramel Arrow Cookie": "<:Soulstone_caramel_arrow:1439651557745623185>",
    "Affogato Cookie": "<:Soulstone_affogato:1439651428250681404>", 
    "Tea Knight Cookie": "<:Soulstone_tea_knight:1439654010910015638>", 
    "Eclair Cookie": "<:Soulstone_eclair:1439653535129276447>", 
    "Cocoa Cookie": "<:Soulstone_cocoa:1439653422185058457>", 
    "Cotton Cookie": "<:Soulstone_cotton:1439653455177318513>", 
    "Pumpkin Pie Cookie": "<:Soulstone_pumpkin_pie:1439653831691599894>",
    "Twizzly Gummy Cookie": "<:Soulstone_twizzly_gummy:1439657151457923314>", 
    "Mala Sauce Cookie": "<:Soulstone_mala_sauce:1439656901347639488>", 
    "Moon Rabbit Cookie": "<:Soulstone_moon_rabbit:1439656947950292993>", 
    "Raspberry Cookie": "<:Soulstone_raspberry:1439657015587770378>", 
    "Sorbet Shark Cookie": "<:Soulstone_sorbet_shark:1439657072475115726>",
    "Parfait Cookie": "<:Soulstone_parfait:1439656972080382074>", 
    "Squid Ink Cookie": "<:Soulstone_squid_ink:1439657101495631972>", 
    "Lilac Cookie": "<:Soulstone_lilac:1439656877276266690>", 
    "Mango Cookie": "<:Soulstone_mango:1439656923426459809>", 
    "Red Velvet Cookie": "<:Soulstone_red_velvet:1439657043601395763>", 
    "Pastry Cookie": "<:Soulstone_pastry:1439656993219678308>",
    "Strawberry Crepe Cookie": "<:Soulstone_strawberry_crepe:1439657126627774636>", 
    "Pig Cookie": "<:Soulstone_fig:1439656800134889492>", 
    "Black Raisin Cookie": "<:Soulstone_black_raisin:1439656756908392619>", 
    "Almond Cookie": "<:Soulstone_almond:1439656737580781578>", 
    "Cream Puff Cookie": "<:Soulstone_cream_puff:1439656776218837128>",
    "Latte Cookie": "<:Soulstone_latte:1439656852001652887>", 
    "Kumiho Cookie": "<:Soulstone_kumiho:1439656829188706435>", 
    "Rye Cookie": "<:Soulstone_rye:1439659600306634812>", 
    "Espresso Cookie": "<:Soulstone_espresso:1439659346437865645>", 
    "Madeleine Cookie": "<:Soulstone_madeleine:1439659439195029545>", 
    "Milk Cookie": "<:Soulstone_milk:1439659460305096876>",
    "Licorice Cookie": "<:Soulstone_licorice:1439659414608019547>", 
    "Poison Mushroom Cookie": "<:Soulstone_poison_mushroom:1439659530240921652>", 
    "Pomegranate Cookie": "<:Soulstone_pomegranate:1439659556501459140>", 
    "Purple Yam Cookie": "<:Soulstone_purple_yam:1439659579880243200>", 
    "Herb Cookie": "<:Soulstone_herb:1439659386342740209>",
    "Chilli Pepper Cookie": "<:Soulstone_chili_pepper:1439659208068038688>", 
    "Sparkling Cookie": "<:Soulstone_sparkling:1439659692468080774>", 
    "Dark Choco Cookie": "<:Soulstone_dark_choco:1439659274581311609>", 
    "Mint Choco Cookie": "<:Soulstone_mint_choco:1439659485332508712>", 
    "Werewolf Cookie": "<:Soulstone_werewolf:1439659788697866443>",
    "Tiger Lily Cookie": "<:Soulstone_tiger_lily:1439659746079539380>", 
    "Vampire Cookie": "<:Soulstone_vampire:1439659768909398026>", 
    "Snow Sugar Cookie": "<:Soulstone_snow_sugar:1439659673421742282>",
    "Kumiho Cookie": "<:Soulstone_kumiho:1439656829188706435>",
    "Doughael Cookie": "<:Soulstone_doughael:1439659301349232844>", 
    "Elder Faerie Cookie": "<:Soulstone_elder_faerie:1439659322240925912>", 
    "Camellia Cookie": "<:Soulstone_camellia:1439659163650101358>", 
    "Crimson Coral Cookie": "<:Soulstone_crimson_coral:1439659254565961970>", 
    "Shining Glitter Cookie": "<:Soulstone_shining_glitter:1439659646171480154>",
    "Capsaicin Cookie": "<:Soulstone_capsaicin:1439659186802659469>", 
    "Stardust Cookie": "<:Soulstone_stardust:1439659716711284866>", 
    "Sherbet Cookie": "<:Soulstone_sherbet:1439659626160197852>", 
    "Oyster Cookie": "<:Soulstone_oyster:1439659508787052724>", 
    "Clotted Cream Cookie": "<:Soulstone_clottedcream:1439659232239685714>",
    "Wind Archer Cookie": "<:Soulstone_wind_archer:1439659818179887135>", 
    "Fire Spirit Cookie": "<:Soulstone_fire_spirit:1439659366478385324>",
    "Pure Vanilla Cookie": "<:Soulstone_pure_vanilla:1439654215927595048>", 
    "Hollyberry Cookie": "<:Soulstone_hollyberry:1439655187236262050>", 
    "Dark Cacao Cookie": "<:Soulstone_dark_cacao:1439655051382751373>", 
    "Golden Cheese Cookie": "<:Soulstone_golden_cheese:1439655128507355196>", 
    "White Lily Cookie": "<:Soulstone_white_lily:1439655232392007680>",
    "Shadow Milk Cookie": "<:Soulstone_shadow_milk:1439654236395802705>", 
    "Eternal Sugar Cookie": "<:Soulstone_eternal_sugar:1439655156512849931>", 
    "Mystic Flour Cookie": "<:Soulstone_mystic_flour:1439655021028442274>", 
    "Burning Spice Cookie": "<:Soulstone_burning_spice:1439655108194472079>", 
    "Silent Salt Cookie": "<:Soulstone_silent_salt:1439655210279637103>",
    "Pitaya Dragon Cookie": "<:Soulstone_pitaya_dragon:1439676929988104283>",
    "Black Pearl Cookie": "<:Soulstone_black_pearl:1439677211887009873>",
    "Frost Queen Cookie": "<:Soulstone_frost_queen:1439676976062529586>",
    "Moonlight Cookie": "<:Soulstone_moonlight:1439676955287879834>",
    "Sea Fairy Cookie": "<:Soulstone_sea_fairy:1439676891505098824>",
    "Stormbringer Cookie": "<:Soulstone_stormbringer:1439676860022784110>"
    # ... fill in rest later
}

# Ascension cost structure
ASCENSION_COSTS = {
    0: 20,  # Unlock
    1: 20,
    2: 30,
    3: 50,
    4: 70,
    5: 100,
    "A1": 20,
    "A2": 30,
    "A3": 50,
    "A4": 70,
    "A5": 100
}

MAX_STARS = {
    "Default": "A5",  # Normal cookies can go up to A5
    "Beast": "6"      # Beast cookies max out at 6 (Max Ascension)
}


def simulate_gacha(draws: int):
    """Simulates gacha pulls. Returns list of dicts containing cookie data."""
    results = []
    for _ in range(draws):
        rarity = random.choices(list(RARITY_WEIGHTS.keys()), weights=RARITY_WEIGHTS.values(), k=1)[0]
        cookie = random.choice(RARITY_POOLS[rarity])

        # 20% chance of full cookie, 80% chance of soulstones (3)
        if random.random() < 0.2:
            soulstones = 20
            pull_type = "Full Cookie"
        else:
            soulstones = 3
            pull_type = "Soulstones"

        emoji = COOKIE_EMOJIS.get(cookie, "🍪")
        results.append({
            "rarity": rarity,
            "cookie": cookie,
            "emoji": emoji,
            "soulstones": soulstones,
            "pull_type": pull_type
        })

    return results


def get_ascension_cost(stars: int, ascension: int):
    """
    Returns the soulstone cost needed for the NEXT upgrade.

    stars: number of stars (0–5)
    ascension: ascension tier (0–5)
    """

    # Star ascensions
    star_costs = {
        0: 20,   # 0 → ⭐
        1: 30,   # ⭐ → ⭐⭐
        2: 50,   # ⭐⭐ → ⭐⭐⭐
        3: 70,   # ⭐⭐⭐ → ⭐⭐⭐⭐
        4: 100,  # ⭐⭐⭐⭐ → ⭐⭐⭐⭐⭐
    }

    # A-level ascensions
    ascension_costs = {
        0: 20,   # ⭐⭐⭐⭐⭐ → A1
        1: 30,   # A1 → A2
        2: 50,   # A2 → A3
        3: 70,   # A3 → A4
        4: 100,  # A4 → A5
    }

    # STAR-level upgrades
    if stars < 5:
        return star_costs.get(stars, None)

    # ASCENSION-level upgrades
    if stars == 5 and ascension < 5:
        return ascension_costs.get(ascension, None)

    # Maxed out
    return None


def generate_ascension_embed(cookie_name, stars, ascension, soulstones_owned):
    """
    Creates an embed-style dict containing:
    - current rank
    - next upgrade
    - cost
    - progress
    - lock/unlock emojis
    """

    # Emojis
    LOCKED = "<:sm_lock:1439610863911829627>"
    UNLOCKED = "<:sm_unlock:1439610901912354906>"
    STAR = "⭐"

    # Determine title rank
    if stars < 5:
        current_rank = STAR * stars if stars > 0 else "○"
        next_rank = STAR * (stars + 1)
    else:
        current_rank = f"{STAR*5} | A{ascension}"
        next_rank = f"A{ascension + 1}" if ascension < 5 else "MAX"

    # Get cost
    cost = get_ascension_requirements(stars, ascension)

    if cost is None:
        status = "✨ **This cookie is fully maxed!**"
        lock_state = UNLOCKED
        progress_bar = "██████████ (MAX)"
    else:
        # Progress bar calculation
        percent = min(soulstones_owned / cost, 1)
        filled = int(percent * 10)
        bar = "█" * filled + "░" * (10 - filled)

        # Locked or unlocked
        lock_state = UNLOCKED if soulstones_owned >= cost else LOCKED

        status = (
            f"**Next Upgrade:** {next_rank}\n"
            f"**Required Soulstones:** {cost}\n"
            f"**You Have:** {soulstones_owned}\n"
        )

        progress_bar = f"{bar} ({soulstones_owned}/{cost})"

    # Return an embed dict to be used by Discord bots
    return {
        "title": f"{cookie_name} Ascension",
        "fields": [
            {"name": "Current Rank", "value": current_rank, "inline": True},
            {"name": "Next Rank", "value": next_rank, "inline": True},
            {"name": "Status", "value": status, "inline": False},
            {"name": "Progress", "value": progress_bar, "inline": False},
            {"name": "Lock State", "value": lock_state, "inline": True},
        ],
        "color": 0x9b59b6
    }
