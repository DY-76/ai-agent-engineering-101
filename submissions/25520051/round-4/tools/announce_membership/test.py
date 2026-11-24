def test(run, kit):
    import json, os
    class Kit:
        shop_url = 'http://shopurl'
        market = 'http://market.ourolabs.ai'
        def token(self, x): return 'tok'
        def address(self, x): return 'ADDR'
    kit = Kit()
    kit.testing = True
    if os.path.exists('card.json'): os.remove('card.json')
    res = run({'text': '테스트 회원제 정책 공지'}, kit)
    body = open('card.json', encoding='utf-8').read()
    assert '회원' in body
    assert res['status'] in (200, 201)
