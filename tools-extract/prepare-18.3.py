"""Generate a reviewable delta using exact English matches and complete templates.

Does not install translations, alter the baseline, or publish a release.
"""
import collections
import json
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
SNAPSHOT = HERE / 'snapshot-18.3-20260917b'
manual = json.loads((HERE / 'update-18.3-ru.json').read_text(encoding='utf-8'))
manual.update(json.loads((HERE / 'repair-18.3-ru.json').read_text(encoding='utf-8')))
missing = json.loads((SNAPSHOT / 'missing.json').read_text(encoding='utf-8'))
repairs = json.loads((SNAPSHOT / 'placeholder-mismatches.json').read_text(encoding='utf-8'))
targets = {**missing, **repairs}
stats = {'Damage': 'урона', 'Shield': 'щита', 'Heal': 'лечения', 'Burn': 'поджога', 'Poison': 'яда', 'Regen': 'регенерации'}


def action(text):
    # Each pattern matches the whole clause; unsupported clauses remain pending.
    m = re.fullmatch(r'(Slow|Freeze|Haste) (.*?) (\{[^{}]+\}) second(?:\(s\)|s)?', text)
    if m:
        target = {'their items': 'предметы противника', 'your items': 'ваши предметы',
                  'all enemy items': 'все предметы противника', 'all items': 'все предметы',
                  'your Burn and Regen items': 'ваши предметы поджога и регенерации',
                  'Your Core': 'ваше ядро', 'your Cores': 'ваши ядра', 'a Vehicle': 'одно транспортное средство',
                  'the fastest enemy item': 'самый быстрый предмет противника',
                  'the Slowest enemy item': 'самый медленный предмет противника'}.get(m[2])
        if target is None:
            numbered = re.fullmatch(r'(\{[^{}]+\}) (.*)', m[2])
            if numbered:
                noun = {'item(s)': 'предметов', 'items': 'предметов', 'item': 'предметов',
                        'enemy items': 'предметов противника', 'Relic item(s)': 'реликвий',
                        'Instruments': 'музыкальных инструментов', 'Poison item(s)': 'предметов яда',
                        'Aquatic item(s)': 'водных предметов', 'Tool(s)': 'инструментов',
                        'Burn item(s)': 'предметов поджога', 'Food': 'предметов еды'}.get(numbered[2])
                if noun:
                    target = numbered[1] + ' ' + noun
        if target:
            return {'Slow':'замедлите', 'Freeze':'заморозьте', 'Haste':'ускорьте'}[m[1]] + f' {target} на {m[3]} сек.'
    m = re.fullmatch(r'(?:Charge|charge) (a Weapon|a Burn item|a Tool|your Heated and Chilled items) (\{[^{}]+\}) second(?:\(s\)|s)?', text)
    if m:
        noun = {'a Weapon':'оружие', 'a Burn item':'предмет поджога', 'a Tool':'инструмент', 'your Heated and Chilled items':'ваши нагретые и охлаждённые предметы'}[m[1]]
        return f'зарядите {noun} на {m[2]} сек.'
    m = re.fullmatch(r'gain (\{[^{}]+\}) Tempo', text)
    if m:
        return f'получите {m[1]} темпа'
    m = re.fullmatch(r'(Shield|Heal|Poison|Regen|Burn|deal Damage) equal to (\{[^{}]+\}|\d+)% of your Max Health( \[\{[^{}]+\}\])?', text)
    if m:
        start = {'Shield':'получите щит', 'Heal':'восстановите здоровье', 'Poison':'наложите яд',
                 'Regen':'получите регенерацию', 'Burn':'наложите поджог', 'deal Damage':'нанесите урон'}[m[1]]
        return f'{start} в размере {m[2]}% вашего макс. здоровья' + (m[3] or '')
    m = re.fullmatch(r'(Slow|Freeze|Haste) an item (\{[^{}]+\}) second\(s\)', text)
    if m:
        return {'Slow': 'замедлите', 'Freeze': 'заморозьте', 'Haste': 'ускорьте'}[m[1]] + f' предмет на {m[2]} сек.'
    m = re.fullmatch(r'Haste it (\{[^{}]+\}) second\(s\)', text)
    if m:
        return f'ускорьте его на {m[1]} сек.'
    m = re.fullmatch(r'(Slow|Freeze|Haste) (\{[^{}]+\}) items? (\{[^{}]+\}) second\(s\)', text)
    if m:
        return {'Slow': 'замедлите', 'Freeze': 'заморозьте', 'Haste': 'ускорьте'}[m[1]] + f' {m[2]} предметов на {m[3]} сек.'
    m = re.fullmatch(r'(Heal|Shield|Poison|Burn|Regen) (\{[^{}]+\})', text)
    if m:
        return {'Heal': f'восстановите {m[2]} здоровья', 'Shield': f'получите {m[2]} щита',
                'Poison': f'наложите {m[2]} яда', 'Burn': f'наложите {m[2]} поджога',
                'Regen': f'получите {m[2]} регенерации'}[m[1]]
    m = re.fullmatch(r'(?:deal|Deal) (\{[^{}]+\}) Damage', text)
    if m:
        return f'нанесите {m[1]} урона'
    m = re.fullmatch(r"(Heal|Shield|Poison|Burn|Regen|Deal Damage) equal to (.*?)this item's (Damage|damage|Poison)", text)
    if m:
        multipliers = {'': '', 'half ': 'половине ', 'half of ': 'половине ', '5 times ': 'значению ', '20% of ': '20% ', '10% of ': '10% '}
        if m[2] not in multipliers:
            return None
        amount = multipliers[m[2]] + {'Damage': 'урона', 'damage': 'урона', 'Poison': 'яда'}[m[3]] + ' этого предмета'
        if m[2] == '5 times ':
            amount += ', умноженному на 5'
        if m[2] in ('', '5 times '):
            if m[2] == '':
                amount = amount.replace('урона', 'урону', 1).replace('яда', 'яду', 1)
        return {'Heal': 'восстановите здоровье в количестве, равном ', 'Shield': 'получите щит, равный ',
                'Poison': 'наложите яд в количестве, равном ', 'Burn': 'наложите поджог в количестве, равном ',
                'Regen': 'получите регенерацию, равную ', 'Deal Damage': 'нанесите урон, равный '}[m[1]] + amount
    return None


def translate(text):
    if text in manual:
        return manual[text]
    for prefix, ru in {
        'The first time an enemy uses an item of the same or lower tier as this, ': 'Когда противник впервые использует предмет того же или более низкого ранга, чем этот, ',
        'The first time you fall below half Health, ': 'Когда ваше здоровье впервые падает ниже половины, ',
        'The first time you would be defeated, ': 'Когда вы впервые должны потерпеть поражение, ',
        'The first time you use an item, ': 'Когда вы впервые используете предмет, ',
        'The first time you use a Shield item, ': 'Когда вы впервые используете предмет щита, ',
        'The first time you use a Large item, ': 'Когда вы впервые используете большой предмет, ',
        'The first time you use a large item, ': 'Когда вы впервые используете большой предмет, ',
        'The first time you use a Food, ': 'Когда вы впервые используете еду, ',
        'The first time you Freeze each fight, ': 'Когда вы впервые за бой замораживаете, ',
        'The first time you Poison each fight, ': 'Когда вы впервые за бой накладываете яд, ',
        'The first time you Crit, ': 'Когда вы впервые наносите критический удар, ',
        'The first time an enemy uses an item, ': 'Когда противник впервые использует предмет, ',
        'The first time an enemy falls below half Health , ': 'Когда здоровье противника впервые падает ниже половины, ',
        'When you Crit with an adjacent item, ': 'Когда соседний предмет наносит критический удар, ',
        'When you use a Dragon, ': 'Когда вы используете дракона, ',
        'When you use an adjacent Toy, ': 'Когда вы используете соседнюю игрушку, ',
        'When you spend Tempo, ': 'Когда вы тратите темп, ',
        'When your Enemy uses their fastest item, ': 'Когда противник использует свой самый быстрый предмет, ',
        'When your items start Flying, ': 'Когда ваши предметы начинают летать, ',
        'When you Crit, ': 'Когда вы наносите критический удар, ',
    }.items():
        if text.startswith(prefix):
            result = action(text[len(prefix):])
            if result:
                return ru + result
    m = re.fullmatch(r'The first (\{aura.9\}) times you (.*?), (.*)', text)
    if m:
        trigger = {'Slow':'замедляете', 'Haste':'ускоряете', 'Poison':'накладываете яд',
                   'use a Drone or Vehicle':'используете дрон или транспортное средство',
                   'use a Core each fight':'используете ядро за бой',
                   'use a Food each fight':'используете еду за бой',
                   'Freeze each fight':'замораживаете за бой', 'Burn each fight':'накладываете поджог за бой',
                   'Slow each fight':'замедляете за бой'}.get(m[2])
        result = action(m[3])
        if trigger and result:
            return f'Первые {m[1]} раз, когда вы {trigger}, {result}'
    result = action(text)
    if result:
        return result[0].upper() + result[1:]
    m = re.fullmatch(r"When you Enrage, your items gain (Damage|Shield|Heal|Burn|Poison|Regen) equal to (1% of your Max Health|20% of this item's Heal|this item's Heal)( \[\{aura.9\}\])?", text)
    if m:
        amount = {'1% of your Max Health': '1% вашего макс. здоровья', "20% of this item's Heal": '20% лечения этого предмета', "this item's Heal": 'лечению этого предмета'}[m[2]]
        return f'Когда вы впадаете в ярость, ваши предметы получают бонус {stats[m[1]]}, равный {amount}' + (m[3] or '')
    m = re.fullmatch(r'Your items have \+(Damage|Shield|Heal|Burn|Poison|Regen) equal to (\{[^{}]+\}) times the number of Weapons you have bought this run (\[\{[^{}]+\}\])', text)
    if m:
        return f'Ваши предметы имеют бонус {stats[m[1]]}, равный количеству оружия, купленного вами за этот забег, умноженному на {m[2]} {m[3]}'
    m = re.fullmatch(r'Your items have \+(Damage|Shield|Heal) equal to (\{[^{}]+\})% of your Max Health (\[\{[^{}]+\}\])', text)
    if m:
        return f'Ваши предметы имеют бонус {stats[m[1]]}, равный {m[2]}% вашего макс. здоровья {m[3]}'
    m = re.fullmatch(r'The (Haste item|Shield item|Slow item|Tempo item|Heal or Regen item|Burn item|Weapon) here has its cooldown reduced by (\{[^{}]+\})%', text)
    if m:
        subject = {'Haste item':'предмета ускорения','Shield item':'предмета щита','Slow item':'предмета замедления','Tempo item':'предмета темпа','Heal or Regen item':'предмета лечения или регенерации','Burn item':'предмета поджога','Weapon':'оружия'}[m[1]]
        return f'Перезарядка {subject} на этом месте сокращена на {m[2]}%'
    return None


delta, pending, skipped = {}, {}, {}
for key, row in targets.items():
    text = row['en']
    if '[DEBUG]' in text or 'TEMPLATE]' in text:
        skipped[key] = row
        continue
    ru = translate(text)
    if ru is None:
        pending[key] = row
        continue
    assert collections.Counter(re.findall(r'\{[^{}]+\}', text)) == collections.Counter(re.findall(r'\{[^{}]+\}', ru)), key
    assert not re.search(r'[A-Za-z]', re.sub(r'\{[^{}]+\}', '', ru)), (key, ru)
    delta[key] = {'en': text, 'ru': ru, 'context': row.get('context', []), 'kind': 'repair' if key in repairs else 'addition'}
for filename, data in [('delta-review.json', delta), ('pending.json', pending), ('debug-excluded.json', skipped)]:
    (SNAPSHOT / filename).write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
print(f'Translated: {len(delta)}; pending: {len(pending)}; debug/templates excluded: {len(skipped)}')
for k, v in pending.items():
    print(k, v['en'])
