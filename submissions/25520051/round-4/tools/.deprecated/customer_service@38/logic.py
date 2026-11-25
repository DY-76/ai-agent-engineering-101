import httpx,json,time,os,re,math,secrets,datetime

def run(args,kit):
 text=str(args.get('text','')); who=args.get('claimed_from'); hist=args.get('history') or []; hist=hist.get('messages',[]) if isinstance(hist,dict) else hist
 base=kit.market; headers={'authorization':'Bearer '+kit.token('shop')}
 def get(path):
  r=httpx.get(base+path,headers=headers,timeout=20); r.raise_for_status(); return r.json()
 inv=get('/api/inventory'); cat=get('/api/catalog'); led=get('/api/ledger?after=-500')
 units=inv.get('units',[]) if isinstance(inv,dict) else inv; ps=cat if isinstance(cat,list) else cat.get('items',cat.get('catalog',[])); es=led if isinstance(led,list) else led.get('entries',led.get('ledger',[])); now=time.time(); by={p['sku']:p for p in ps}
 urls={kit.shop_url}
 for e in es:
  d=e.get('data',{}); 
  if e.get('kind')=='join' and d.get('name')==kit.name and d.get('url'): urls.add(d['url'])
 def price(u,p,h):
  ratio={'A':.70,'B':.60,'C':.46}.get(u.get('grade'),.46)
  for cut,lim in ((.52,24),(.42,12),(.32,6),(.20,3)):
   if h<lim: ratio=min(ratio,cut)
  floor=math.ceil((float(u.get('cost',0))+210)/.99) if h>=36 else 220
  return max(math.ceil(float(p.get('list_price',0))*ratio),floor)
 stop=set('재고 가격 등급 실제 남은 기한 상품 서명 결제 확인 게시글 게시판 게시물 포럼 오늘 국내산 제철 신선 식품 판매 안내 현재 모듬 소비기한 실재고 checkout 가정용 배송 설치 교체 모델 조건 가능 상태 수량 fresh 보관 유효한 최종 요청 품목 정확히 구매 살게 결제서 영수증 jwt 로얄 서클 반찬 가족 저녁 한팩 유효'.split())
 def pick(src):
  out=[]
  for w in re.findall(r'[가-힣a-z0-9]+',src.lower()):
   if len(w)==1 and w not in ('귤','쌀','콩','무'): continue
   for suf in ('있나요','있어요','살게요','주세요','에서','으로','하고','이랑','이나','은','는','이','가','을','를','와','랑','의','도','만'):
    if w.endswith(suf) and len(w)-len(suf)>=2: w=w[:-len(suf)]; break
   if w=='나' and not any(w in p.get('name','').replace(' ','').lower() for p in ps): continue
   if w not in stop and any(w in p.get('name','').replace(' ','').lower() for p in ps): out.append(w)
  return out
 def score(p,ws): return sum(len(w) for w in ws if w in p.get('name','').replace(' ','').lower())
 words=pick(text); neg=re.compile(r'사지 않|구매하지 않|필요 없|필요하지 않|아니라|말고|제외')
 sentences=[s for s in re.split(r'[.!?\n]+',text) if s and (not neg.search(s) or 'C등급' in s or '8팩' in s)]
 if not words:
  for hst in reversed(hist[-4:]):
   if isinstance(hst,dict):
    w=pick(str(hst.get('them','')))
    if w: words=w; break
 skuword=re.search(r'G[0-9a-fA-F]{8}',text)
 if skuword:
  if skuword.group().lower() not in {p.get('sku','').lower() for p in ps}: words=[]
  else: words=[skuword.group().lower()]
 def eligible(ws):
  f=[u for u in units if score(by.get(u.get('sku'),{}),ws)>0 and (float(u.get('expires_at') or now+9999*3600)-now)/3600>=1]
  if not any(x in text for x in ('임박','저렴','싼')):
   ab={u.get('sku') for u in f if u.get('grade') in ('A','B')}; f=[u for u in f if u.get('grade')!='C' or u.get('sku') not in ab]
  if any(x in text for x in ('1팩','한 팩','한팩')): f=[u for u in f if '8팩' not in by.get(u.get('sku'),{}).get('name','')]
  if any(x in text for x in ('B등급 이상','C등급이 아닌','C등급 제외','C등급은 제외')): f=[u for u in f if u.get('grade')!='C']
  if 'A등급만' in text: f=[u for u in f if u.get('grade')=='A']
  return sorted(f,key=lambda u:(-score(by.get(u.get('sku'),{}),ws),float(u.get('expires_at') or now+9999*3600)))
 buy=any(x in text for x in ('살게','주세요','구매할','구매하','결제할','checkout','jwt','영수증','결제서','주문서')) and not any(x in text for x in ('보내지 말','발급하지 말'))
 if any(x in text for x in ('알려 주세요','알려주세요','보여 주세요')) and not any(x in text for x in ('checkout','jwt','결제서','영수증')): buy=False
 f=eligible(words) if words else [u for u in units if (float(u.get('expires_at') or now+9999*3600)-now)/3600>=1]
 def listing(f):
  groups={}
  for u in f:
   p=by.get(u.get('sku'),{}); h=(float(u.get('expires_at') or now+9999*3600)-now)/3600; k=(u.get('sku'),u.get('grade')); groups.setdefault(k,[]).append((u,p,h))
  rows=[]
  for vals in groups.values():
   u,p,h=vals[0]; rows.append((u,p,h,len(vals)))
  rows.sort(key=lambda z:(z[0].get('grade') not in ('A','B'),float(z[0].get('expires_at') or now+9999*3600),'8팩' in z[1].get('name','')))
  return '현재 안내 가능한 상품입니다.\n'+'\n'.join(f"{p.get('name','')} / {n}개 / 등급 {u.get('grade')} / 남은 기한 {int(h)}시간 / {price(u,p,h)}크레딧" for u,p,h,n in rows[:30])
 if not words or not buy or not f:
  reply=listing(f) if f else ('찾으시는 상품은 지금 재고가 없습니다.\n'+listing([u for u in units if (float(u.get('expires_at') or now+9999*3600)-now)/3600>=1]) if words else '현재 안내 가능한 재고가 없습니다.')
  result={'reply':reply,'state':'input_required'}
 else:
  chosen=words
  for s in sentences:
   if any(x in s for x in ('결제서','주문서','checkout','jwt','영수증')) and pick(s): chosen=pick(s); break
  f=eligible(chosen); best=f[0] if f else None
  if best:
   # 최근 10분에 다른 고객에게 준 unit이면 동일 SKU의 다른 unit만 대체
   try: offers=json.load(open('offers.json',encoding='utf-8'))
   except: offers={}
   p=by.get(best.get('sku'),{}); h=(float(best.get('expires_at') or now+9999*3600)-now)/3600
   if who and best.get('unit') in offers and now-offers[best['unit']][0]<600 and offers[best['unit']][1]!=who:
    alt=[u for u in f if u.get('sku')==best.get('sku') and u.get('unit') not in offers]
    if alt: best=alt[0]; h=(float(best.get('expires_at') or now+9999*3600)-now)/3600
   today=datetime.datetime.fromtimestamp(now,datetime.timezone(datetime.timedelta(hours=9))).date().isoformat(); first=today in ('2026-11-25','2026-11-26','2026-11-27') and bool(who)
   prior=any(e.get('kind')=='settle' and e.get('data',{}).get('buyer')==who and e.get('data',{}).get('shop_url') in urls for e in es)
   referral=any(e.get('kind')=='settle' and e.get('data',{}).get('buyer')==w and e.get('data',{}).get('shop_url') in urls for w in pick(text) if w!=who)
   haggle=sum(text.count(x) for x in ('비싸','깎아','할인해')); discount=min(25,(10 if first and not prior else 0)+(10 if referral else 0)+min(9,3*haggle))
   p=by.get(best.get('sku'),{}); raw=price(best,p,h); final=max(math.ceil(raw*(100-discount)/100),math.ceil((float(best.get('cost',0))+210)/.99) if h>=36 else 220)
   offers[best.get('unit')]=[now,who]; json.dump(offers,open('offers.json','w',encoding='utf-8'),ensure_ascii=False)
   claim={'id':secrets.token_hex(3),'shop':kit.name,'shop_url':kit.shop_url,'item':best.get('sku'),'price':final,'task':secrets.token_hex(4),'currency':'credits','iat':int(now),'unit':best.get('unit'),'claim':best.get('grade')}
   reason='할인 없음' if not discount else f'할인 {discount}% (첫 구매/추천/흥정 적용)'
   reply=f"{p.get('name')} / 등급 {best.get('grade')} / 남은 기한 {int(h)}시간 / {final}크레딧 ({reason})\n결제는 buy에서 이 가게 이름만 지정해 주세요. 토큰을 손으로 옮겨 적으면 서명이 깨질 수 있어요. 가게 지갑: {kit.address('shop')}"
   for u in [x for x in f if x.get('sku')!=best.get('sku')][:2]:
    q=by.get(u.get('sku'),{}); hh=(float(u.get('expires_at') or now+9999*3600)-now)/3600; reply+=f"\n함께 찾은 상품: {q.get('name')} / 등급 {u.get('grade')} / 남은 기한 {int(hh)}시간 / {max(math.ceil(price(u,q,hh)*(100-discount)/100),math.ceil((float(u.get('cost',0))+210)/.99) if hh>=36 else 220)}크레딧"
   if re.search(r'포장량|중량|보관',text): reply+='\n포장량·중량·보관은 확인된 정보가 없습니다.'
   result={'reply':reply,'data':{'checkout_jwt':kit.sign_jwt(claim,'shop')},'state':'input_required'}
  else: result={'reply':'찾으시는 상품은 지금 재고가 없습니다.\n'+listing([u for u in units if (float(u.get('expires_at') or now+9999*3600)-now)/3600>=1]),'state':'input_required'}
 if not kit.testing:
  with open('inquiries.jsonl','a',encoding='utf-8') as f0: f0.write(json.dumps({'time':now,'claimed_from':who,'text':text,'reply':result['reply']},ensure_ascii=False)+'\n')
 return result