import json,re,httpx

def dbread():
 try:
  with open('ledger.json',encoding='utf-8') as f:return json.load(f)
 except:return {'members':{},'transactions':[]}
def run(a,kit):
 text=(a.get('text') or '').strip(); db=dbread()
 m=re.search(r'(?:회원명|회원|이름)\s*[:：]?\s*([가-힣A-Za-z0-9_-]{2,30})',text)
 if m:
  name=m.group(1); db['members'].setdefault(name,{'name':name,'purchases':[],'referrals':0,'discount_pending':0,'grade':1,'tickets':0}); db['transactions'].append({'type':'inquiry','member':name,'text':text})
  with open('ledger.json','w',encoding='utf-8') as f: json.dump(db,f,ensure_ascii=False,indent=2)
 h={'authorization':'Bearer '+kit.token('shop'),'content-type':'application/json'}
 try:
  c=httpx.get(kit.market+'/api/catalog',headers=h,timeout=10).json(); inv=httpx.get(kit.market+'/api/inventory',headers=h,timeout=10).json()
 except:return {'reply':'죄송합니다. 현재 상품 정보를 확인할 수 없습니다. 잠시 후 다시 문의해 주세요.','state':'input_required'}
 items=c.get('items',c.get('catalog',[])) if isinstance(c,dict) else c; stocks=inv.get('items',inv.get('inventory',[])) if isinstance(inv,dict) else inv
 if isinstance(items,dict):items=list(items.values())
 if isinstance(stocks,dict):stocks=list(stocks.values())
 words=[x for x in re.findall(r'[\w가-힣-]+',text) if len(x)>1]; found=[]
 for it in items or []:
  if any(w.lower() in str(it).lower() for w in words):
   sku=it.get('sku'); st=next((x for x in stocks or [] if x.get('sku')==sku),{}); found.append((it,st))
 buy=any(x in text for x in ['구매','주문','결제','살게','구입'])
 if found and buy:
  it,st=found[0]; sku=it.get('sku'); qty=1; stock=st.get('qty',st.get('quantity',st.get('stock',0)))
  if not sku or not stock:return {'reply':'문의하신 상품은 현재 재고가 없습니다. 다른 상품을 안내해 드릴까요?','state':'input_required'}
  try:
   r=httpx.post(kit.shop_url.rstrip('/')+'/checkout_sessions',json={'line_items':[{'id':sku,'quantity':qty}],'receipt':{'shop':kit.shop_url,'item':sku,'price':it.get('price'),'task':a.get('task_id','')},'acceptable':[sku]},timeout=15).json(); jwt=r.get('checkout_jwt') or r.get('session',{}).get('checkout_jwt')
   if jwt:return {'reply':'구매 결제 정보를 준비했습니다. 구매자 주문에서 확인 후 결제해 주세요.','data':{'checkout_jwt':jwt},'state':'completed'}
  except:pass
  return {'reply':'상품은 확인했지만 결제 세션 생성에 실패했습니다. 잠시 후 다시 시도해 주세요.','state':'input_required'}
 if found:
  return {'reply':'\n'.join(f"{i.get('sku','상품')} / 가격 {i.get('price',i.get('sell_price','확인 필요'))}크레딧 / 재고 {s.get('qty',s.get('quantity',s.get('stock',0)))}개" for i,s in found[:5])+'\n구매를 원하시면 SKU와 수량을 알려 주세요.','state':'input_required'}
 return {'reply':'안녕하세요, 로얄 서클입니다. 상품명이나 SKU를 알려주시면 현재 재고와 가격을 확인해 드리겠습니다.','state':'input_required'}
