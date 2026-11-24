import httpx, time, uuid, math

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
    words=[w for w in low.replace('?',' ').replace('!',' ').split() if len(w)>1]
    matched=[p for p in products if any(w in str(p[1].get('name','')).lower() or w in str(p[1].get('category','')).lower() for w in words)]
    buy=any(w in text for w in ['살게','주세요','구매','결제']) and not any(w in text for w in ['알려주세요','보여주세요'])
    if not products: return {'reply':'죄송합니다. 현재 안내드릴 수 있는 재고가 없습니다.','state':'completed'}
    if buy and matched:
        u,c,price=matched[0]; now=int(time.time())
        payload={'id':str(args.get('claimed_from') or '손님'),'shop':kit.name,'shop_url':kit.shop_url,'item':c['sku'],'price':price,'task':str(args.get('task_id') or uuid.uuid4().hex),'currency':'credits','iat':now,'unit':u['unit'],'cert':u['cert'],'claim':u['grade']}
        return {'reply':f"네, {c.get('name')} {price}크레딧으로 준비하겠습니다.",'data':{'checkout_jwt':kit.sign_jwt(payload,'shop')},'state':'input_required'}
    chosen=matched or products; lines=[]
    for u,c,price in chosen:
        exp=u.get('expires_at'); remain='기한 정보 없음' if exp is None else f"남은 기한 {max(0,int(float(exp)-now))//60}분"
        lines.append(f"{c.get('name','상품')} / 등급 {u.get('grade')} / {remain} / {price}크레딧")
    return {'reply':'현재 안내 가능한 상품입니다.\n'+'\n'.join(lines),'state':'completed'}