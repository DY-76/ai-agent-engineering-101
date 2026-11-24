import json,httpx,time
def load():
 try:
  with open('ledger.json',encoding='utf-8') as f:return json.load(f)
 except:return {'members':{},'transactions':[]}
def save(x):
 with open('ledger.json','w',encoding='utf-8') as f:json.dump(x,f,ensure_ascii=False,indent=2)
def run(a,k):
 d=load(); op=a.get('op'); h={'authorization':'Bearer '+k.token('shop'),'content-type':'application/json'}
 if op=='ledger_read': return d
 if op=='ledger_write':
  if a.get('member'): d['members'][a['member']]=a.get('record',{})
  else: d['transactions'].append(a.get('record',{}))
  save(d); return {'ok':True,'ledger':d}
 if op in ('inventory','catalog'):
  r=httpx.get(k.market+('/api/inventory' if op=='inventory' else '/api/catalog'),headers=h,timeout=25); return {'status':r.status_code,'result':r.json()}
 if op=='ledger_verify':
  r=httpx.get(k.market+'/api/ledger?after=-500',headers=h,timeout=25); return {'status':r.status_code,'result':r.json()}
 if op=='supply_batch':
  total=0; out=[]
  for it in a.get('items',[]):
   try:
    r=httpx.post(k.market+'/api/supply',headers=h,json={'sku':it['sku'],'qty':int(it['qty'])},timeout=25); q=r.json(); cost=int(q.get('total',0)); p=q.get('pay',{})
    if r.status_code>=400 or not p or total+cost>200000: out.append({'sku':it['sku'],'status':'skipped','quote':q}); continue
    tx=k.pay(p['to'],int(p['wei']),p['data'],role='shop'); s=httpx.post(k.market+'/api/supply',headers=h,json={'quote':q.get('quote'),'tx_hash':tx},timeout=45); z=s.json(); total+=cost
    out.append({'sku':it['sku'],'qty':it['qty'],'cost':cost,'status':s.status_code,'tx_hash':tx,'result':z}); d['transactions'].append({'type':'supply','sku':it['sku'],'qty':it['qty'],'cost':cost,'quote':q.get('quote'),'tx_hash':tx,'time':int(time.time())})
   except Exception as e: out.append({'sku':it.get('sku'),'status':'error','error':str(e)})
  save(d); return {'total':total,'results':out}
 return {'error':'unknown op'}