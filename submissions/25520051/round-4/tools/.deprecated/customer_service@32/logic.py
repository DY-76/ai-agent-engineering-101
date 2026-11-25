import httpx,re,json,os,time,math,datetime

def run(args,kit):
 text=str(args.get('text','')); claimed=args.get('claimed_from'); history=args.get('history') or []; now=int(time.time()); headers={'authorization':'Bearer '+kit.token('shop')}
 inv=httpx.get(kit.market+'/api/inventory',headers=headers,timeout=20).json().get('units',[])
 cat=httpx.get(kit.market+'/api/catalog',timeout=20).json(); cat=cat.get('items',cat.get('catalog',[])) if isinstance(cat,dict) else cat
 led=httpx.get(kit.market+'/api/ledger?after=-500',headers=headers,timeout=20).json(); led=led.get('entries',led.get('ledger',[])) if isinstance(led,dict) else led
 cmap={x.get('sku'):x for x in cat}; stop=set('재고 가격 등급 실제 남은 기한 상품 서명 결제 확인 게시글 게시판 게시물 포럼 오늘 국내산 제철 신선 식품 판매 안내 현재 모듬 소비기한 실재고 checkout 가정용 배송 설치 교체 모델 조건 가능 상태 수량 fresh 보관 유효한 최종 요청 품목 정확히 구매 살게 결제서 영수증 jwt 로얄 서클 반찬 가족 저녁 한팩 유효'.split()); particles=['알려주시고','부탁합니다','있나요','있어요','살게요','주세요','이나','에서','으로','하고','이랑','은','는','이','가','을','를','와','랑','의','도','만']
 def clean(s):
  out=[]
  for w in re.sub(r'[^가-힣a-z0-9]+',' ',str(s).lower()).split():
   for p in particles:
    if w.endswith(p) and len(w)-len(p)>=2: w=w[:-len(p)]; break
   if w=='나' and not any(w in str(c.get('name','')).lower() for c in cat): continue
   if w in stop or re.search(r'\d',w) or (len(w)==1 and w not in ('귤','쌀','콩','무')): continue
   out.append(w)
  return out
 words=clean(text)
 def score(name,ws):
  n=re.sub(r'\s+','',str(name).lower()); return sum(len(w) for w in set(ws) if w in n or (w=='생선' and any(z in n for z in ['가자미','고등어','자반'])))
 if not words:
  for h in reversed(history):
   if isinstance(h,dict) and h.get('them'):
    words=clean(h['them'])
    if words: break
 units=[]
 for u in inv:
  c=cmap.get(u.get('sku'),{}); exp=u.get('expires_at'); hours=(int(exp)-now)/3600 if exp else 99999
  if hours<1: continue
  g=str(u.get('grade','')).upper(); cost=int(u.get('cost',0)); lp=int(c.get('list_price',0)); ratio={'A':.84,'B':.72,'C':.58}.get(g,.72)
  if hours<12: ratio=min(ratio,.5)
  if hours<6: ratio=min(ratio,.4)
  if hours<3: ratio=min(ratio,.25)
  price=max(math.ceil(lp*ratio),math.ceil((cost+210)/.99) if hours>=12 else 220)
  units.append({'unit':u.get('unit'),'sku':u.get('sku'),'name':c.get('name',u.get('name','상품')),'grade':g,'h':hours,'cost':cost,'price':price})
 q=re.search(r'G[0-9a-fA-F]{8}',text)
 if q: units=[x for x in units if str(x['sku']).lower()==q.group().lower()]
 if any(k in text for k in ['1팩','한 팩','한팩']): units=[x for x in units if '8팩' not in x['name']]
 if any(k in text for k in ['B등급 이상','C등급이 아닌','C등급 제외','C등급은 제외']): units=[x for x in units if x['grade']!='C']
 if 'A등급만' in text: units=[x for x in units if x['grade']=='A']
 if not any(k in text for k in ['임박','저렴','싼']):
  ab={x['sku'] for x in units if x['grade'] in ('A','B')}; units=[x for x in units if not(x['grade']=='C' and x['sku'] in ab)]
 for x in units: x['score']=score(x['name'],words)
 buying=any(k in text for k in ['살게','주세요','구매할','구매하','결제할','checkout','jwt','영수증','결제서','주문서']) and not any(k in text for k in ['보내지 말','발급하지 말'])
 if not words:
  buying=False
 if words and not any(x['score']>0 for x in units):
  buying=False; prefix='찾으시는 상품은 지금 재고가 없습니다. 지금 있는 상품입니다.\n'
 else: prefix=''
 units.sort(key=lambda x:(-x['score'],x['h']))
 if words and units and units[0]['score']>0:
  bestcat=max([score(c.get('name',''),words) for c in cat] or [0])
  if bestcat-units[0]['score']>=4:
   matches=sorted([x for x in units if x['score']>0],key=lambda x:(-x['score'],x['h']))[:3]
   reply=f"찾으시는 {cmap.get(matches[0]['sku'],{}).get('name','상품')}은(는) 지금 재고가 없습니다. 비슷한 상품 안내입니다.\n"+'\n'.join(f"{x['name']} / 1개 / 등급 {x['grade']} / 남은 기한 {int(x['h'])}시간 / {x['price']}크레딧" for x in matches)
   return _finish(reply,None,args,kit)
 if not units: return _finish(prefix+'현재 안내 가능한 상품이 없습니다.',None,args,kit)
 selected=[x for x in units if x['score']>0] if words else units
 if not selected: selected=units
 if not buying or text.strip() in ('알려 주세요','알려주세요','보여 주세요'):
  grouped={}
  for x in selected:
   k=(x['sku'],x['grade']); grouped.setdefault(k,[]).append(x)
  rows=[]
  for xs in grouped.values():
   xs.sort(key=lambda z:z['h']); x=xs[0]; rows.append((x['name'],x['grade'],x['h'],x['price'],len(xs)))
  rows.sort(key=lambda r:(r[0].endswith('8팩'),r[2]))
  reply=prefix+'현재 안내 가능한 상품입니다.\n'+'\n'.join(f'{n} / {qty}개 / 등급 {g} / 남은 기한 {int(h)}시간 / {p}크레딧' for n,g,h,p,qty in rows)
  return _finish(reply,None,args,kit)
 x=selected[0]; settles=[e.get('data',{}) for e in led if e.get('kind')=='settle']; joins={str(e.get('data',{}).get('name')):str(e.get('data',{}).get('url')) for e in led if e.get('kind')=='join' and e.get('data',{}).get('name')==kit.name}; urls=set(joins.values())|{kit.shop_url}; disc=0; reasons=[]
 today=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).date().isoformat()
 if claimed and today in ('2026-11-25','2026-11-26','2026-11-27') and not any(e.get('buyer')==claimed and e.get('shop') in urls for e in settles): disc+=10; reasons.append('첫 구매 행사 10%')
 buyers={e.get('buyer'):e for e in settles if e.get('shop') in urls}
 if claimed and any(n!=claimed and n in text and n in buyers for n in buyers): disc+=10; reasons.append('추천 10%')
 count=sum((text+' '+' '.join(str(h.get('them','')) for h in history if isinstance(h,dict))).count(k) for k in ['비싸','깎아','할인해']); b=min(9,count*3)
 if b: disc+=b; reasons.append(f'흥정 {b}%')
 disc=min(disc,25); floor=math.ceil((x['cost']+210)/.99) if x['h']>=12 else 220; price=max(math.ceil(x['price']*(100-disc)/100),floor)
 payload={'id':os.urandom(3).hex(),'shop':kit.name,'shop_url':kit.shop_url,'item':x['sku'],'price':price,'task':os.urandom(4).hex(),'currency':'credits','iat':now,'unit':x['unit'],'claim':x['grade']}; jwt=kit.sign_jwt(payload,'shop')
 reply=f"{x['name']} / 등급 {x['grade']} / 남은 기한 {int(x['h'])}시간 / 최종 가격 {price}크레딧"+((' ('+', '.join(reasons)+')') if reasons else '')+'\n결제 토큰은 수정하지 말고 그대로 사용해 주세요.'
 others=[]
 for y in selected:
  if y['sku']!=x['sku'] and y['score']>0 and all(z['sku']!=y['sku'] for z in others): others.append(y)
 for y in others[:2]: reply+=f"\n함께 찾은 상품: {y['name']} / 등급 {y['grade']} / 남은 기한 {int(y['h'])}시간 / {max(math.ceil(y['price']*(100-disc)/100),220)}크레딧"
 try:
  offers=json.load(open('offers.json',encoding='utf-8'))
 except: offers={}
 prior=offers.get(str(x['unit']))
 if prior and now-prior[0]<600 and prior[1]!=claimed:
  alt=next((z for z in selected if not(offers.get(str(z['unit'])) and now-offers[str(z['unit'])][0]<600 and offers[str(z['unit'])][1]!=claimed)),None)
  if alt: x=alt
 offers[str(x['unit'])]=[now,claimed]
 with open('offers.json','w',encoding='utf-8') as f: json.dump(offers,f,ensure_ascii=False)
 return _finish(reply,jwt,args,kit)
def _finish(reply,jwt,args,kit):
 if not kit.testing:
  with open('inquiries.jsonl','a',encoding='utf-8') as f: f.write(json.dumps({'time':int(time.time()),'claimed_from':args.get('claimed_from'),'text':args.get('text',''),'reply':reply},ensure_ascii=False)+'\n')
 out={'reply':reply,'state':'input_required'}
 if jwt: out['data']={'checkout_jwt':jwt}
 return out
