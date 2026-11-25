import os
import httpx

def run(args,kit):
 p='tools/.deprecated/customer_service@22/logic.py'
 if not os.path.exists(p): p='tools/customer_service/logic.py'
 old=httpx.get
 t=str(args.get('text',''))
 filt='B등급 이상' in t or 'B 등급 이상' in t or 'A등급만' in t or 'C등급이 아닌' in t or 'C등급 아닌' in t or 'C등급은 제외' in t or 'C등급 제외' in t
 def get(*a,**k):
  r=old(*a,**k)
  if not filt or not str(a[0] if a else k.get('url','')).endswith('/api/inventory'): return r
  class R:
   status_code=r.status_code
   def json(self):
    d=r.json(); u=d.get('units',[])
    if 'A등급만' in t: u=[x for x in u if x.get('grade')=='A']
    else: u=[x for x in u if x.get('grade')!='C']
    d=dict(d); d['units']=u; return d
  return R()
 try:
  if filt: httpx.get=get
  g={'__name__':'cs22'}
  exec(open(p,encoding='utf-8').read(),g)
  return g['run'](args,kit)
 finally: httpx.get=old
