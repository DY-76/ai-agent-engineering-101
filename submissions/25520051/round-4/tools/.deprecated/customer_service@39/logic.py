import os,re,httpx

def run(args,kit):
 path='tools/.deprecated/customer_service@38/logic.py'
 if not os.path.exists(path): path='tools/customer_service/logic.py'
 ns={}
 exec(compile(open(path,encoding='utf-8').read(),path,'exec'),ns)
 a=dict(args); text=str(a.get('text',''))
 m=re.search(r'G[0-9a-fA-F]{8}',text)
 if m:
  r=httpx.get(kit.market+'/api/catalog',headers={'authorization':'Bearer '+kit.token('shop')},timeout=20); r.raise_for_status(); data=r.json(); items=data if isinstance(data,list) else data.get('items',data.get('catalog',[]))
  p=next((x for x in items if x.get('sku','').lower()==m.group().lower()),None)
  if p: text=text.replace(m.group(),p.get('name',m.group()))
 if 'B등급' in text and 'C등급' not in text and 'B등급 이상' not in text: text+=' C등급 제외'
 a['text']=text
 h=a.get('history') or []; h=h.get('messages',[]) if isinstance(h,dict) else h
 a['history']=[{'them':x['them']} for x in h if isinstance(x,dict) and isinstance(x.get('them'),str)]
 return ns['run'](a,kit)
