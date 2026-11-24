import json,re,time,httpx

def load():
    try:
        with open('ledger.json',encoding='utf-8') as f:return json.load(f)
    except:return {'members':{},'transactions':[]}
def save(x):
    with open('ledger.json','w',encoding='utf-8') as f:json.dump(x,f,ensure_ascii=False,indent=2)
def words(s): return re.findall(r'[A-Za-z0-9가-힣_-]+',s or '')
def run(a,kit):
    text=(a.get('text') or '').strip(); db=load(); claimed=(a.get('claimed_from') or '').strip()
    # claimed_from is an unverified identity; retain it as a contact/member label only, never as proof of purchase
    if claimed:
        db['members'].setdefault(claimed,{'name':claimed,'purchases':[],'referrals':0,'discount_pending':0,'grade':1,'tickets':0})
    h={'authorization':'Bearer '+kit.token('shop')}
    try:
        c=httpx.get(kit.market+'/api/catalog',headers=h,timeout=8).json()
        iv=httpx.get(kit.market+'/api/inventory',headers=h,timeout=8).json()
    except Exception:
        return {'reply':'죄송합니다. 현재 재고와 가격을 확인할 수 없습니다. 잠시 후 다시 문의해 주세요.','state':'input_required'}
    items=c.get('items',c.get('catalog',[])) if isinstance(c,dict) else c
    units=iv.get('units',iv.get('items',[])) if isinstance(iv,dict) else iv
    # Match product name/SKU, preferring the longest matching catalog name
    low=text.lower(); matches=[]
    for it in items or []:
        nm=str(it.get('name',it.get('sku',''))); sku=str(it.get('sku',''))
        if nm.lower() in low or sku.lower() in low or any(w.lower() in nm.lower() and len(w)>1 for w in words(text)):
            us=[u for u in units or [] if str(u.get('sku'))==sku]
            if us: matches.append((len(nm),it,us))
    if not matches:
        return {'reply':'문의하신 상품은 현재 재고가 없습니다. 원하시는 상품명이나 SKU를 알려주시면 재고가 있는 대체 상품도 정중히 안내해 드리겠습니다.','state':'input_required'}
    _,it,us=max(matches,key=lambda x:x[0]); base=int(it.get('list_price',it.get('price',0)) or 0)
    bargain=any(x in text for x in ['비싸','깎','할인','흥정','조금만'])
    # referral name explicitly supplied in the message; only an existing member with a completed purchase qualifies
    ref=None
    m=re.search(r'(?:추천인|추천|회원명|회원|이름)\s*[:：]?\s*([가-힣A-Za-z0-9_-]{2,30})',text)
    if m and m.group(1) in db.get('members',{}):
        cand=db['members'][m.group(1)]
        if cand.get('purchases'): ref=m.group(1)
    member=db.get('members',{}).get(claimed) if claimed else None
    refs=int(member.get('referrals',0)) if member else 0
    discount=(10+5*(refs//10)) if refs else 0
    discount=min(50,discount)
    price=base*(100-discount)//100 if discount else base
    if bargain and price>0:
        # modest negotiation, never below cost or zero; use prior history only as context
        cost=int(us[0].get('cost',0) or 0); price=max(cost+1,price- max(1,price//20))
    buy=any(x in text for x in ['살게','주세요','사고 싶','구매','주문','결제','구입'])
    db['transactions'].append({'type':'inquiry','member':claimed or None,'referrer':ref,'sku':it.get('sku'),'text':text,'time':int(time.time())})
    save(db)
    nm=it.get('name',it.get('sku')); avail=len(us)
    if not buy:
        return {'reply':f'{nm}({it.get("sku")})은 {avail}개 재고가 있으며 가격은 {base}크레딧입니다. 현재 회원 적용 가격은 {price}크레딧입니다. 구매를 원하시면 “살게요”라고 말씀해 주세요.','state':'input_required'}
    u=us[0]; payload={'id':'rc-'+str(time.time_ns()),'shop':kit.name,'shop_url':kit.shop_url,'item':it.get('sku'),'price':price,'task':a.get('task_id') or 'rc-'+str(time.time_ns()),'currency':'credits','iat':int(time.time()),'unit':u.get('unit'),'cert':u.get('cert')}
    jwt=kit.sign_jwt(payload,'shop')
    return {'reply':f'{nm} 1개를 {price}크레딧으로 준비했습니다'+(f' (회원 {discount}% 할인 적용)' if discount else '')+'. 구매자의 주문과 함께 이 결제 정보를 제출해 주세요.','data':{'checkout_jwt':jwt},'state':'completed'}
