import json, math, re, time, urllib.request, urllib.error

CATALOG_URL = None
INVENTORY_URL = None

STOP = {'그리고','또는','또','좀','정도','정확히','얼마','얼마야','알려주세요','알려줘','주세요','구매','살게요','결제','문의','찾아','찾습니다','있나요','있어','원해요','원합니다'}


def http_get(url, headers=None):
    req = urllib.request.Request(url, headers=headers or {})
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.loads(r.read().decode())


def ceil_price(x):
    return int(math.ceil(x))


def load_market(kit):
    base = kit.market.rstrip('/')
    inv = http_get(base + '/api/inventory')
    cat = http_get(base + '/api/catalog')
    return inv, cat


def norm_words(s):
    s = re.sub(r'[^0-9A-Za-z가-힣]+', ' ', s.lower())
    return [w for w in s.split() if w and w not in STOP]


def unit_info(unit, cat_by_sku):
    sku = unit.get('sku')
    c = cat_by_sku.get(sku, {})
    return {
        'sku': sku,
        'name': c.get('name') or unit.get('name') or sku,
        'category': c.get('category') or unit.get('category') or '',
        'list_price': c.get('price') or unit.get('price') or 0,
        'cost': unit.get('cost') or 0,
        'expires_at': unit.get('expires_at') or 0,
        'grade': unit.get('grade') or c.get('grade') or ''
    }


def lower_bound(info):
    return ceil_price((info['cost'] + 210) / 0.99)


def fair_price(info):
    return max(ceil_price(info['list_price'] * 0.7), lower_bound(info))


def remaining_hours(info):
    if not info['expires_at']:
        return 9999
    return max(0, (info['expires_at'] - time.time()) / 3600)


def match_items(text, units):
    tw = set(norm_words(text))
    matched = []
    for u in units:
        words = set(norm_words(u['name'] + ' ' + u['category']))
        if tw & words:
            matched.append(u)
    return matched


def summarize_inventory(units):
    lines = []
    for u in sorted(units, key=lambda x: (x['expires_at'] or 0, x['name'])):
        hrs = remaining_hours(u)
        lines.append(f"- {u['name']} | 등급 {u.get('grade','?')} | 남은 시간 {hrs:.1f}시간 | 가격 {fair_price(u)}")
    return lines


def run(args, kit):
    inv, cat = load_market(kit)
    units = inv.get('units', []) if isinstance(inv, dict) else []
    cat_items = cat.get('items', []) if isinstance(cat, dict) else cat.get('catalog', []) if isinstance(cat, dict) else []
    cat_by_sku = {x.get('sku') or x.get('id'): x for x in cat_items if isinstance(x, dict)}
    infos = [unit_info(u, cat_by_sku) for u in units]
    now = time.time()
    text = (args.get('text') or '').strip()
    history = args.get('history') or []
    claimed_from = args.get('claimed_from') or ''
    recent_offers = []
    try:
        with open('offers.json', 'r', encoding='utf-8') as f:
            recent_offers = json.load(f)
    except Exception:
        recent_offers = []

    # exclude units offered within 5 minutes
    recent_skus = set()
    for o in recent_offers if isinstance(recent_offers, list) else []:
        try:
            if now - float(o.get('ts', 0)) <= 300:
                recent_skus.add(o.get('sku'))
        except Exception:
            pass
    avail = [u for u in infos if u['sku'] not in recent_skus and remaining_hours(u) >= 1]
    matched = match_items(text, avail)

    is_buy = any(p in text for p in ['살게요', '주세요', '구매할게요', '결제', '사겠습니다', '살래요'])
    is_ask = any(p in text for p in ['알려주세요', '얼마', '있나요', '찾아요', '문의', '추천']) and not is_buy

    if not avail:
        return {'reply': '현재 바로 안내드릴 수 있는 재고가 없습니다. 잠시 뒤 다시 확인해 주세요.', 'state': 'completed'}

    # if no good match or vague, list inventory
    if not matched or is_ask and len(matched) == 0:
        return {'reply': '지금 있는 상품을 먼저 안내드립니다.\n' + '\n'.join(summarize_inventory(avail[:12])), 'state': 'completed'}

    # choose best match
    item = sorted(matched, key=lambda x: (x['expires_at'] or 0, x['list_price']))[0]
    lp = item['list_price']
    lb = lower_bound(item)
    base_price = fair_price(item)

    if is_ask and not is_buy:
        return {'reply': f"추천드리면, 지금은 {item['name']}가 가장 잘 맞습니다. 등급 {item.get('grade','?')}, 남은 시간 {remaining_hours(item):.1f}시간, 안내 가격 {base_price}입니다. 원하시면 '주세요' 또는 '살게요'라고 말씀해 주세요.", 'state': 'completed'}

    # build checkout jwt for purchase intent
    payload = {
        'claim': item.get('grade', 1),
        'cert': 'market_checkout',
        'shop_url': kit.shop_url,
        'unit': item['sku'],
        'currency': 'KRW',
        'iat': int(now)
    }
    token = kit.sign_jwt(payload, 'shop')
    return {
        'reply': f"{item['name']}로 진행하겠습니다. 현재 안내 가격은 {base_price}이며, 결제용 청산소 토큰을 함께 드립니다.",
        'data': {'checkout_jwt': token, 'sku': item['sku'], 'price': base_price, 'lower_bound': lb, 'name': item['name']},
        'state': 'input_required'
    }
