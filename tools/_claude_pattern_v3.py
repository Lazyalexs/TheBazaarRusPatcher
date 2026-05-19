"""Universal trigger/subject/action parser — covers most 'When you X Y, Z' patterns generically."""
import json, hashlib, re, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')


# ---------- Subject translation ----------

ITEM_TYPE = {
    "Weapon": "Оружие", "Weapons": "Оружие",
    "Vehicle": "Транспорт", "Vehicles": "Транспорт",
    "Property": "Имущество", "Properties": "Имущество",
    "Tool": "Инструмент", "Tools": "Инструменты",
    "Tech": "Техника", "Tech item": "Техника",
    "Food": "Еда", "Foods": "Еда",
    "Aquatic": "Морской", "Aquatic item": "Морской предмет",
    "Apparel": "Снаряжение",
    "Friend": "Союзник", "Friends": "Союзники",
    "Toy": "Игрушка", "Toys": "Игрушки",
    "Potion": "Зелье", "Potions": "Зелья",
    "Relic": "Реликвия", "Relics": "Реликвии",
    "Reagent": "Реагент", "Reagents": "Реагенты",
    "Core": "Ядро", "Cores": "Ядра",
    "Ray": "Луч", "Rays": "Лучи",
    "Drone": "Дрон", "Drones": "Дроны",
    "Dinosaur": "Динозавр",
    "Heated item": "Раскалённый предмет",
    "Chilled item": "Охлаждённый предмет",
    "Enchanted item": "Зачарованный предмет",
    "Flying item": "Летающий предмет", "Flying items": "Летающие предметы",
    "Burn item": "предмет поджога", "Burn items": "предметы поджога",
    "Poison item": "предмет яда", "Poison items": "предметы яда",
    "Shield item": "предмет щита", "Shield items": "предметы щита",
    "Heal item": "предмет исцеления", "Heal items": "предметы исцеления",
    "Regen item": "предмет регенерации", "Regen items": "предметы регенерации",
    "Slow item": "предмет замедления",
    "Freeze item": "предмет заморозки",
    "Haste item": "предмет ускорения",
    "Crit item": "предмет крита",
    "Ammo item": "предмет боезапаса",
    "non-Weapon item": "не-Оружейный предмет",
    "non-Weapon": "не-Оружие",
    "non-Burn or non-Poison item": "не-Поджог и не-Ядовитый предмет",
    "Small item": "Малый предмет",
    "Medium item": "Средний предмет",
    "Large item": "Большой предмет",
    "item": "предмет", "items": "предметы",
    "adjacent item": "соседний предмет",
    "adjacent Weapon": "соседнее Оружие",
    "adjacent Food": "соседнюю Еду",
    "adjacent Property": "соседнее Имущество",
    "adjacent Burn item": "соседний предмет поджога",
    "adjacent Poison item": "соседний предмет яда",
    "adjacent Shield item": "соседний предмет щита",
}


def translate_subject(subj: str) -> str | None:
    """Translate item-type phrase. Returns None if can't translate."""
    subj = subj.strip()
    # Exact match
    if subj in ITEM_TYPE:
        return ITEM_TYPE[subj]
    # "X or Y" / "X or another Y"
    m = re.match(r"^(.+?) or (?:another )?(.+)$", subj)
    if m:
        a = translate_subject(m.group(1))
        b = translate_subject(m.group(2))
        if a and b:
            another = "другой " if " or another " in subj else ""
            return f"{a} или {another}{b.lower() if not b.startswith('О') else b}"
    # "X and Y items"
    m = re.match(r"^([A-Z][a-z]+) and ([A-Z][a-z]+) items?$", subj)
    if m:
        a = ITEM_TYPE.get(m.group(1) + " item", m.group(1))
        b = ITEM_TYPE.get(m.group(2) + " item", m.group(2))
        if a in ITEM_TYPE or m.group(1) in ITEM_TYPE:
            return f"{ITEM_TYPE.get(m.group(1), m.group(1))} и {ITEM_TYPE.get(m.group(2), m.group(2)).lower()} предметы"
    # "another X"
    m = re.match(r"^another (.+)$", subj)
    if m:
        a = translate_subject(m.group(1))
        if a: return f"другой {a.lower() if not a[0].isupper() or a in ('Союзник','Игрушка','Зелье','Транспорт') else a}"
    # "X with Y"
    if subj == "an item with Ammo": return "предмет с боезапасом"
    if subj == "an item with Cooldown": return "предмет с перезарядкой"
    if subj == "an item with value over 10": return "предмет стоимостью больше 10"
    if subj == "an item from another hero": return "предмет от другого героя"
    if subj == "the item to the left of this": return "предмет слева от этого"
    if subj == "the item to the right of this": return "предмет справа от этого"
    if subj == "the Weapon to the left of this": return "Оружие слева от этого"
    if subj == "the Weapon to the right of this": return "Оружие справа от этого"
    if subj == "the Property to the left of this": return "Имущество слева от этого"
    if subj == "the Property to the right of this": return "Имущество справа от этого"
    if subj == "the Tech item to the left of this": return "Технику слева от этого"
    if subj == "the Tech item to the right of this": return "Технику справа от этого"
    if subj == "the Ammo item to the right of this": return "предмет боезапаса справа от этого"
    if subj == "your leftmost item": return "крайний левый предмет"
    if subj == "your rightmost item": return "крайний правый предмет"
    if subj == "any item": return "любой предмет"
    if subj == "this": return "этот предмет"
    if subj == "this item": return "этот предмет"
    return None


# ---------- Generic trigger translation ----------

WHEN_VERB_PATTERNS = [
    # When you use another SUBJECT, ACTION
    (r"^When you use another (.+?),\s*", "Когда вы используете другой"),
    # When you use any item SUBJECT-tail
    (r"^When you use any item to the (left|right) of this,\s*", lambda dir_: f"Когда вы используете любой предмет {('слева' if dir_=='left' else 'справа')} от этого, "),
    # When you use [a|an|the] SUBJECT, ACTION
    (r"^When you use (a|an|the) (.+?),\s*", "Когда вы используете"),
    # When you sell another SUBJECT
    (r"^When you [Ss]ell another (.+?),\s*", "Когда вы продаёте другой"),
    # When you Sell|sell SUBJECT, ACTION
    (r"^When you [Ss]ell (a|an) (.+?),\s*", "Когда вы продаёте"),
    # When you Buy another SUBJECT
    (r"^When you [Bb]uy another (.+?),\s*", "Когда вы покупаете другой"),
    # When you Buy|buy SUBJECT
    (r"^When you [Bb]uy (a|an) (.+?),\s*", "Когда вы покупаете"),
    # When you Crit with [a|an|the] SUBJECT
    (r"^When you Crit with (a|an|the) (.+?),\s*", "Когда вы наносите критический удар"),
    # When you Crit with another SUBJECT
    (r"^When you Crit with another (.+?),\s*", "Когда вы наносите критический удар другим"),
]

# Special triggers (no subject)
SIMPLE_TRIGGERS = {
    "When you sell this": "Когда вы продаёте этот предмет",
    "When you buy this": "Когда вы покупаете этот предмет",
    "When you Slow": "Когда вы замедляете",
    "When you Freeze": "Когда вы замораживаете",
    "When you Burn": "Когда вы поджигаете",
    "When you Poison": "Когда вы отравляете",
    "When you Heal": "Когда вы исцеляете",
    "When you Haste": "Когда вы ускоряете",
    "When you Shield": "Когда вы заряжаете щит",
    "When you Regen": "Когда вы получаете регенерацию",
    "When you Crit": "Когда вы наносите критический удар",
    "When you Enrage": "Когда вы впадаете в ярость",
    "When you Poison yourself": "Когда вы отравляете себя",
    "When you Heal or gain Regen": "Когда вы исцеляете или получаете регенерацию",
    "When you Heal Regen": "Когда вы исцеляете регенерацию",
    "When you stop being Enraged": "Когда вы перестаёте быть в ярости",
    "When you stop being Slowed": "Когда вас перестают замедлять",
    "When you stop being Frozen": "Когда вас перестают замораживать",
    "When you stop being Burned": "Когда вас перестают поджигать",
    "When you stop being Poisoned": "Когда вас перестают отравлять",
    "When you Enrage and stop being Enraged": "Когда вы впадаете в ярость и перестаёте быть в ярости",
    "When you visit a Merchant": "Когда вы посещаете Торговца",
    "When you win a fight": "Когда вы выигрываете бой",
    "When you transform a Reagent": "Когда вы трансформируете Реагент",
    "When you Repair": "Когда вы чините",
    "When you Repair an item": "Когда вы чините предмет",
    "When your items start Flying": "Когда ваши предметы начинают летать",
    "When your items stop Flying": "Когда ваши предметы перестают летать",
    "When your Weapons start Flying": "Когда ваше Оружие начинает летать",
    "When your Weapons stop Flying": "Когда ваше Оружие перестаёт летать",
    "When your items run out of Ammo": "Когда у ваших предметов кончается боезапас",
    "When your Drones deal Damage": "Когда ваши Дроны наносят урон",
    "When your Enemy uses their leftmost item": "Когда враг использует свой крайний левый предмет",
    "When your Enemy uses their rightmost item": "Когда враг использует свой крайний правый предмет",
    "When your opponent uses an item": "Когда ваш противник использует предмет",
    "While in play": "Пока в игре",
    "While this is Flying": "Пока этот предмет летает",
    "While this is Frozen": "Пока этот предмет заморожен",
    "While this is Slowed": "Пока этот предмет замедлен",
    "While you are Enraged": "Пока вы в ярости",
    "While you have an item Burning": "Пока у вас горит предмет",
    "While your enemy has more Health than you": "Пока у врага больше здоровья чем у вас",
}


# ---------- Action translation ----------

EFFECTS_DATIVE = {
    "Damage": "к урону", "Burn": "к поджогу", "Heal": "к исцелению", "Shield": "к щиту",
    "Poison": "к яду", "Regen": "к регенерации", "Joy": "к радости",
    "Crit Chance": "к шансу крита", "Max Health": "к макс. здоровью",
    "Ammo": "к боезапасу", "Max Ammo": "к макс. боезапасу",
    "Income": "к доходу", "Multicast": "к мультикасту",
    "Value": "к стоимости",
}

EFFECTS_GENITIVE = {
    "Burn": "поджога", "Heal": "исцеления", "Shield": "щита",
    "Damage": "урона", "Poison": "яда", "Regen": "регенерации",
    "Joy": "радости", "Value": "стоимости", "Crit": "крита",
    "Ammo": "боезапаса", "Multicast": "мультикаста",
}


def translate_action(s: str) -> str:
    """Apply action regex rules to translate the right side of triggers."""
    rules = [
        # Charge
        (r"\bCharge this ({[^}]+}) (?:seconds?|second\(s\))\.?", lambda m: f"зарядите этот предмет на {m.group(1)} сек."),
        (r"\bCharge an adjacent item ({[^}]+}) second\(s\)\.?", lambda m: f"зарядите соседний предмет на {m.group(1)} сек."),
        (r"\bCharge another item ({[^}]+}) second\(s\)\.?", lambda m: f"зарядите другой предмет на {m.group(1)} сек."),
        (r"\bCharge an item ({[^}]+}) second\(s\)\.?", lambda m: f"зарядите предмет на {m.group(1)} сек."),
        (r"\bCharge a ([A-Z][a-z]+) ({[^}]+}) second\(s\)\.?", lambda m: f"зарядите {ITEM_TYPE.get(m.group(1), m.group(1)).lower()} на {m.group(2)} сек."),
        (r"\bCharge the other adjacent item for ({[^}]+}) second\(s\)\.?", lambda m: f"зарядите другой соседний предмет на {m.group(1)} сек."),
        (r"\bCharge your Relics ({[^}]+}) second\.?", lambda m: f"зарядите ваши Реликвии на {m.group(1)} сек."),
        (r"\bCharge your ([A-Z][a-z]+) items? ({[^}]+}) second\(s\)\.?",
         lambda m: f"зарядите ваши предметы {EFFECTS_GENITIVE.get(m.group(1), m.group(1).lower())} на {m.group(2)} сек."),

        # Freeze
        (r"\bFreeze all enemy items? for ({[^}]+}) second\(s\)\.?", lambda m: f"заморозьте все вражеские предметы на {m.group(1)} сек."),
        (r"\bFreeze an adjacent item for ({[^}]+}) second\(s\)\.?", lambda m: f"заморозьте соседний предмет на {m.group(1)} сек."),
        (r"\bFreeze an enemy item for ({[^}]+}) second\(s\)\.?", lambda m: f"заморозьте вражеский предмет на {m.group(1)} сек."),
        (r"\bFreeze an item for ({[^}]+}) second\(s\)\.?", lambda m: f"заморозьте предмет на {m.group(1)} сек."),
        (r"\bFreeze ({[^}]+}) ([a-zA-Z ]+?) for ({[^}]+}) second\(s\)\.?",
         lambda m: f"заморозьте {m.group(1)} {translate_subject(m.group(2)) or m.group(2).lower()} на {m.group(3)} сек."),

        # Haste
        (r"\bHaste all ([a-zA-Z ]+?) for ({[^}]+}) second\(s\)\.?",
         lambda m: f"ускорьте все {translate_subject(m.group(1)) or m.group(1).lower()} на {m.group(2)} сек."),
        (r"\bHaste an adjacent item for ({[^}]+}) second\(s\)\.?",
         lambda m: f"ускорьте соседний предмет на {m.group(1)} сек."),
        (r"\bHaste your other items for ({[^}]+}) seconds?\.?",
         lambda m: f"ускорьте ваши другие предметы на {m.group(1)} сек."),
        (r"\bHaste your items for ({[^}]+}) second\(s\)\.?",
         lambda m: f"ускорьте ваши предметы на {m.group(1)} сек."),
        (r"\bHaste your ([A-Z][a-z]+) items? for ({[^}]+}) second\(s\)\.?",
         lambda m: f"ускорьте ваши {ITEM_TYPE.get(m.group(1)+' items', m.group(1).lower())} на {m.group(2)} сек."),
        (r"\bHaste an item for ({[^}]+}) second\(s\)\.?", lambda m: f"ускорьте предмет на {m.group(1)} сек."),
        (r"\bHaste a ([A-Z][a-z]+) for ({[^}]+}) second\(s\)\.?",
         lambda m: f"ускорьте {ITEM_TYPE.get(m.group(1), m.group(1)).lower()} на {m.group(2)} сек."),
        (r"\bHaste ({[^}]+}) ([a-zA-Z ]+?) for ({[^}]+}) second\(s\)\.?",
         lambda m: f"ускорьте {m.group(1)} {translate_subject(m.group(2)) or m.group(2).lower()} на {m.group(3)} сек."),
        (r"\bHaste it for ({[^}]+}) second\(s\)\.?", lambda m: f"ускорьте его на {m.group(1)} сек."),

        # Slow
        (r"\bSlow all enemy items? for ({[^}]+}) second\(s\)\.?",
         lambda m: f"замедлите все вражеские предметы на {m.group(1)} сек."),
        (r"\bSlow ALL items? ({[^}]+}) seconds?\.?",
         lambda m: f"замедлите ВСЕ предметы на {m.group(1)} сек."),
        (r"\bSlow an adjacent item for ({[^}]+}) second\(s\)\.?", lambda m: f"замедлите соседний предмет на {m.group(1)} сек."),
        (r"\bSlow an enemy item for ({[^}]+}) second\(s\)\.?", lambda m: f"замедлите вражеский предмет на {m.group(1)} сек."),
        (r"\bSlow an item for ({[^}]+}) second\(s\)?\.?", lambda m: f"замедлите предмет на {m.group(1)} сек."),
        (r"\bSlow ({[^}]+}) ([a-zA-Z ]+?) for ({[^}]+}) second\(s\)\.?",
         lambda m: f"замедлите {m.group(1)} {translate_subject(m.group(2)) or m.group(2).lower()} на {m.group(3)} сек."),
        (r"\bSlow it for ({[^}]+}) second\(s\)\.?", lambda m: f"замедлите его на {m.group(1)} сек."),

        # Heal/Poison/Regen/Burn/Shield with values
        (r"\bHeal equal to ([0-9]+)% of your Max Health\.?", lambda m: f"исцеление равное {m.group(1)}% от вашего макс. здоровья."),
        (r"\bShield equal to ([0-9]+)% of your Max Health\.?", lambda m: f"щит равный {m.group(1)}% от вашего макс. здоровья."),
        (r"\bHeal equal to ({[^}]+}) times this item's ([A-Z][a-z]+)\.?",
         lambda m: f"исцеление равное {m.group(1)} от {EFFECTS_GENITIVE.get(m.group(2), m.group(2).lower())} этого предмета."),
        (r"\bShield equal to ({[^}]+}) times this item's ([A-Z][a-z]+)\.?",
         lambda m: f"щит равный {m.group(1)} от {EFFECTS_GENITIVE.get(m.group(2), m.group(2).lower())} этого предмета."),
        (r"\bBurn equal to this item's ([A-Z][a-z]+)\.?",
         lambda m: f"поджог равный {EFFECTS_GENITIVE.get(m.group(1), m.group(1).lower())} этого предмета."),
        (r"\bRegen equal to this item's ([A-Z][a-z]+)\.?",
         lambda m: f"регенерация равная {EFFECTS_GENITIVE.get(m.group(1), m.group(1).lower())} этого предмета."),
        (r"\bdeal Damage equal to ({[^}]+}) times this item's ([A-Z][a-z]+)\.?",
         lambda m: f"нанесите урон равный {m.group(1)} от {EFFECTS_GENITIVE.get(m.group(2), m.group(2).lower())} этого предмета."),
        (r"\bdeal Damage equal to this item's ([A-Z][a-z]+)\.?",
         lambda m: f"нанесите урон равный {EFFECTS_GENITIVE.get(m.group(1), m.group(1).lower())} этого предмета."),
        (r"\bdeal Damage equal to ([0-9]+)% of this item's ([A-Z][a-z]+)\.?",
         lambda m: f"нанесите урон равный {m.group(1)}% от {EFFECTS_GENITIVE.get(m.group(2), m.group(2).lower())} этого предмета."),
        (r"\bBurn equal to ([0-9]+)% of this item's ([A-Z][a-z]+)\.?",
         lambda m: f"поджог равный {m.group(1)}% от {EFFECTS_GENITIVE.get(m.group(2), m.group(2).lower())} этого предмета."),
        (r"\bHeal equal to ([0-9]+)% of this item's ([A-Z][a-z]+)\.?",
         lambda m: f"исцеление равное {m.group(1)}% от {EFFECTS_GENITIVE.get(m.group(2), m.group(2).lower())} этого предмета."),
        (r"\bShield equal to ([0-9]+)% of this item's ([A-Z][a-z]+)\.?",
         lambda m: f"щит равный {m.group(1)}% от {EFFECTS_GENITIVE.get(m.group(2), m.group(2).lower())} этого предмета."),
        (r"\bPoison equal to ([0-9]+)% of this item's ([A-Z][a-z]+)\.?",
         lambda m: f"отравление равное {m.group(1)}% от {EFFECTS_GENITIVE.get(m.group(2), m.group(2).lower())} этого предмета."),
        (r"\bHeal to full\.?", "исцелитесь полностью."),
        (r"\bHeal ({[^}]+})\.?", lambda m: f"исцеление {m.group(1)}."),
        (r"\bPoison ({[^}]+})\.?", lambda m: f"отравление {m.group(1)}."),
        (r"\bRegen ({[^}]+})\.?", lambda m: f"регенерация {m.group(1)}."),
        (r"\bBurn ({[^}]+})\.?", lambda m: f"поджог {m.group(1)}."),
        (r"\bShield ({[^}]+})\.?", lambda m: f"щит {m.group(1)}."),

        # Damage
        (r"\bdeal ({[^}]+}) Damage\.?", lambda m: f"нанесите {m.group(1)} урона."),
        (r"\bDeal ({[^}]+}) Damage\.?", lambda m: f"нанесите {m.group(1)} урона."),

        # Item modifications
        (r"\byour items gain \+?({[^}]+})% Crit Chance for the fight\.?",
         lambda m: f"ваши предметы получают +{m.group(1)}% к шансу крита до конца боя."),
        (r"\byour items gain \+?({[^}]+}) Damage for the fight\.?",
         lambda m: f"ваши предметы получают +{m.group(1)} к урону до конца боя."),
        (r"\byour items gain \+?({[^}]+}) ([A-Z][a-z]+) for the fight\.?",
         lambda m: f"ваши предметы получают +{m.group(1)} {EFFECTS_DATIVE.get(m.group(2), m.group(2).lower())} до конца боя."),
        (r"\bthis gains \+?({[^}]+}) ([A-Z][a-z]+) for the fight\.?",
         lambda m: f"этот предмет получает +{m.group(1)} {EFFECTS_DATIVE.get(m.group(2), m.group(2).lower())} до конца боя."),
        (r"\bthis and adjacent ([A-Z][a-z]+) items gain ({[^}]+}) ([A-Z][a-z]+) for the fight\.?",
         lambda m: f"этот и соседние предметы {EFFECTS_GENITIVE.get(m.group(1), m.group(1).lower())} получают +{m.group(2)} {EFFECTS_DATIVE.get(m.group(3), m.group(3).lower())} до конца боя."),
        (r"\badjacent items? gain \+?({[^}]+}) ([A-Z][a-z]+) for the fight\.?",
         lambda m: f"соседние предметы получают +{m.group(1)} {EFFECTS_DATIVE.get(m.group(2), m.group(2).lower())} до конца боя."),
        (r"\badjacent ([A-Z][a-z]+ items?) gain \+?({[^}]+}) ([A-Z][a-z]+) for the fight\.?",
         lambda m: f"соседние {ITEM_TYPE.get(m.group(1), m.group(1).lower())} получают +{m.group(2)} {EFFECTS_DATIVE.get(m.group(3), m.group(3).lower())} до конца боя."),
        (r"\bWeapons adjacent to it gain \+?({[^}]+}) Damage for the fight\.?",
         lambda m: f"Оружие рядом с ним получает +{m.group(1)} к урону до конца боя."),
        (r"\b([A-Z][a-z]+ items?) adjacent to it gain \+?({[^}]+}) ([A-Z][a-z]+) for the fight\.?",
         lambda m: f"{ITEM_TYPE.get(m.group(1), m.group(1).lower())} рядом с ним получают +{m.group(2)} {EFFECTS_DATIVE.get(m.group(3), m.group(3).lower())} до конца боя."),
        (r"\byour ([A-Z][a-z]+) items? gain \+?({[^}]+}) ([A-Z][a-z]+) for the fight\.?",
         lambda m: f"ваши {ITEM_TYPE.get(m.group(1)+' items', m.group(1).lower())} получают +{m.group(2)} {EFFECTS_DATIVE.get(m.group(3), m.group(3).lower())} до конца боя."),
        (r"\byour Weapons gain \+?({[^}]+}) Damage for the fight\.?",
         lambda m: f"ваше Оружие получает +{m.group(1)} к урону до конца боя."),
        (r"\breduce its Cooldown by ({[^}]+})% for the fight\.?",
         lambda m: f"его перезарядка снижается на {m.group(1)}% до конца боя."),

        # use this / reload this
        (r"\bReload all your items\.?", "перезарядите все ваши предметы."),
        (r"\bReload an enemy item ({[^}]+}) Ammo\.?", lambda m: f"перезарядите вражеский предмет на {m.group(1)} боезапаса."),
        (r"\bReload an item ({[^}]+}) Ammo\.?", lambda m: f"перезарядите предмет на {m.group(1)} боезапаса."),
        (r"\breload this\.?", "перезарядите этот предмет."),
        (r"\bReload this\.?", "перезарядите этот предмет."),
        (r"\buse this\.?", "используйте этот предмет."),

        # gain X
        (r"\bgain ({[^}]+}) Gold\.?", lambda m: f"получите {m.group(1)} золота."),
        (r"\bgain ({[^}]+}) XP\.?", lambda m: f"получите {m.group(1)} XP."),
        (r"\bgain ({[^}]+}) Rage\.?", lambda m: f"получите {m.group(1)} ярости."),
        (r"\bgain ({[^}]+}) Max Health for the fight\.?",
         lambda m: f"получите {m.group(1)} к макс. здоровью до конца боя."),

        # destroy
        (r"\bdestroy this and a Small enemy item for the fight\.?",
         "уничтожьте этот предмет и Малый вражеский предмет до конца боя."),

        # Compound this gains +X and +Y
        (r"\bthis gains \+?({[^}]+}) Burn and \+?({[^}]+}) Regen\.?",
         lambda m: f"этот предмет получает +{m.group(1)} к поджогу и +{m.group(2)} к регенерации."),
        (r"\bthis gains \+?({[^}]+}) Burn and \+?({[^}]+}) Poison\.?",
         lambda m: f"этот предмет получает +{m.group(1)} к поджогу и +{m.group(2)} к яду."),
        (r"\bthis gains \+?({[^}]+}) ([A-Z][a-z]+) and \+?({[^}]+}) ([A-Z][a-z]+)\.?",
         lambda m: f"этот предмет получает +{m.group(1)} {EFFECTS_DATIVE.get(m.group(2), m.group(2).lower())} и +{m.group(3)} {EFFECTS_DATIVE.get(m.group(4), m.group(4).lower())}."),

        # Charge X N second and this gains Y for the fight
        (r"\bCharge Your Core ({[^}]+}) seconds? and this gains ({[^}]+}) ([A-Z][a-z]+) for the fight\.?",
         lambda m: f"зарядите ваше Ядро на {m.group(1)} сек., и этот предмет получает {m.group(2)} {EFFECTS_DATIVE.get(m.group(3), m.group(3).lower())} до конца боя."),

        # Charge Another Toy / Charge a X N second
        (r"\bCharge another Toy ({[^}]+}) second\(s\)\.?",
         lambda m: f"зарядите другую Игрушку на {m.group(1)} сек."),

        # this gains +N type-name for the fight (e.g., +N Burn)
        (r"\bthis gains ({[^}]+}) ([A-Z][a-z]+) for the fight\.?",
         lambda m: f"этот предмет получает {m.group(1)} {EFFECTS_DATIVE.get(m.group(2), m.group(2).lower())} до конца боя."),
    ]

    out = s
    for pat, repl in rules:
        out = re.sub(pat, repl, out)
    return out


# ---------- Your X / While X handlers ----------

YOUR_RULES = [
    # Your leftmost item gains the X type
    (r"^Your leftmost item gains the (\w+) type\.?$",
     lambda m: f"Ваш крайний левый предмет получает тип {ITEM_TYPE.get(m.group(1), m.group(1))}."),
    (r"^Your rightmost item gains the (\w+) type\.?$",
     lambda m: f"Ваш крайний правый предмет получает тип {ITEM_TYPE.get(m.group(1), m.group(1))}."),
    # Your X items gain +N Y for the fight
    (r"^Your items gain \+?({[^}]+})% Crit Chance for the fight\.?",
     lambda m: f"Ваши предметы получают +{m.group(1)}% к шансу крита до конца боя."),
    (r"^Your items gain \+?({[^}]+}) Damage for the fight\.?",
     lambda m: f"Ваши предметы получают +{m.group(1)} к урону до конца боя."),
    (r"^Your items gain \+?({[^}]+}) ([A-Z][a-z]+) for the fight\.?",
     lambda m: f"Ваши предметы получают +{m.group(1)} {EFFECTS_DATIVE.get(m.group(2), m.group(2).lower())} до конца боя."),
    (r"^Your items have \+?({[^}]+})% Crit Chance\.?",
     lambda m: f"Ваши предметы имеют +{m.group(1)}% к шансу крита."),
    (r"^Your items have \+?({[^}]+}) ([A-Z][a-z]+)\.?",
     lambda m: f"Ваши предметы имеют +{m.group(1)} {EFFECTS_DATIVE.get(m.group(2), m.group(2).lower())}."),
    # Your X items deal +N Damage
    (r"^Your ([A-Z][a-z]+) Weapons deal \+?({[^}]+}) Damage\.?",
     lambda m: f"Ваше {m.group(1)} Оружие наносит +{m.group(2)} к урону."),
    (r"^Your ([A-Z][a-z]+) Weapons gain \+?({[^}]+}) Damage for the fight\.?",
     lambda m: f"Ваше {m.group(1)} Оружие получает +{m.group(2)} к урону до конца боя."),
    (r"^Your Weapons deal double Crit Damage\.?",
     "Ваше Оружие наносит двойной критический урон."),
    (r"^Your Weapons deal \+?({[^}]+}) Damage\.?",
     lambda m: f"Ваше Оружие наносит +{m.group(1)} к урону."),
    (r"^Your Weapons gain \+?({[^}]+}) Damage for the fight\.?",
     lambda m: f"Ваше Оружие получает +{m.group(1)} к урону до конца боя."),
    (r"^Your Weapons gain \+?({[^}]+}) Damage\.?",
     lambda m: f"Ваше Оружие получает +{m.group(1)} к урону."),
    (r"^Your Weapons have \+?({[^}]+}) Damage\.?",
     lambda m: f"Ваше Оружие имеет +{m.group(1)} к урону."),
    (r"^Your ([A-Z][a-z]+) items? have \+?({[^}]+}) ([A-Z][a-z]+)\.?",
     lambda m: f"Ваши {ITEM_TYPE.get(m.group(1)+' items', m.group(1).lower())} имеют +{m.group(2)} {EFFECTS_DATIVE.get(m.group(3), m.group(3).lower())}."),
    (r"^Your ([A-Z][a-z]+) items? gain \+?({[^}]+}) ([A-Z][a-z]+) for the fight\.?",
     lambda m: f"Ваши {ITEM_TYPE.get(m.group(1)+' items', m.group(1).lower())} получают +{m.group(2)} {EFFECTS_DATIVE.get(m.group(3), m.group(3).lower())} до конца боя."),
    # "are affected by Freeze and Slow for half as long"
    (r"^Your ([A-Z][a-z]+) (?:items?|Weapons|Tools) are affected by Freeze and Slow for half as long\.?",
     lambda m: f"На ваши {ITEM_TYPE.get(m.group(1), m.group(1).lower())} Заморозка и Замедление действуют вдвое короче."),
    (r"^Your Aquatic items are Friends\.?",
     "Ваши Морские предметы являются Союзниками."),
    (r"^Your Lifesteal Weapons have \+?({[^}]+}) Damage\.?",
     lambda m: f"Ваше Оружие с Вампиризмом имеет +{m.group(1)} к урону."),
    (r"^Your Lifesteal Weapons gain \+?({[^}]+}) Damage for the fight\.?",
     lambda m: f"Ваше Оружие с Вампиризмом получает +{m.group(1)} к урону до конца боя."),

    # Your leftmost item is/has
    (r"^Your leftmost item is a ([A-Z][a-z]+) and has its cooldown reduced by ({[^}]+})%\.?",
     lambda m: f"Ваш крайний левый предмет — это {ITEM_TYPE.get(m.group(1), m.group(1)).lower()}, и его перезарядка снижается на {m.group(2)}%."),
    (r"^Your leftmost item is a ([A-Z][a-z]+) and has \+?({[^}]+}) ([A-Z][a-z]+)\.?",
     lambda m: f"Ваш крайний левый предмет — это {ITEM_TYPE.get(m.group(1), m.group(1)).lower()}, и имеет +{m.group(2)} {EFFECTS_DATIVE.get(m.group(3), m.group(3).lower())}."),
    (r"^Your leftmost Weapon has \+?({[^}]+}) Damage\.?",
     lambda m: f"Ваше крайнее левое Оружие имеет +{m.group(1)} к урону."),
    (r"^Your leftmost Weapon gains \+?({[^}]+}) Damage for the fight\.?",
     lambda m: f"Ваше крайнее левое Оружие получает +{m.group(1)} к урону до конца боя."),
    (r"^Your leftmost item has \+?({[^}]+}) ([A-Z][a-z]+)\.?",
     lambda m: f"Ваш крайний левый предмет имеет +{m.group(1)} {EFFECTS_DATIVE.get(m.group(2), m.group(2).lower())}."),
    (r"^Your leftmost item gains \+?({[^}]+}) ([A-Z][a-z]+) for the fight\.?",
     lambda m: f"Ваш крайний левый предмет получает +{m.group(1)} {EFFECTS_DATIVE.get(m.group(2), m.group(2).lower())} до конца боя."),
    # Your Regen items have + Regen equal to ...
    (r"^Your ([A-Z][a-z]+) items? have \+?\s*([A-Z][a-z]+) equal to ([0-9]+)% of this item's ([A-Z][a-z]+)\.?",
     lambda m: f"Ваши {ITEM_TYPE.get(m.group(1)+' items', m.group(1).lower())} имеют +{EFFECTS_DATIVE.get(m.group(2), m.group(2).lower())} равное {m.group(3)}% от {EFFECTS_GENITIVE.get(m.group(4), m.group(4).lower())} этого предмета."),
]

WHILE_RULES = [
    (r"^While in play, you have \+?({[^}]+}) ([A-Z][a-z]+)\.?",
     lambda m: f"Пока в игре, у вас есть +{m.group(1)} {EFFECTS_DATIVE.get(m.group(2), m.group(2).lower())}."),
    (r"^While in play, you have \+?({[^}]+}) Income\.?",
     lambda m: f"Пока в игре, у вас есть +{m.group(1)} к доходу."),
    (r"^While this is Flying, this has \+?({[^}]+}) ([A-Z][a-z]+)\.?",
     lambda m: f"Пока этот предмет летает, он имеет +{m.group(1)} {EFFECTS_DATIVE.get(m.group(2), m.group(2).lower())}."),
    (r"^While this is Flying, reduce its cooldown by ({[^}]+}) seconds?\.?",
     lambda m: f"Пока этот предмет летает, его перезарядка снижается на {m.group(1)} сек."),
    (r"^While this is Flying, reduce its cooldown by ([0-9.]+) seconds?\.?",
     lambda m: f"Пока этот предмет летает, его перезарядка снижается на {m.group(1)} сек."),
    (r"^While this is Flying, it has \+?({[^}]+}) ([A-Z][a-z]+)\.?",
     lambda m: f"Пока этот предмет летает, он имеет +{m.group(1)} {EFFECTS_DATIVE.get(m.group(2), m.group(2).lower())}."),
    (r"^While an enemy item is Slowed, this has \+?({[^}]+})% Crit Chance\.?",
     lambda m: f"Пока вражеский предмет замедлен, этот предмет имеет +{m.group(1)}% к шансу крита."),
    (r"^While you are Enraged, this has \+?({[^}]+}) ([A-Z][a-z]+)\.?",
     lambda m: f"Пока вы в ярости, этот предмет имеет +{m.group(1)} {EFFECTS_DATIVE.get(m.group(2), m.group(2).lower())}."),
    (r"^While your enemy has more Health than you, this has \+?({[^}]+}) ([A-Z][a-z]+)\.?",
     lambda m: f"Пока у врага больше здоровья чем у вас, этот предмет имеет +{m.group(1)} {EFFECTS_DATIVE.get(m.group(2), m.group(2).lower())}."),
    (r"^While your enemy is Poisoned, their items' Cooldowns are increased by ({[^}]+})%",
     lambda m: f"Пока ваш враг отравлен, перезарядка его предметов увеличивается на {m.group(1)}%."),
    (r"^While you are Enraged, your Weapons have Lifesteal\.?",
     "Пока вы в ярости, ваше Оружие имеет Вампиризм."),
    (r"^While you are Enraged, this has \+?({[^}]+}) Multicast\.?",
     lambda m: f"Пока вы в ярости, этот предмет имеет +{m.group(1)} к мультикасту."),
    (r"^While you are Enraged, your items have \+?({[^}]+}) ([A-Z][a-z]+)\.?",
     lambda m: f"Пока вы в ярости, ваши предметы имеют +{m.group(1)} {EFFECTS_DATIVE.get(m.group(2), m.group(2).lower())}."),
    (r"^While you are Enraged, your items gain \+?({[^}]+})% Crit Chance\.?",
     lambda m: f"Пока вы в ярости, ваши предметы получают +{m.group(1)}% к шансу крита."),
]


YOU_RULES = [
    (r"^You have \+?({[^}]+}) Max Health for each (.+?)\.?$",
     lambda m: f"У вас есть +{m.group(1)} к макс. здоровью за каждый {translate_subject(m.group(2)) or m.group(2).lower()}."),
    (r"^You have \+?({[^}]+}) ([A-Z][a-z]+) for each (.+?)\.?$",
     lambda m: f"У вас есть +{m.group(1)} {EFFECTS_DATIVE.get(m.group(2), m.group(2).lower())} за каждый {translate_subject(m.group(3)) or m.group(3).lower()}."),
    (r"^You are Enraged for ({[^}]+}) seconds? longer\.?$",
     lambda m: f"Вы в ярости на {m.group(1)} сек. дольше."),
    (r"^You are Enraged for ({[^}]+}) seconds? shorter\.?$",
     lambda m: f"Вы в ярости на {m.group(1)} сек. короче."),
    (r"^You are Enraged for 1 second longer$",
     "Вы в ярости на 1 сек. дольше."),
    (r"^You are Enraged for 1 second shorter$",
     "Вы в ярости на 1 сек. короче."),
]


def looks_translated(ru: str) -> bool:
    test = re.sub(r"\{[^{}]+\}", "", ru)
    test = re.sub(r"\[[^\]]+\]", "", test)
    for ok in ("XP", "HP", "MP"):
        test = test.replace(ok, "")
    bad = re.findall(r"\b[A-Za-z]{2,}\b", test)
    return len(bad) == 0


def translate_when(s: str) -> str | None:
    # Try simple triggers first (longest first)
    for trig_en in sorted(SIMPLE_TRIGGERS.keys(), key=len, reverse=True):
        if s.startswith(trig_en + ",") or s.startswith(trig_en + " "):
            tail = s[len(trig_en):].lstrip(", ")
            action_ru = translate_action(tail)
            result = f"{SIMPLE_TRIGGERS[trig_en]}, {action_ru}"
            return result if looks_translated(result) else None
    # Try verb patterns with subject extraction
    for pat, verb in WHEN_VERB_PATTERNS:
        m = re.match(pat, s)
        if m:
            groups = m.groups()
            # Some patterns have 1 group (like "When you use any item to the left of this")
            # Others have 2 groups (article + subject)
            if len(groups) == 1:
                # Custom lambda case for "any item to the left/right"
                if callable(verb):
                    head = verb(groups[0])
                else:
                    head = f"{verb} {groups[0]}, "
                tail = s[m.end():]
                action_ru = translate_action(tail)
                result = head + action_ru
            else:
                article, subj = groups[0], groups[1]
                subj_ru = translate_subject(subj)
                if not subj_ru:
                    continue  # try next pattern
                tail = s[m.end():]
                action_ru = translate_action(tail)
                result = f"{verb} {subj_ru}, {action_ru}"
            if looks_translated(result):
                return result
    return None


def translate_your(s: str) -> str | None:
    for pat, repl in YOUR_RULES:
        m = re.match(pat, s)
        if m:
            result = repl(m) if callable(repl) else m.expand(repl)
            if looks_translated(result):
                return result
    return None


def translate_while(s: str) -> str | None:
    for pat, repl in WHILE_RULES:
        m = re.match(pat, s)
        if m:
            result = repl(m) if callable(repl) else m.expand(repl)
            if looks_translated(result):
                return result
    return None


def translate_you(s: str) -> str | None:
    for pat, repl in YOU_RULES:
        m = re.match(pat, s)
        if m:
            result = repl(m) if callable(repl) else m.expand(repl)
            if looks_translated(result):
                return result
    return None


def translate_string(s: str) -> str | None:
    if s.startswith("When "):
        return translate_when(s)
    if s.startswith("Your "):
        return translate_your(s)
    if s.startswith("While "):
        return translate_while(s)
    if s.startswith("You "):
        return translate_you(s)
    return None


def main():
    with open("tools/.translate-final-todo.json", encoding="utf-8") as f:
        todo = json.load(f)
    with open("tools/.translate-progress.json", encoding="utf-8") as f:
        progress = json.load(f)

    added = 0
    unmatched = 0
    for s in todo:
        k = hashlib.md5(s.encode("utf-8")).hexdigest()
        if k in progress:
            continue
        ru = translate_string(s)
        if ru:
            progress[k] = ru
            added += 1
        else:
            unmatched += 1

    with open("tools/.translate-progress.json", "w", encoding="utf-8") as f:
        json.dump(progress, f, ensure_ascii=False, indent=1)

    print(f"v3 added: {added}")
    print(f"Still unmatched: {unmatched}")
    print(f"Total progress: {len(progress)}")


if __name__ == "__main__":
    main()
