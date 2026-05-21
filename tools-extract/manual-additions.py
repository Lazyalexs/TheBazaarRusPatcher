"""
Manual Russian translations for the 74 narrative / proper-noun strings
that pattern-translate.py could not handle. After running this, merge.py
will pick the entries up via .missing-translated.json (overwritten in place).
"""
import json
from pathlib import Path

OUT = Path(r"E:\memore\the-bazaar-rus-patcher\tools-extract")

MANUAL = {
    # Item names
    "Lag-bolt":                          "Лаг-болт",
    "Shell Necklace":                    "Ожерелье из ракушек",
    "Tracer Pistol":                     "Трассирующий пистолет",
    "Starfish":                          "Морская звезда",
    "Rimestone Amulet":                  "Амулет из инея",
    "Dreampearl":                        "Жемчуг снов",
    "Aged Cask":                         "Выдержанная бочка",
    "Spark Plug":                        "Свеча зажигания",
    "Crimson Orchid":                    "Багровая орхидея",
    "Gorgon Spore":                      "Спора горгоны",
    "Foundation Robe":                   "Мантия основания",
    "Stickybeans":                       "Липкие бобы",
    "Fairy Statue":                      "Статуя феи",
    "Stress Ball":                       "Антистресс-мячик",
    "Infernal Catapult":                 "Инфернальная катапульта",
    "Penthouse":                         "Пентхаус",
    "Championship Belt":                 "Чемпионский пояс",
    "Gourmet Kitchen":                   "Кухня гурмана",
    "Portable Stove":                    "Походная плита",
    "Truffle":                           "Трюфель",
    "Pelt":                              "Шкура",

    # NPC / event names
    "Overwhelmed Student":               "Перегруженный студент",
    "Surly Mechanic":                    "Угрюмый механик",
    "Shelter Shelby":                    "Шелби из приюта",
    "Mad Diver":                         "Сумасшедший ныряльщик",
    "Overbearing Teacher":               "Властный учитель",
    "C.O.R.A":                           "К.О.Р.А.",
    "Byg":                               "Биг",
    "The Boss":                          "Босс",

    # Encounter / event titles
    "Just Keep Moving":                  "Просто продолжай идти",
    "Risky! Anything could happen here": "Рискованно! Здесь может случиться что угодно",
    "Prepared for Anything":             "Готов ко всему",
    "Happy Accident":                    "Счастливая случайность",
    "This is not the end":               "Это ещё не конец",
    "Not a Spy":                         "Не шпион",
    "Old Memories":                      "Старые воспоминания",
    "Raffle Ticket":                     "Лотерейный билет",

    # Action / choice text
    "Keep the wallet for yourself":      "Оставить кошелёк себе",
    "Return home and get back into shape": "Вернуться домой и привести себя в форму",
    "Buy out the circus":                "Выкупить цирк",
    "Visit the Artist":                  "Посетить художника",
    "Aid a caravan descending the Great Plateau": "Помочь каравану спуститься с Великого плато",
    "Look for opportunities in the Financial District": "Искать возможности в Финансовом районе",
    "Boost your stats with tasty treats": "Улучшите свои характеристики вкусными лакомствами",
    "Test your build against the Sparring Partner": "Протестируйте сборку против спарринг-партнёра",
    "Finders keepers":                   "Кто нашёл, тот и хозяин",
    "Select an Enchantment location":    "Выберите место для зачарования",

    # Story / flavor text
    "The Roughtown Kyvers Lost..":       "Грубоград Киверс проиграл..",
    "The Kyvers fall to the Rogues {aura.4}-{aura.3}!\nBut at least you got something to eat": "Киверс уступает Разбойникам {aura.4}-{aura.3}!\nНо хоть еда у тебя есть",
    "An echo of the past. A vision of the future": "Эхо прошлого. Видение будущего",
    "Stelle's sister shows up to get her to come home": "Сестра Стелл появляется, чтобы забрать её домой",
    "The mighty Guardian has sealed the temple. Return to the Bazaar": "Могучий Страж запечатал храм. Возвращайтесь на Базар",
    "The Monster returns and sniffed you out": "Монстр возвращается и учуял вас",
    "You are overwhelmed with cosmic visions! Return home to ponder these mysteries": "Вы переполнены космическими видениями! Возвращайтесь домой, чтобы поразмыслить над этими тайнами",
    "You learned a lot in your seminar": "Вы многому научились на семинаре",
    "You know what? He makes a good point, actually": "Знаешь что? А он ведь дело говорит",
    "Return to the Bazaar and purge the toxins": "Вернитесь на Базар и очистите токсины",

    # Trigger / mechanic strings the pattern translator missed
    "When you buy this, get a Truffle":  "Когда вы покупаете этот предмет, получите Трюфель",
    "When you buy this, get {ability.1} Nanobots": "Когда вы покупаете этот предмет, получите {ability.1} нанобота",
    "When you buy this, get a Piranha":  "Когда вы покупаете этот предмет, получите Пиранью",
    "When you defeat a Monster with this, get a Pelt": "Когда вы побеждаете монстра этим предметом, получите Шкуру",
    "When you sell this at the start of Hours 1 to 5, reroll {aura.9} new Encounter(s)": "Когда вы продаёте это в начале часов 1-5, переброс {aura.9} новых встреч",
    "When this is destroyed, deal {ability.1} damage": "Когда этот предмет уничтожен, нанесите {ability.1} урона",
    "When this runs out of ammo, destroy it": "Когда у этого предмета заканчиваются боеприпасы, уничтожить его",
    "You take {aura.9}% less damage":    "Вы получаете на {aura.9}% меньше урона",
    "Double the effects of the Artisans' options": "Удваивает эффекты от опций Ремесленников",

    # Internal templates that ARE user-visible
    "This is an Encounter Step Template": "Это шаблон шага встречи",
    "This is an Event Template":         "Это шаблон события",
    "Stelle Template PVP":               "Шаблон Стеллы для PVP",
    # Internal IDs that the game shouldn't render to users — skipping these
    # (identity-translating to themselves pollutes the patch dictionary).
    #   "PVE_Karnok_D6_001", "PVE_Jules_D6_001", "x"

    # Challenge text — uses {completionRequirement} placeholder
    "Defeat {completionRequirement} Monsters":          "Победите {completionRequirement} монстров",
    "Use weapons {completionRequirement} times":        "Используйте оружие {completionRequirement} раз",
    "Complete {completionRequirement} days":            "Завершите {completionRequirement} дней",
    "Learn {completionRequirement} skills":             "Изучите {completionRequirement} навыков",
    "Visit {completionRequirement} shops":              "Посетите {completionRequirement} магазинов",
    "Learn {completionRequirement} Monster skills":     "Изучите {completionRequirement} навыков монстров",
    "Collect {completionRequirement} spare change":     "Соберите {completionRequirement} мелочи",
    "Sell {completionRequirement} weapons":             "Продайте {completionRequirement} оружия",
}

def main():
    # Load missing English source map (hash -> English)
    with (OUT / ".missing-from-ru-RU.json").open(encoding="utf-8") as f:
        en_by_hash = json.load(f)

    # Load current translated file
    with (OUT / ".missing-translated.json").open(encoding="utf-8") as f:
        tr = json.load(f)

    updated = 0
    for h, en in en_by_hash.items():
        if en in MANUAL:
            tr[h] = MANUAL[en]
            updated += 1

    with (OUT / ".missing-translated.json").open("w", encoding="utf-8") as f:
        json.dump(tr, f, ensure_ascii=False, indent=2)

    print(f"Overrode {updated} entries with manual Russian translations.")
    print(f"Now run merge.py to push them into ru-RU.bytes + patch JSON.")

if __name__ == "__main__":
    main()
