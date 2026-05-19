"""Aggressive pattern-based translator v2 — covers When/Your/While/You patterns.

Saves only high-confidence translations (no unexpected English words remaining).
"""
import json, hashlib, re, sys, io, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Words that are allowed to remain English in translation (proper nouns, abbreviations)
ALLOWED_ENGLISH = {
    "XP", "HP", "MP", "Vae'rynn",
    "Vanessa", "Dooley", "Stelle", "Pygmalien", "Mak", "Jules", "Karnok",
}


# ---------- Trigger / prefix mapping ----------

WHEN_TRIGGERS = {
    # Action verbs
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
    "When you Sell a Relic": "Когда вы продаёте Реликвию",
    "When you Sell a Reagent": "Когда вы продаёте Реагент",
    "When you Sell a Burn item": "Когда вы продаёте предмет поджога",
    "When you Sell a Poison item": "Когда вы продаёте предмет яда",
    "When you Sell a Shield item": "Когда вы продаёте предмет щита",
    "When you Sell a Heal item": "Когда вы продаёте предмет исцеления",
    "When you Sell a Small item": "Когда вы продаёте Малый предмет",
    "When you Sell a Medium item": "Когда вы продаёте Средний предмет",
    "When you Sell a Large item": "Когда вы продаёте Большой предмет",
    "When you Sell this": "Когда вы продаёте этот предмет",
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
    "When you Buy a Relic": "Когда вы покупаете Реликвию",
    "When you Buy a Reagent": "Когда вы покупаете Реагент",
    "When you Buy a Small item": "Когда вы покупаете Малый предмет",
    "When you Buy a Medium item": "Когда вы покупаете Средний предмет",
    "When you Buy a Large item": "Когда вы покупаете Большой предмет",
    "When you Buy this": "Когда вы покупаете этот предмет",
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
    "When you stop being Enraged": "Когда вы перестаёте быть в ярости",
    "When you Repair": "Когда вы чините",
    "When you Destroy an item": "Когда вы уничтожаете предмет",
    "When you destroy an item": "Когда вы уничтожаете предмет",
    "When you gain Gold": "Когда вы получаете золото",
    "When you gain XP": "Когда вы получаете XP",
    "When you gain Income": "Когда вы получаете доход",
    "When you gain Max Health": "Когда вы получаете макс. здоровье",
    "When you take Damage": "Когда вы получаете урон",
    "When you Equip a Weapon": "Когда вы экипируете Оружие",
    "When you Equip an item": "Когда вы экипируете предмет",
    "When you Equip this": "Когда вы экипируете этот предмет",
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
    "When you Crit with a Weapon": "Когда вы наносите критический удар Оружием",
    "When you Crit with a Flying item": "Когда вы наносите критический удар Летающим предметом",
    "When you Crit with a Shield item": "Когда вы наносите критический удар предметом щита",
    "When you Crit with a Burn item": "Когда вы наносите критический удар предметом поджога",
    "When you Crit with a Poison item": "Когда вы наносите критический удар предметом яда",
    "When you Crit with a Heal item": "Когда вы наносите критический удар предметом исцеления",
    "When you Crit with an adjacent item": "Когда вы наносите критический удар соседним предметом",
    "When you Slow an enemy item": "Когда вы замедляете вражеский предмет",
    "When you Slow an item": "Когда вы замедляете предмет",
    "When you Freeze an enemy item": "Когда вы замораживаете вражеский предмет",
    "When you Freeze an item": "Когда вы замораживаете предмет",
    "When you Haste a Friend": "Когда вы ускоряете Союзника",
    "When you Haste an adjacent item": "Когда вы ускоряете соседний предмет",
    "When you Haste an item": "Когда вы ускоряете предмет",
    "When you Heal a Friend": "Когда вы исцеляете Союзника",
    "When you Heal an adjacent item": "Когда вы исцеляете соседний предмет",
    "When you Burn an enemy": "Когда вы поджигаете врага",
    "When you Poison an enemy": "Когда вы отравляете врага",
    "When you Poison an enemy item": "Когда вы отравляете вражеский предмет",
    "When you Repair a Vehicle": "Когда вы чините Транспорт",
    "When you Repair an item": "Когда вы чините предмет",
    "When you Repair this": "Когда вы чините этот предмет",
    "When you reload an enemy item": "Когда вы перезаряжаете вражеский предмет",
    "When you stop being Slowed": "Когда вас перестают замедлять",
    "When you stop being Frozen": "Когда вас перестают замораживать",
    "When you stop being Burned": "Когда вас перестают поджигать",
    "When you stop being Poisoned": "Когда вас перестают отравлять",
    "When you destroy this": "Когда вы уничтожаете этот предмет",
    "When you Destroy this": "Когда вы уничтожаете этот предмет",
    "When you gain Crit": "Когда вы получаете крит",
    "When you gain a charge": "Когда вы получаете заряд",
    # Compound "or" triggers
    "When you use a Vehicle or Flying item": "Когда вы используете Транспорт или Летающий предмет",
    "When you use a Weapon or Shield item": "Когда вы используете Оружие или предмет щита",
    "When you use a Weapon or Tool": "Когда вы используете Оружие или Инструмент",
    "When you use a Toy or Friend": "Когда вы используете Игрушку или Союзника",
    "When you use a Toy or Food": "Когда вы используете Игрушку или Еду",
    "When you use a Property or Vehicle": "Когда вы используете Имущество или Транспорт",
    "When you use a Friend or Toy": "Когда вы используете Союзника или Игрушку",
    "When you use a Friend or Food": "Когда вы используете Союзника или Еду",
    "When you use a Burn or Poison item": "Когда вы используете предмет поджога или яда",
    "When you use an Enchanted item": "Когда вы используете Зачарованный предмет",
    "When you use an Enchanted or Heated item": "Когда вы используете Зачарованный или Раскалённый предмет",
    "When you use an Ammo item": "Когда вы используете предмет боезапаса",
    "When you use an Aquatic item": "Когда вы используете Морской предмет",
    "When you use your leftmost item": "Когда вы используете крайний левый предмет",
    "When you use your rightmost item": "Когда вы используете крайний правый предмет",
    "When you use the item to the left of this": "Когда вы используете предмет слева от этого",
    "When you use the item to the right of this": "Когда вы используете предмет справа от этого",
    "When you use the Weapon to the left of this": "Когда вы используете Оружие слева от этого",
    "When you use the Weapon to the right of this": "Когда вы используете Оружие справа от этого",
    "When you use an adjacent Weapon": "Когда вы используете соседнее Оружие",
    "When you use an adjacent Food": "Когда вы используете соседнюю Еду",
    "When you use an adjacent Property": "Когда вы используете соседнее Имущество",
    "When you use an adjacent Burn item": "Когда вы используете соседний предмет поджога",
    "When you use an adjacent Poison item": "Когда вы используете соседний предмет яда",
    "When you use an item with Ammo": "Когда вы используете предмет с боезапасом",
    "When you use an item with Cooldown": "Когда вы используете предмет с перезарядкой",
    "When you sell this, your leftmost item": "Когда вы продаёте этот предмет, ваш крайний левый предмет",
    "When you sell this, your rightmost item": "Когда вы продаёте этот предмет, ваш крайний правый предмет",
    "When you sell this": "Когда вы продаёте этот предмет",
    "When your items run out of Ammo": "Когда у ваших предметов кончается боезапас",
    "When your items run out of Cooldown": "Когда у ваших предметов кончается перезарядка",
}

WHILE_PATTERNS = [
    (r"^While in play, ", "Пока в игре, "),
    (r"^While this is Flying, ", "Пока этот предмет летает, "),
    (r"^While this is Frozen, ", "Пока этот предмет заморожен, "),
    (r"^While this is Slowed, ", "Пока этот предмет замедлен, "),
    (r"^While this is Hasted, ", "Пока этот предмет ускорен, "),
    (r"^While this is Burning, ", "Пока этот предмет горит, "),
    (r"^While this is Poisoned, ", "Пока этот предмет отравлен, "),
    (r"^While an enemy item is Slowed, ", "Пока вражеский предмет замедлен, "),
    (r"^While an enemy item is Frozen, ", "Пока вражеский предмет заморожен, "),
    (r"^While an enemy item is Burning, ", "Пока вражеский предмет горит, "),
    (r"^While an enemy item is Poisoned, ", "Пока вражеский предмет отравлен, "),
    (r"^While you are Enraged, ", "Пока вы в ярости, "),
    (r"^While you have ", "Пока у вас есть "),
    (r"^While you are ", "Пока вы "),
]


YOU_PATTERNS = [
    (r"^You are Enraged for ({[^}]+}) seconds? longer\s*", r"Вы в ярости на \1 сек. дольше"),
    (r"^You are Enraged for ({[^}]+}) seconds? shorter\s*", r"Вы в ярости на \1 сек. короче"),
    (r"^You are Enraged for 1 second longer", "Вы в ярости на 1 сек. дольше"),
    (r"^You are Enraged for 1 second shorter", "Вы в ярости на 1 сек. короче"),
    (r"^You have ", "У вас есть "),
    (r"^You start", "Вы начинаете"),
    (r"^You gain ", "Вы получаете "),
    (r"^You are ", "Вы "),
]


# ---------- Action translation rules ----------

ITEM_TYPES = {
    "Weapons": "Оружие", "Weapon": "Оружие",
    "Vehicles": "Транспорт", "Vehicle": "Транспорт",
    "Properties": "Имущество", "Property": "Имущество",
    "Tools": "Инструменты", "Tool": "Инструмент",
    "Tech items": "Техника", "Tech item": "Техника", "Tech": "Техника",
    "Food": "Еда",
    "Aquatic items": "Морские предметы", "Aquatic item": "Морской предмет", "Aquatic": "Морской",
    "Apparel": "Снаряжение",
    "Friends": "Союзники", "Friend": "Союзник",
    "Toys": "Игрушки", "Toy": "Игрушка",
    "Potions": "Зелья", "Potion": "Зелье",
    "Relics": "Реликвии", "Relic": "Реликвия",
    "Burn items": "предметы поджога", "Burn item": "предмет поджога",
    "Poison items": "предметы яда", "Poison item": "предмет яда",
    "Shield items": "предметы щита", "Shield item": "предмет щита",
    "Heal items": "предметы исцеления", "Heal item": "предмет исцеления",
    "Regen items": "предметы регенерации", "Regen item": "предмет регенерации",
    "Slow items": "предметы замедления",
    "Freeze items": "предметы заморозки",
    "Haste items": "предметы ускорения",
    "Crit items": "предметы крита",
    "Flying items": "Летающие предметы", "Flying item": "Летающий предмет",
    "Small items": "Малые предметы", "Small item": "Малый предмет",
    "Medium items": "Средние предметы", "Medium item": "Средний предмет",
    "Large items": "Большие предметы", "Large item": "Большой предмет",
    "Ammo items": "предметы боезапаса", "Ammo item": "предмет боезапаса",
    "Core items": "предметы-Ядра", "Core item": "предмет-Ядро", "Core": "Ядро",
    "Reagent items": "предметы-Реагенты", "Reagent": "Реагент",
}

EFFECTS_NOUN = {
    "Damage": "урон", "Burn": "поджог", "Heal": "исцеление", "Shield": "щит",
    "Poison": "яд", "Freeze": "заморозка", "Slow": "замедление", "Haste": "ускорение",
    "Regen": "регенерация", "Crit": "крит", "Ammo": "боезапас", "Max Ammo": "макс. боезапас",
    "Cooldown": "перезарядка", "Multicast": "мультикаст", "Lifesteal": "вампиризм",
    "Income": "доход", "Gold": "золото", "Stamina": "выносливость",
    "Health": "здоровье", "Max Health": "макс. здоровье", "Crit Chance": "шанс крита",
    "Joy": "радость", "Value": "стоимость",
}

EFFECTS_DATIVE = {  # "+X к Y"
    "Damage": "к урону", "Burn": "к поджогу", "Heal": "к исцелению", "Shield": "к щиту",
    "Poison": "к яду", "Regen": "к регенерации",
    "Crit Chance": "к шансу крита", "Max Health": "к макс. здоровью",
    "Ammo": "к боезапасу", "Max Ammo": "к макс. боезапасу",
}


def translate_action(action: str) -> str:
    """Apply action-level regex substitutions."""
    s = action

    # Common substitutions first
    rules = [
        # Charge
        (r"\bCharge this ({[^}]+}) seconds?\.?", lambda m: f"зарядите этот предмет на {m.group(1)} сек."),
        (r"\bCharge this ({[^}]+}) second\(s\)\.?", lambda m: f"зарядите этот предмет на {m.group(1)} сек."),
        (r"\bCharge an adjacent item ({[^}]+}) second\(s\)\.?", lambda m: f"зарядите соседний предмет на {m.group(1)} сек."),
        (r"\bCharge an item ({[^}]+}) second\(s\)\.?", lambda m: f"зарядите предмет на {m.group(1)} сек."),
        (r"\bCharge a ([A-Z][a-z ]+?) ({[^}]+}) second\(s\)\.?", lambda m: f"зарядите {translate_target_lower(m.group(1))} на {m.group(2)} сек."),
        (r"\bCharge your ([^,.]+?) items? ({[^}]+}) second\(s\)\.?", lambda m: f"зарядите ваши {translate_target_lower(m.group(1)+' items')} на {m.group(2)} сек."),
        (r"\bCharge your Relics ({[^}]+}) second\.?", lambda m: f"зарядите ваши Реликвии на {m.group(1)} сек."),
        (r"\bCharge ({[^}]+}) second\(s\)\.?", lambda m: f"зарядите на {m.group(1)} сек."),

        # Freeze
        (r"\bFreeze all ([^,.]+?) for ({[^}]+}) second\(s\)\.?", lambda m: f"заморозьте все {translate_target_lower(m.group(1))} на {m.group(2)} сек."),
        (r"\bFreeze ({[^}]+}) ([^,.]+?) for ({[^}]+}) second\(s\)\.?", lambda m: f"заморозьте {m.group(1)} {translate_target_lower(m.group(2))} на {m.group(3)} сек."),
        (r"\bFreeze an adjacent item for ({[^}]+}) second\(s\)\.?", lambda m: f"заморозьте соседний предмет на {m.group(1)} сек."),
        (r"\bFreeze an enemy item for ({[^}]+}) second\(s\)\.?", lambda m: f"заморозьте вражеский предмет на {m.group(1)} сек."),
        (r"\bFreeze an item for ({[^}]+}) second\(s\)\.?", lambda m: f"заморозьте предмет на {m.group(1)} сек."),

        # Haste
        (r"\bHaste all ([^,.]+?) for ({[^}]+}) second\(s\)\.?", lambda m: f"ускорьте все {translate_target_lower(m.group(1))} на {m.group(2)} сек."),
        (r"\bHaste ({[^}]+}) ([^,.]+?) for ({[^}]+}) second\(s\)\.?", lambda m: f"ускорьте {m.group(1)} {translate_target_lower(m.group(2))} на {m.group(3)} сек."),
        (r"\bHaste an adjacent item for ({[^}]+}) second\(s\)\.?", lambda m: f"ускорьте соседний предмет на {m.group(1)} сек."),
        (r"\bHaste your other items for ({[^}]+}) seconds?\.?", lambda m: f"ускорьте ваши другие предметы на {m.group(1)} сек."),
        (r"\bHaste your ([^,.]+?) items? for ({[^}]+}) second\(s\)\.?", lambda m: f"ускорьте ваши {translate_target_lower(m.group(1)+' items')} на {m.group(2)} сек."),
        (r"\bHaste your items for ({[^}]+}) second\(s\)\.?", lambda m: f"ускорьте ваши предметы на {m.group(1)} сек."),
        (r"\bHaste a ([A-Z][a-z ]+?) for ({[^}]+}) second\(s\)\.?", lambda m: f"ускорьте {translate_target_lower(m.group(1))} на {m.group(2)} сек."),
        (r"\bHaste an item for ({[^}]+}) second\(s\)\.?", lambda m: f"ускорьте предмет на {m.group(1)} сек."),

        # Slow
        (r"\bSlow all enemy items for ({[^}]+}) second\(s\)\.?", lambda m: f"замедлите все вражеские предметы на {m.group(1)} сек."),
        (r"\bSlow ({[^}]+}) ([^,.]+?) for ({[^}]+}) second\(s\)\.?", lambda m: f"замедлите {m.group(1)} {translate_target_lower(m.group(2))} на {m.group(3)} сек."),
        (r"\bSlow an adjacent item for ({[^}]+}) second\(s\)\.?", lambda m: f"замедлите соседний предмет на {m.group(1)} сек."),
        (r"\bSlow an enemy item for ({[^}]+}) second\(s\)\.?", lambda m: f"замедлите вражеский предмет на {m.group(1)} сек."),
        (r"\bSlow an item for ({[^}]+}) second\(s\)\.?", lambda m: f"замедлите предмет на {m.group(1)} сек."),

        # Heal / Poison / Regen / Burn / Shield
        (r"\bHeal equal to ([0-9]+)% of your Max Health\.?", lambda m: f"исцеление равное {m.group(1)}% от вашего макс. здоровья."),
        (r"\bShield equal to ([0-9]+)% of your Max Health\.?", lambda m: f"щит равный {m.group(1)}% от вашего макс. здоровья."),
        (r"\bHeal equal to ({[^}]+}) times this item's Poison\.?", lambda m: f"исцеление равное {m.group(1)} от яда этого предмета."),
        (r"\bShield equal to ({[^}]+}) times this item's Poison\.?", lambda m: f"щит равный {m.group(1)} от яда этого предмета."),
        (r"\bBurn equal to this item's Poison\.?", "поджог равный яду этого предмета."),
        (r"\bRegen equal to this item's Poison\.?", "регенерация равная яду этого предмета."),
        (r"\bdeal Damage equal to ({[^}]+}) times this item's Poison\.?", lambda m: f"нанесите урон равный {m.group(1)} от яда этого предмета."),
        (r"\bHeal to full\.?", "исцелитесь полностью."),
        (r"\bHeal ({[^}]+})\.?", lambda m: f"исцеление {m.group(1)}."),
        (r"\bPoison ({[^}]+})\.?", lambda m: f"отравление {m.group(1)}."),
        (r"\bRegen ({[^}]+})\.?", lambda m: f"регенерация {m.group(1)}."),
        (r"\bBurn ({[^}]+})\.?", lambda m: f"поджог {m.group(1)}."),
        (r"\bShield ({[^}]+})\.?", lambda m: f"щит {m.group(1)}."),

        # Damage
        (r"\bdeal ({[^}]+}) Damage\.?", lambda m: f"нанесите {m.group(1)} урона."),
        (r"\bDeal ({[^}]+}) Damage\.?", lambda m: f"нанесите {m.group(1)} урона."),

        # Item modifications (for the fight)
        (r"\byour items gain \+?({[^}]+})% Crit Chance for the fight\.?",
         lambda m: f"ваши предметы получают +{m.group(1)}% к шансу крита до конца боя."),
        (r"\byour items gain \+?({[^}]+}) Damage for the fight\.?",
         lambda m: f"ваши предметы получают +{m.group(1)} к урону до конца боя."),
        (r"\byour ([A-Z][a-z]+ items?) gain \+?({[^}]+}) ([A-Z][a-z]+) for the fight\.?",
         lambda m: f"ваши {translate_target_lower(m.group(1))} получают +{m.group(2)} {EFFECTS_DATIVE.get(m.group(3), m.group(3).lower())} до конца боя."),
        (r"\bthis gains \+?({[^}]+}) ([A-Z][a-z]+) for the fight\.?",
         lambda m: f"этот предмет получает +{m.group(1)} {EFFECTS_DATIVE.get(m.group(2), m.group(2).lower())} до конца боя."),
        (r"\badjacent items? gain \+?({[^}]+}) ([A-Z][a-z]+) for the fight\.?",
         lambda m: f"соседние предметы получают +{m.group(1)} {EFFECTS_DATIVE.get(m.group(2), m.group(2).lower())} до конца боя."),
        (r"\badjacent ([A-Z][a-z]+ items?) gain \+?({[^}]+}) ([A-Z][a-z]+) for the fight\.?",
         lambda m: f"соседние {translate_target_lower(m.group(1))} получают +{m.group(2)} {EFFECTS_DATIVE.get(m.group(3), m.group(3).lower())} до конца боя."),

        # Cooldown reduction
        (r"\breduce its Cooldown by ({[^}]+})% for the fight\.?", lambda m: f"его перезарядка снижается на {m.group(1)}% до конца боя."),

        # use this / reload this
        (r"\bReload all your items\.?", "перезарядите все ваши предметы."),
        (r"\breload this\.?", "перезарядите этот предмет."),
        (r"\bReload this\.?", "перезарядите этот предмет."),
        (r"\buse this\.?", "используйте этот предмет."),

        # gain X
        (r"\bgain ({[^}]+}) Gold\.?", lambda m: f"получите {m.group(1)} золота."),
        (r"\bgain ({[^}]+}) XP\.?", lambda m: f"получите {m.group(1)} XP."),
        (r"\bgain ({[^}]+}) Max Health for the fight\.?", lambda m: f"получите {m.group(1)} к макс. здоровью до конца боя."),

        # destroy
        (r"\bdestroy this and a Small enemy item for the fight\.?", "уничтожьте этот предмет и Малый вражеский предмет до конца боя."),

        # "it" pronoun referring to just-used item
        (r"\bHaste it for ({[^}]+}) second\(s\)\.?", lambda m: f"ускорьте его на {m.group(1)} сек."),
        (r"\bFreeze it for ({[^}]+}) second\(s\)\.?", lambda m: f"заморозьте его на {m.group(1)} сек."),
        (r"\bSlow it for ({[^}]+}) second\(s\)\.?", lambda m: f"замедлите его на {m.group(1)} сек."),
        (r"\bCharge it for ({[^}]+}) second\(s\)\.?", lambda m: f"зарядите его на {m.group(1)} сек."),

        # Charge other / adjacent
        (r"\bCharge the other adjacent item for ({[^}]+}) second\(s\)\.?",
         lambda m: f"зарядите другой соседний предмет на {m.group(1)} сек."),
        (r"\bCharge another item for ({[^}]+}) second\(s\)\.?",
         lambda m: f"зарядите другой предмет на {m.group(1)} сек."),

        # Items adjacent to it
        (r"\bWeapons adjacent to it gain \+?({[^}]+}) Damage for the fight\.?",
         lambda m: f"Оружие рядом с ним получает +{m.group(1)} к урону до конца боя."),
        (r"\bitems? adjacent to it gain \+?({[^}]+}) ([A-Z][a-z]+) for the fight\.?",
         lambda m: f"предметы рядом с ним получают +{m.group(1)} {EFFECTS_DATIVE.get(m.group(2), m.group(2).lower())} до конца боя."),
        (r"\b([A-Z][a-z]+ items?) adjacent to it gain \+?({[^}]+}) ([A-Z][a-z]+) for the fight\.?",
         lambda m: f"{translate_phrase(m.group(1))} рядом с ним получают +{m.group(2)} {EFFECTS_DATIVE.get(m.group(3), m.group(3).lower())} до конца боя."),

        # gain Rage / etc.
        (r"\bgain ({[^}]+}) Rage\.?", lambda m: f"получите {m.group(1)} ярости."),

        # "give your Leftmost X"
        (r"\bgive your Leftmost Weapon \+?({[^}]+}) damage for the fight\.?",
         lambda m: f"дайте вашему крайнему левому Оружию +{m.group(1)} к урону до конца боя."),
        (r"\bgive your Rightmost Weapon \+?({[^}]+}) damage for the fight\.?",
         lambda m: f"дайте вашему крайнему правому Оружию +{m.group(1)} к урону до конца боя."),

        # Burn/Heal/Shield/Damage equal to X% of this item's Y
        (r"\bBurn equal to ([0-9]+)% of this item's ([A-Z][a-z]+)\.?",
         lambda m: f"поджог равный {m.group(1)}% от {translate_term(m.group(2))} этого предмета."),
        (r"\bHeal equal to ([0-9]+)% of this item's ([A-Z][a-z]+)\.?",
         lambda m: f"исцеление равное {m.group(1)}% от {translate_term(m.group(2))} этого предмета."),
        (r"\bShield equal to ([0-9]+)% of this item's ([A-Z][a-z]+)\.?",
         lambda m: f"щит равный {m.group(1)}% от {translate_term(m.group(2))} этого предмета."),
        (r"\bPoison equal to ([0-9]+)% of this item's ([A-Z][a-z]+)\.?",
         lambda m: f"отравление равное {m.group(1)}% от {translate_term(m.group(2))} этого предмета."),
        (r"\bdeal Damage equal to ([0-9]+)% of this item's ([A-Z][a-z]+)\.?",
         lambda m: f"нанесите урон равный {m.group(1)}% от {translate_term(m.group(2))} этого предмета."),
    ]

    for pat, repl in rules:
        s = re.sub(pat, repl, s)

    return s


def translate_term(t: str) -> str:
    """Genitive form for 'equal to N% of this item's Y'."""
    mapping = {
        "Burn": "поджога", "Heal": "исцеления", "Shield": "щита",
        "Damage": "урона", "Poison": "яда", "Regen": "регенерации",
        "Joy": "радости", "Value": "стоимости", "Crit": "крита",
        "Ammo": "боезапаса",
    }
    return mapping.get(t, t.lower())


def translate_target_lower(t: str) -> str:
    """Translate item-type target to lowercase Russian."""
    t = t.strip()
    m = ITEM_TYPES.get(t)
    if m:
        return m.lower() if not m[0].isupper() or m.split()[0].isupper() else m.lower()
    # Try matching individual words
    return t.lower()


# Your X patterns (passive item bonuses)
def translate_your(s: str) -> str | None:
    """Translate 'Your X items <verb> Y' patterns."""
    # Your items gain +N Y for the fight.
    rules = [
        (r"^Your items gain \+?({[^}]+}) Damage for the fight\.?",
         lambda m: f"Ваши предметы получают +{m.group(1)} к урону до конца боя."),
        (r"^Your items gain \+?({[^}]+})% Crit Chance for the fight\.?",
         lambda m: f"Ваши предметы получают +{m.group(1)}% к шансу крита до конца боя."),
        (r"^Your items gain \+?({[^}]+}) ([A-Z][a-z]+) for the fight\.?",
         lambda m: f"Ваши предметы получают +{m.group(1)} {EFFECTS_DATIVE.get(m.group(2), m.group(2).lower())} до конца боя."),
        (r"^Your items have \+?({[^}]+})% Crit Chance\.?",
         lambda m: f"Ваши предметы имеют +{m.group(1)}% к шансу крита."),
        (r"^Your items have \+?({[^}]+}) ([A-Z][a-z]+)\.?",
         lambda m: f"Ваши предметы имеют +{m.group(1)} {EFFECTS_DATIVE.get(m.group(2), m.group(2).lower())}."),

        # Your X items gain/have +N Y for the fight
        (r"^Your ([A-Z][a-z]+(?: and [A-Z][a-z]+)? items?) gain \+?({[^}]+}) ([A-Z][a-z]+) for the fight\.?",
         lambda m: f"Ваши {translate_phrase(m.group(1))} получают +{m.group(2)} {EFFECTS_DATIVE.get(m.group(3), m.group(3).lower())} до конца боя."),
        (r"^Your ([A-Z][a-z]+(?: and [A-Z][a-z]+)? items?) have \+?({[^}]+})% Crit Chance\.?",
         lambda m: f"Ваши {translate_phrase(m.group(1))} имеют +{m.group(2)}% к шансу крита."),
        (r"^Your ([A-Z][a-z]+(?: and [A-Z][a-z]+)? items?) have \+?({[^}]+}) ([A-Z][a-z]+)\.?",
         lambda m: f"Ваши {translate_phrase(m.group(1))} имеют +{m.group(2)} {EFFECTS_DATIVE.get(m.group(3), m.group(3).lower())}."),
        (r"^Your ([A-Z][a-z]+(?: and [A-Z][a-z]+)? items?) gain \+?({[^}]+})% Crit Chance for the fight\.?",
         lambda m: f"Ваши {translate_phrase(m.group(1))} получают +{m.group(2)}% к шансу крита до конца боя."),
        (r"^Your ([A-Z][a-z]+(?: and [A-Z][a-z]+)? items?) deal \+?({[^}]+}) Damage\.?",
         lambda m: f"Ваши {translate_phrase(m.group(1))} наносят +{m.group(2)} к урону."),

        # Your X Y deal +N Damage. (where Y is item type, e.g. Aquatic Weapons)
        (r"^Your ([A-Z][a-z]+) Weapons deal \+?({[^}]+}) Damage\.?",
         lambda m: f"Ваше Оружие типа \"{translate_phrase(m.group(1))}\" наносит +{m.group(2)} к урону."),
        (r"^Your ([A-Z][a-z]+) Weapons gain \+?({[^}]+}) Damage for the fight\.?",
         lambda m: f"Ваше Оружие типа \"{translate_phrase(m.group(1))}\" получает +{m.group(2)} к урону до конца боя."),

        # Your X items are Friends
        (r"^Your Aquatic items are Friends\.?", "Ваши Морские предметы являются Союзниками."),

        # Your X items are affected by Freeze and Slow for half as long
        (r"^Your Aquatic items are affected by Freeze and Slow for half as long\.?",
         "На ваши Морские предметы Заморозка и Замедление действуют вдвое короче."),
    ]
    for pat, repl in rules:
        m = re.match(pat, s)
        if m:
            return repl(m) if callable(repl) else m.expand(repl)
    return None


def translate_phrase(p: str) -> str:
    """Translate a phrase like 'Aquatic and Toy items' or 'Burn items'."""
    p = p.strip()
    if p in ITEM_TYPES:
        return ITEM_TYPES[p].lower() if ITEM_TYPES[p][0].islower() else ITEM_TYPES[p]
    # Handle "X and Y items"
    m = re.match(r"^([A-Z][a-z]+) and ([A-Z][a-z]+) items?$", p)
    if m:
        a = ITEM_TYPES.get(m.group(1), m.group(1))
        b = ITEM_TYPES.get(m.group(2), m.group(2))
        return f"{a.lower()} и {b.lower()} предметы"
    # Try as type name
    return ITEM_TYPES.get(p, p)


def looks_translated(ru: str) -> bool:
    """Heuristic: does this look fully Russian?"""
    test = re.sub(r"\{[^{}]+\}", "", ru)  # strip placeholders
    test = re.sub(r"\[[^\]]+\]", "", test)  # strip bracket annotations
    for ok in ALLOWED_ENGLISH:
        test = test.replace(ok, "")
    # Find English words (2+ consecutive Latin letters)
    bad_words = re.findall(r"\b[A-Za-z]{2,}\b", test)
    return len(bad_words) == 0


def translate_when(s: str) -> str | None:
    # Find longest matching trigger prefix
    best = None
    for trig_en, trig_ru in WHEN_TRIGGERS.items():
        if s.startswith(trig_en + ",") or s.startswith(trig_en + " "):
            if best is None or len(trig_en) > len(best[0]):
                best = (trig_en, trig_ru)
    if not best:
        return None
    trig_en, trig_ru = best
    tail = s[len(trig_en):].lstrip(", ").strip()
    action_ru = translate_action(tail)
    result = f"{trig_ru}, {action_ru}"
    return result if looks_translated(result) else None


def translate_while(s: str) -> str | None:
    for pat, repl in WHILE_PATTERNS:
        if re.match(pat, s):
            head = re.sub(pat, repl, s, count=1)
            # head now has Russian prefix + English tail
            # Extract tail manually
            m = re.match(pat, s)
            tail = s[m.end():]
            action_ru = translate_action(tail)
            result = re.sub(pat, repl, s, count=1).split(', ', 1)[0] + ", " + action_ru if ',' in repl else repl + action_ru
            # Simpler: just do prefix substitution + translate action
            result = repl + action_ru
            return result if looks_translated(result) else None
    return None


def translate_you(s: str) -> str | None:
    for pat, repl in YOU_PATTERNS:
        if re.match(pat, s):
            head_m = re.match(pat, s)
            tail = s[head_m.end():]
            head_ru = re.sub(pat, repl, s[:head_m.end()])
            action_ru = translate_action(tail)
            result = head_ru + action_ru
            return result if looks_translated(result) else None
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
    with open("tools/.translate-combined-todo.json", encoding="utf-8") as f:
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
    print(f"Unmatched: {unmatched}")
    print(f"Total progress: {len(progress)}")


if __name__ == "__main__":
    main()
