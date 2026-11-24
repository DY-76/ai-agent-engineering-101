import httpx

def run(args, kit):
    base = kit.market
    headers = {"authorization": f"Bearer {kit.token('shop')}"}
    # 판매 기록 조회 (최대 500건)
    resp = httpx.get(f"{base}/api/ledger?after=-500", headers=headers, timeout=30)
    resp.raise_for_status()
    ledger = resp.json()
    # settle에 해당하는 기록만 shop == 내 주소로 필터
    my_addr = kit.address('shop')
    members = args.get('members', None)
    cache = {}
    for row in ledger:
        # 확인된 settle 필드: buyer, buyer_label(닉), shop, shop_label(닉), sku, qty, price, recommended_by, time, etc
        if row.get('shop','').lower()!=my_addr.lower(): continue
        buyer = row.get('buyer_label', row.get('buyer')) or ''
        recommender = row.get('recommended_by','') or ''
        t = row.get('time',0)
        key_buyer = buyer.strip()
        key_rec = recommender.strip()
        # 멤버 제약 필터
        if members is not None and key_buyer not in members and key_rec not in members:
            continue
        # 구매 처리
        if key_buyer:
            m = cache.setdefault(key_buyer, {'purchase_count':0, 'recommend_count':0, 'recommended_count':0, 'grade':1, 'discount_rate':0, 'half_price_tickets':0, 'half_price_tickets_used':0, 'last_purchase_at':0, 'last_recommend_at':0, 'recommenders':{}, 'used_half_tickets':[]})
            m['purchase_count'] += 1
            m['last_purchase_at'] = max(m['last_purchase_at'], t)
        # 추천인 처리
        if key_rec and key_rec!=key_buyer:
            r = cache.setdefault(key_rec, {'purchase_count':0, 'recommend_count':0, 'recommended_count':0, 'grade':1, 'discount_rate':0, 'half_price_tickets':0, 'half_price_tickets_used':0, 'last_purchase_at':0, 'last_recommend_at':0, 'recommenders':{}, 'used_half_tickets':[]})
            r['recommended_count'] += 1
            r['last_recommend_at'] = max(r['last_recommend_at'], t)
    # 할인·등급·반값티켓 계산
    for n, m in cache.items():
        k = m['recommended_count']
        if k >= 30:
            drate = 25
        elif k >= 20:
            drate = 20
        elif k >= 10:
            drate = 15
        elif k >= 1:
            drate = 10
        else:
            drate = 0
        m['discount_rate'] = drate
        m['grade'] = 1 + (k // 10)
        tickets_owned = k // 10
        used_tickets = 0
        for row in ledger:
            if row.get('shop','').lower()!=my_addr.lower(): continue
            if (row.get('buyer_label','') or '').strip() == n and row.get('half_price_ticket', False):
                used_tickets += 1
        m['half_price_tickets'] = tickets_owned
        m['half_price_tickets_used'] = used_tickets
    # 최종 산출 멤버
    result = {}
    for k, v in cache.items():
        if members is None or k in members:
            result[k] = {k2: v[k2] for k2 in ['purchase_count', 'recommend_count', 'recommended_count', 'grade', 'discount_rate', 'half_price_tickets', 'half_price_tickets_used', 'last_purchase_at', 'last_recommend_at']}
    with open('settle_master.json', 'w', encoding='utf8') as f:
        import json
        json.dump(result, f, ensure_ascii=False, indent=1)
    return {'members': result}
