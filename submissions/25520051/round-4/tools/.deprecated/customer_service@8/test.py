import json,base64,math

def test(run,kit):
 import httpx
 old=httpx.get
 class R:
  def __init__(self,o): self.o=o
  def json(self): return self.o
 unit={'unit':'u-test1','sku':'s1','cost':100,'grade':'A','expires_at':9999999999,'cert':'cert-test'}
 def fake(url,**kw):
  if url.endswith('/api/inventory'): return R({'units':[unit]})
  if url.endswith('/api/catalog'): return R([{'sku':'s1','name':'사과','category':'과일','list_price':1000}])
  return R([{'kind':'settle','data':{'shop':'https://shop.example','buyer':'기존손님'}}])
 httpx.get=fake
 class K:
  market='https://market.ourolabs.ai'; name='Royal Circle'; shop_url='https://shop.example'; testing=True
  def token(self,r): return 'token'
  def sign_jwt(self,p,r): return 'h.'+base64.urlsafe_b64encode(json.dumps(p).encode()).decode().rstrip('=')+'.sig'
 try:
  k=K(); r=run({'text':'사과 살게요','claimed_from':'새손님'},k)
  p=json.loads(base64.urlsafe_b64decode(r['data']['checkout_jwt'].split('.')[1]+'=='))
  floor=math.ceil(310/.99)
  assert p['price']==math.ceil(630*.9) and p['price']>=floor and '오픈 첫 구매' in r['reply']
  r=run({'text':'사과 기존손님 추천해서 살게요','claimed_from':'새손님'},k)
  p=json.loads(base64.urlsafe_b64decode(r['data']['checkout_jwt'].split('.')[1]+'=='))
  assert p['price']>=floor and p['price']<=630 and '추천' in r['reply']
 finally: httpx.get=old