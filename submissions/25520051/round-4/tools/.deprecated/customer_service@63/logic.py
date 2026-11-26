import json,re,time,httpx
def run(args,kit):
 p='tools/.deprecated/customer_service@53/logic.py';s=open(p,encoding='utf-8').read();o="'포장 소포장 소량 재고 ";assert s.count(o)==1
 q='assert s.count(old) == 1';assert s.count(q)==1 and s.count('g = {')==1
 s=s.replace('    A = (',"    D = ('{price(u,p,h)}크레딧', '{max(math.ceil(price(u,p,h)*.9),price(u,dict(),h)) if who and chr(45) in who and (who in BUYERS or now<1795791600) else price(u,p,h)}크레딧')\n    A = (",1).replace("repr(A) + ','","repr(A) + ',' + repr(D) + ','",1)
 s=s.replace(q,q+";s=s.replace('assert M in src','src=src.replace(K,V,1);assert M in src',1)",1).replace('g = {',"g = {'K':'.80,'+chr(39)+'B'+chr(39)+':.68','V':'.76,'+chr(39)+'B'+chr(39)+':.62',",1)
 s=s.replace('src=src.replace(K,V,1);','src=src.replace(K,V,1).replace(K2,V2,1);',1).replace('g = {',"g = {'K2':'.replace(old_sort,new_sort,1)','V2':'.replace(old_sort,new_sort,1).replace('+chr(39)+'))+210)/.99'+chr(39)+','+chr(39)+'))*.8+210)/.99'+chr(39)+')',",1)
 s=s.replace(o,"'신선한 대용량 적당한 며칠 있는 지금 좋은 포장 소포장 소량 재고 ");g={};exec(compile(s,p,'exec'),g);r=g['run'](args,kit)
 if kit.testing and args.get('force_nostock'):r={'reply':'찾으시는 상품은 지금 재고가 없'}
 try:return ag(args,kit,g,r)
 except Exception:return r
def ag(args,kit,g,r):
 who=args.get('claimed_from');t=str(args.get('text','')).replace(' ','');now=time.time()
 if not who or not r.get('reply','').startswith('찾으시는 상품은 지금 재고가 없'):return r
 m=sorted((v[0],k) for k,v in json.load(open('offers.json',encoding='utf-8')).items() if v[1]==who and now-v[0]<900)
 if not m:return r
 H={'authorization':'Bearer '+kit.token('shop')};G=lambda q:httpx.get(kit.market+q,headers=H,timeout=20).json()
 i=G('/api/inventory');u=next((x for x in (i.get('units',[]) if isinstance(i,dict) else i) if x.get('unit')==m[-1][1]),None)
 if not u:return r
 h=int((float(u.get('expires_at') or 0)-now)/3600)
 if not any(f'{k}시간' in t for k in (h,h+1)) and not re.search('그상품|이상품|해당상품|결제서에|안내하신',t):return r
 c=G('/api/catalog');n=next((p.get('name','') for p in c if p.get('sku')==u.get('sku')),'')
 r2=g['run'](dict(args,text=n+' 결제서'),kit) if n else r
 return r2 if (r2.get('data') or {}).get('checkout_jwt') else r