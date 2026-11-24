import json, base64, math

def test(run, kit):
    import httpx
    old=httpx.get
    class R:
        def __init__(self,obj): self.obj=obj
        def json(self): return self.obj
    unit={'unit':'u-test1','sku':'s1','name':'사과','cost':100,'grade':'A','expires_at':9999999999,'cert':'cert-test'}
    catalog=[{'sku':'s1','name':'사과','category':'과일','list_price':1000}]
    def fake(url,**kw): return R({'units':[unit]} if url.endswith('/api/inventory') else catalog)
    httpx.get=fake
    class K:
        market='https://market.ourolabs.ai'; name='Royal Circle'; shop_url='https://shop.example'
        def token(self,r): return 'token'
        def sign_jwt(self,p,r): return 'h.'+base64.urlsafe_b64encode(json.dumps(p,ensure_ascii=False).encode()).decode().rstrip('=')+'.sig'
    try:
        k=K(); result=run({'text':'뭐 있어요?'},k)
        assert '사과' in result['reply'] and '등급 A' in result['reply']
        result=run({'text':'사과 살게요','claimed_from':'손님','task_id':'t1'},k)
        assert result['state']=='input_required'
        p=json.loads(base64.urlsafe_b64decode(result['data']['checkout_jwt'].split('.')[1]+'=='))
        assert p['item']=='s1' and p['unit'].startswith('u-') and p['price']==max(630,math.ceil(310/.99))
    finally: httpx.get=old