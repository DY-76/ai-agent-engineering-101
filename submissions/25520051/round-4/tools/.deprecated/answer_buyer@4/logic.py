import os,json,re,time,httpx

def run(args,kit):
 base=kit.market.rstrip('/'); headers={'authorization':'Bearer '+kit.token('shop')}
 root=os.path.dirname(__file__); path=os.path.normpath(os.path.join(root,'..','replied.json'))
 try:
  with open(path,encoding='utf-8') as f: done=set(map(str,json.load(f)))
 except: done=set()
 r=httpx.get(base+'/api/forum',params={'role':'buyer','limit':100},headers=headers,timeout=25); r.raise_for_status(); d=r.json(); posts=d if isinstance(d,list) else d.get('posts',d.get('items',[]))
 posts=sorted(posts,key=lambda x:float(x.get('ts',0) or 0),reverse=True); now=time.time()
 posts=[p for p in posts if 0 <= now-float(p.get('ts',0) or 0)<=1500 and str(p.get('id')) not in done]
 src=os.path.normpath(os.path.join(root,'..','customer_service','logic.py')); ns={}; exec(compile(open(src,encoding='utf-8').read(),src,'exec'),ns)
 service=ns['run']({'text':'뭐 있어요?','claimed_from':'가격확인'},kit); inventory=[]
 for line in service.get('reply','').splitlines():
  parts=line.rsplit(' / ',4)
  if len(parts)!=5: continue
  name,qty,grade,remaining,price=parts; grade=grade.strip().replace('등급 ','')
  if grade not in ('A','B') or '8팩' in name or '김수미' in name: continue
  m=re.search(r'([0-9]+(?:\.[0-9]+)?)',remaining)
  if not m or float(m.group(1))<8: continue
  inventory.append((name.strip(),grade,m.group(1),price.strip()))
 cr=httpx.get(base+'/api/catalog',headers=headers,timeout=20); cr.raise_for_status(); d=cr.json(); cat=d if isinstance(d,list) else d.get('items',d.get('catalog',[])); byname={x.get('name',''):x.get('sku','') for x in cat}
 ignored=set('국내산 제철과일 정식수입 당일수확 인증 모듬 상등급 햅쌀 프리미엄 신선 무농약 상온보관 가정용 소포장 단백질 식단관리 Fresh 한끼해줘'.split())
 triggers=('없다','못 샀','못했','찾았지만','찾던','입고가 안','입고되지','재고가 없','구매하지 않','구매는 못','안 샀','없었')
 bought=('실제로 샀','샀어요','구매했어요','결제했어요')
 for p in posts:
  text=str(p.get('text',p.get('content',''))); sentences=[s.strip() for s in re.split(r'[!?\n]+|\.(?!\d)|요\.|다\.',text) if s.strip()]
  for sentence in sentences:
   if not any(w in sentence for w in triggers) or any(w in sentence for w in ('대신','대안','권했','권하')): continue
   best=None
   for name,grade,hours,price in inventory:
    words=[w for w in re.split(r'[\s\W_]+',name) if len(w)>=2 and not any(c.isdigit() for c in w) and w not in ignored]
    score=sum(len(w) for w in words if w in sentence)
    if score<5 or (any(w in sentence for w in bought) and any(w in sentence for w in words)): continue
    if best is None or score>best[0]: best=(score,name,grade,hours,price)
   if not best: continue
   _,name,grade,hours,price=best; sku=byname.get(name,'')
   if not sku: continue
   author=str(p.get('author_name',p.get('name',p.get('author','손님')))).split('-')[0].strip() or '손님'
   clean_price=re.sub(r'\s*\(크레딧\)','',price); price_text=clean_price if '크레딧' in clean_price else clean_price+'크레딧'
   msg=f'{author}님, 찾으시던 {name[:28]}을(를) 로얄 서클에 준비했습니다: 등급 {grade}, 남은 {hours}시간, {price_text} ({sku}). 첫 구매·회원 10% 할인. buy에 로얄 서클(Royal Circle)이라고 하시면 됩니다.'
   result={'id':p.get('id'),'sentence':sentence,'text':msg,'sku':sku}
   if kit.testing: return result
   pr=httpx.post(base+'/api/forum',json={'text':msg,'thread':p.get('id'),'refs':[]},headers=headers,timeout=30)
   if pr.status_code==429:
    try: wait=pr.json().get('wait',30)
    except: wait=30
    return {'wait':wait,'id':p.get('id'),'sentence':sentence}
   pr.raise_for_status(); done.add(str(p.get('id')))
   with open(path,'w',encoding='utf-8') as f: json.dump(list(done)[-200:],f,ensure_ascii=False)
   return {'replied':p.get('id'),'sentence':sentence,'text':msg}
 return {'none':True}
