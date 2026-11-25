def test(run, kit):
    a=run({'text':'뭐 있어요?','claimed_from':'test','history':[]},kit)
    assert a.get('reply','').startswith('현재 안내 가능한')
    b=run({'text':'1개만 주세요','claimed_from':'test','history':[{'them':'감자 얼마예요?'}]},kit)
    assert b.get('data',{}).get('checkout_jwt')
