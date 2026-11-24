import json,re,time,httpx

def load():
 try:
  with open('ledger.json',encoding='utf-8') as f:return json.load(f)
 except:return {'members':{},'transactions':[]}
def save(db):
 with open('ledger.json','w',encoding='utf-8') as f:json.dump(db,f,ensure_ascii=False,indent=2)
def run(a,kit):
 text=(a.get('text') or '').strip(); db=load()
 mm=re.search(r'(?:회원명|회원|이름)\s*[:：]?\s*([가-힣A-Za-z0-9_-]{2,30})',text)
 name=mm.group(1) if mm else None
 if name:
  db['members'].setdefault(name,{'name':name,'purchases':[],'referrals':0,'discount_pending':0,'grade':1,'tickets':0})
  db['transactions'].append({'type':'inquiry','member':name,'text':text,'time':int(time.time())});save(db)
 h={'authorization':'Bearer '+kit.token('shop')}
 try:
  cat=httpx.get(kit.market+'/api/catalog',headers=h,timeout=8).json(); inv=httpx.get(kit.market+'/api/inventory',headers=h,timeout=8).json()
 except:return {'reply':'죄송합니다. 현재 상품 정보를 확인할 수 없습니다.','state':'input_required'}
 items=cat.get('items',cat.get('catalog',[])) if isinstance(cat,dict) else cat; units=inv.get('units',inv.get('items',[])) if isinstance(inv,dict) else inv
 words=[w for w in re.findall(r'[\w가-힣-]+',text) if len(w)>1]; found=[]
 for it in items or []:
  if any(w.lower() in str(it).lower() for w in words):
   sku=it.get('sku'); us=[u for u in units or [] if u.get('sku')==sku];
   if us: found.append((it,us[0]))
 buy=any(w in text for w in ['구매','주문','결제','살게','구입'])
 if not found:return {'reply':'문의하신 상품은 현재 재고가 없습니다. 상품명이나 SKU를 알려주시면 다른 상품도 안내해 드리겠습니다.','state':'input_required'}
 if buy:
  it,u=found[0]; base=int(it.get('list_price',it.get('price',0))); discount=0
  if name:
   mem=db['members'][name]; discount=min(50,10+5*(int(mem.get('discount_pending',0))//10)) if mem.get('discount_pending',0) else 0
   price=max(1,base*(100-discount)//100)
  else: price=base
  payload={'id':'rc-'+str(int(time.time()*1000)),'shop':kit.name,'shop_url':kit.shop_url,'item':it.get('sku'),'price':price,'task':a.get('task_id') or 'rc-'+str(time.time_ns()),'currency':'credits','iat':int(time.time()),'unit':u.get('unit'),'cert':u.get('cert')}
  jwt=kit.sign_jwt(payload,'shop')
  if name: db['transactions'].append({'type':'checkout','member':name,'sku':it.get('sku'),'price':price,'discount':discount,'unit':u.get('unit'),'time':int(time.time())});save(db)
  return {'reply':f"{it.get('name',it.get('sku'))} {price}크레딧({discount}% 할인) 결제 정보를 준비했습니다.",'data':{'checkout_jwt':jwt},'state':'completed'}
 return {'reply':f"{found[0][0].get('name',found[0][0].get('sku'))} / {found[0][0].get('sku')} / 가격 {found[0][0].get('list_price',found[0][0].get('price'))}크레딧 / 재고 {len([u for u in units if u.get('sku')==found[0][0].get('sku')])}개",'state':'input_required'}
