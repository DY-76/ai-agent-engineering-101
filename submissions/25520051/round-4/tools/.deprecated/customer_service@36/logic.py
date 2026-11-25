import httpx,json,os,re,time,math,secrets
from datetime import datetime,timezone
STOP=set('재고 가격 등급 실제 남은 기한 상품 서명 결제 확인 게시글 게시판 게시물 포럼 오늘 국내산 제철 신선 식품 판매 안내 현재 모듬 소비기한 실재고 checkout 가정용 배송 설치 교체 모델 조건 가능 상태 수량 fresh 보관 유효한 최종 요청 품목 정확히 구매 살게 결제서 영수증 jwt 로얄 서클 반찬 가족 저녁 한팩 유효'.split())
PART=['있나요','있어요','살게요','주세요','이나','에서','으로','하고','이랑','은','는','이','가','을','를','와','랑','의','도','만']
def getj(url,t):
 r=httpx.get(url,headers={'authorization':'Bearer '+t},timeout=15);r.raise_for_status();return r.json()
def run(args,kit):
 now=time.time(); base=kit.market.rstrip('/'); tok=kit.token('shop')
 inv=getj(base+'/api/inventory',tok); cat=getj(base+'/api/catalog',tok); led=getj(base+'/api/ledger?after=-500',tok)
 units=inv.get('units',[]) if isinstance(inv,dict) else inv
 products=cat if isinstance(cat,list) else cat.get('items',cat.get('catalog',[]))
 entries=led if isinstance(led,list) else led.get('items',led.get('ledger',[]))
 text=str(args.get('text','')); hist=args.get('history') or []; claimed=args.get('claimed_from')
 def words(s):
  out=[]
  for w in re.findall(r'[가-힣a-z0-9]+',s.lower()):
   if len(w)==1 and w not in ('귤','쌀','콩','무') or any(c.isdigit() for c in w):continue
   for p in PART:
    if w.endswith(p) and len(w)-len(p)>=2:w=w[:-len(p)];break
   if w not in STOP:out.append(w)
  return out
 sentences=re.split(r'[.!?\n]+',text); good=[]
 for s in sentences:
  if any(x in s for x in ['사지 않','구매하지 않','필요 없','필요하지 않','아니라','말고','제외']) and not any(x in s for x in ['C등급','8팩']):continue
  good.append(s)
 terms=words(' '.join(good)); sku_m=re.search(r'G[0-9a-fA-F]{8}',text); reqsku=sku_m.group(0) if sku_m else None
 if not terms:
  for h in reversed(hist[-4:]):
   terms=words(str(h.get('them','')))
   if terms:break
 checkout=any(x in text for x in ['살게','주세요','구매할','구매하','결제할','checkout','jwt','영수증','결제서','주문서']) and not any(x in text for x in ['보내지 말','발급하지 말'])
 if any(x in text for x in ['알려 주세요','알려주세요','보여 주세요']) and not any(x in text for x in ['살게','구매할','결제할']):checkout=False
 if reqsku and not any(p.get('sku')==reqsku for p in products):
  reply='요청하신 SKU 상품은 지금 재고가 없습니다.';data={}
 else:
  scored=[]
  for p in products:
   name=re.sub(r'\s+','',str(p.get('name','')).lower());score=sum(len(w) for w in terms if w in name)
   if reqsku and p.get('sku')!=reqsku:score=0
   if score:scored.append((score,p))
  scored.sort(key=lambda x:-x[0])
  cands=[]
  for score,p in scored:
   for u in units:
    if u.get('sku')!=p.get('sku'):continue
    h=(float(u.get('expires_at',now))-now)/3600
    if h<1 or (u.get('grade')=='C' and h<6 and not any(x in text for x in ['임박','저렴','싼'])):continue
    if 'A등급만' in text and u.get('grade')!='A':continue
    if any(x in text for x in ['B등급 이상','C등급이 아닌','C등급 제외','C등급은 제외']) and u.get('grade')=='C':continue
    if any(x in text for x in ['1팩','한 팩','한팩']) and '8팩' in p.get('name',''):continue
    ratio={'A':.70,'B':.60,'C':.46}.get(u.get('grade'),.46)
    for threshold,r in [(24,.52),(12,.42),(6,.32),(3,.20)]:
     if h<threshold:ratio=min(ratio,r)
    floor=math.ceil((float(u.get('cost',0))+210)/.99) if h>=36 else 220
    raw=max(math.ceil(float(p.get('list_price',0))*ratio),floor)
    cands.append((score,h,p,u,raw,floor))
  cands.sort(key=lambda x:(-x[0],x[1]))
  if not cands:
   reply='현재 안내 가능한 상품입니다.';data={}
  else:
   c=cands[0];score,h,p,u,raw,floor=c
   ownurls={kit.shop_url}; settles=[]; ownname=kit.name
   for e in entries:
    d=e.get('data') or {}
    if e.get('kind')=='join' and d.get('name')==ownname and d.get('url'):ownurls.add(d['url'])
    if e.get('kind')=='settle':settles.append(d)
   first=bool(claimed and datetime.fromtimestamp(now,timezone.utc).strftime('%Y-%m-%d') in ('2026-11-25','2026-11-26','2026-11-27') and not any(d.get('buyer_url')==claimed and d.get('shop_url') in ownurls for d in settles))
   haggles=sum(1 for x in ['비싸','깎아','할인해'] if x in text+' '+' '.join(str(z.get('them','')) for z in hist)); referral=bool(re.search(r'추천인\s*[:은는]?\s*[가-힣A-Za-z0-9]+',text)); rate=min(.25,(.10 if first else 0)+(.10 if referral else 0)+min(.09,haggles*.03)); price=max(floor,math.ceil(raw*(1-rate)))
   if checkout:
    payload={'id':secrets.token_hex(3),'shop':kit.name,'shop_url':kit.shop_url,'item':p['sku'],'price':price,'task':secrets.token_hex(4),'currency':'credits','iat':int(now),'unit':u.get('unit'),'claim':u.get('grade')}
    jwt=kit.sign_jwt(payload,'shop');reply=f"{p['name']} / 등급 {u.get('grade')} / 남은 기한 {h:.1f}시간 / {price}크레딧 (할인 {int(rate*100)}%)\n결제는 buy에서 이 가게 이름만 지정해 주세요. 토큰을 손으로 옮겨 적으면 서명이 깨질 수 있어요. 가게 지갑: {kit.address('shop')}";data={'checkout_jwt':jwt}
   else:reply='현재 안내 가능한 상품입니다.\n'+f"{p['name']} / 1개 / 등급 {u.get('grade')} / 남은 기한 {h:.1f}시간 / {price}크레딧";data={}
 if not kit.testing:
  with open('inquiries.jsonl','a',encoding='utf-8') as f:f.write(json.dumps({'time':now,'claimed_from':claimed,'text':text,'reply':reply},ensure_ascii=False)+'\n')
 return {'reply':reply,'data':data,'state':'input_required'}
