import httpx, statistics, time

def arr(d, keys):
    if isinstance(d, list): return d
    if isinstance(d, dict):
        for k in keys:
            if isinstance(d.get(k), list): return d[k]
    return []

def run(args, kit):
    b = kit.market
    h = {'authorization': 'Bearer ' + kit.token('shop')}
    def g(p, q=None, a=False):
        r = httpx.get(b + p, params=q, headers=h if a else {}, timeout=20)
        r.raise_for_status()
        return r.json()
    first = g('/api/ledger', {'after': -500})
    rs = arr(first, ['entries', 'settles'])
    last = max([int(x.get('seq', 0)) for x in rs] or [0])
    after = max(-1, last - 2500)
    rows = []
    while len(rows) < 2500:
        xs = arr(g('/api/ledger', {'after': after, 'limit': 500}), ['entries', 'settles'])
        if not xs: break
        rows += xs
        n = max(int(x.get('seq', after)) for x in xs)
        if n <= after or len(xs) < 500: break
        after = n
    counts = {}
    now = time.time()
    for x in rows:
        if x.get('kind') != 'settle': continue
        try: t = float(x.get('ts', 0))
        except (TypeError, ValueError): continue
        if not now - 10800 <= t <= now: continue
        d = x.get('data', {})
        sku = d.get('sku') if isinstance(d, dict) else None
        if sku:
            amount = x.get('amount', d.get('amount', 0))
            try: amount = float(amount)
            except (TypeError, ValueError): amount = 0
            counts.setdefault(sku, []).append(amount)
    cs = arr(g('/api/catalog'), ['items', 'catalog'])
    iu = arr(g('/api/inventory', a=True), ['units'])
    stock = {}
    total_units = len(iu)
    for u in iu:
        sku = u.get('sku')
        stock[sku] = stock.get(sku, 0) + 1
    tab = []
    for c in cs:
        s = c.get('sku')
        v = counts.get(s, [])
        if not v or c.get('kind') != 'food' or s in ('G013cad55', 'G0102056d'): continue
        q = max(0, min(6, len(v) // 4 + 1) - stock.get(s, 0))
        if c.get('shelf_hours', 999) <= 24: q = min(q, 2)
        if q <= 0: continue
        tab.append({'sku': s, 'name': c.get('name'), 'count': len(v), 'median_amount': statistics.median(v), 'stock': stock.get(s, 0), 'want': q, 'list_price': c.get('list_price'), 'shelf_hours': c.get('shelf_hours')})
    tab.sort(key=lambda x: x['count'], reverse=True)
    items = [] if total_units > 90 else [{'sku': x['sku'], 'qty': x['want']} for x in tab[:8]]
    return {'items': items, 'table': tab[:8], 'total_units': total_units}
