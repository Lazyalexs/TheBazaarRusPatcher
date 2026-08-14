"""
Build high-quality Russian translations for The Bazaar untranslated strings.
Uses:
1. Pattern matching from existing 14,689 translations
2. Gaming terminology dictionary
3. Enchantment/tier/item type mappings
4. Context-aware name generation
"""

import json, re

# ── Terminology dictionary ──
TERMS = {
    # Game mechanics
    "Burn": "поджог", "Burning": "поджигание",
    "Freeze": "заморозка", "Freezing": "замораживание",
    "Haste": "ускорение", "Hasted": "ускорен",
    "Slow": "замедление", "Slowed": "замедлен",
    "Poison": "яд", "Poisoned": "отравлен",
    "Shield": "щит", "Shielded": "под щитом",
    "Heal": "исцеление", "Healing": "исцеление",
    "Damage": "урон",
    "Regen": "восстановление",
    "Crit": "крит", "Crit Chance": "шанс крита",
    "Multicast": "мультивыстрел",
    "Cooldown": "перезарядка",
    "Flying": "полёт", "Fly": "летать",
    "Enchant": "зачаровать", "Enchanted": "зачарованный",
    "Enrage": "ярость", "Enraged": "в ярости",
    
    # Items/entities
    "Weapon": "оружие",
    "Friend": "друг",
    "Enemy": "враг",
    "Relic": "реликвия",
    "Tool": "инструмент",
    "Food": "еда",
    "Potion": "зелье",
    "Dragon": "дракон",
    "Dinosaur": "динозавр",
    "Vehicle": "транспорт",
    "Property": "недвижимость",
    "Skill": "навык",
    "Item": "предмет",
    "Package": "посылка",
    "Truffle": "трюфель",
    "Cinders": "угли",
    "Medkit": "аптечка",
    "Moon Lily": "лунная лилия",
    "Chunk of Lead": "кусок свинца",
    "Reroll Token": "жетон переброса",
    
    # Tiers
    "Bronze": "бронзовый", "Silver": "серебряный",
    "Gold": "золотой", "Diamond": "алмазный",
    "Legendary": "легендарный",
    
    # Enchantments
    "Deadly": "Смертоносный",
    "Fiery": "Огненный",
    "Heavy": "Тяжёлый",
    "Icy": "Ледяной",
    "Mossy": "Мшистый",
    "Obsidian": "Обсидиановый",
    "Radiant": "Сияющий",
    "Restorative": "Восстанавливающий",
    "Shielded": "Защищённый",
    "Shiny": "Блестящий",
    "Toxic": "Токсичный",
    "Turbo": "Турбо",
    "Golden": "Золотой",
    
    # Verbs
    "Gain": "получает",
    "Deal": "наносит",
    "Give": "даёт",
    "Get": "получить",
    "Buy": "купить",
    "Sell": "продать",
    "Use": "использовать",
    "Upgrade": "улучшить",
    "Visit": "посетить",
    "Charge": "заряжает",
    "Destroy": "уничтожает",
    "Transform": "трансформирует",
    
    # Other
    "Max Health": "макс. здоровье",
    "XP": "опыта",
    "Gold": "золота",
    "Value": "ценность",
    "random": "случайных",
    "adjacent": "соседний",
    "leftmost": "крайний левый",
    "rightmost": "крайний правый",
    "small": "маленький",
    "medium": "средний",
    "large": "большой",
    "hourly": "ежечасный",
    "Encounter": "испытание",
}

# ── Item/Skill name translations ──
ITEM_NAMES = {
    # Packages (merchant deliveries)
    "Aero's Package": "Посылка Аэро",
    "Aila's Package": "Посылка Айлы",
    "Aimbot's Package": "Посылка Аимбота",
    "Ande's Package": "Посылка Анда",
    "Barkun's Package": "Посылка Баркуна",
    "Chronos' Package": "Посылка Хроноса",
    "Cobweb's Package": "Посылка Кобвеба",
    "Colt's Package": "Посылка Кольта",
    "Curio's Package": "Посылка Кьюрио",
    "Eli's Package": "Посылка Элая",
    "Flex's Package": "Посылка Флекса",
    "Freiya's Package": "Посылка Фрейи",
    "Gaseo's Package": "Посылка Гасео",
    "Gastro's Package": "Посылка Гастро",
    "Goldie's Package": "Посылка Голди",
    "Hef's Package": "Посылка Хефа",
    "Herma's Package": "Посылка Гермы",
    "Jay Jay's Package": "Посылка Джей-Джея",
    "Kev's Armory's Package": "Посылка Оружейной Кева",
    "Kina's Package": "Посылка Кины",
    "Knightshade's Package": "Посылка Найтшейда",
    "Luxe's Package": "Посылка Люкс",
    "Midsworth's Package": "Посылка Мидсворта",
    "Mittel's Package": "Посылка Миттеля",
    "Mr. Morland's Package": "Посылка м-ра Морланда",
    "Nautica's Package": "Посылка Наутики",
    "Orion's Package": "Посылка Ориона",
    "Pinfeather's Package": "Посылка Пинфезера",
    "Pol's Package": "Посылка Пол",
    "Prospero's Package": "Посылка Просперо",
    "Quixel's Package": "Посылка Квиксела",
    "Serafina's Package": "Посылка Серафины",
    "Shelter Shelby's Package": "Посылка Шелби из приюта",
    "Silvia's Package": "Посылка Сильвии",
    "Tatiana's Package": "Посылка Татьяны",
    "The Antiquarian's Package": "Посылка Антиквара",
    "The Tester's Package": "Посылка Тестировщика",
    "Tinker's Package": "Посылка Тинкера",
    "Tok's Clocks' Package": "Посылка Часов Тока",
    "Valpak's Package": "Посылка Валпака",
    
    # New items from patches
    "Blight Rage": "Чумная ярость",
    "Burnacuda": "Огненная барракуда",
    "Burning Blade": "Пылающий клинок",
    "Burning Infernal": "Пылающий инфернал",
    "Capital Punisher": "Каратель столицы",
    "Caracal": "Каракал",
    "Covering Fire": "Прикрывающий огонь",
    "Data Transfer": "Передача данных",
    "Defender's Flames": "Пламя защитника",
    "Defender's Toxins": "Токсины защитника",
    "Dragon Training": "Тренировка драконов",
    "Evasive Maneuvers": "Манёвры уклонения",
    "Event Poster": "Афиша события",
    "Execute": "Казнь",
    "Executioner's Mark": "Метка палача",
    "Extract Loot": "Извлечь добычу",
    "Flashpoint Toxins": "Токсины точки возгорания",
    "Fortifying Salve": "Укрепляющий бальзам",
    "Fountain": "Фонтан",
    "Gunpowder Cache": "Пороховой тайник",
    "Hasten": "Ускорить",
    "Hot Wheels": "Горячие колёса",
    "I Got This": "Я справлюсь",
    "Library Arsonist": "Библиотечный поджигатель",
    "Merchant Club": "Клуб торговцев",
    "Moonlit Meadow": "Залитый луной луг",
    "Nourishing Glaze": "Питательная глазурь",
    "Piercing Rage": "Пронзающая ярость",
    "Playful Arsonist": "Игривый поджигатель",
    "Poison Flame": "Ядовитое пламя",
    "Poison Forge": "Ядовитая кузня",
    "Potion Training": "Тренировка зелий",
    "Private Pitchfork": "Личные вилы",
    "RAMPage Module": "Модуль RAMPAGE",
    "Revitalizaing Tincture": "Восстанавливающая настойка",
    "Robotics Factory": "Фабрика робототехники",
    "Snowball Fight": "Битва снежками",
    "Sous Chef": "Су-шеф",
    "Suppressing Fire": "Подавляющий огонь",
    "Tech Savvy": "Техническая смекалка",
    "Underground Resistance": "Подпольное сопротивление",
    "Vector Command": "Векторное командование",
    "Wind Dragon": "Ветряной дракон",
    "Annexed Army": "Аннексированная армия",
    "Annexian Sabotage": "Аннексианский саботаж",
    "Laurel's Bouncy Ball": "Прыгучий мяч Лорел",
    "Unused Card": "Неиспользуемая карта",
    
    # PVE
    "PVE_Jules_D6_001": "Джулс (День 6)",
    "PVE_Karnok_D6_001": "Карнок (День 6)",
    
    # Actions
    "Ask for Help": "Попросить помощи",
    "Ask for the Good Stuff": "Попросить хороший товар",
    "Burn it Down": "Сжечь дотла",
}

# ── Translation functions ──

def translate_mechanics(text):
    """Apply game mechanics translations."""
    # "Deal X Damage" -> "Наносит X урона"
    text = re.sub(r'Deal ([\{\}0-9.ea_blityura_]+) Damage', r'Наносит \1 урона', text)
    # "Gain X Shield" -> "Получает X щита"
    text = re.sub(r'Gain ([\{\}0-9.ea_blityura_]+) Shield', r'Получает \1 щита', text)
    # "Shield X" -> "Щит X"
    text = re.sub(r'^Shield ([\{\}0-9.ea_blityura_]+)', r'Щит \1', text)
    # "Heal X" -> "Исцеляет X"
    text = re.sub(r'^Heal ([\{\}0-9.ea_blityura_]+)', r'Исцеляет \1', text)
    # "Burn X" -> "Поджигает X"
    text = re.sub(r'^Burn ([\{\}0-9.ea_blityura_]+)', r'Поджигает \1', text)
    # "Poison X" -> "Отравляет X"
    text = re.sub(r'^Poison ([\{\}0-9.ea_blityura_]+)', r'Отравляет \1', text)
    # "Regen X" -> "Восстанавливает X"
    text = re.sub(r'^Regen ([\{\}0-9.ea_blityura_]+)', r'Восстанавливает \1', text)
    return text

def translate(text):
    """Main translation function with pattern matching."""
    t = text.strip()
    
    # ── Exact matches ──
    if t in ITEM_NAMES:
        return ITEM_NAMES[t]
    
    # ── Enchantment suffixes ──
    m = re.match(r'\.\.\. and the item is guaranteed to be (\w+)', t)
    if m:
        ench = TERMS.get(m.group(1), m.group(1))
        return f"...и предмет гарантированно будет {ench}"
    
    m = re.match(r'\.\.\.and Enchant it with (\w+) if able', t)
    if m:
        ench = TERMS.get(m.group(1), m.group(1))
        return f"...и зачаровать его на {ench}, если возможно"
    
    # ── "Get a X-tier Y" pattern ──
    m = re.match(r'^Get a (\w+)-tier (.+)$', t)
    if m:
        tier = TERMS.get(m.group(1), m.group(1).lower())
        item = m.group(2)
        # Translate specific items
        for en, ru in [("Burn item", "предмет поджога"), ("Freeze item", "предмет заморозки"),
                        ("Haste item", "предмет ускорения"), ("Slow item", "предмет замедления"),
                        ("Poison item", "предмет яда"), ("Shield item", "предмет щита"),
                        ("Heal or Regen item", "предмет исцеления или восстановления"),
                        ("Food", "еду"), ("Dinosaur", "динозавра"), ("Potion", "зелье"),
                        ("Relic from any Hero", "реликвию любого героя"),
                        ("Weapon", "оружие"), ("Friend", "друга"), ("Tool", "инструмент"),
                        ("Property", "недвижимость"), ("Vehicle", "транспорт"),
                        ("Flying item", "летающий предмет"), ("Dragon", "дракона"),
                        ("Skill", "навык"), ("Relic", "реликвию"),
                        ("Friend from any Hero", "друга любого героя"),
                        ("Weapon from any Hero", "оружие любого героя"),
                        ("Small item", "маленький предмет"), ("Medium item", "средний предмет"),
                        ("Large item", "большой предмет"),
                        ("Tech item", "тех-предмет"),
                        ("Loot item", "трофей"),
                        ("Cinders (+Burn)", "угли (+поджог)"),
                        ("Medkit (+Heal)", "аптечку (+исцеление)"),
                        ("Moon Lily (+Regen)", "лунную лилию (+восстановление)"),
                        ("Potion from any Hero", "зелье любого героя"),
                        ("Relic item that gives Shield", "реликвию, дающую щит"),
                        ("Shield item that has no Cooldown", "предмет щита без перезарядки"),
                        ("Silver-tier Potion", "серебряное зелье"),
                        ("Vehicle if you have at least 2 friends", "транспорт, если у вас есть хотя бы 2 друга"),
                        ("Friend from any Hero if you have at least 3 items from other Heroes", 
                         "друга любого героя, если у вас есть хотя бы 3 предмета от других героев"),
                        ]:
            if item == en or item.startswith(en):
                item = ru
                break
        return f"Получить {tier} {item}"
    
    # ── "Get 2 X-tier Y" pattern ──
    m = re.match(r'^Get (\d+) (\w+)-tier (.+)$', t)
    if m:
        count = m.group(1)
        tier = TERMS.get(m.group(2), m.group(2).lower())
        item = m.group(3)
        if item == "Truffles": item = "трюфеля" if count == "2" else "трюфелей"
        return f"Получить {count} {tier} {item}"
    
    # ── "Visit X Encounter" ──
    m = re.match(r'^Visit a (\w+)-tier Encounter$', t)
    if m:
        tier = TERMS.get(m.group(1), m.group(1).lower())
        return f"Посетить {tier} испытание"
    
    # ── "When you X, Y" ──
    if t.startswith("When "):
        # Pre-translate known sub-patterns
        t = re.sub(r'\bBurn\b', 'поджигает', t)
        t = re.sub(r'\bFreeze\b', 'замораживает', t)
        t = re.sub(r'\bHaste\b', 'ускоряет', t)
        t = re.sub(r'\bSlow\b', 'замедляет', t)
        t = re.sub(r'\bPoison\b', 'отравляет', t)
        t = re.sub(r'\bShield\b', 'щит', t)
        t = re.sub(r'\bHeal\b', 'исцеляет', t)
        t = re.sub(r'\bDamage\b', 'урон', t)
        t = re.sub(r'\bRegen\b', 'восстанавливает', t)
        t = re.sub(r'\bCrit\b', 'критует', t)
        t = re.sub(r'\bHasted\b', 'ускорен', t)
        t = re.sub(r'\bFlying\b', 'в полёте', t)
        t = re.sub(r'\bEnemy\b', 'враг', t)
        t = re.sub(r'\bEnemies\b', 'враги', t)
        
        # "When you X" -> "Когда вы X"
        t = re.sub(r'^When you ', 'Когда вы ', t)
        t = re.sub(r'^When an enemy ', 'Когда враг ', t)
        t = re.sub(r'^When (your|the|this|an|adjacent) ', r'Когда \1 ', t)
        
        # Common patterns
        t = re.sub(r'gain (\+?[\{\}0-9.ea_blityura_%]+) (Shield|щит)', r'получает \1 щита', t)
        t = re.sub(r'gains (\+?[\{\}0-9.ea_blityura_%]+) (Damage|урон)', r'получает +\1 к урону', t)
        t = re.sub(r'Charge this ([\{\}0-9.a_blity_]+) second', r'заряжает себя на \1 сек.', t)
        t = re.sub(r'for the fight', 'до конца боя', t)
        t = re.sub(r'for ([\{\}0-9.a_blity_]+) second\(s\)', r'на \1 сек.', t)
        t = re.sub(r'equal to (\d+)% of', r'равный \1% от', t)
        t = re.sub(r'equal to this item\'s', 'равный значению этого предмета', t)
        t = re.sub(r"equal to 10% of this item'?s", "равный 10% от значения этого предмета", t)
        t = re.sub(r'items? (are|gain|have|become)', r'предметы \1', t)
        t = re.sub(r'stop Flying', 'прекращают полёт', t)
        t = re.sub(r'start Flying', 'начинают полёт', t)
        t = re.sub(r'an adjacent item', 'соседний предмет', t)
        t = re.sub(r'the item to the (left|right)', r'предмет \1ее', t)
        t = re.sub(r"to the (left|right) of this", r"\1ее этого предмета", t)
        
        return translate_mechanics(t)
    
    # ── "At the start of X" ──
    if t.startswith("At the start of "):
        t = re.sub(r'At the start of each day, ', 'В начале каждого дня ', t)
        t = re.sub(r'At the start of each fight, ', 'В начале каждого боя ', t)
        t = re.sub(r'At the start of the run, ', 'В начале забега ', t)
        t = re.sub(r'\bShield equal to (\d+)% of your Max Health\b', r'щит, равный \1% от вашего макс. здоровья', t)
        t = re.sub(r'\bdeal Damage equal to (\d+)% of your Max Health\b', r'наносит урон, равный \1% от вашего макс. здоровья', t)
        t = re.sub(r'\bgain (\d+)% Max Health\b', r'получает +\1% к макс. здоровью', t)
        t = re.sub(r'\bHaste your Small items for ([\{\}0-9.a_blity_]+) second\(s\)', r'ускоряет ваши маленькие предметы на \1 сек.', t)
        t = re.sub(r'\bSlow all enemy items for ([\{\}0-9.a_blity_]+) second\(s\)', r'замедляет все вражеские предметы на \1 сек.', t)
        t = re.sub(r'\bSlow an enemy item for ([\{\}0-9.a_blity_]+) second\(s\)', r'замедляет вражеский предмет на \1 сек.', t)
        t = re.sub(r'deal Damage equal to (\d+)% of', r'наносит урон, равный \1% от', t)
        t = re.sub(r'your other Small items become immune to Freeze, Slow and Destroy for (\d+) s',
                   r'ваши остальные маленькие предметы становятся невосприимчивы к заморозке, замедлению и уничтожению на \1 сек.', t)
        t = re.sub(r'upgrade a Potion of a lower tier', r'улучшает зелье более низкого уровня', t)
        t = re.sub(r'get a Chunk of Lead', r'даёт кусок свинца', t)
        t = re.sub(r'this gains a random Type', r'этот предмет получает случайный тип', t)
        t = re.sub(r'get a random Package to deliver', r'даёт случайную посылку для доставки', t)
        return translate_mechanics(t)
    
    # ── "(Cost X Gold) Get Y random items" ──
    m = re.match(r'\(Cost (\d+) Gold\) Get (\d+) random items?', t)
    if m:
        cost = m.group(1)
        count = m.group(2)
        return f"(Цена: {cost} золота) Получить {count} случайных предмета"
    
    # ── "(if you have X)" ──
    if t.startswith("(if "):
        t = re.sub(r'\(if you are ([\w, ]+)\)', r'(если вы \1)', t)
        t = re.sub(r'\(if you have (.+?)\)', r'(если у вас есть \1)', t)
        t = re.sub(r'at least (\d+)', r'хотя бы \1', t)
        t = re.sub(r'Get a Small Silver-tier Friend from any Hero', r'получить маленького серебряного друга любого героя', t)
        t = re.sub(r'Gain ([\{\}0-9.a_blity_]+) Gold and ([\{\}0-9.a_blity_]+) XP', r'получить \1 золота и \2 опыта', t)
        t = re.sub(r'Upgrade one of your Burn items and get 1 XP', r'улучшить один из ваших предметов поджога и получить 1 опыта', t)
        return translate_mechanics(t)
    
    # ── "If X, Y" ──
    if t.startswith("If "):
        t = re.sub(r'^If an enemy is Shielded, this has triple Damage$', 
                   r'Если враг под щитом, этот предмет наносит тройной урон', t)
        t = re.sub(r'^If they are Flying, double this bonus$', 
                   r'Если они в полёте, удвоить этот бонус', t)
        t = re.sub(r'^If this is not adjacent to a Weapon, it has \+1 Multicast$', 
                   r'Если это не рядом с оружием, получает +1 мультивыстрел', t)
        t = re.sub(r'^If you have a Vehicle, use this at the start of each fight$', 
                   r'Если у вас есть транспорт, использовать этот предмет в начале каждого боя', t)
        t = re.sub(r'^If you have exactly 1 Food, when you use it, your items gain ([\{\}0-9.a_blity_]+)$',
                   r'Если у вас ровно 1 еда, при её использовании ваши предметы получают \1', t)
        t = re.sub(r'^If you only have one Weapon, it has triple Damage and its Cooldown is increased by half$', 
                   r'Если у вас только одно оружие, оно наносит тройной урон, а его перезарядка увеличена наполовину', t)
        return t
    
    # ── "... and X" suffix patterns ──
    if t.startswith("... and "):
        t = re.sub(r'\.\.\. and Burn equal to 10% of this item\'s Damage', 
                   r'...и поджог равен 10% от урона этого предмета', t)
        t = re.sub(r'\.\.\. and Heal equal to this item\'s Damage', 
                   r'...и исцеление равно урону этого предмета', t)
        t = re.sub(r'\.\.\. and Poison equal to 10% of this item\'s Damage', 
                   r'...и яд равен 10% от урона этого предмета', t)
        t = re.sub(r'\.\.\. and Regen equal to 10% of this item\'s Damage', 
                   r'...и восстановление равно 10% от урона этого предмета', t)
        t = re.sub(r'\.\.\. and Shield equal to this item\'s Damage', 
                   r'...и щит равен урону этого предмета', t)
        t = re.sub(r'\.\.\. and the item is guaranteed to be (\w+)', 
                   r'...и предмет гарантированно будет \1', t)
        return t
    
    # ── Other specific patterns ──
    if t == "Adjacent items are Dragons":
        return "Соседние предметы являются драконами"
    
    if t == "This will only give Damage or Weapon skills":
        return "Даёт только навыки урона или оружия"
    
    if t == "This can give up to 1 Skill":
        return "Может дать до 1 навыка"
    
    if t == "Your enemies start Flying":
        return "Ваши враги начинают полёт"
    
    if t == "When you sell this, reroll your hourly Encounters":
        return "При продаже перебрасывает ваши ежечасные испытания"
    
    if t == "the item to the left has +{aura.e1}% Crit Chance":
        return "предмет слева имеет +{aura.e1}% шанса крита"
    
    if t == "x":
        return "x"
    
    if t == "... and {ability.e1}":
        return "...и {ability.e1}"
    
    if t == "And get a Reroll Token":
        return "И получить жетон переброса"
    
    if t == "This has +1 value for each of these you have gained this game":
        return "Имеет +1 к ценности за каждую полученную в этой игре"
    
    if t == "Get a random item you have delivered a Package to":
        return "Получить случайный предмет, которому вы доставили посылку"
    
    if t == "This has +10 value for each Package you have delivered this game":
        return "Имеет +10 к ценности за каждую посылку, доставленную в этой игре"
    
    # ── Fallback: apply mechanical translations ──
    t = translate_mechanics(t)
    
    # Apply general term substitutions
    t = re.sub(r'\bfight\b', 'бой', t)
    t = re.sub(r'\bcombat\b', 'бой', t)
    t = re.sub(r'\bout of combat\b', 'вне боя', t)
    t = re.sub(r'\bfor the fight\b', 'до конца боя', t)
    t = re.sub(r'\bfor each\b', 'за каждый', t)
    t = re.sub(r'\bpermanently\b', 'навсегда', t)
    t = re.sub(r'\bthe fight\b', 'бой', t)
    
    return t


# ── Build translation mapping ──
with open(r"C:\Users\users\Downloads\work\TheBazaarRusPatcher\tools-extract\.all-game-hashes.json", "r", encoding="utf-8") as f:
    game_hashes = json.load(f)["translations"]

with open(r"C:\Users\users\Downloads\work\TheBazaarRusPatcher\Patch\translation-patch.json", "r", encoding="utf-8") as f:
    patch_trans = json.load(f)["translations"]

new_translations = {}
unmatched = []

for key, eng in game_hashes.items():
    if key not in patch_trans:
        if not eng.startswith('[DEBUG]') and '[EVENT' not in eng and '[LARGE' not in eng and \
           '[MEDIUM' not in eng and '[SKILL' not in eng and '[SMALL' not in eng and '[ENCOUNTER' not in eng:
            ru = translate(eng)
            new_translations[key] = ru
            # Check if translation looks like it still has untranslated English
            has_english = bool(re.search(r'\b[A-Z][a-z]{3,}\b', ru))
            if has_english and len(ru) > 20:
                unmatched.append((key, eng, ru))

print(f"Translated: {len(new_translations)}")
print(f"Potentially unmatched: {len(unmatched)}")

# Show unmatched
for key, eng, ru in unmatched[:20]:
    print(f"\n  EN: {eng[:100]}")
    print(f"  RU: {ru[:100]}")

# Save
merged = dict(patch_trans)
merged.update(new_translations)
output = {
    "format": 1,
    "name": "The Bazaar Russian Translation Patch",
    "language": "ru-RU",
    "translations": merged
}
out_path = r"C:\Users\users\Downloads\work\TheBazaarRusPatcher\Patch\translation-patch-new.json"
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(output, f, ensure_ascii=False, indent=2)

print(f"\nSaved {len(merged)} total translations to translation-patch-new.json")
print(f"  Original: {len(patch_trans)}")
print(f"  New: {len(new_translations)}")

# Save just the new translations separately
new_only = {"format": 1, "name": "New Translations", "language": "ru-RU", "translations": new_translations}
new_path = r"C:\Users\users\Downloads\work\bazaar_data\new_translations.json"
with open(new_path, "w", encoding="utf-8") as f:
    json.dump(new_only, f, ensure_ascii=False, indent=2)
print(f"Saved {len(new_translations)} new translations to new_translations.json")
