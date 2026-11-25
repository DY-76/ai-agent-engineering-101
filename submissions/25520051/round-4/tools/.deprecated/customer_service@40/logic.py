import os,re,json,time,httpx

def run(args,kit):
 path='tools/.deprecated/customer_service@38/logic.py'
 if not os.path.exists(path): path='tools/customer_service/logic.py'
 ns={}; exec(compile(open(path,encoding='utf-8').read(),path,'exec'),ns)
 a=dict(args); text=str(a.get('text','')); m=re.search(r'G[0-9a-fA-F]{8}',text)
 if m:
  headers={'authorization':'Bearer '+kit.token('shop')}; c=httpx.get(kit.market+'/api/catalog',headers=headers,timeout=20); c.raise_for_status(); d=c.json(); items=d if isinstance(d,list) else d.get('items',d.get('catalog',[])); sku=m.group().lower(); p=next((x for x in items if x.get('sku','').lower()==sku),None)
  if p:
   r=httpx.get(kit.market+'/api/inventory',headers=headers,timeout=20); r.raise_for_status(); q=r.json(); units=q.get('units',[]) if isinstance(q,dict) else []; 
   if not any(x.get('sku','').lower()==sku for x in units):
    b=dict(a,text='뭐 있어요?',history=[]); out=ns['run'](b,kit); reply='찾으시는 '+p.get('name',m.group())+'은(는) 지금 재고가 없습니다.\n'+out.get('reply','')
    if not kit.testing:
     with open('inquiries.jsonl','a',encoding='utf-8') as f: f.write(json.dumps({'time':time.time(),'claimed_from':a.get('claimed_from'),'text':text,'reply':reply},ensure_ascii=False)+'\n')
    return {'reply':reply,'state':out.get('state','input_required')}
  if 'B등급' in text and 'C등급' not in text and 'B등급 이상' not in text: text+=' C등급 제외'
 a['text']=text; h=a.get('history') or []; h=h.get('messages',[]) if isinstance(h,dict) else h; a['history']=[{'them':x['them']} for x in h if isinstance(x,dict) and isinstance(x.get('them'),str)]
 return ns['run'](a,kit)
