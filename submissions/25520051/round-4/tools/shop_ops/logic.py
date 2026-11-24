import json,httpx,time

def read():
 try:
  with open('ledger.json',encoding='utf-8') as f:return json.load(f)
 except:return {'members':{},'transactions':[]}
def write(x):
 with open('ledger.json','w',encoding='utf-8') as f:json.dump(x,f,ensure_ascii=False,indent=2)
def run(a,k):
 op=a.get('op'); db=read()
 if op=='ledger_read': return db
 if op=='ledger_write':
  if a.get('member'): db['members'][a['member']]=a.get('record',{})
  else: db['transactions'].append(a.get('record',{}))
  write(db); return {'ok':True,'ledger':db}
 h={'authorization':'Bearer '+k.token('shop'),'content-type':'application/json'}
 try:
  if op=='inventory': r=httpx.get(k.market+'/api/inventory',headers=h,timeout=20)
  elif op=='catalog': r=httpx.get(k.market+'/api/catalog',headers=h,timeout=20)
  elif op=='ledger_verify':
   paths=['/api/ledger','/api/settlements','/api/public-ledger']
   for p in paths:
    q=httpx.get(k.market+p,headers=h,timeout=15)
    if q.status_code<400:
     return {'status':q.status_code,'result':q.json()}
   return {'status':404,'result':{'error':'ledger endpoint unavailable'}}
  elif op=='supply_quote':
   if int(a.get('qty',0))<1:return {'error':'qty must be positive'}
   r=httpx.post(k.market+'/api/supply',headers=h,json={'sku':a['sku'],'qty':int(a['qty'])},timeout=30)
  elif op=='supply_buy':
   wei=int(a['wei'])
   if wei<=0 or wei>200000:return {'error':'단일 매입 한도는 200000 이하입니다'}
   if not a.get('to') or not a.get('data') or not a.get('quote'):return {'error':'quote,to,wei,data required'}
   tx=k.pay(a['to'],wei,a['data'],role='shop')
   r=httpx.post(k.market+'/api/supply',headers=h,json={'quote':a['quote'],'tx_hash':tx},timeout=60)
   result=r.json()
   if r.status_code<300 and result.get('received',result.get('accepted',True)):
    db['transactions'].append({'type':'supply','sku':a['quote'].get('sku',a.get('sku')),'qty':a['quote'].get('qty',a.get('qty')),'wei':wei,'tx_hash':tx,'receipt':result,'time':int(time.time())});write(db)
   return {'status':r.status_code,'tx_hash':tx,'result':result}
  else:return {'error':'unknown op'}
  try:x=r.json()
  except:x={'text':r.text}
  return {'status':r.status_code,'result':x}
 except Exception as e:return {'error':str(e)}
