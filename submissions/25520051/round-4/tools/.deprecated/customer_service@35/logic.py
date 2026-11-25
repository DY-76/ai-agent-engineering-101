import os,re,time

def run(args,kit):
 p='tools/.deprecated/customer_service@33/logic.py'
 if not os.path.exists(p): p='tools/customer_service/logic.py'
 g={}; exec(compile(open(p,encoding='utf-8').read(),p,'exec'),g)
 t=args.get('text',''); ss=re.split(r'(?<=[.?!])\\s+|\\n',t)
 keep=[s for s in ss if not (any(x in s for x in ('사지 않','구매하지 않','필요 없','필요하지 않','필요는 없','아니라','말고','제외')) and 'C등급' not in s and '8팩' not in s)]
 T=' '.join(keep) or t
 B=' '.join(s for s in re.split(r'(?<=[.?!])\\s+|\\n',T) if any(x in s for x in ('checkout','jwt','결제서','영수증','주문서','살게','주세요','구매할','구매하')))
 import httpx
 old=httpx.get
 def filt(*a,**kw):
  r=old(*a,**kw)
  if '/api/inventory' in str(a[0] if a else kw.get('url','')) and not any(x in T for x in ('임박','저렴','싼')):
   j=r.json(); j['units']=[u for u in j.get('units',[]) if not (u.get('grade')=='C' and (u.get('expires_at',0)-time.time())/3600<6)]
   class R:
    def json(self): return j
   return R()
  return r
 def finish(o):
  reply=o.get('reply','')
  if o.get('data',{}).get('checkout_jwt'):
   reply=reply.replace('결제 토큰은 수정하지 말고 그대로 사용해 주세요.','결제는 buy에서 이 가게 이름만 지정해 주세요. 토큰을 손으로 옮겨 적으면 서명이 깨질 수 있어요. 가게 지갑: '+kit.address('shop')+'.')
  elif any(x in t for x in ('지갑','서명')):
   reply+='\\n저희 결제서는 가게 지갑 '+kit.address('shop')+' 로 서명합니다.'
  o['reply']=reply
  return o
 def no_stock(o): return o.get('reply','').startswith('찾으시는 상품은 지금 재고가 없습니다')
 try:
  httpx.get=filt
  if B:
   out=g['run'](dict(args,text=B,history=[]),kit)
   if out.get('data',{}).get('checkout_jwt'): return finish(out)
  out=g['run'](dict(args,text=T),kit)
  trigger=('그 품목','그 상품','이 상품','방금','앞서','해당','새 결제서','새로','1개만','한 개')
  if no_stock(out) and any(x in t for x in trigger):
   hist=args.get('history',[]); them=[]
   for h in reversed(hist if isinstance(hist,list) else []):
    if isinstance(h,dict) and (h.get('role')=='them' or h.get('speaker')=='them'):
     them.append(h)
     if len(them)>=3: break
   if them:
    retry=dict(args,text=' '.join(str(h.get('text','')) for h in reversed(them))+' '+T,history=[])
    again=g['run'](retry,kit)
    if again.get('data',{}).get('checkout_jwt'): out=again
  return finish(out)
 finally:
  httpx.get=old
