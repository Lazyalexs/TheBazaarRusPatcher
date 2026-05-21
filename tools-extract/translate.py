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
    # "items" and "item" — context-sensitive. Sentence templates handle most
    # cases; here we only do safe defaults (singular -> "предмет",
    # plural -> "предметы"). Order matters: longer pattern first.
    (r"\bitems\b",            "предметы"),
    (r"\bItems\b",            "Предметы"),
    (r"\bitem\b",             "предмет"),
    (r"\bItem\b",             "Предмет"),
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
    # "When you Burn/Heal/Slow/Shield/Freeze/Enrage, Y" — explicit verb list
    (r"^When you (Burn|Heal|Slow|Shield|Freeze|Charge|Enrage|Haste|Crit|Poison|Regen|Destroy|Transform|Enchant|Sell|Buy|Repair|Reroll|gain Max Health|use an item|use a Skill|win a fight|lose a fight), (.+)$",
        r"Когда вы \1, \2"),
    # Catch-all "When you X, Y" — preserve X for glossary/phrase pass to translate
    (r"^When you (.+?), (.+)$",
        r"Когда вы \1, \2"),
    # "When your X" / "When this X" / "When an enemy X"
    (r"^When your enemy uses their (.+?), (.+)$",
        r"Когда враг использует свой \1, \2"),
    (r"^When your Enemy uses their (.+?), (.+)$",
        r"Когда враг использует свой \1, \2"),
    (r"^When your (.+?) items? (.+)$",
        r"Когда ваши \1 предметы \2"),
    (r"^When your (.+)$",
        r"Когда ваш \1"),
    (r"^When this (.+?), (.+)$",
        r"Когда этот предмет \1, \2"),
    (r"^When this (.+)$",
        r"Когда этот предмет \1"),
    (r"^When (an?|the) (.+?) is (destroyed|sold|bought|enchanted), (.+)$",
        r"Когда \1 \2 \3, \4"),
    # "Haste/Slow/Freeze/Charge X for Y second(s)" — full sentence
    (r"^(Haste|Slow|Freeze|Charge) (.+?) for (.+?) seconds?\(?s?\)?$",
        lambda m: f"{ {'Haste':'Ускорьте','Slow':'Замедлите','Freeze':'Заморозьте','Charge':'Зарядите'}[m.group(1)] } {m.group(2)} на {m.group(3)} сек."),
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

# ----- Phrase rules: substring patterns, applied ALL in order -----
# Run after the (single matching) sentence template, before the word glossary.
# These handle the leftover English fragments inside a sentence body the
# template captured but didn't translate (e.g. "Когда вы X, gain {Y}" still
# needs "gain" -> "получите").
PHRASE_RULES = [
    # Verbs taking "an item" / "the item"
    (r"\bHaste an item\b",       "ускорьте предмет"),
    (r"\bSlow an item\b",        "замедлите предмет"),
    (r"\bFreeze an item\b",      "заморозьте предмет"),
    (r"\bCharge an item\b",      "зарядите предмет"),
    (r"\bShield an item\b",      "защитите предмет"),
    (r"\bDestroy an item\b",     "уничтожьте предмет"),
    (r"\bHeal an item\b",        "восстановите предмет"),
    (r"\banother (\w+) item\b",  r"другой \1 предмет"),
    (r"\bAdjacent items?\b",     "Соседние предметы"),
    (r"\badjacent items?\b",     "соседние предметы"),
    (r"\bAn adjacent item\b",    "Соседний предмет"),
    (r"\ban adjacent item\b",    "соседний предмет"),
    (r"\banother item\b",        "другой предмет"),
    (r"\bany item\b",            "любой предмет"),
    (r"\ban item\b",             "предмет"),
    (r"\bthe item\b",            "предмет"),
    (r"\bthis item'?s\b",        "этого предмета"),
    (r"\bthis item\b",           "этот предмет"),

    # "gains X" / "gain X" after subject
    (r"\bgains \+?(\{[\w.]+\})",  r"получает \1"),
    (r"\bgain \+?(\{[\w.]+\})",   r"получают \1"),
    (r"\bgains \+?(\d+)",         r"получает \1"),
    (r"\bgain \+?(\d+)",          r"получают \1"),
    (r"\bgains a\b",              "получает"),
    (r"\bgain a\b",               "получают"),
    (r"\bgains\b",                "получает"),
    (r"\bgain\b",                 "получают"),

    # "for X seconds" tail
    (r"\bfor \{([\w.]+)\} seconds?\(?s?\)?",  r"на {\1} сек."),
    (r"\bfor (\d+) seconds?\(?s?\)?",         r"на \1 сек."),
    (r"\bfor \{([\w.]+)\} sec\b",             r"на {\1} сек."),
    (r"\bsecond\(s\)",                        "сек."),

    # Damage / Heal / Burn / Shield / Poison / Regen amounts
    (r"\bdeal \+?(\{[\w.]+\}) [Dd]amage",     r"нанесите \1 урона"),
    (r"\bdeal \+?(\d+) [Dd]amage",            r"нанесите \1 урона"),
    (r"\bdeals \+?(\{[\w.]+\}) [Dd]amage",    r"наносит \1 урона"),
    (r"\bdeals \+?(\d+) [Dd]amage",           r"наносит \1 урона"),
    (r"\bHeal \+?(\{[\w.]+\})",               r"восстанавливает \1 здоровья"),
    (r"\bHeal \+?(\d+)",                      r"восстанавливает \1 здоровья"),
    (r"\bShield \+?(\{[\w.]+\})",             r"щит \1"),
    (r"\bShield \+?(\d+)",                    r"щит \1"),
    (r"\bBurn \+?(\{[\w.]+\})",               r"поджигает на \1"),
    (r"\bBurn \+?(\d+)",                      r"поджигает на \1"),
    (r"\bPoison \+?(\{[\w.]+\})",             r"яд \1"),
    (r"\bPoison \+?(\d+)",                    r"яд \1"),
    (r"\bRegen \+?(\{[\w.]+\})",              r"регенерация \1"),

    # Connectives
    (r"\bequal to (.+?)$",        r"равное \1"),
    (r"\beach fight\b",           "в каждом бою"),
    (r"\bevery fight\b",          "в каждом бою"),
    (r"\beach turn\b",            "каждый ход"),
    (r"\bout of combat\b",        "вне боя"),
    (r"\bover time\b",            "со временем"),
    (r"\binstead of\b",           "вместо"),
    (r"\bof your\b",              "от ваших",),
    (r"\buse this\b",             "используйте этот предмет"),
    (r"\buse another\b",          "используете другой"),
    (r"\buse the\b",              "используете"),
    (r"\bup to\b",                "до"),
    (r"\bat the start of\b",      "в начале"),
    (r"\bat the end of\b",        "в конце"),
    (r"\bthe right\b",            "справа"),
    (r"\bthe left\b",             "слева"),

    # Common English-only sentence fragments that survived
    (r"\bstart of combat\b",      "начало боя"),
    (r"\bend of combat\b",        "конец боя"),
    (r"\bWhen used\b",            "При использовании"),
    (r"\bIf able\b",              "если возможно"),
    (r"\bif you have\b",          "если у вас есть"),
    (r"\bget a\b",                "получите"),
    (r"\bget an\b",               "получите"),
    (r"\bGet a\b",                "Получите"),
    (r"\bGet an\b",               "Получите"),

    # "use a/an X" mid-sentence (typically inside captured sentence body)
    (r"\buse an (\w)",            r"используете \1"),
    (r"\buse a (\w)",             r"используете \1"),
    (r"\bUse an (\w)",            r"Используете \1"),
    (r"\bUse a (\w)",             r"Используете \1"),
    (r"\buse this\b",             "используйте этот"),
    (r"\buse another\b",          "используете другой"),

    # "deal" — generic verb still left over
    (r"\bdeal\b",                 "нанесите"),
    (r"\bdeals\b",                "наносит"),
    (r"\bdealt\b",                "нанесён"),

    # Standalone leftovers
    (r"\bthis\b",                 "это"),
    (r"\bThis\b",                 "Это"),
    (r"\b or \b",                 " или "),
    (r"\b and \b",                " и "),
    (r"\b to \b",                 " к "),
    (r"\b from \b",               " от "),
    (r"\b with \b",               " с "),
    (r"\b of \b",                 " "),  # often safe to drop (already implied by genitive)

    # Common short phrases
    (r"\bsell this\b",            "продайте это"),
    (r"\bbuy this\b",             "купите это"),
    (r"\bdestroy this\b",         "уничтожьте это"),
    (r"\bcharge this\b",          "зарядите это"),
    (r"\bare reduced\b",          "уменьшены"),
    (r"\bis reduced\b",           "уменьшен"),

    # Trailing "times" / "as much"
    (r"\btimes\b",                "раз"),
    (r"\bas much\b",              "столько же"),
    (r"\bas long\b",              "столько же по времени"),
]

# ----- Declension postprocess: case agreement after Russian verbs -----
# Glossary outputs noun lemmas in nominative ("Друг", "Дракон"), but Russian
# requires accusative after action verbs ("используете друга", not "...друг"),
# and genitive plural after counts. Rules below run LAST, after everything
# else has produced mostly-Russian text, and fix the case of nouns that
# follow specific trigger verbs.
#
# Convention: животное-мужской accusative singular = nominative + "а"/"я".
# For nouns we know in the game: Друг → Друга, Дракон → Дракона,
# Динозавр → Динозавра, Дрон → Дрона, Монстр → Монстра, Герой → Героя,
# Враг → Врага, Торговец → Торговца. Inanimate (Щит, Предмет, Оружие)
# stay unchanged in accusative — no rule needed.
POSTPROCESS_RULES = [
    # After "используете/используйте" (use, imperative or 2nd person plural)
    (r"\b(использует[еь]?) Друг\b",      r"\1 Друга"),
    (r"\b(использует[еь]?) друг\b",      r"\1 друга"),
    (r"\b(использует[еь]?) Дракон\b",    r"\1 Дракона"),
    (r"\b(использует[еь]?) дракон\b",    r"\1 дракона"),
    (r"\b(использует[еь]?) Динозавр\b",  r"\1 Динозавра"),
    (r"\b(использует[еь]?) динозавр\b",  r"\1 динозавра"),
    (r"\b(использует[еь]?) Дрон\b",      r"\1 Дрона"),
    (r"\b(использует[еь]?) дрон\b",      r"\1 дрона"),
    (r"\b(использует[еь]?) Монстр\b",    r"\1 Монстра"),
    (r"\b(использует[еь]?) монстр\b",    r"\1 монстра"),
    (r"\b(использует[еь]?) Герой\b",     r"\1 Героя"),
    (r"\b(использует[еь]?) герой\b",     r"\1 героя"),
    (r"\b(использует[еь]?) Враг\b",      r"\1 Врага"),
    (r"\b(использует[еь]?) враг\b",      r"\1 врага"),
    (r"\b(использует[еь]?) Торговец\b",  r"\1 Торговца"),

    # After "продайте/продаёте" / "купите/покупаете" / "уничтожьте/уничтожаете"
    # / "победите/побеждаете" / "защитите/защищаете" / "получите/получаете"
    (r"\b(продайте|продаёте|купите|покупаете|уничтожьте|уничтожаете|победите|побеждаете|защитите|защищаете|получите|получаете) Друг\b",   r"\1 Друга"),
    (r"\b(продайте|продаёте|купите|покупаете|уничтожьте|уничтожаете|победите|побеждаете|защитите|защищаете|получите|получаете) друг\b",   r"\1 друга"),
    (r"\b(продайте|продаёте|купите|покупаете|уничтожьте|уничтожаете|победите|побеждаете|защитите|защищаете|получите|получаете) Дракон\b", r"\1 Дракона"),
    (r"\b(продайте|продаёте|купите|покупаете|уничтожьте|уничтожаете|победите|побеждаете|защитите|защищаете|получите|получаете) дракон\b", r"\1 дракона"),
    (r"\b(продайте|продаёте|купите|покупаете|уничтожьте|уничтожаете|победите|побеждаете|защитите|защищаете|получите|получаете) Динозавр\b", r"\1 Динозавра"),
    (r"\b(продайте|продаёте|купите|покупаете|уничтожьте|уничтожаете|победите|побеждаете|защитите|защищаете|получите|получаете) динозавр\b", r"\1 динозавра"),
    (r"\b(продайте|продаёте|купите|покупаете|уничтожьте|уничтожаете|победите|побеждаете|защитите|защищаете|получите|получаете) Монстр\b", r"\1 Монстра"),
    (r"\b(продайте|продаёте|купите|покупаете|уничтожьте|уничтожаете|победите|побеждаете|защитите|защищаете|получите|получаете) монстр\b", r"\1 монстра"),

    # Plural animate accusative = genitive plural form
    #   Друзья → Друзей, Драконы → Драконов, Динозавры → Динозавров,
    #   Дроны → Дронов, Монстры → Монстров, Герои → Героев, Враги → Врагов
    (r"\b(использует[еь]?|победите|побеждаете|уничтожьте|уничтожаете) Друзья\b",   r"\1 Друзей"),
    (r"\b(использует[еь]?|победите|побеждаете|уничтожьте|уничтожаете) друзья\b",   r"\1 друзей"),
    (r"\b(использует[еь]?|победите|побеждаете|уничтожьте|уничтожаете) Драконы\b",  r"\1 Драконов"),
    (r"\b(использует[еь]?|победите|побеждаете|уничтожьте|уничтожаете) Динозавры\b", r"\1 Динозавров"),
    (r"\b(использует[еь]?|победите|побеждаете|уничтожьте|уничтожаете) Монстры\b",  r"\1 Монстров"),
    (r"\b(использует[еь]?|победите|побеждаете|уничтожьте|уничтожаете) монстры\b",  r"\1 монстров"),
    (r"\b(использует[еь]?|победите|побеждаете|уничтожьте|уничтожаете) Герои\b",    r"\1 Героев"),
    (r"\b(использует[еь]?|победите|побеждаете|уничтожьте|уничтожаете) Враги\b",    r"\1 Врагов"),
    (r"\b(использует[еь]?|победите|побеждаете|уничтожьте|уничтожаете) Дроны\b",    r"\1 Дронов"),

    # After "победите/побеждаете {N}" — accusative count, the noun is in genitive plural
    # This matches templates like "Победите {completionRequirement} монстры" -> "...монстров"
    (r"(Победите|Побеждаете|Уничтожьте|Уничтожаете|Защитите|Защищаете) (\{[\w.]+\}) Монстры?\b", r"\1 \2 Монстров"),
    (r"(победите|побеждаете|уничтожьте|уничтожаете|защитите|защищаете) (\{[\w.]+\}) монстры?\b", r"\1 \2 монстров"),
    (r"(Используйте|Используете|Используй) (\{[\w.]+\}) Оружие\b",  r"\1 \2 единиц оружия"),
    (r"(используйте|используете|используй) (\{[\w.]+\}) оружие\b",  r"\1 \2 единиц оружия"),
    (r"(Изучите|Изучайте) (\{[\w.]+\}) Навыки?\b",                  r"\1 \2 навыков"),
    (r"(изучите|изучайте) (\{[\w.]+\}) навыки?\b",                  r"\1 \2 навыков"),

    # "крайний левый/правый X" — X needs to agree in case if it's animate
    (r"\b(крайний левый|крайний правый) Друг\b",   r"\1 Друг"),       # nominative subject - OK as-is
    (r"\b(вашего крайнего левого|вашего крайнего правого) Друг\b", r"\1 Друга"),

    # Possessive "вашего" forces genitive on what follows
    (r"\bвашего Друг\b",     "вашего Друга"),
    (r"\bвашего Дракон\b",   "вашего Дракона"),
    (r"\bвашего Монстр\b",   "вашего Монстра"),
    (r"\bвашего Героя?\b",   "вашего Героя"),

    # "Когда вы продаёте, ваш ... получает" — make "ваш" agree with noun gender
    (r"\bваш крайний левый Оружие\b",   "ваше крайнее левое Оружие"),
    (r"\bваш крайний правый Оружие\b",  "ваше крайнее правое Оружие"),

    # Sentence-start "Это" before a noun — should be "Этот / Эта / Это"
    # Defaults to "Это" (neuter) which is wrong before masculine/feminine.
    # Pattern translator emits "Это предмет" — should be "Этот предмет".
    (r"^Это предмет\b",      "Этот предмет"),
    (r"^Это карта\b",        "Эта карта"),
    (r"^Это герой\b",        "Этот герой"),
    (r"^Это монстр\b",       "Этот монстр"),

    # Plural concord: "ваши X предметы" — drop the duplicate "items" if we
    # added one. Already mostly clean, but catch some leftovers.
    (r"\bваши предметы предметы\b", "ваши предметы"),
    (r"\bпредметы предметы\b",      "предметы"),

    # Genitive after numeric tokens — game inserts a number at {X}, so the
    # following noun must be in genitive (Russian: "5 уронов" / "1 урон").
    # We can't know singular vs plural without runtime data, so use the
    # "генитив множественного" form which is acceptable for any N>1.
    # The standalone {X} placeholder usually means "an arbitrary number".
    (r"(\{[\w.]+\}|\d+) Урона?\b",       r"\1 урона"),
    (r"(\{[\w.]+\}|\d+) Лечения?\b",     r"\1 лечения"),
    (r"(\{[\w.]+\}|\d+) Щита?\b",        r"\1 щита"),
    (r"(\{[\w.]+\}|\d+) Поджога?\b",     r"\1 поджога"),
    (r"(\{[\w.]+\}|\d+) Яда?\b",         r"\1 яда"),
    (r"(\{[\w.]+\}|\d+) Заряда?\b",      r"\1 заряда"),
    (r"(\{[\w.]+\}|\d+) Регенерации\b",  r"\1 регенерации"),
    (r"(\{[\w.]+\}|\d+) Заморозки\b",    r"\1 заморозки"),
    (r"(\{[\w.]+\}|\d+) Замедления\b",   r"\1 замедления"),
    (r"(\{[\w.]+\}|\d+) Ускорения\b",    r"\1 ускорения"),
    (r"(\{[\w.]+\}|\d+) Здоровья?\b",    r"\1 здоровья"),
    (r"(\{[\w.]+\}|\d+) Золота?\b",      r"\1 золота"),
    (r"(\{[\w.]+\}|\d+) Дохода?\b",      r"\1 дохода"),
    (r"(\{[\w.]+\}|\d+) Опыта?\b",       r"\1 опыта"),
    (r"(\{[\w.]+\}|\d+) Ярости\b",       r"\1 ярости"),
    (r"(\{[\w.]+\}|\d+) Брони\b",        r"\1 брони"),
    (r"(\{[\w.]+\}|\d+) Скорости\b",     r"\1 скорости"),

    # Lowercase the same nouns when they appear mid-sentence (Russian style)
    (r"\bУрон\b(?!\s*[А-Я])",            "урон"),         # not at title case continuation
    (r"\bЛечение\b(?!\s*[А-Я])",         "лечение"),
    (r"\bЩит\b(?!\s*[А-Я])",             "щит"),
    (r"\bПоджог\b(?!\s*[А-Я])",          "поджог"),
    (r"\bЯд\b(?!\s*[А-Я])",              "яд"),

    # "уровень Алмазный" → "Алмазного уровня"
    (r"\b(Бронзовый|Серебряный|Золотой|Алмазный|Легендарный) уровень\b",
        lambda m: f"{ {'Бронзовый':'Бронзового', 'Серебряный':'Серебряного', 'Золотой':'Золотого', 'Алмазный':'Алмазного', 'Легендарный':'Легендарного'}[m.group(1)] } уровня"),
    # "Алмазный-предмет: Letающий" → "Алмазный Летающий предмет"
    (r"\b(Бронзовый|Серебряный|Золотой|Алмазный|Легендарный)-предмет: (\w+)",
        r"\1 \2 предмет"),

    # Tooltip-style "Шанс крита bonus" → "бонус Шанса крита"
    (r"\bШанс крита бонус\b",            "бонус к Шансу крита"),

    # "{X}% Шанс крита" → "{X}% Шанса крита"
    (r"(\{[\w.]+\}|\d+)% Шанс крита\b",  r"\1% Шанса крита"),
    (r"(\+\{[\w.]+\}|\+\d+)% Шанс крита\b",  r"\1% Шанса крита"),

    # Plural agreement: "+{X} Уроны" → "+{X} урона"
    (r"\+?(\{[\w.]+\}|\d+) Уроны\b",     r"+\1 урона"),
    (r"\+?(\{[\w.]+\}|\d+) Лечения\b",   r"+\1 лечения"),

    # "получают +N" / "получает +N" + adj.singular noun
    (r"\bполучают \+(\{[\w.]+\}|\d+) Урон\b",     r"получают +\1 урона"),
    (r"\bполучает \+(\{[\w.]+\}|\d+) Урон\b",     r"получает +\1 урона"),

    # "Когда вы продаёте, ваш ..." artifacts: missing accusative
    (r"\bваш крайний левый Друг\b",      "вашего крайнего левого Друга"),
    (r"\bваш крайний правый Друг\b",     "вашего крайнего правого Друга"),
]

OUT_DIR = Path(r"E:\memore\the-bazaar-rus-patcher\tools-extract")

def translate(text: str) -> str:
    """sentence (1st match) -> phrase (all) -> glossary (all) -> postprocess (all)."""
    s = text
    for pattern, repl in SENTENCE_RULES:
        new = re.sub(pattern, repl, s, count=1)
        if new != s:
            s = new
            break
    for pattern, repl in PHRASE_RULES:
        s = re.sub(pattern, repl, s)
    for pattern, repl in GLOSSARY:
        s = re.sub(pattern, repl, s)
    # Final cleanup: case agreement for animate nouns after action verbs
    for pattern, repl in POSTPROCESS_RULES:
        s = re.sub(pattern, repl, s)
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
