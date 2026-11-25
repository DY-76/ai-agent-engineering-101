import os,re,httpx
def run(args,kit):
 p='tools/.deprecated/customer_service@29/logic.py'
 if not os.path.exists(p):p='tools/customer_service/logic.py'
 g={};exec(open(p,encoding='utf-8').read(),g)
 t=str(args.get('text',''));o=g['run'](dict(args,text=t),kit);d=o.get('data',{});r=str(o.get('reply',''))
 if not d.get('checkout_jwt'):return o
 stop=set('재고 가격 등급 실제 남은 기한 상품 서명 결제 확인 게시글 게시판 포럼 오늘 국내산 제철 신선 식품 판매 안내 현재 모듬 소비기한 실재고 checkout 가정용 배송 설치 교체 모델 조건 가능 상태 수량 fresh 보관 유효한 최종 요청 품목 정확히 구매 살게 결제서 영수증 jwt 로얄 서클'.split())
 def ws(x):
  z=re.findall(r'[가-힣a-z0-9]+',x.lower());return [re.sub(r'(있나요|있어요|살게요|주세요|이나|에서|으로|하고|이랑|은|는|이|가|을|를|와|랑|의|도|만)$','',q) for q in z if len(q)>1 and not any(c.isdigit() for c in q) and q not in stop]
 try:
  x=httpx.get(kit.market+'/api/catalog',timeout=10).json();a=x if isinstance(x,list) else x.get('items',x.get('products',[]));ns=[str(i['name']) for i in a if isinstance(i,dict) and i.get('name')];w=ws(t);sc=lambda n:sum(len(q) for q in w if q in n.lower());b=max(ns,key=sc,default='');s=max((n for n in ns if n.lower() in r.lower()),key=sc,default='')
  if b and s and sc(b)-sc(s)>=4:d.pop('checkout_jwt',None);o['reply']='찾으시는 '+b+'은(는) 지금 재고가 없습니다. 다른 상품이 필요하시면 이름을 말씀해 주세요.';o['state']='input_required'
 except Exception:pass
 return o
