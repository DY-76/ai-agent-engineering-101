import os
import httpx

def run(args,kit):
 p='tools/.deprecated/customer_service@25/logic.py'
 if not os.path.exists(p): p='tools/customer_service/logic.py'
 class K:
  def __getattr__(self,n): return getattr(kit,n)
  def sign_jwt(self,p,role):
   p=dict(p); p['id']=p['id'][:6]; p['task']=str(p['task'])[-8:]
   return kit.sign_jwt(p,role)
 g={ '__name__':'cs25' }
 exec(open(p,encoding='utf-8').read(),g)
 out=g['run'](args,K())
 if out.get('data',{}).get('checkout_jwt'):
  q=args.get('text','')
  for x in ['살게요','살게','주세요','구매','결제서','결제','checkout','jwt','영수증','주문서']: q=q.replace(x,'')
  o2=g['run'](dict(args,text=q,claimed_from='가격확인',history=[]),K())
  lines=[x for x in o2.get('reply','').splitlines() if ' / ' in x and x.split(' / ')[0] not in out.get('reply','').splitlines()]
  if not o2.get('data',{}).get('checkout_jwt') and len(lines)<=4 and lines:
   out['reply']=out.get('reply','')+' 함께 찾으신 상품(할인 전): '+' · '.join(lines[:2])+'. 원하시면 이름을 말씀해 주세요.'
 return out
