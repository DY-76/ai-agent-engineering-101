import time,json,re,httpx
STOP=set('재고 가격 등급 실제 남은 기한 상품 서명 결제 확인 게시글 게시판 포럼 오늘 국내산 제철 신선 식품 판매 안내 현재 모듬 소비기한 실재고 checkout'.split())
def log_inquiry(args,reply):
 rec={'time':time.time(),'claimed_from':args.get('claimed_from'),'text':args.get('text',''),'reply':reply}
 with open('inquiries.jsonl','a',encoding='utf-8') as f:f.write(json.dumps(rec,ensure_ascii=False,separators=(',',':'))+'\n')
def run(args,kit):
 text=args.get('text','')
 skus=re.findall(r'G[0-9a-f]{8}',text)
 if skus:
  try:
   r=httpx.get(kit.market+'/api/inventory',headers={'authorization':'Bearer '+kit.token('shop')},timeout=20)
   inv=r.json() if r.status_code<400 else {}; units=inv.get('units',[]) if isinstance(inv,dict) else []
   have={str(u.get('sku')) for u in units if isinstance(u,dict)}
   if not any(s in have for s in skus):
    reply='문의하신 상품은 지금 재고가 없습니다.'
    if not kit.testing: log_inquiry(args,reply)
    return {'reply':reply,'state':'input_required'}
  except Exception: pass
 p='tools/.deprecated/customer_service@8/logic.py'
 with open(p,encoding='utf-8') as f: src=f.read()
 assert "if len(w)>1 and w not in words: words.append(w)" in src
 assert "if score: name_matches.append" in src
 src=src.replace("'cert':u['cert'],",'')
 src=src.replace("name=str(p[1].get('name','')).lower()","name=str(p[1].get('name','')).lower().replace(' ','')")
 src=src.replace("float(c.get('expires_at',0))","float(u.get('expires_at') or 99999999)")
 src=src.replace("c.get('expires_at',0)","u.get('expires_at')")
 src=src.replace("if len(w)>1 and w not in words: words.append(w)","if len(w)>1 and not re.search(r'[0-9]',w) and w not in STOP and w not in words: words.append(w)")
 src=src.replace("if score: name_matches.append","if score and not ('8팩' in name and '8팩' not in text): name_matches.append")
 ns={'__file__':p,'__name__':'deprecated_customer_service','kit':kit,'time':time,'STOP':STOP,'re':re}
 exec(compile(src,p,'exec'),ns)
 out=ns['run'](args,kit)
 if isinstance(out,dict) and isinstance(out.get('reply'),str):
  out['reply']=out['reply'].replace('\\n','\n')
  if out.get('data',{}).get('checkout_jwt'): out['reply']+=' 결제 토큰은 고치지 말고 그대로 사용해 주세요.'
  if not kit.testing: log_inquiry(args,out['reply'])
 return out
