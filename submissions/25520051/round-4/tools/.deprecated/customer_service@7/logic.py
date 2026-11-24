import httpx, time, uuid, math, re

def run(args, kit):
    headers={'authorization':'Bearer '+kit.token('shop')}
    inv=httpx.get(kit.market.rstrip('/')+'/api/inventory',headers=headers,timeout=20).json()
    cat=httpx.get(kit.market.rstrip('/')+'/api/catalog',headers=headers,timeout=20).json()
    units=inv.get('units',[]) if isinstance(inv,dict) else inv
    catalog=cat.get('items',cat.get('catalog',[])) if isinstance(cat,dict) else cat
    bysku={x.get('sku'):x for x in catalog}; now=int(time.time()); products=[]
    for u in units:
        c=bysku.get(u.get('sku'))
        if not c: continue
        exp=u.get('expires_at')
        if exp is not None and float(exp)-now < 3600: continue
        price=max(math.ceil(float(c.get('list_price',0))*.63),math.ceil((float(u.get('cost',0))+210)/.99))
        products.append((u,c,price))
    text=str(args.get('text','')); low=text.lower()
    raw=re.findall(r'[가-힣a-zA-Z0-9]+',low)
    endings=['있어요','살게요','주세요','보여주세요','알려주세요','해주세요','입니다','은','는','이','가','을','를','에','도','요']
    words=[]
    for w in raw:
        for e in endings:
            if len(w)>len(e) and w.endswith(e):
                w=w[:-len(e)]; break
        if len(w)>1 and w not in words: words.append(w)
    name_matches=[]
    for p in products:
        name=str(p[1].get('name','')).lower()
        score=sum(1 for w in words if w in name)
        if score: name_matches.append((score,p))
    name_matches.sort(key=lambda z:(-z[0], float(z[1][0].get('expires_at') or 1e30)))
    category_matches=[p for p in products if any(w in str(p[1].get('category','')).lower() for w in words)]
    buy=any(w in text for w in ['살게','주세요','구매','결제']) and not any(w in text for w in ['알려주세요','보여주세요'])
    if not products: return {'reply':'죄송합니다. 현재 안내드릴 수 있는 재고가 없습니다.','state':'completed'}
    matched=[p for _,p in name_matches] if name_matches else category_matches
    if buy and name_matches:
        u,c,price=matched[0]; now=int(time.time())
        payload={'id':str(uuid.uuid4()),'shop':kit.name,'shop_url':kit.shop_url,'item':c['sku'],'price':price,'task':str(args.get('task_id') or uuid.uuid4().hex),'currency':'credits','iat':now,'unit':u['unit'],'cert':u['cert'],'claim':u['grade']}
        return {'reply':f"네, {c.get('name')} {price}크레딧으로 준비하겠습니다.",'data':{'checkout_jwt':kit.sign_jwt(payload,'shop')},'state':'input_required'}
    chosen=matched or products; grouped={}
    for u,c,price in chosen:
        key=c.get('sku'); grouped.setdefault(key,{'c':c,'price':price,'units':[]})['units'].append(u)
    lines=[]
    for g in grouped.values():
        u=min(g['units'],key=lambda x:float(x.get('expires_at') or 1e30)); exp=u.get('expires_at')
        remain='기한 정보 없음' if exp is None else f"남은 기한 {max(0,int(float(exp)-now))//3600}시간"
        lines.append(f"{g['c'].get('name','상품')} / {len(g['units'])}개 / 등급 {u.get('grade')} / {remain} / {g['price']}크레딧")
    prefix='이 상품 맞으세요?\n' if buy and not name_matches and category_matches else '현재 안내 가능한 상품입니다.\n'
    return {'reply':prefix+'\n'.join(lines),'state':'input_required'}