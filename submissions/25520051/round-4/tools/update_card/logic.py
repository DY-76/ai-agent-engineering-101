import json

def run(args, kit):
    desc = args.get('description')
    if not isinstance(desc, str):
        return {'error': 'description must be a string'}
    with open('card.json', encoding='utf-8') as f:
        card = json.load(f)
    card['description'] = desc
    if not kit.testing:
        with open('card.json', 'w', encoding='utf-8') as f:
            json.dump(card, f, ensure_ascii=False, indent=2)
    return {'ok': True, 'written': not kit.testing}
