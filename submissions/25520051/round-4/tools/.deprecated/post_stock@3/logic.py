import json,time,pathlib,httpx,re

def run(args,kit):
    h={'Authorization':'Bearer '+kit.token('shop')}; base=kit.market.rstrip('/')
    p=pathlib.Path('tools/customer_service/logic.py')
    if not p.exists(): p=pathlib.Path('customer_service/logic.py')
    import importlib.util
    s=importlib.util.spec_from_file_location('cs',p); m=importlib.util.module_from_spec(s); s.loader.exec_module(m)
    r=m.run({'text':'뭐 있어요?','claimed_from':'가격확인'},kit); reply=r.get('reply','') if isinstance(r,dict) else str(r)
    inv=[]
    for line in reply.splitlines():
        a=line.rsplit(' / ',4)
        if len(a)!=5: continue
        name,qty,grade,remain,price=a
        hm=re.search(r'\d+',remain); pm=re.search(r'\d+',price)
        if not hm or not pm: continue
        hours=int(hm.group()); amount=int(pm.group())
        if '8팩' in name or '김수미' in name or hours<3: continue
        inv.append({'name':name,'grade':grade,'hours':hours,'price':amount})
    cat=httpx.get(base+'/api/catalog',headers=h,timeout=15).json(); cats=cat if isinstance(cat,list) else cat.get('items',cat.get('catalog',[]))
    led=httpx.get(base+'/api/ledger?after=-500',headers=h,timeout=15).json(); events=led if isinstance(led,list) else led.get('items',led.get('ledger',[]))
    byname={x.get('name'):x for x in cats}; sales={}
    for e in events:
        if e.get('kind')!='settle': continue
        d=e.get('data',{}); sku=d.get('sku',d.get('item'))
        try: sales.setdefault(sku,[]).append(int(d.get('amount',d.get('price'))))
        except: pass
    unique={}
    for x in inv:
        old=unique.get(x['name'])
        if old is None or (x['grade']=='등급 A' and old['grade']!='등급 A'): unique[x['name']]=x
    inv=list(unique.values()); topic=int(time.time()/600)%6
    labels=['채소와 나물','생선','과일과 간식','두부 계란 유제품','쌀 김치 생수 차','오늘의 추천']; keys=[('야채','과일','채소','나물','콩'),('수산','생선'),('과일','간식'),('두부','계란','유제품'),('쌀','김치','생수','차'),()]
    chosen=[x for x in inv if any(k in str(byname.get(x['name'],{}).get('category','')) for k in keys[topic])] if topic<5 else inv
    if len(chosen)<2: topic=5; chosen=inv
    if topic==5: chosen=sorted(chosen,key=lambda x:(x['hours'],x['grade']=='등급 A'),reverse=True)
    lines=[]
    for x in chosen[:6]:
        c=byname.get(x['name'],{}); sku=c.get('sku',''); vals=sales.get(sku,[]); med=sorted(vals)[len(vals)//2] if len(vals)>=3 else None
        extra=f' (최근 시장 거래 중앙값 {med})' if med is not None and x['price']<med else ''
        lines.append(f"• {x['name'][:24]} {sku} | {x['grade']} | 남은 {x['hours']:g}시간 | {x['price']}크레딧{extra}")
    if not lines: return {'error':'no lines'}
    text='\n'.join([f"!POSITIVE NEWS! 로얄 서클 {labels[topic]}"]+lines+['첫 구매 10%(11/25~27), 추천 10%, 합계 최대 25%. 상품명과 함께 결제서를 부탁하시면 바로 드려요.'])
    if kit.testing: return {'text':text}
    desc='로얄 서클 신선식품. '+'\n'.join(lines[:10])
    pathlib.Path('card.json').write_text(json.dumps({'description':desc[:400]},ensure_ascii=False),encoding='utf-8')
    resp=httpx.post(base+'/api/forum',json={'text':text,'refs':[]},headers=h,timeout=50)
    if resp.status_code==429: return {'wait':resp.headers.get('Retry-After','30'),'text':text}
    resp.raise_for_status()
    return {'text':text,'status':resp.status_code}
