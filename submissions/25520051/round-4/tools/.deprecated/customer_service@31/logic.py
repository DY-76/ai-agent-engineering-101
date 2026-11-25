import httpx, re, json, os, time, math, base64, datetime
from urllib.parse import quote

def run(args, kit):
    text=str(args.get('text','')); claimed=args.get('claimed_from'); history=args.get('history') or []
    headers={'authorization':'Bearer '+kit.token('shop')}
    inv=httpx.get(kit.market+'/api/inventory',headers=headers,timeout=20).json().get('units',[])
    cat=httpx.get(kit.market+'/api/catalog',timeout=20).json()
    if isinstance(cat,dict): cat=cat.get('items',cat.get('catalog',[]))
    ledger=httpx.get(kit.market+'/api/ledger?after=-500',headers=headers,timeout=20).json()
    if isinstance(ledger,dict): ledger=ledger.get('entries',ledger.get('ledger',[]))
    now=int(time.time()); catalog={x.get('sku'):x for x in cat}
    def clean(s):
        s=re.sub(r'[^가-힣a-z0-9]+',' ',str(s).lower())
        words=[]
        stop=set('재고 가격 등급 실제 남은 기한 상품 서명 결제 확인 게시글 게시판 게시물 포럼 오늘 국내산 제철 신선 식품 판매 안내 현재 모듬 소비기한 실재고 checkout 가정용 배송 설치 교체 모델 조건 가능 상태 수량 fresh 보관 유효한 최종 요청 품목 정확히 구매 살게 결제서 영수증 jwt 로얄 서클 반찬 가족 저녁 한팩 유효'.split())
        particles=['있나요','있어요','살게요','주세요','이나','에서','으로','하고','이랑','은','는','이','가','을','를','와','랑','의','도','만']
        for w in s.split():
            for p in particles:
                if w.endswith(p) and len(w)-len(p)>=2: w=w[:-len(p)]; break
            if w in ('나','1','8') or w in stop or len(w)==1 and w not in ('귤','쌀','콩','무'): continue
            if re.search(r'\d',w): continue
            words.append(w)
        return words
    words=clean(text)
    if not words:
        for h in reversed(history[-3:]):
            if isinstance(h,dict): words+=clean(h.get('text',''))
            elif isinstance(h,str): words+=clean(h)
    def score(name):
        n=re.sub(r'\s+','',str(name).lower()); return sum(len(w) for w in set(words) if w in n)
    units=[]
    for u in inv:
        sku=u.get('sku'); c=catalog.get(sku,{})
        exp=u.get('expires_at'); h=(int(exp)-now)/3600 if exp else 99999
        if h<1: continue
        grade=str(u.get('grade','')).upper(); lp=int(c.get('list_price',0)); cost=int(u.get('cost',0))
        ratio={'A':.84,'B':.72,'C':.58}.get(grade,.72)
        if h<3: ratio=min(ratio,.25)
        elif h<6: ratio=min(ratio,.40)
        elif h<12: ratio=min(ratio,.50)
        price=math.ceil(lp*ratio)
        floor=math.ceil((cost+210)/.99) if h>=12 else 220
        price=max(price,floor)
        units.append({'unit':u.get('unit'),'sku':sku,'name':c.get('name',u.get('name','상품')),'grade':grade,'h':h,'price':price,'cost':cost})
    qsku=re.search(r'G[0-9a-fA-F]{8}',text)
    if qsku and not any(x['sku'].lower()==qsku.group().lower() for x in units):
        return {'reply':'요청하신 SKU는 지금 재고가 없습니다.','state':'input_required'}
    if qsku: units=[x for x in units if x['sku'].lower()==qsku.group().lower()]
    if '1팩' in text or '한 팩' in text or '한팩' in text: units=[x for x in units if '8팩' not in x['name']]
    if any(x in text for x in ['B등급 이상','C등급이 아닌','C등급 제외','C등급은 제외']): units=[x for x in units if x['grade']!='C']
    if 'A등급만' in text: units=[x for x in units if x['grade']=='A']
    if not any(x in text for x in ['임박','저렴','싼']):
        bysku={x['sku'] for x in units if x['grade'] in ('A','B')}; units=[x for x in units if not (x['grade']=='C' and x['sku'] in bysku)]
    for x in units: x['score']=score(x['name'])
    units.sort(key=lambda x:(-x['score'],x['h']))
    buying=any(k in text for k in ['살게','주세요','구매할','구매하','결제할','checkout','jwt','영수증','결제서','주문서']) and not any(k in text for k in ['보내지 말','발급하지 말'])
    if not units: reply='현재 안내 가능한 상품이 없습니다.'
    elif not buying or text.strip() in ('알려 주세요','알려주세요','보여 주세요'):
        reply='현재 안내 가능한 상품입니다.\n'+'\n'.join(f"{x['name']} / 1개 / 등급 {x['grade']} / 남은 기한 {max(0,int(x['h']))}시간 / {x['price']}크레딧" for x in units[:30])
    else:
        x=units[0]; discount=0; reasons=[]
        settles=[e for e in ledger if e.get('kind')=='settle']
        joined={str(e.get('data',{}).get('name')):str(e.get('data',{}).get('url')) for e in ledger if e.get('kind')=='join'}
        if claimed and datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).date().isoformat() in ('2026-11-25','2026-11-26','2026-11-27') and not any(e.get('data',{}).get('buyer')==claimed and e.get('data',{}).get('shop_url') in set(joined.values())|{kit.shop_url} for e in settles): discount+=10; reasons.append('첫 구매 행사 10%')
        if claimed and re.search(r'\b'+re.escape(str(claimed))+r'\b',text): discount+=10; reasons.append('추천 10%')
        bargaining=sum((text+' '+' '.join(str(h.get('text','')) for h in history if isinstance(h,dict))).count(k) for k in ['비싸','깎아','할인해']); b=min(9,bargaining*3)
        if b: discount+=b; reasons.append(f'흥정 {b}%')
        discount=min(discount,25); price=max(math.ceil(x['price']*(100-discount)/100),math.ceil((x['cost']+210)/.99) if x['h']>=12 else 220)
        payload={'id':os.urandom(3).hex(),'shop':kit.name,'shop_url':kit.shop_url,'item':x['sku'],'price':price,'task':os.urandom(4).hex(),'currency':'credits','iat':now,'unit':x['unit'],'claim':x['grade']}
        jwt=kit.sign_jwt(payload,'shop')
        reply=f"{x['name']} / 등급 {x['grade']} / 남은 기한 {max(0,int(x['h']))}시간 / 최종 가격 {price}크레딧"+((' ('+', '.join(reasons)+')') if reasons else '')+f"\n결제 토큰은 수정하지 말고 그대로 사용해 주세요.\ncheckout_jwt: {jwt}"
        for y in units[1:3]: reply+=f"\n함께 찾은 상품: {y['name']} / 등급 {y['grade']} / 남은 기한 {max(0,int(y['h']))}시간 / {max(math.ceil(y['price']*(100-discount)/100),220)}크레딧"
        if not kit.testing:
            path='offers.json'; old={}
            try: old=json.load(open(path))
            except: pass
            old[x['unit']]=[now,claimed]; json.dump(old,open(path,'w'))
    if not kit.testing:
        with open('inquiries.jsonl','a') as f: f.write(json.dumps({'time':now,'claimed_from':claimed,'text':text,'reply':reply},ensure_ascii=False)+'\n')
    return {'reply':reply,'state':'input_required'}