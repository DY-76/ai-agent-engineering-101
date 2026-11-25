import os

def run(args,kit):
 p='tools/.deprecated/customer_service@21/logic.py'
 if not os.path.exists(p): p='tools/customer_service/logic.py'
 g={'__name__':'cs21'}
 exec(open(p,encoding='utf-8').read(),g)
 out=g['run'](args,kit)
 if not out.get('data',{}).get('checkout_jwt') and str(out.get('reply','')).startswith('현재 안내 가능한 상품입니다'):
  hs=args.get('history',[])
  t=next((x.get('them') for x in hs[::-1] if isinstance(x,dict) and isinstance(x.get('them'),str)),None)
  if t:
   o=g['run'](dict(args,text=t+' '+args.get('text','')),kit)
   if o.get('data',{}).get('checkout_jwt') or len(str(o.get('reply','')).splitlines())<len(str(out.get('reply','')).splitlines()): return o
 return out
