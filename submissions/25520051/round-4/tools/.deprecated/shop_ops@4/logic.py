import json,httpx,time
def run(a,k):
 try:
  with open('ledger.json',encoding='utf-8') as f:d=json.load(f)
 except:d={'members':{},'transactions':[]}
 op=a.get('op')
 if op=='ledger_read':return d
 if op=='ledger_write':
  if a.get('member'):d['members'][a['member']]=a.get('record',{})
  else:d['transactions'].append(a.get('record',{}))
  with open('ledger.json','w',encoding='utf-8') as f:json.dump(d,f,ensure_ascii=False)
  return {'ok':True,'ledger':d}
 h={'authorization':'Bearer '+k.token('shop'),'content-type':'application/json'}
 if op=='inventory':r=httpx.get(k.market+'/api/inventory',headers=h,timeout=20)
 elif op=='catalog':r=httpx.get(k.market+'/api/catalog',headers=h,timeout=20)
 elif op=='supply_quote':r=httpx.post(k.market+'/api/supply',headers=h,json={'sku':a['sku'],'qty':int(a['qty'])},timeout=30)
 elif op=='supply_buy':
  q=a.get('quote',{}); total=int(q.get('total',0))
  if total>200000:return {'error':'단일 매입 한도는 200000크레딧 이하입니다'}
  tx=k.pay(a['to'],int(a['wei']),a['data'],role='shop')
  r=httpx.post(k.market+'/api/supply',headers=h,json={'quote':q.get('quote',q),'tx_hash':tx},timeout=60)
  return {'status':r.status_code,'tx_hash':tx,'result':r.json()}
 elif op=='ledger_verify':r=httpx.get(k.market+'/api/ledger',headers=h,timeout=20)
 else:return {'error':'unknown op'}
 return {'status':r.status_code,'result':r.json()}