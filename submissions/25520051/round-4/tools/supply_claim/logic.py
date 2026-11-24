import json,time,httpx
def run(a,k):
 try:
  tx=k.pay(a['to'],int(a['wei']),a['data'],role='shop')
  h={'authorization':'Bearer '+k.token('shop'),'content-type':'application/json'}
  r=httpx.post(k.market+'/api/supply',headers=h,json={'quote':a['quote'],'tx_hash':tx},timeout=45)
  z=r.json()
  try:
   with open('ledger.json',encoding='utf-8') as f:d=json.load(f)
  except:d={'members':{},'transactions':[]}
  d.setdefault('transactions',[]).append({'type':'supply','sku':a.get('sku'),'qty':a.get('qty',1),'quote':a['quote'],'tx_hash':tx,'time':int(time.time())})
  with open('ledger.json','w',encoding='utf-8') as f:json.dump(d,f,ensure_ascii=False,indent=2)
  return {'status':r.status_code,'tx_hash':tx,'result':z}
 except Exception as e:return {'error':str(e)}
