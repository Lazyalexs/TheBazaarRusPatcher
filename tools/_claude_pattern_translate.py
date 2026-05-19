"""Pattern-based translator for the Bazaar's repetitive 'When you X, Y' template strings.

Goes through all not-yet-translated entries in `.translate-claude-todo.json` and
applies a sequence of phrase-level regex substitutions modelled on the glossary.
Anything that's not fully covered after rules apply is left untouched (so the
DeepSeek pipeline can finish it).
"""
import json, hashlib, re, sys, io, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# ---------- glossary-level rules ----------

TRIGGERS = {
    "When you use a Weapon": "Когда вы используете Оружие",
    "When you use a Vehicle": "Когда вы используете Транспорт",
    "When you use a Property": "Когда вы используете Имущество",
    "When you use a Tool": "Когда вы используете Инструмент",
    "When you use a Tech": "Когда вы используете Технику",
    "When you use a Food": "Когда вы используете Еду",
    "When you use an Aquatic": "Когда вы используете Морской предмет",
    "When you use an Apparel": "Когда вы используете Снаряжение",
    "When you use a Friend": "Когда вы используете Союзника",
    "When you use a Toy": "Когда вы используете Игрушку",
    "When you use a Potion": "Когда вы используете Зелье",
    "When you use a Flying item": "Когда вы используете Летающий предмет",
    "When you use a Burn item": "Когда вы используете предмет поджога",
    "When you use a Poison item": "Когда вы используете предмет яда",
    "When you use a Shield item": "Когда вы используете предмет щита",
    "When you use a Heal item": "Когда вы используете предмет исцеления",
    "When you use a Regen item": "Когда вы используете предмет регенерации",
    "When you use a Slow item": "Когда вы используете предмет замедления",
    "When you use a Freeze item": "Когда вы используете предмет заморозки",
    "When you use a Haste item": "Когда вы используете предмет ускорения",
    "When you use a Crit item": "Когда вы используете предмет крита",
    "When you use a Relic": "Когда вы используете Реликвию",
    "When you use a Reagent": "Когда вы используете Реагент",
    "When you use a Heated item": "Когда вы используете Раскалённый предмет",
    "When you use a Core": "Когда вы используете Ядро",
    "When you use a Small item": "Когда вы используете Малый предмет",
    "When you use a Medium item": "Когда вы используете Средний предмет",
    "When you use a Large item": "Когда вы используете Большой предмет",
    "When you use a non-Weapon": "Когда вы используете не-Оружие",
    "When you use a non-Weapon item": "Когда вы используете не-Оружейный предмет",
    "When you use any item": "Когда вы используете любой предмет",
    "When you use an item": "Когда вы используете предмет",
    "When you use an adjacent item": "Когда вы используете соседний предмет",
    "When you use another Weapon": "Когда вы используете другое Оружие",
    "When you use another item": "Когда вы используете другой предмет",
    "When you use this": "Когда вы используете этот предмет",
    "When you use this item": "Когда вы используете этот предмет",
    "When you Sell a Weapon": "Когда вы продаёте Оружие",
    "When you Sell a Vehicle": "Когда вы продаёте Транспорт",
    "When you Sell a Property": "Когда вы продаёте Имущество",
    "When you Sell a Tool": "Когда вы продаёте Инструмент",
    "When you Sell a Tech": "Когда вы продаёте Технику",
    "When you Sell a Food": "Когда вы продаёте Еду",
    "When you Sell an Aquatic": "Когда вы продаёте Морской предмет",
    "When you Sell an Apparel": "Когда вы продаёте Снаряжение",
    "When you Sell a Friend": "Когда вы продаёте Союзника",
    "When you Sell a Toy": "Когда вы продаёте Игрушку",
    "When you Sell a Potion": "Когда вы продаёте Зелье",
    "When you Sell an item": "Когда вы продаёте предмет",
    "When you Sell any item": "Когда вы продаёте любой предмет",
    "When you sell a Weapon": "Когда вы продаёте Оружие",
    "When you sell a Vehicle": "Когда вы продаёте Транспорт",
    "When you sell a Property": "Когда вы продаёте Имущество",
    "When you sell a Tool": "Когда вы продаёте Инструмент",
    "When you sell a Tech": "Когда вы продаёте Технику",
    "When you sell a Food": "Когда вы продаёте Еду",
    "When you sell an Aquatic": "Когда вы продаёте Морской предмет",
    "When you sell an Apparel": "Когда вы продаёте Снаряжение",
    "When you sell a Friend": "Когда вы продаёте Союзника",
    "When you sell a Toy": "Когда вы продаёте Игрушку",
    "When you sell a Potion": "Когда вы продаёте Зелье",
    "When you sell an item": "Когда вы продаёте предмет",
    "When you sell any item": "Когда вы продаёте любой предмет",
    "When you sell a Relic": "Когда вы продаёте Реликвию",
    "When you sell a Reagent": "Когда вы продаёте Реагент",
    "When you sell a Small item": "Когда вы продаёте Малый предмет",
    "When you sell a Medium item": "Когда вы продаёте Средний предмет",
    "When you sell a Large item": "Когда вы продаёте Большой предмет",
    "When you Buy a Weapon": "Когда вы покупаете Оружие",
    "When you Buy a Vehicle": "Когда вы покупаете Транспорт",
    "When you Buy a Property": "Когда вы покупаете Имущество",
    "When you Buy a Tool": "Когда вы покупаете Инструмент",
    "When you Buy a Tech": "Когда вы покупаете Технику",
    "When you Buy a Food": "Когда вы покупаете Еду",
    "When you Buy an Aquatic": "Когда вы покупаете Морской предмет",
    "When you Buy an Apparel": "Когда вы покупаете Снаряжение",
    "When you Buy a Friend": "Когда вы покупаете Союзника",
    "When you Buy a Toy": "Когда вы покупаете Игрушку",
    "When you Buy a Potion": "Когда вы покупаете Зелье",
    "When you Buy an item": "Когда вы покупаете предмет",
    "When you buy a Weapon": "Когда вы покупаете Оружие",
    "When you buy a Vehicle": "Когда вы покупаете Транспорт",
    "When you buy a Property": "Когда вы покупаете Имущество",
    "When you buy a Tool": "Когда вы покупаете Инструмент",
    "When you buy a Tech": "Когда вы покупаете Технику",
    "When you buy a Food": "Когда вы покупаете Еду",
    "When you buy a Friend": "Когда вы покупаете Союзника",
    "When you buy a Toy": "Когда вы покупаете Игрушку",
    "When you buy a Potion": "Когда вы покупаете Зелье",
    "When you buy an item": "Когда вы покупаете предмет",
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
    "When you Stop being Enraged": "Когда вы перестаёте быть в ярости",
    "When you stop being Enraged": "Когда вы перестаёте быть в ярости",
    "When you Repair": "Когда вы чините",
    "When you Destroy an item": "Когда вы уничтожаете предмет",
    "When you destroy an item": "Когда вы уничтожаете предмет",
    "When you gain Gold": "Когда вы получаете золото",
    "When you gain XP": "Когда вы получаете XP",
    "When you gain Income": "Когда вы получаете доход",
    "When you gain Max Health": "Когда вы получаете макс. здоровье",
    "When you take Damage": "Когда вы получаете урон",
    "When you Equip": "Когда вы экипируете",
    "When you Equip a Weapon": "Когда вы экипируете Оружие",
    "When you Equip an item": "Когда вы экипируете предмет",
    "When you Reload an item": "Когда вы перезаряжаете предмет",
    "When you reload an item": "Когда вы перезаряжаете предмет",
    "When you Reload this": "Когда вы перезаряжаете этот предмет",
    "When you reload this": "Когда вы перезаряжаете этот предмет",
    "When you Refresh": "Когда вы обновляете",
    "When you Crit with the item to the left of this": "Когда вы наносите критический удар предметом слева от этого",
    "When you Crit with the item to the right of this": "Когда вы наносите критический удар предметом справа от этого",
    "When you Crit with this": "Когда вы наносите критический удар этим предметом",
    "When you Crit with an item": "Когда вы наносите критический удар предметом",
    "When you Crit with another item": "Когда вы наносите критический удар другим предметом",
    "When you Crit with a Vehicle": "Когда вы наносите критический удар Транспортом",
    "When you Crit with a Property": "Когда вы наносите критический удар Имуществом",
    "When you Crit with a Tool": "Когда вы наносите критический удар Инструментом",
    "When you Crit with a Tech": "Когда вы наносите критический удар Техникой",
    "When you Crit with a Food": "Когда вы наносите критический удар Едой",
    "When you Crit with a Friend": "Когда вы наносите критический удар Союзником",
    "When you Crit with a Toy": "Когда вы наносите критический удар Игрушкой",
    "When you Crit with a Potion": "Когда вы наносите критический удар Зельем",
    "When you Crit with a Relic": "Когда вы наносите критический удар Реликвией",
    "When you Crit with a Burn item": "Когда вы наносите критический удар предметом поджога",
    "When you Crit with a Poison item": "Когда вы наносите критический удар предметом яда",
    "When you Crit with a Heal item": "Когда вы наносите критический удар предметом исцеления",
    "When you Slow an enemy item": "Когда вы замедляете вражеский предмет",
    "When you Slow an item": "Когда вы замедляете предмет",
    "When you Freeze an enemy item": "Когда вы замораживаете вражеский предмет",
    "When you Freeze an item": "Когда вы замораживаете предмет",
    "When you Haste a Friend": "Когда вы ускоряете Союзника",
    "When you Haste an adjacent item": "Когда вы ускоряете соседний предмет",
    "When you Haste an item": "Когда вы ускоряете предмет",
    "When you Heal a Friend": "Когда вы исцеляете Союзника",
    "When you Heal an adjacent item": "Когда вы исцеляете соседний предмет",
    "When you use a Reagent": "Когда вы используете Реагент",
    "When you Sell a Relic": "Когда вы продаёте Реликвию",
    "When you Sell a Reagent": "Когда вы продаёте Реагент",
    "When you Sell a Burn item": "Когда вы продаёте предмет поджога",
    "When you Sell a Poison item": "Когда вы продаёте предмет яда",
    "When you Sell a Shield item": "Когда вы продаёте предмет щита",
    "When you Sell a Heal item": "Когда вы продаёте предмет исцеления",
    "When you Sell a Small item": "Когда вы продаёте Малый предмет",
    "When you Sell a Medium item": "Когда вы продаёте Средний предмет",
    "When you Sell a Large item": "Когда вы продаёте Большой предмет",
    "When you Buy a Relic": "Когда вы покупаете Реликвию",
    "When you Buy a Reagent": "Когда вы покупаете Реагент",
    "When you Buy a Small item": "Когда вы покупаете Малый предмет",
    "When you Buy a Medium item": "Когда вы покупаете Средний предмет",
    "When you Buy a Large item": "Когда вы покупаете Большой предмет",
    "When you stop being Frozen": "Когда вас перестают замораживать",
    "When you stop being Slowed": "Когда вас перестают замедлять",
    "When you stop being Hasted": "Когда вы перестаёте быть ускоренным",
    "When you stop being Burned": "Когда вас перестают поджигать",
    "When you stop being Poisoned": "Когда вас перестают отравлять",
    "When you Sell this": "Когда вы продаёте этот предмет",
    "When you Buy this": "Когда вы покупаете этот предмет",
    "When you Equip this": "Когда вы экипируете этот предмет",
    "When you Equip a Friend": "Когда вы экипируете Союзника",
    "When you Equip a Weapon": "Когда вы экипируете Оружие",
    "When you Repair this": "Когда вы чините этот предмет",
    "When you Repair an item": "Когда вы чините предмет",
    "When you Repair a Vehicle": "Когда вы чините Транспорт",
    "When you Destroy this": "Когда вы уничтожаете этот предмет",
    "When you destroy this": "Когда вы уничтожаете этот предмет",
    "When you gain a charge": "Когда вы получаете заряд",
    "When you gain Crit": "Когда вы получаете крит",
}

# Action-level patterns to translate the right side of "When you X,"
def translate_action(action: str) -> str:
    """Translate an action clause. Returns translated text."""
    s = action

    # Order matters: longer matches first
    replacements = [
        # Effects with placeholder targets and durations
        (r"\bCharge this ({[^}]+}) seconds?\.", r"зарядите этот предмет на \1 сек."),
        (r"\bCharge this ({[^}]+}) second\(s\)\.", r"зарядите этот предмет на \1 сек."),
        (r"\bCharge this ({[^}]+}) second\(s\)\b", r"зарядите этот предмет на \1 сек"),
        (r"\bCharge this ({[^}]+}) second\b", r"зарядите этот предмет на \1 сек"),
        (r"\bCharge an adjacent item ({[^}]+}) second\(s\)\.", r"зарядите соседний предмет на \1 сек."),
        (r"\bCharge an item ({[^}]+}) second\(s\)\.", r"зарядите предмет на \1 сек."),
        (r"\bCharge your ([^,.]+?) items? ({[^}]+}) second\(s\)\.", lambda m: f"зарядите ваши {m.group(1).lower()} предметы на {m.group(2)} сек."),
        (r"\bCharge your ([^,.]+?) items? ({[^}]+}) second\b", lambda m: f"зарядите ваши {m.group(1).lower()} предметы на {m.group(2)} сек"),
        (r"\bCharge ({[^}]+}) second\(s\)\b", r"зарядите на \1 сек"),

        # Freeze / Haste / Slow with targets
        (r"\bFreeze all ([^,.]+?) for ({[^}]+}) second\(s\)\.", lambda m: f"заморозьте все {translate_target(m.group(1))} на {m.group(2)} сек."),
        (r"\bFreeze ({[^}]+}) ([^,.]+?) for ({[^}]+}) second\(s\)\.", lambda m: f"заморозьте {m.group(1)} {translate_target(m.group(2))} на {m.group(3)} сек."),
        (r"\bFreeze an adjacent item for ({[^}]+}) second\(s\)\.", r"заморозьте соседний предмет на \1 сек."),
        (r"\bFreeze an item for ({[^}]+}) second\(s\)\.", r"заморозьте предмет на \1 сек."),
        (r"\bFreeze an item for ({[^}]+}) second\(s\)", r"заморозьте предмет на \1 сек"),

        (r"\bHaste all ([^,.]+?) for ({[^}]+}) second\(s\)\.", lambda m: f"ускорьте все {translate_target(m.group(1))} на {m.group(2)} сек."),
        (r"\bHaste ({[^}]+}) ([^,.]+?) for ({[^}]+}) second\(s\)\.", lambda m: f"ускорьте {m.group(1)} {translate_target(m.group(2))} на {m.group(3)} сек."),
        (r"\bHaste an adjacent item for ({[^}]+}) second\(s\)\.", r"ускорьте соседний предмет на \1 сек."),
        (r"\bHaste your ([^,.]+?) items? for ({[^}]+}) second\(s\)\.", lambda m: f"ускорьте ваши {translate_target(m.group(1)+' items')} на {m.group(2)} сек."),
        (r"\bHaste an item for ({[^}]+}) second\(s\)\.", r"ускорьте предмет на \1 сек."),
        (r"\bHaste an item for ({[^}]+}) second\(s\)", r"ускорьте предмет на \1 сек"),
        (r"\bHaste your items for ({[^}]+}) second\(s\)\.", r"ускорьте ваши предметы на \1 сек."),
        (r"\bHaste a ([A-Z][a-z]+) for ({[^}]+}) second\(s\)\.", lambda m: f"ускорьте {translate_target(m.group(1))} на {m.group(2)} сек."),

        (r"\bSlow all ([^,.]+?) for ({[^}]+}) second\(s\)\.", lambda m: f"замедлите все {translate_target(m.group(1))} на {m.group(2)} сек."),
        (r"\bSlow ({[^}]+}) ([^,.]+?) for ({[^}]+}) second\(s\)\.", lambda m: f"замедлите {m.group(1)} {translate_target(m.group(2))} на {m.group(3)} сек."),
        (r"\bSlow an adjacent item for ({[^}]+}) second\(s\)\.", r"замедлите соседний предмет на \1 сек."),
        (r"\bSlow an item for ({[^}]+}) second\(s\)\.", r"замедлите предмет на \1 сек."),
        (r"\bSlow an item for ({[^}]+}) second\(s\)", r"замедлите предмет на \1 сек"),

        # Heal / Poison / Regen / Burn / Shield with values
        (r"\bHeal equal to ([0-9]+)% of your Max Health\.?", lambda m: f"исцеление равное {m.group(1)}% от вашего макс. здоровья."),
        (r"\bShield equal to ([0-9]+)% of your Max Health\.?", lambda m: f"щит равный {m.group(1)}% от вашего макс. здоровья."),
        (r"\bHeal ({[^}]+})\.", r"исцеление \1."),
        (r"\bHeal ({[^}]+})\b", r"исцеление \1"),
        (r"\bPoison ({[^}]+})\.", r"отравление \1."),
        (r"\bPoison ({[^}]+})\b", r"отравление \1"),
        (r"\bRegen ({[^}]+})\.", r"регенерация \1."),
        (r"\bRegen ({[^}]+})\b", r"регенерация \1"),
        (r"\bBurn ({[^}]+})\.", r"поджог \1."),
        (r"\bBurn ({[^}]+})\b", r"поджог \1"),
        (r"\bShield ({[^}]+})\.", r"щит \1."),
        (r"\bShield ({[^}]+})\b", r"щит \1"),

        # Damage
        (r"\bdeal ({[^}]+}) Damage\.", r"нанесите \1 урона."),
        (r"\bdeal ({[^}]+}) Damage\b", r"нанесите \1 урона"),
        (r"\bDeal ({[^}]+}) Damage\.", r"нанесите \1 урона."),
        (r"\bDeal ({[^}]+}) Damage\b", r"нанесите \1 урона"),

        # Item modifications
        (r"\byour items gain \+?({[^}]+})% Crit Chance for the fight\.?", lambda m: f"ваши предметы получают +{m.group(1)}% к шансу крита до конца боя."),
        (r"\byour items gain \+?({[^}]+}) Damage for the fight\.?", lambda m: f"ваши предметы получают +{m.group(1)} к урону до конца боя."),
        (r"\byour ([A-Z][a-z]+) items? gain \+?({[^}]+}) ([A-Z][a-z]+) for the fight\.?",
         lambda m: f"ваши предметы {translate_term(m.group(1)).lower()} получают +{m.group(2)} {translate_term(m.group(3)).lower()} до конца боя."),
        (r"\bthis gains \+?({[^}]+}) ([A-Z][a-z]+) for the fight\.?",
         lambda m: f"этот предмет получает +{m.group(2)} {translate_term(m.group(2)).lower()} до конца боя."),

        # Adjacent item modifications
        (r"\badjacent items? gain \+?({[^}]+}) ([A-Z][a-z]+) for the fight\.?",
         lambda m: f"соседние предметы получают +{m.group(2)} {translate_term(m.group(2)).lower()} до конца боя."),
        (r"\badjacent ([A-Z][a-z]+) items? gain \+?({[^}]+}) ([A-Z][a-z]+) for the fight\.?",
         lambda m: f"соседние предметы {translate_term(m.group(1)).lower()} получают +{m.group(2)} {translate_term(m.group(3)).lower()} до конца боя."),

        # Other common verbs
        (r"\bReload all your items\.?", "перезарядите все ваши предметы."),
        (r"\breload this\.?", "перезарядите этот предмет."),
        (r"\bReload this\.?", "перезарядите этот предмет."),
        (r"\buse this\.?", "используйте этот предмет."),

        # "gain X" with single placeholder
        (r"\bgain ({[^}]+}) Gold", r"получите \1 золота"),
        (r"\bgain ({[^}]+}) XP", r"получите \1 XP"),
    ]

    for pat, repl in replacements:
        if callable(repl):
            s = re.sub(pat, repl, s)
        else:
            s = re.sub(pat, repl, s)

    return s


# Common item-type targets
def translate_target(t: str) -> str:
    """Translate item-type plurals/singulars in target position."""
    t = t.strip()
    mapping = {
        "items": "предметы", "item": "предмет",
        "enemy items": "вражеские предметы", "enemy item": "вражеский предмет",
        "Weapons": "Оружие", "Weapon": "Оружие",
        "Vehicles": "Транспорт", "Vehicle": "Транспорт",
        "Properties": "Имущество", "Property": "Имущество",
        "Tools": "Инструменты", "Tool": "Инструмент",
        "Tech": "Техника",
        "Food": "Еду",
        "Friends": "Союзники", "Friend": "Союзника",
        "Toys": "Игрушки", "Toy": "Игрушку",
        "Potions": "Зелья", "Potion": "Зелье",
        "Burn items": "предметы поджога", "Burn item": "предмет поджога",
        "Poison items": "предметы яда", "Poison item": "предмет яда",
        "Shield items": "предметы щита", "Shield item": "предмет щита",
        "Heal items": "предметы исцеления", "Heal item": "предмет исцеления",
        "Regen items": "предметы регенерации", "Regen item": "предмет регенерации",
        "Flying items": "Летающие предметы", "Flying item": "Летающий предмет",
        "Relic items": "Реликвии", "Relic item": "Реликвию",
        "Relics": "Реликвии", "Relic": "Реликвию",
        "Small items": "Малые предметы", "Small item": "Малый предмет",
        "Medium items": "Средние предметы", "Medium item": "Средний предмет",
        "Large items": "Большие предметы", "Large item": "Большой предмет",
        "non-Weapon items": "не-Оружейные предметы", "non-Weapon item": "не-Оружейный предмет",
        "adjacent items": "соседние предметы", "adjacent item": "соседний предмет",
        "your items": "ваши предметы", "your other items": "ваши другие предметы",
    }
    if t in mapping:
        return mapping[t]
    # try lowercase
    if t.lower() in {k.lower(): v for k, v in mapping.items()}:
        return {k.lower(): v for k, v in mapping.items()}[t.lower()]
    return t  # fallback: return as-is


def translate_term(t: str) -> str:
    mapping = {
        "Burn": "поджога", "Heal": "к исцелению", "Shield": "щита",
        "Damage": "к урону", "Poison": "яда", "Regen": "к регенерации",
        "Joy": "радости",
    }
    return mapping.get(t, t)


# ---------- main loop ----------

def translate_string(s: str) -> str | None:
    """Try to translate s using pattern rules. Return None if no rule matched."""
    # 1. Match trigger
    for trig_en, trig_ru in TRIGGERS.items():
        if s.startswith(trig_en + ","):
            tail = s[len(trig_en) + 1:].strip()  # text after ", "
            action_ru = translate_action(tail)
            # Heuristic: if action_ru still has uppercase English words (other than placeholders),
            # we probably didn't translate it fully → don't write a half-done translation.
            test = re.sub(r"\{[^}]+\}", "", action_ru)  # strip placeholders
            test = re.sub(r"[A-Z][a-z]+", "", test, count=0)  # actually no — keep
            if re.search(r"\b[A-Z][a-zA-Z]{2,}\b", action_ru):
                # Has English words still → only accept if they're known PROPER nouns or item types we keep
                ok_words = {"XP", "Gold", "Income", "HP", "Crit", "Chance"}
                bad = [w for w in re.findall(r"\b[A-Z][a-zA-Z]{2,}\b", action_ru) if w not in ok_words]
                if bad:
                    return None
            return f"{trig_ru}, {action_ru}"
    return None


def main():
    with open("tools/.translate-claude-todo.json", encoding="utf-8") as f:
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

    print(f"Pattern-translated: {added}")
    print(f"Unmatched (left for DeepSeek or manual): {unmatched}")
    print(f"Total progress: {len(progress)}")


if __name__ == "__main__":
    main()
