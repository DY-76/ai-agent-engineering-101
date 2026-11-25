import json,time,httpx

def run(a,k):
 h={'authorization':'Bearer '+k.token('shop'),'content-type':'application/json'}; total=0; out=[]; start=time.monotonic()
 for it in a.get('items',[]):
  if time.monotonic()-start>170: break
  sku=it['sku']; qty=int(it.get('qty',1))
  while True:
   r=httpx.post(k.market+'/api/supply',headers=h,json={'sku':sku,'qty':qty},timeout=25)
   if r.status_code!=429: break
   try:w=float(r.json().get('wait',1))
   except:w=1
   time.sleep(min(w,170-(time.monotonic()-start)))
  try:q=r.json()
  except:q={}
  pay=q.get('pay',{}); cost=int(q.get('total',0) or 0)
  if not pay or not q.get('quote') or total+cost>200000:
   out.append({'sku':sku,'status':'skipped','http_status':r.status_code,'quote':q}); continue
  tx=k.pay(pay['to'],int(pay['wei']),pay['data'],role='shop'); total+=cost
  while True:
   s=httpx.post(k.market+'/api/supply',headers=h,json={'quote':q['quote'],'tx_hash':tx},timeout=25)
   if s.status_code!=429: break
   try:w=float(s.json().get('wait',1))
   except:w=1
   time.sleep(min(w,170-(time.monotonic()-start)))
  try:z=s.json()
  except:z={'text':s.text}
  out.append({'sku':sku,'qty':qty,'cost':cost,'status':s.status_code,'tx_hash':tx,'result':z})
 return {'total':total,'results':out}
