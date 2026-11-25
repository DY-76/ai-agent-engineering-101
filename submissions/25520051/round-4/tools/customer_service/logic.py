import os,re,json,time,httpx

def run(args,kit):
 path='tools/.deprecated/customer_service@38/logic.py'
 if not os.path.exists(path): path='tools/customer_service/logic.py'
 src=open(path,encoding='utf-8').read()
 prior="prior=any(e.get('kind')=='settle' and e.get('data',{}).get('buyer')==who and e.get('data',{}).get('shop_url') in urls for e in es)"
 referral="referral=any(e.get('kind')=='settle' and e.get('data',{}).get('buyer')==w and e.get('data',{}).get('shop_url') in urls for w in pick(text) if w!=who)"
 assert prior in src, 'prior pattern missing'
 assert referral in src, 'referral pattern missing'
 src=src.replace(prior,'prior=who in BUYERS',1)
 src=src.replace(referral,"referral=any(b!=who and (b in text or (len(b.split('-')[0])>=3 and b.split('-')[0] in text)) for b in BUYERS)",1)
 old1='(10 if first and not prior else 0)'
 new1='(10 if (first and not prior) or prior else 0)'
 old2="reason='할인 없음' if not discount else f'할인 {discount}% (첫 구매/추천/흥정 적용)'"
 new2='reason=\'할인 없음\' if not discount else f\'할인 {discount}% ({"회원 재구매" if prior else "첫 구매"}/추천/흥정)\''
 assert old1 in src, 'discount pattern missing'
 assert old2 in src, 'reason pattern missing'
 src=src.replace(old1,new1,1).replace(old2,new2,1)
 old3='and pick(s): chosen=pick(s); break'
 new3='and eligible(pick(s)): chosen=pick(s); break'
 old4='f=eligible(chosen); best=f[0] if f else None'
 new4='f=eligible(chosen) or eligible(words); best=f[0] if f else None'
 assert old3 in src, 'pick pattern missing'
 assert old4 in src, 'eligible pattern missing'
 src=src.replace(old3,new3,1).replace(old4,new4,1)
 old_ratio="ratio={'A':.70,'B':.60,'C':.46}.get(u.get('grade'),.46)"
 new_ratio="ratio={'A':.80,'B':.68,'C':.50}.get(u.get('grade'),.50)"
 old_sort="return sorted(f,key=lambda u:(-score(by.get(u.get('sku'),{}),ws),float(u.get('expires_at') or now+9999*3600)))"
 new_sort="return sorted(f,key=lambda u:(-score(by.get(u.get('sku'),{}),ws),u.get('grade')=='C',float(u.get('expires_at') or now+9999*3600)<now+12*3600,float(u.get('expires_at') or now+9999*3600)))"
 assert old_ratio in src, 'price ratio pattern missing'
 assert old_sort in src, 'sorting pattern missing'
 src=src.replace(old_ratio,new_ratio,1).replace(old_sort,new_sort,1)
 buyers=set(); state={'seq':0,'urls':[],'buyers':[]}
 try:
  if os.path.exists('buyers.json'):
   old=json.load(open('buyers.json',encoding='utf-8')); state=old if isinstance(old,dict) else state
  buyers=set(state.get('buyers',[])); urls=set(state.get('urls',[])); seq=int(state.get('seq',0))
  headers={'authorization':'Bearer '+kit.token('shop')}; cursor=seq
  for _ in range(100):
   r=httpx.get(kit.market+'/api/ledger',headers=headers,params={'after':cursor},timeout=20); r.raise_for_status(); d=r.json(); es=d if isinstance(d,list) else d.get('entries',d.get('ledger',[]))
   if not es: break
   for e in es:
    n=int(e.get('seq',e.get('id',cursor)) or cursor); cursor=max(cursor,n); data=e.get('data',{}) or {}
    if e.get('kind')=='join' and data.get('name')==kit.name and data.get('url'): urls.add(data['url'])
    if e.get('kind')=='settle' and data.get('shop') in (urls|{kit.shop_url}) and data.get('buyer'): buyers.add(data['buyer'])
   if len(es)<500 or cursor<=seq: break
   seq=cursor
  seq=cursor
  if not kit.testing:
   with open('buyers.json','w',encoding='utf-8') as f: json.dump({'seq':seq,'urls':sorted(urls),'buyers':sorted(buyers)},f,ensure_ascii=False)
 except Exception: pass
 ns={'BUYERS':buyers}; exec(compile(src,path,'exec'),ns)
 a=dict(args); text=str(a.get('text','')); m=re.search(r'G[0-9a-fA-F]{8}',text)
 if m:
  headers={'authorization':'Bearer '+kit.token('shop')}; c=httpx.get(kit.market+'/api/catalog',headers=headers,timeout=20); c.raise_for_status(); d=c.json(); items=d if isinstance(d,list) else d.get('items',d.get('catalog',[])); sku=m.group().lower(); p=next((x for x in items if x.get('sku','').lower()==sku),None)
  if p:
   r=httpx.get(kit.market+'/api/inventory',headers=headers,timeout=20); r.raise_for_status(); q=r.json(); units=q.get('units',[]) if isinstance(q,dict) else []
   if not any(x.get('sku','').lower()==sku for x in units):
    b=dict(a,text='뭐 있어요?',history=[]); out=ns['run'](b,kit); reply='찾으시는 '+p.get('name',m.group())+'은(는) 지금 재고가 없습니다.\n'+out.get('reply','')
    if not kit.testing:
     with open('inquiries.jsonl','a',encoding='utf-8') as f: f.write(json.dumps({'time':time.time(),'claimed_from':a.get('claimed_from'),'text':text,'reply':reply},ensure_ascii=False)+'\n')
    return {'reply':reply,'state':out.get('state','input_required')}
   text=text.replace(m.group(),p.get('name',m.group()))
 if 'B등급' in text and 'C등급' not in text and 'B등급 이상' not in text: text+=' C등급 제외'
 h=a.get('history') or []; h=h.get('messages',[]) if isinstance(h,dict) else h; a['text']=text; a['history']=[{'them':x['them']} for x in h if isinstance(x,dict) and isinstance(x.get('them'),str)]
 out=ns['run'](a,kit)
 if (out.get('data') or {}).get('checkout_jwt'):
  greeting='다시 찾아 주셔서 감사합니다. ' if a.get('claimed_from') in buyers else ''
  out['reply']=out.get('reply','')+'\n'+greeting+'회원이 되시면 다음 구매도 10% 할인, 이웃이 추천인으로 회원님 이름을 말하면 이웃도 10% 할인입니다. 또 찾아 주세요.'
 return out
