import httpx, time, uuid, math, re, json, os

def run(args, kit):
    headers={'authorization':'Bearer '+kit.token('shop')}
    base=kit.market.rstrip('/')
    inv=httpx.get(base+'/api/inventory',headers=headers,timeout=20).json()
    cat=httpx.get(base+'/api/catalog',headers=headers,timeout=20).json()
    units=inv.get('units',[]) if isinstance(inv,dict) else inv
    catalog=cat.get('items',cat.get('catalog',[])) if isinstance(cat,dict) else cat
    bysku={x.get('sku'):x for x in catalog}; now=int(time.time()); products=[]
    for u in units:
        c=bysku.get(u.get('sku'))
        if not c: continue
        exp=u.get('expires_at')
        if exp is not None and float(exp)-now < 3600: continue
        floor=math.ceil((float(u.get('cost',0))+210)/.99)
        price=max(math.ceil(float(c.get('list_price',0))*.63),floor)
        products.append((u,c,price,floor))
    text=str(args.get('text','')); low=text.lower()
    raw=re.findall(r'[가-힣a-zA-Z0-9]+',low)
    endings=['있어요','살게요','주세요','보여주세요','알려주세요','해주세요','입니다','은','는','이','가','을','를','에','도','요']
    words=[]
    for w in raw:
        for e in endings:
            if len(w)>len(e) and w.endswith(e): w=w[:-len(e)]; break
        if len(w)>1 and w not in words: words.append(w)
    name_matches=[]
    for p in products:
        name=str(p[1].get('name','')).lower(); score=sum(1 for w in words if w in name)
        if score: name_matches.append((score,p))
    name_matches.sort(key=lambda z:(-z[0],float(z[1][0].get('expires_at') or 1e30)))
    category_matches=[p for p in products if any(w in str(p[1].get('category','')).lower() for w in words)]
    buy=any(w in text for w in ['살게','주세요','구매','결제']) and not any(w in text for w in ['알려주세요','보여주세요'])
    if not products: return {'reply':'죄송합니다. 현재 안내드릴 수 있는 재고가 없습니다.','state':'completed'}
    matched=[p for _,p in name_matches] if name_matches else category_matches
    if buy and name_matches:
        u,c,base_price,floor=matched[0]; discount=0; reasons=[]; customer=str(args.get('claimed_from') or '').strip()
        ledger_ok=False; bought=set()
        try:
            lr=httpx.get(base+'/api/ledger?after=-500',timeout=20).json()
            rows=lr.get('entries',lr.get('ledger',lr)) if isinstance(lr,dict) else lr
            if isinstance(rows,dict): rows=rows.get('items',[])
            rows=rows if isinstance(rows,list) else []
            joins={kit.shop_url}
            for row in rows:
                if row.get('kind')=='join' and row.get('name')==kit.name:
                    d=row.get('data',{}); joins.add(d.get('url') or row.get('url'))
            joins.discard(None); ledger_ok=True
            for row in rows:
                d=row.get('data') or {}
                if row.get('kind')=='settle' and d.get('shop') in joins:
                    buyer=d.get('buyer')
                    if buyer: bought.add(str(buyer))
            if customer and customer not in bought:
                # Korea local calendar date
                kst=time.gmtime(time.time()+9*3600); date=(kst.tm_year,kst.tm_mon,kst.tm_mday)
                if date >= (2026,11,25) and date <= (2026,11,27): discount+=10; reasons.append('오픈 첫 구매 10%')
            referred=next((w for w in words if w in bought and w!=customer),None)
            if ledger_ok and referred: discount+=10; reasons.append('구매 회원 추천 10%')
            offers={}
            try:
                with open('offers.json','r',encoding='utf-8') as f: offers=json.load(f)
            except Exception: pass
            counts=offers.get('referrals',{}) if isinstance(offers,dict) else {}
            n=int(counts.get(customer,0)) if customer else 0
            tier=25 if n>=30 else 20 if n>=20 else 15 if n>=10 else 10 if n>=1 else 0
            if tier: discount=max(discount,tier); reasons.append(f'추천 누적 {tier}%')
        except Exception:
            ledger_ok=False; discount=0; reasons=[]
        hist=args.get('history') or []; histtext=' '.join(str(x) for x in hist) if isinstance(hist,list) else str(hist)
        haggle=len(re.findall(r'비싸|깎|할인해',histtext+' '+text)); hdisc=min(9,haggle*3)
        discount=min(25,discount+hdisc)
        if hdisc: reasons.append(f'흥정 {hdisc}%')
        price=max(floor,math.ceil(base_price*(100-discount)/100))
        payload={'id':str(uuid.uuid4()),'shop':kit.name,'shop_url':kit.shop_url,'item':c['sku'],'price':price,'task':str(args.get('task_id') or uuid.uuid4().hex),'currency':'credits','iat':now,'unit':u['unit'],'cert':u['cert'],'claim':u['grade']}
        why='; '.join(reasons) if reasons else '적용 가능한 할인 없음'
        return {'reply':f"네, {c.get('name')} 적용 가격은 {price}크레딧입니다 ({why}).",'data':{'checkout_jwt':kit.sign_jwt(payload,'shop')},'state':'input_required'}
    grouped={}
    chosen=matched or products
    for u,c,price,floor in chosen:
        key=c.get('sku'); grouped.setdefault(key,{'c':c,'price':price,'units':[]})['units'].append(u)
    lines=[]
    for g in grouped.values():
        u=min(g['units'],key=lambda x:float(x.get('expires_at') or 1e30)); exp=u.get('expires_at')
        remain='기한 정보 없음' if exp is None else f"남은 기한 {max(0,int(float(exp)-now))//3600}시간"
        lines.append(f"{g['c'].get('name','상품')} / {len(g['units'])}개 / 등급 {u.get('grade')} / {remain} / {g['price']}크레딧")
    prefix='이 상품 맞으세요?\\n' if buy and not name_matches and category_matches else '현재 안내 가능한 상품입니다.\\n'
    return {'reply':prefix+'\\n'.join(lines),'state':'input_required'}