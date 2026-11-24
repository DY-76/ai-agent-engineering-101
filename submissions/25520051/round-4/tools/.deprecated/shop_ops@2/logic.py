import json,httpx
def run(a,k):
 o=a.get('op')
 if o=='ledger_read':
  try:return json.load(open('ledger.json',encoding='utf8'))
  except:return {'members':{},'transactions':[]}
 if o=='ledger_write':
  try:d=json.load(open('ledger.json',encoding='utf8'))
  except:d={'members':{},'transactions':[]}
  if a.get('member'):d['members'][a['member']]=a.get('record',{})
  else:d['transactions'].append(a.get('record',{}))
  json.dump(d,open('ledger.json','w',encoding='utf8'),ensure_ascii=False);return {'ok':True,'ledger':d}
 h={'authorization':'Bearer '+k.token('shop'),'content-type':'application/json'}
 if o=='inventory':r=httpx.get(k.market+'/api/inventory',headers=h,timeout=30)
 elif o=='catalog':r=httpx.get(k.market+'/api/catalog',headers=h,timeout=30)
 elif o=='supply_quote':r=httpx.post(k.market+'/api/supply',headers=h,json={'sku':a['sku'],'qty':a['qty']},timeout=30)
 elif o=='supply_pay':
  tx=k.pay(a['to'],int(a['wei']),a['data'],role='shop');r=httpx.post(k.market+'/api/supply',headers=h,json={'quote':a['quote'],'tx_hash':tx},timeout=30)
 else:return {'error':'unknown op'}
 try:x=r.json()
 except:x={'text':r.text}
 return {'status':r.status_code,'result':x}