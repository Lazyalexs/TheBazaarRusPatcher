"""
Pattern + glossary translator for The Bazaar card text strings.

Input:  .missing-from-ru-RU.json  ({hash: english_text, ...})
Output: .missing-translated.json  ({hash: russian_text, ...})

Approach: apply a long ordered list of (regex, replacement) rules,
then run a glossary substitution pass. Strings that come out
identical to the input (no rule matched) are reported separately
so we can iterate on the rule set.
"""
import json
import re
from pathlib import Path
from collections import Counter

# ----- Glossary: single-word/short-phrase substitutions ----------------------
# Order matters: longer/more-specific keys first. All substitutions are word-
# boundary aware (where \b makes sense for the English token).
GLOSSARY = [
    # Multi-word terms (must precede single-word ones)
    (r"\bCrit Chance\b",      "Шанс крита"),
    (r"\bMax Health\b",       "Макс. здоровья"),
    (r"\bMaxHealth\b",        "Макс. здоровья"),
    (r"\bWhen Sold:\s*",      "При продаже: "),
    (r"\bJust Purchased\b",   "Только что куплено"),
    (r"\bNo Space\b",         "Нет места"),
    (r"\bCannot Afford\b",    "Недостаточно средств"),
    (r"\bLevel up\b",         "Повышение уровня"),
    (r"\bLevel Up\b",         "Повышение уровня"),
    # Mechanics — keep verbs vs nouns mostly distinct
    (r"\bLifesteal\b",        "Вампиризм"),
    (r"\bMulticast\b",        "Мультивыстрел"),
    (r"\bDualcast\b",         "Двойной выстрел"),
    (r"\bTricast\b",          "Тройной выстрел"),
    (r"\bQuadcast\b",         "Четверной выстрел"),
    (r"\bCooldowns\b",        "Перезарядки"),
    (r"\bCooldown\b",         "Перезарядка"),
    (r"\bReloads\b",          "Перезаряжает"),
    (r"\bReload\b",           "Перезарядка"),
    (r"\bRegeneration\b",     "Регенерация"),
    (r"\bRegens\b",           "Регенерирует"),
    (r"\bRegen\b",            "Регенерация"),
    (r"\bRepairs\b",          "Чинит"),
    (r"\bRepair\b",           "Починка"),
    (r"\bShielding\b",        "Щитование"),
    (r"\bShields\b",          "Щиты"),
    (r"\bShield\b",           "Щит"),
    (r"\bHeals\b",            "Лечит"),
    (r"\bHealing\b",          "Лечение"),
    (r"\bHeal\b",             "Лечение"),
    (r"\bBurns\b",            "Поджигает"),
    (r"\bBurned\b",           "Горит"),
    (r"\bBurn\b",             "Поджог"),
    (r"\bPoisons\b",          "Отравляет"),
    (r"\bPoisoned\b",         "Отравлен"),
    (r"\bPoison\b",           "Яд"),
    (r"\bFreezes\b",          "Замораживает"),
    (r"\bFrozen\b",           "Заморожен"),
    (r"\bFreeze\b",           "Заморозка"),
    (r"\bSlows\b",            "Замедляет"),
    (r"\bSlowed\b",           "Замедлен"),
    (r"\bSlow\b",             "Замедление"),
    (r"\bHastes\b",           "Ускоряет"),
    (r"\bHaste\b",            "Ускорение"),
    (r"\bCharges\b",          "Заряды"),
    (r"\bCharge\b",           "Заряд"),
    (r"\bChilled\b",          "охлаждён"),
    (r"\bChill\b",            "охлаждение"),
    (r"\bHeated\b",           "нагрет"),
    (r"\bDamages\b",          "Уроны"),
    (r"\bDamaged\b",          "повреждён"),
    (r"\bDamage\b",           "Урон"),
    (r"\bDestroys\b",         "Уничтожает"),
    (r"\bDestroyed\b",        "уничтожен"),
    (r"\bDestroy\b",          "Уничтожение"),
    (r"\bTransforms\b",       "Трансформирует"),
    (r"\bTransform\b",        "Трансформация"),
    (r"\bUpgrades\b",         "Улучшения"),
    (r"\bUpgrade\b",          "Улучшить"),
    (r"\bEnchants\b",         "Зачаровывает"),
    (r"\bEnchant\b",          "Зачаровать"),
    (r"\bEnraged\b",          "Разъярён"),
    (r"\bEnrage\b",           "Ярость"),
    (r"\bRage\b",             "Ярость"),
    (r"\bRays\b",             "Лучи"),
    (r"\bRay\b",              "Луч"),
    (r"\bDrones\b",           "Дроны"),
    (r"\bDrone\b",            "Дрон"),
    (r"\bDinosaurs\b",        "Динозавры"),
    (r"\bDinosaur\b",         "Динозавр"),
    (r"\bDragons\b",          "Драконы"),
    (r"\bDragon\b",           "Дракон"),
    (r"\bFriends\b",          "Друзья"),
    (r"\bFriend\b",           "Друг"),
    (r"\bFlying\b",           "Летающий"),
    (r"\bAquatic\b",          "Водный"),
    (r"\bRelics\b",           "Реликвии"),
    (r"\bRelic\b",            "Реликвия"),
    (r"\bReagents\b",         "Реагенты"),
    (r"\bReagent\b",          "Реагент"),
    (r"\bIngredients\b",      "Ингредиенты"),
    (r"\bIngredient\b",       "Ингредиент"),
    (r"\bPotions\b",          "Зелья"),
    (r"\bPotion\b",           "Зелье"),
    (r"\bTools\b",            "Инструменты"),
    (r"\bTool\b",             "Инструмент"),
    (r"\bToys\b",             "Игрушки"),
    (r"\bToy\b",              "Игрушка"),
    (r"\bWeapons\b",          "Оружие"),
    (r"\bWeapon\b",           "Оружие"),
    (r"\bVehicles\b",         "Транспорт"),
    (r"\bVehicle\b",          "Транспорт"),
    (r"\bMaps\b",             "Карты"),
    (r"\bMap\b",              "Карта"),
    (r"\bApparels?\b",        "Одежда"),
    (r"\bFood\b",             "Еда"),
    (r"\bAmmo\b",             "Боеприпасы"),
    (r"\bLoot\b",             "Добыча"),
    (r"\bTech\b",             "Техника"),
    (r"\bCore\b",             "Ядро"),
    (r"\bGumballs\b",         "Жвачки"),
    (r"\bGumball\b",          "Жвачка"),
    (r"\bGold\b",             "Золото"),
    (r"\bIncome\b",           "Доход"),
    (r"\bBank\b",             "Банк"),
    (r"\bExperience\b",       "Опыт"),
    (r"\bXP\b",               "опыта"),
    (r"\bPrestige\b",         "Престиж"),
    (r"\bProperties\b",       "Свойства"),
    (r"\bProperty\b",         "Свойство"),
    (r"\bMerchants\b",        "Торговцы"),
    (r"\bMerchant\b",         "Торговец"),
    (r"\bStash\b",            "тайник"),
    (r"\bTrap\b",             "Ловушка"),
    (r"\bJoy\b",              "Радость"),
    (r"\bReroll\b",           "Переброс"),
    (r"\bRerolls\b",          "Перебросы"),
    (r"\bExit\b",             "Покинуть"),
    (r"\bVictories\b",        "Победы"),
    # Common structural words
    (r"\bpermanently\b",      "навсегда"),
    (r"\btemporarily\b",      "временно"),
    (r"\binstead\b",          "вместо этого"),
    (r"\btwice\b",            "вдвое"),
    (r"\bhalf as fast\b",     "вдвое медленнее"),
    (r"\btwice as fast\b",    "вдвое быстрее"),
    (r"\bhalf as long\b",     "вдвое короче"),
    (r"\btwice as long\b",    "вдвое дольше"),
    (r"\bsecond\(s\)\b",      "секунд(ы)"),
    (r"\bseconds\b",          "секунд"),
    (r"\bsecond\b",           "секунду"),
    (r"\bMinute\b",           "минуту"),
    (r"\bdouble\b",           "удвоенный"),
    (r"\bdoubles\b",          "удваивает"),
    (r"\btriple\b",           "утроенный"),
    (r"\bleftmost\b",         "крайний левый"),
    (r"\brightmost\b",        "крайний правый"),
    (r"\badjacent\b",         "соседний"),
    (r"\bAdjacent\b",         "Соседние"),
    (r"\bto the left\b",      "слева"),
    (r"\bto the right\b",     "справа"),
    (r"\bremaining\b",        "осталось"),
    (r"\bRemaining\b",        "Осталось"),
    (r"\bbonus\b",            "бонус"),
    (r"\benemy\b",            "враг"),
    (r"\benemies\b",          "враги"),
    (r"\bowner\b",            "владелец"),
    (r"\bowners\b",           "владельцы"),
    (r"\breward\b",           "награда"),
    (r"\brewards\b",          "награды"),
    # Tier names
    (r"\bBronze-tier\b",      "Бронзовый"),
    (r"\bSilver-tier\b",      "Серебряный"),
    (r"\bGold-tier\b",        "Золотой"),
    (r"\bDiamond-tier\b",     "Алмазный"),
    (r"\bLegendary-tier\b",   "Легендарный"),
    (r"\bBronze\b",           "Бронза"),
    (r"\bSilver\b",           "Серебро"),
    (r"\bDiamond\b",          "Алмаз"),
    (r"\bLegendary\b",        "Легендарный"),
    # Sizes
    (r"\blarge\b",            "большой"),
    (r"\bmedium\b",           "средний"),
    (r"\bsmall\b",            "маленький"),
    # Misc
    (r"\bUnsellable\b",       "Непродаваемый"),
    (r"\bunsellable\b",       "непродаваемый"),
    (r"\bImmune\b",           "Иммунен"),
    (r"\bimmune\b",           "иммунен"),
    (r"\bDay\b",              "День"),
    (r"\bday\b",              "день"),
    (r"\bHour\b",             "Час"),
    (r"\bhour\b",             "час"),
    (r"\bvalue\b",            "ценность"),
    (r"\bValue\b",            "Ценность"),
    (r"\bduration\b",         "длительность"),
    (r"\bDuration\b",         "Длительность"),
    (r"\bitems?\b",           "предмет(ы)"),
    (r"\bCrit\b",             "крит"),
    (r"\bCrits\b",            "криты"),
    (r"\bWin\b",              "Победа"),
    (r"\bwins\b",             "побед"),
    (r"\bwon\b",              "выиграно"),
    (r"\bfight\b",            "бой"),
    (r"\bfights\b",           "бои"),
    (r"\bHealth\b",           "Здоровье"),
    (r"\bhealth\b",           "здоровье"),
    (r"\bcombat\b",           "бой"),
    (r"\bSpare Change\b",     "Сдача"),
    (r"\bChocolate Bars?\b",  "шоколадки"),
    (r"\bBag of Jewels\b",    "Мешок с драгоценностями"),
    (r"\bCatalysts?\b",       "Катализатор"),
    (r"\bSells\b",            "Продаёт"),
    (r"\bBuys\b",             "Покупает"),
    (r"\bSmall and Large\b",  "Маленькие и Большие"),
    (r"\bSmall and Medium\b", "Маленькие и Средние"),
    (r"\bMedium and Large\b", "Средние и Большие"),
    (r"\bSmall\b",            "Маленький"),
    (r"\bMedium\b",           "Средний"),
    (r"\bLarge\b",            "Большой"),
    (r"\bSkill\b",            "Навык"),
    (r"\bskill\b",            "навык"),
    (r"\bHero\b",             "Герой"),
    (r"\bhero\b",             "герой"),
    (r"\bany Hero\b",         "любого героя"),
    (r"\bBoss\b",             "Босс"),
    (r"\bMechanic\b",         "Механик"),
    (r"\bblacksmith\b",       "кузнец"),
    (r"\bshop\b",             "магазин"),
    (r"\bcamp\b",             "лагерь"),
    (r"\bwounds\b",           "раны"),
    (r"\bruins\b",            "руины"),
    (r"\bjungle\b",           "джунгли"),
    (r"\bmushroom\b",         "гриб"),
    (r"\bMountain Pass\b",    "Горный перевал"),
    (r"\bGreenheart\b",       "Зелёное сердце"),
    (r"\bConvoys?\b",         "Караван"),
    (r"\bRaffle Ticket\b",    "Лотерейный билет"),
    (r"\bOld Memories\b",     "Старые воспоминания"),
    (r"\bSurly Mechanic\b",   "Угрюмый механик"),
    (r"\bThe Boss\b",         "Босс"),
]

# ----- Sentence-level templates ----------------------------------------------
# Applied BEFORE the glossary so multi-word English fragments are captured.
# Replacement strings use captured groups (\1, \2, ...) which still contain
# raw English — the glossary pass below converts those.
SENTENCE_RULES = [
    # "Get a Diamond-tier Flying item" / "Get a Silver-tier Weapon"
    (r"^Get a (Bronze|Silver|Gold|Diamond|Legendary)-tier (.+)$",
        r"Получите \1-предмет: \2"),
    (r"^Get a (Bronze|Silver|Gold|Diamond|Legendary) (.+)$",
        r"Получите \1-вариант: \2"),
    # "Get X Gumballs [Gumballs Remaining: N]"
    (r"^Get (\{\w+(?:\.\w+)?\}) Gumballs?\s*\[Gumballs? Remaining: (\d+)\]$",
        r"Получите \1 жвачек [Жвачек осталось: \2]"),
    (r"^Get a Gumball\s*\[Gumballs Remaining: (\d+)\]$",
        r"Получите жвачку [Жвачек осталось: \1]"),
    # "This has double X"
    (r"^This has double (.+)$",          r"У этого предмета двойной \1"),
    # "This has +{X} Multicast" / "This has +{X}% Crit Chance"
    (r"^This has \+(\{[\w.]+\})% (.+)$", r"У этого предмета +\1% \2"),
    (r"^This has \+(\{[\w.]+\}) (.+)$",  r"У этого предмета +\1 \2"),
    (r"^This has (.+)$",                 r"У этого предмета \1"),
    # "This is immune to X"
    (r"^This is immune to (.+)$",        r"Этот предмет иммунен к \1"),
    # "This {verb}s for twice as long"
    (r"^This (\w+)s for twice as long$", r"Этот предмет \1 вдвое дольше"),
    # "When you sell this, your leftmost X gains Y"
    (r"^When you sell this, your leftmost (.+?) gains (.+)$",
        r"Когда вы продаёте, ваш крайний левый \1 получает \2"),
    (r"^When you sell this, your leftmost (.+?) permanently gains (.+)$",
        r"Когда вы продаёте, ваш крайний левый \1 навсегда получает \2"),
    (r"^When you sell this, gain (.+)$",
        r"Когда вы продаёте этот предмет, получите \1"),
    (r"^When you sell this, (.+)$",
        r"Когда вы продаёте этот предмет, \1"),
    # "When you X, Y" — generic
    (r"^When you use another (.+?), Charge this (.+) second(?:\(s\))?$",
        r"Когда вы используете другой \1, заряжайте этот на \2 сек."),
    (r"^When you use another (.+?), (.+)$",
        r"Когда вы используете другой \1, \2"),
    (r"^When you use a (Flying|Aquatic|Friend|Weapon|Shield|Ammo|Vehicle|Reagent|Ingredient|Potion|Tool|Toy|Relic|Map|Property|Food|Apparel) item, (.+)$",
        r"Когда вы используете предмет \1, \2"),
    (r"^When you use a (.+?), (.+)$",
        r"Когда вы используете \1, \2"),
    (r"^When you use an (Ammo) item, (.+)$",
        r"Когда вы используете предмет \1, \2"),
    (r"^When you use the item to the (left|right), (.+)$",
        lambda m: f"Когда вы используете предмет {'слева' if m.group(1) == 'left' else 'справа'}, {m.group(2)}"),
    # "When you Burn/Heal/Slow/Shield/Freeze/Enrage, Y"
    (r"^When you (Burn|Heal|Slow|Shield|Freeze|Charge|Enrage|gain Max Health|use an item), (.+)$",
        r"Когда вы \1, \2"),
    (r"^When your items stop Flying, (.+)$",
        r"Когда ваши предметы перестают быть Летающими, \1"),
    (r"^When one of your items stops Flying, (.+)$",
        r"Когда один из ваших предметов перестаёт быть Летающим, \1"),
    (r"^When this is transformed, (.+)$",
        r"Когда этот предмет трансформирован, \1"),
    (r"^When an enemy uses an item, (.+)$",
        r"Когда враг использует предмет, \1"),
    (r"^When this Crits, (.+)$",
        r"Когда этот предмет наносит крит, \1"),
    (r"^When you crit, (.+)$",
        r"Когда вы наносите крит, \1"),
    # "Your X items have +Y"
    (r"^Your (Flying|Aquatic|Friend|Weapon|Shield|Ammo|Vehicle|Reagent|Ingredient|Potion|Tool|Toy|Relic|Map|Property|Food|Apparel|Lifesteal) items? (?:have|has) \+?(.+)$",
        r"Ваши \1-предметы имеют +\2"),
    (r"^Your Non-(Flying|Aquatic|Friend|Weapon|Shield|Ammo|Vehicle|Reagent|Ingredient|Potion|Tool|Toy|Relic|Map|Property|Food|Apparel) items? (?:have|has) \+?(.+)$",
        r"Ваши не-\1 предметы имеют +\2"),
    (r"^Your items? have \+?(.+)$",
        r"Ваши предметы имеют +\1"),
    (r"^Your items? gain (.+)$",
        r"Ваши предметы получают \1"),
    # "Adjacent X have/has +Y"
    (r"^Adjacent (Flying|Aquatic|Weapon|Shield|Ammo|Vehicle|Property|Properties|items?) (?:have|has) \+?(.+)$",
        r"Соседние предметы (\1) имеют +\2"),
    (r"^Adjacent items? (?:have|has) \+?(.+)$",
        r"Соседние предметы имеют +\1"),
    (r"^Adjacent items?' Cooldowns? are reduced by (.+)$",
        r"Перезарядка соседних предметов уменьшена на \1"),
    (r"^An adjacent item gains (.+)$",
        r"Соседний предмет получает \1"),
    # "Haste/Slow the item to the left/right for X second(s)"
    (r"^(Haste|Slow|Charge) the item to the (left|right) for (.+?) second\(s\)$",
        lambda m: f"{ {'Haste':'Ускорьте', 'Slow':'Замедлите', 'Charge':'Зарядите'}[m.group(1)] } предмет {'слева' if m.group(2)=='left' else 'справа'} на {m.group(3)} сек."),
    # "Gain X Max Health"
    (r"^Gain (.+?) Max Health$",
        r"Получите \1 макс. здоровья"),
    (r"^Gain (.+)$",
        r"Получите \1"),
    # "The item to the right/left gains X"
    (r"^The item to the (left|right) gains (.+)$",
        lambda m: f"Предмет {'слева' if m.group(1)=='left' else 'справа'} получает {m.group(2)}"),
    # "This item's Cooldown is reduced by X second"
    (r"^This item'?s Cooldown is reduced by (.+?) seconds?$",
        r"Перезарядка этого предмета уменьшена на \1 сек."),
    # "This Freezes for twice as long"
    (r"^This (.+?) for twice as long$",
        r"Этот предмет \1 вдвое дольше"),
    # "You are Enraged for ..."
    (r"^You are Enraged for (.+?) shorter \[Total Duration: (.+?)\]$",
        r"Вы в Ярости на \1 короче [Общая длительность: \2]"),
    # "(if you have X)"
    (r"^\(if you have (.+?)\)\s*(.*)$",
        r"(если у вас есть \1) \2"),
    # "Increase the X's Crit Chance by Y%"
    (r"^Increase the (.+?)'s Crit Chance by (.+?)%$",
        r"Увеличивает шанс крита у \1 на \2%"),
    # Generic "X seconds" tail handling

    # Encounter / narrative templates
    (r"^Sells (.+?) items?\.?$",
        r"Продаёт предметы (\1)"),
    (r"^Sells (.+?) items?\. Buys your (.+?) items? at \+?(.+)$",
        r"Продаёт предметы (\1). Покупает ваши предметы (\2) с +\3"),
    (r"^\.\.\.?\s*and get (\d+|a|an) (.+)$",
        r"... и получите \1 \2"),
    (r"^\.\.\.?\s*and get (.+)$",
        r"... и получите \1"),
    (r"^\.\.\.?\s*and (.+)$",
        r"... и \1"),
    (r"^When you win a fight with this, (.+)$",
        r"Когда вы выигрываете бой с этим предметом, \1"),
    (r"^The first time you fall below half Health each fight, (.+)$",
        r"В первый раз, когда вы упадёте ниже половины здоровья в каждом бою, \1"),
    (r"^Get (\{[\w.]+\}) (.+)$",
        r"Получите \1 \2"),
    (r"^Get an? (.+)$",
        r"Получите \1"),
    (r"^Get (\d+) (.+)$",
        r"Получите \1 \2"),
    (r"^You find (.+)$",
        r"Вы находите \1"),
    (r"^You rush back to (.+)$",
        r"Вы возвращаетесь к \1"),
    (r"^Study the (.+)$",
        r"Изучите \1"),
    (r"^Aid the (.+)$",
        r"Помогите \1"),
    (r"^This gains (.+)$",
        r"Этот предмет получает \1"),
    (r"^When this item'?s value reaches (.+?) out of combat, (.+)$",
        r"Когда ценность этого предмета достигает \1 вне боя, \2"),
    (r"^\(if you are (\w+)\) (.+)$",
        r"(если вы — \1) \2"),
]

OUT_DIR = Path(r"E:\memore\the-bazaar-rus-patcher\tools-extract")

def translate(text: str) -> str:
    """Apply sentence rules first, then glossary substitution."""
    s = text
    # Sentence templates (try each; first match transforms it)
    for pattern, repl in SENTENCE_RULES:
        new = re.sub(pattern, repl, s, count=1)
        if new != s:
            s = new
            break
    # Glossary pass — apply all
    for pattern, repl in GLOSSARY:
        s = re.sub(pattern, repl, s)
    # Fix some common artifacts
    s = re.sub(r"\bgain a (\w)", lambda m: f"получите {m.group(1)}", s, flags=re.IGNORECASE)
    s = re.sub(r"\bgains? (\w)", lambda m: f"получает {m.group(1)}", s, flags=re.IGNORECASE)
    return s

def main():
    src = OUT_DIR / ".missing-from-ru-RU.json"
    with src.open(encoding="utf-8") as f:
        missing = json.load(f)

    translated = {}
    unchanged = []
    for h, en in missing.items():
        ru = translate(en)
        translated[h] = ru
        if ru.strip() == en.strip():
            unchanged.append((h, en))

    out = OUT_DIR / ".missing-translated.json"
    with out.open("w", encoding="utf-8") as f:
        json.dump(translated, f, ensure_ascii=False, indent=2)

    # Save unchanged for visibility
    unchanged_path = OUT_DIR / ".missing-translated-unchanged.txt"
    with unchanged_path.open("w", encoding="utf-8") as f:
        for h, en in unchanged:
            f.write(f"{h} | {en}\n")

    print(f"Total entries:     {len(missing)}")
    print(f"Translated:        {len(translated) - len(unchanged)}")
    print(f"Unchanged (no rule matched): {len(unchanged)}")
    print(f"Wrote {out}")
    print(f"Unchanged entries listed in {unchanged_path}")

    # Random spot check
    import random
    keys = list(translated.keys())
    print()
    print("Spot check (10 random):")
    for h in random.sample(keys, min(10, len(keys))):
        print(f"  EN: {missing[h][:80]}")
        print(f"  RU: {translated[h][:80]}")
        print()

if __name__ == "__main__":
    main()
