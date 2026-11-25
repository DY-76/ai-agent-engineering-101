import httpx,json,time,os,re,math,datetime,secrets

def run(args,kit):
 text=str(args.get('text','')); who=args.get('claimed_from'); hist=args.get('history') or []
 if isinstance(hist,dict): hist=hist.get('messages',[])
 tok=kit.token('shop'); base=kit.market
 def get(path):
  r=httpx.get(base+path,headers={'authorization':'Bearer '+tok},timeout=20); r.raise_for_status(); return r.json()
 inv=get('/api/inventory'); cat=get('/api/catalog'); led=get('/api/ledger?after=-500')
 units=inv.get('units',[]); products=cat if isinstance(cat,list) else cat.get('items',cat.get('catalog',[])); entries=led if isinstance(led,list) else led.get('entries',led.get('ledger',[]))
 now=time.time(); skuinfo={p['sku']:p for p in products}; urls={kit.shop_url,kit.name}
 words=[]
 for m in re.findall(r'[가-힣a-z0-9]+',text.lower()):
  if len(m)==1 and m not in ('귤','쌀','콩','무'): continue
  for suf in ('있나요','있어요','살게요','주세요','에서','으로','하고','이랑','이나','은','는','이','가','을','를','와','랑','의','도','만'):
   if m.endswith(suf) and len(m)-len(suf)>=2: m=m[:-len(suf)]; break
  if m=='나' and any('나' in p['name'].lower() for p in products): continue
  if m not in '재고 가격 등급 실제 남은 기한 상품 서명 결제 확인 게시글 게시판 게시물 포럼 오늘 국내산 제철 신선 식품 판매 안내 현재 모듬 소비기한 실재고 checkout 가정용 배송 설치 교체 모델 조건 가능 상태 수량 fresh 보관 유효한 최종 요청 품목 정확히 구매 살게 결제서 영수증 jwt 로얄 서클 반찬 가족 저녁 한팩 유효'.split(): words.append(m)
 def score(p,ws): return sum(len(w) for w in ws if w in p.get('name','').replace(' ','').lower())
 known=[w for w in words if any(w in p.get('name','').replace(' ','').lower() for p in products)]
 neg=re.compile(r'사지 않|구매하지 않|필요 없|필요하지 않|아니라|말고|제외')
 sentences=[s for s in re.split(r'[.!?\n]+',text) if s and (not neg.search(s) or 'C등급' in s or '8팩' in s)]
 buy=any(x in text for x in ('살게','주세요','구매할','구매하','결제할','checkout','jwt','영수증','결제서','주문서')) and not any(x in text for x in ('보내지 말','발급하지 말'))
 if any(x in text for x in ('알려 주세요','알려주세요','보여 주세요')) and not any(x in text for x in ('checkout','jwt','결제서','영수증')): buy=False
 if re.search(r'포장량|중량|보관',text): return {'reply':'문의하신 포장량·중량·보관 정보는 확인된 정보가 없습니다.','state':'input_required'}
 if not known:
  for h in reversed(hist[-4:]):
   them=h.get('them','') if isinstance(h,dict) else ''
   known=[w for w in re.findall(r'[가-힣a-z0-9]+',them.lower()) if any(w in p.get('name','').replace(' ','').lower() for p in products)]
   if known: break
 skuword=re.search(r'G[0-9a-fA-F]{8}',text)
 if skuword:
  if not any(p.get('sku','').lower()==skuword.group().lower() for p in products): return {'reply':'찾으시는 상품은 지금 재고가 없습니다.','state':'input_required'}
  known=[skuword.group().lower()]
 def rank(u,ws):
  p=skuinfo.get(u.get('sku'),{}); return score(p,ws)
 def eligible(ws):
  found=[u for u in units if rank(u,ws)>0 and float(u.get('expires_at',0))>now+3600]
  if '임박' not in text and '저렴' not in text and '싼' not in text:
   ab={u.get('sku') for u in found if u.get('grade') in ('A','B')}; found=[u for u in found if not(u.get('grade')=='C' and u.get('sku') in ab)]
  if '1팩' in text or '한 팩' in text or '한팩' in text: found=[u for u in found if '8팩' not in skuinfo.get(u.get('sku'),{}).get('name','')]
  if any(x in text for x in ('B등급 이상','C등급이 아닌','C등급 제외','C등급은 제외')): found=[u for u in found if u.get('grade')!='C']
  if 'A등급만' in text: found=[u for u in found if u.get('grade')=='A']
  return sorted(found,key=lambda u:(-rank(u,ws),float(u.get('expires_at',0))))
 if not known or not buy:
  ws=known; found=eligible(ws) if ws else [u for u in units if float(u.get('expires_at',0))>now+3600]
  lines=[]; grouped={}
  for u in found:
   p=skuinfo.get(u.get('sku'),{}); h=(float(u['expires_at'])-now)/3600; g=u.get('grade','?'); ratio={'A':.70,'B':.60,'C':.46}.get(g,.46)
   if h<24: ratio=min(ratio,.52)
   if h<12: ratio=min(ratio,.42)
   if h<6: ratio=min(ratio,.32)
   if h<3: ratio=min(ratio,.20)
   price=max(math.ceil(p.get('list_price',0)*ratio),math.ceil((u.get('cost',0)+210)/.99) if h>=36 else 220)
   k=(u.get('sku'),g); grouped.setdefault(k,[]).append((u,h,price,p))
  rows=[]
  for vals in grouped.values():
   u,h,price,p=vals[0]; rows.append((0 if u.get('grade') in ('A','B') else 1,float(u['expires_at']),('8팩' in p.get('name','')),f"{p.get('name','')} / {len(vals)}개 / 등급 {u.get('grade')} / 남은 기한 {int(h)}시간 / {price}크레딧"))
  rows.sort(); lines=['현재 안내 가능한 상품입니다.']+[r[3] for r in rows[:30]]
  if known and not found: return {'reply':'찾으시는 상품은 지금 재고가 없습니다. 지금 있는 상품입니다.\n'+'\n'.join(lines),'state':'input_required'}
  return {'reply':'\n'.join(lines) if found else '현재 안내 가능한 재고가 없습니다.','state':'input_required'}
 # 구매할 경우 결제를 요청한 문장에 품목이 있으면 그 문장의 낱말을 우선 사용
 chosen=known
 for s in sentences:
  if any(x in s for x in ('결제서','주문서','checkout','jwt','영수증')):
   sw=[w for w in known if w in s.lower()]
   if sw: chosen=sw; break
 found=eligible(chosen)
 if not found: return {'reply':'찾으시는 상품은 지금 재고가 없습니다. 지금 있는 상품입니다.\n현재 안내 가능한 상품입니다.','state':'input_required'}
 best=found[0]; p=skuinfo.get(best.get('sku'),{}); h=(float(best['expires_at'])-now)/3600
 ratio={'A':.70,'B':.60,'C':.46}.get(best.get('grade'),.46)
 if h<24: ratio=min(ratio,.52)
 if h<12: ratio=min(ratio,.42)
 if h<6: ratio=min(ratio,.32)
 if h<3: ratio=min(ratio,.20)
 price=max(math.ceil(p.get('list_price',0)*ratio),math.ceil((best.get('cost',0)+210)/.99) if h>=36 else 220)
 others=[u for u in found[1:] if u.get('sku')!=best.get('sku')][:2]
 if max((score(x,chosen) for x in products),default=0)>=rank(best,chosen)+4: return {'reply':'찾으시는 상품은 지금 재고가 없습니다. 지금 있는 상품입니다.\n현재 안내 가능한 상품입니다.','state':'input_required'}
 settles=[e.get('data',{}) for e in entries if e.get('kind')=='settle']
 first=bool(who) and not any(d.get('buyer')==who and d.get('shop') in urls for d in settles)
 ref=next((d.get('buyer') for d in settles if d.get('shop') in urls and d.get('buyer') and d.get('buyer')!=who and d.get('buyer') in text),None)
 today=datetime.datetime.fromtimestamp(now+9*3600,datetime.timezone.utc).date().isoformat(); opening=first and '2026-11-25'<=today<='2026-11-27'
 disc=min(.25,(.10 if opening or ref else 0)+(.03*min(3,sum(1 for h0 in hist if any(x in str(h0).lower() for x in ('비싸','깎아','할인해')))+sum(text.count(x) for x in ('비싸','깎아','할인해')))))
 final=max(220,math.ceil(price*(1-disc))); reason='첫 구매 오픈 할인' if opening else ('추천 할인' if ref else ('흥정 할인' if disc else ''))
 stamp=int(now); offerfile='offers.json'; offers={}
 try: offers=json.load(open(offerfile,encoding='utf-8'))
 except: pass
 reserved=offers.get(best.get('unit'),[0,''])
 if stamp-reserved[0]<600 and reserved[1]!=who and others: best=others.pop(0)
 offers[best.get('unit')]=[stamp,who]; json.dump(offers,open(offerfile,'w',encoding='utf-8'),ensure_ascii=False)
 payload={'id':secrets.token_hex(3),'shop':kit.name,'shop_url':kit.shop_url,'item':best.get('sku'),'price':final,'task':secrets.token_hex(4),'currency':'credits','iat':stamp,'unit':best.get('unit'),'claim':best.get('grade')}
 jwt=kit.sign_jwt(payload,'shop'); reply=f"{p.get('name','')} / 등급 {best.get('grade')} / 남은 기한 {int(h)}시간 / 최종 가격 {final}크레딧"+(f' ({reason})' if reason else '')+'\n결제는 buy에서 이 가게 이름만 지정해 주세요. 토큰을 손으로 옮겨 적으면 서명이 깨질 수 있어요. 가게 지갑: '+kit.address('shop')
 for u in others:
  q=skuinfo.get(u.get('sku'),{}); reply+=f"\n함께 찾은 상품: {q.get('name','')} / 등급 {u.get('grade')} / 남은 기한 {int((float(u['expires_at'])-now)/3600)}시간 / {final}크레딧"
 reply+='\n결제서가 발급되었습니다.'
 if not kit.testing:
  with open('inquiries.jsonl','a',encoding='utf-8') as f: f.write(json.dumps({'time':stamp,'claimed_from':who,'text':text,'reply':reply},ensure_ascii=False)+'\n')
 return {'reply':reply,'data':{'checkout_jwt':jwt},'state':'input_required'}
