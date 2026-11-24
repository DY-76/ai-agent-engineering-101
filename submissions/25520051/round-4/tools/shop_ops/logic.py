import json,httpx,time

def load():
 try:
  with open('ledger.json',encoding='utf-8') as f:return json.load(f)
 except:return {'members':{},'transactions':[],'pending_supply':[]}

def save(x):
 with open('ledger.json','w',encoding='utf-8') as f:json.dump(x,f,ensure_ascii=False,indent=2)

def run(a,k):
 d=load(); d.setdefault('members',{}); d.setdefault('transactions',[]); d.setdefault('pending_supply',[])
 op=a.get('op'); h={'authorization':'Bearer '+k.token('shop'),'content-type':'application/json'}
 if op=='ledger_read': return d
 if op=='ledger_write':
  if a.get('member'): d['members'][a['member']]=a.get('record',{})
  else:d['transactions'].append(a.get('record',{}))
  save(d); return {'ok':True,'ledger':d}
 if op in ('inventory','catalog'):
  r=httpx.get(k.market+('/api/inventory' if op=='inventory' else '/api/catalog'),headers=h,timeout=25); return {'status':r.status_code,'result':r.json()}
 if op=='ledger_verify':
  r=httpx.get(k.market+'/api/ledger?after=-500',headers=h,timeout=25); return {'status':r.status_code,'result':r.json()}
 if op!='supply_batch': return {'error':'unknown op'}
 start=time.monotonic(); total=0; out=[]
 def post(payload):
  nonlocal start
  while time.monotonic()-start<175:
   r=httpx.post(k.market+'/api/supply',headers=h,json=payload,timeout=25)
   if r.status_code!=429:return r
   try:w=float(r.json().get('wait',r.headers.get('retry-after',1)))
   except:w=1
   time.sleep(max(0.1,min(w,175-(time.monotonic()-start))))
  return None
 # Previously paid but not received: claim first, without paying again.
 for p in list(d['pending_supply']):
  if time.monotonic()-start>=175:break
  r=post({'quote':p['quote'],'tx_hash':p['tx_hash']})
  if r is not None:
   try:z=r.json()
   except:z={'text':r.text}
   if r.status_code<400:
    d['pending_supply'].remove(p); d['transactions'].append(p|{'received':True,'time':int(time.time())}); save(d)
   out.append({'sku':p.get('sku'),'status':r.status_code,'result':z,'pending':True})
 for it in a.get('items',[]):
  if time.monotonic()-start>=175:break
  sku=it.get('sku'); qty=int(it.get('qty',0))
  r=post({'sku':sku,'qty':qty})
  if r is None: break
  try:q=r.json()
  except:q={}
  pay=q.get('pay',{}); cost=int(q.get('total',0) or 0)
  if r.status_code>=400 or not pay or total+cost>200000:
   out.append({'sku':sku,'status':'skipped','quote':q}); continue
  tx=k.pay(pay['to'],int(pay['wei']),pay['data'],role='shop')
  p={'type':'supply','sku':sku,'qty':qty,'cost':cost,'quote':q.get('quote'),'tx_hash':tx}
  d['pending_supply'].append(p); save(d) # persist before attempting receipt
  s=post({'quote':q.get('quote'),'tx_hash':tx})
  if s is None: out.append({'sku':sku,'status':'pending','tx_hash':tx}); continue
  try:z=s.json()
  except:z={'text':s.text}
  total+=cost
  if s.status_code<400:
   d['pending_supply']=[x for x in d['pending_supply'] if x is not p]; d['transactions'].append(p|{'received':True,'time':int(time.time())}); save(d)
  out.append({'sku':sku,'qty':qty,'cost':cost,'status':s.status_code,'tx_hash':tx,'result':z})
 save(d); return {'total':total,'results':out,'pending':len(d['pending_supply'])}