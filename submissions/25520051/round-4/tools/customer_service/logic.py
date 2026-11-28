import json,re,time,httpx
def run(args,kit):
 x=[y for y in re.split(r'(?<=[.!?\n])\s*',str(args.get('text',''))) if y and not re.search('안 ?사겠|안 ?살게|안 ?살래|구매하지 않|사지 않|많아서|많고|짧아 보|되어 있네|로 되어 있',y)];args=dict(args,text=' '.join(x)) if x and args.get('text') else args
 args=dict(args,text=re.sub('(?<![가-힣0-9A-Za-z])(?!쌀|귤|감|떡|빵|차|꿀|콩|밤|잼|안|못)[가-힣](?![가-힣])',' ',str(args.get('text','')))) if args.get('text') else args
 p='tools/.deprecated/customer_service@53/logic.py';s=open(p,encoding='utf-8').read();o="'포장 소포장 소량 재고 ";assert s.count(o)==1
 q='assert s.count(old) == 1';assert s.count(q)==1 and s.count('g = {')==1
 s=s.replace('    A = (',"    D = ('{price(u,p,h)}크레딧', '{max(math.ceil(price(u,p,h)*.9),price(u,dict(),h)) if who and chr(45) in who and (who in BUYERS or now<1795791600) else price(u,p,h)}크레딧')\n    A = (",1).replace("repr(A) + ','","repr(A) + ',' + repr(D) + ','",1)
 s=s.replace(q,q+";s=s.replace('assert M in src','src=src.replace(K,V,1);assert M in src',1)",1).replace('g = {',"g = {'K':'.80,'+chr(39)+'B'+chr(39)+':.68','V':'.76,'+chr(39)+'B'+chr(39)+':.62',",1)
 s=s.replace('src=src.replace(K,V,1);','src=src.replace(K,V,1).replace(K2,V2,1);',1).replace('g = {',"g = {'K2':'.replace(old_sort,new_sort,1)','V2':'.replace(old_sort,new_sort,1).replace('+chr(39)+'))+210)/.99'+chr(39)+','+chr(39)+'))*.8+210)/.99'+chr(39)+')',",1)
 s=s.replace(o,"'신선한 대용량 적당한 며칠 있는 지금 좋은 포장 소포장 소량 재고 ");g={};exec(compile(s,p,'exec'),g);r=g['run'](args,kit)
 t0=str(args.get('text',''));t1=str(args.get('text',''));n1=r.get('reply','').split(' / ')[0];r=g['run'](dict(args,text=re.sub('[0-9A-Za-z.]+',' ',t1)),kit) if (r.get('data') or {}).get('checkout_jwt') and not any(w in t1 for w in re.findall('[가-힣]{2,}',n1)) and not any(w in n1 for w in re.findall('[가-힣]{2,}',t1)) else r
 r=g['run'](dict(args,text=t0.replace('A등급만','').replace('A등급','')),kit) if 'A등급' in t0 and (r.get('data') or {}).get('checkout_jwt') and not any(w in t0 for w in re.findall('[가-힣]{2,}',r.get('reply','').split(' / ')[0])) else r
 if kit.testing and args.get('force_nostock'):r={'reply':'찾으시는 상품은 지금 재고가 없'}
 try:return fa(args,kit,g,ag(args,kit,g,r))
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
def fa(args,kit,g,r):
 import base64
 who=args.get('claimed_from');t=str(args.get('text',''));j=(r.get('data') or {}).get('checkout_jwt');now=time.time()
 if not who or not j or 'A등급' in t:return r
 p=j.split('.')[1];c=json.loads(base64.urlsafe_b64decode(p+'='*(-len(p)%4)))
 m=[k for k,v in json.load(open('offers.json',encoding='utf-8')).items() if v[1]==who and 30<now-v[0]<900 and k!=c.get('unit')]
 if c.get('claim')=='A' or not m:return r
 i=httpx.get(kit.market+'/api/inventory',headers={'authorization':'Bearer '+kit.token('shop')},timeout=20).json();i=i.get('units',[]) if isinstance(i,dict) else i
 if not any(x.get('unit') in m and x.get('sku')==c.get('item') and x.get('grade')=='A' for x in i):return r
 r2=g['run'](dict(args,text=t+' A등급만'),kit);return r2 if (r2.get('data') or {}).get('checkout_jwt') else r