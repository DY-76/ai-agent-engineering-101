
import httpx, datetime

def run(args, kit):
    # args: since, until, members(선택)
    base = kit.market
    headers = {"authorization": f"Bearer {kit.token('shop')}"}
    params = {}
    if 'since' in args and args['since']:
        params['since'] = args['since']
    if 'until' in args and args['until']:
        params['until'] = args['until']

    # 원장 settle 기록 조회 (최대 1000건)
    resp = httpx.get(f"{base}/api/ledger/settle", headers=headers, params=params, timeout=30)
    resp.raise_for_status()
    settles = resp.json()
    
    members = args.get('members', None)
    result = {}
    cache = {}

    for settle in settles:
        # settle: {buyer, buyer_label, shop, shop_label, sku, qty, price, recommended_by, time, ...}
        buyer = settle.get('buyer_label', settle.get('buyer')) or ''
        recommender = settle.get('recommended_by','') or ''
        t = settle.get('time',0)
        key_buyer = buyer.strip()
        key_rec = recommender.strip()
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
    
    # 할인·등급·반값티켓 계싼
    for n, m in cache.items():
        k = m['recommended_count']
        # 할인율(누적, 상한 25)
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
        # 반값티켓 부여: 10회마다 1장. 사용(티켓 사용 settle 방식 미정, 아래에서 카운트)
        tickets_owned = k // 10
        # 티켓 사용 여부: 구매기록 중 할인 >=50 이 있으면 티켓 사용 처리(구체 settle 로그에서 확인)
        used_tickets = 0
        for settle in settles:
            if (settle.get('buyer_label','') or '') .strip() == n and settle.get('half_price_ticket', False):
                used_tickets += 1
        m['half_price_tickets'] = tickets_owned
        m['half_price_tickets_used'] = used_tickets
    
    # 최종 산출 멤버만 반영
    for k,v in cache.items():
        if members is None or k in members:
            result[k] = {k2:v[k2] for k2 in ['purchase_count','recommend_count','recommended_count','grade','discount_rate','half_price_tickets','half_price_tickets_used','last_purchase_at','last_recommend_at']}
    # 저장
    with open('settle_master.json','w',encoding='utf8') as f:
        import json
        json.dump(result, f, ensure_ascii=False, indent=1)
    return {'members': result}
