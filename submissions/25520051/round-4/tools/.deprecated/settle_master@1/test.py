import httpx

def test(run, kit):
    # 테스트용 settle 로그 모킹
    import json, time
    # settle API 모킹(실제 네트워크 대신 sandbox용: kit.testing)
    now = int(time.time())
    dummy = [
        {'buyer':'0x111', 'buyer_label':'회원1','shop':'0xshop','sku':'S1','qty':1,'price':4000,'recommended_by':'회원2','time':now-3600,'half_price_ticket':False},
        {'buyer':'0x222', 'buyer_label':'회원2','shop':'0xshop','sku':'S3','qty':1,'price':5000,'recommended_by':'','time':now-3200,'half_price_ticket':False},
        {'buyer':'0x111','buyer_label':'회원1','shop':'0xshop','sku':'S1','qty':1,'price':3999,'recommended_by':'회원2','time':now-2200,'half_price_ticket':True},
        {'buyer':'0x333','buyer_label':'회원3','shop':'0xshop','sku':'S1','qty':1,'price':4050,'recommended_by':'회원2','time':now-1800,'half_price_ticket':False},
    ]
    # patch httpx.get
    import types
    def fake_get(url, headers=None, params=None, timeout=None):
        class Dummy:
            def raise_for_status(self):
                pass
            def json(self):
                return dummy
        return Dummy()
    httpx.get, old = fake_get, httpx.get
    out = run({'members':['회원1','회원2','회원3']}, kit)
    # 리턴값 체크
    assert 'members' in out
    m1, m2, m3 = out['members']['회원1'], out['members']['회원2'], out['members']['회원3']
    assert m1['purchase_count'] == 2 and m2['purchase_count']==1
    assert m2['recommended_count'] == 3  # 3회 추천받음
    assert m1['half_price_tickets_used']==1
    httpx.get = old
    return True
