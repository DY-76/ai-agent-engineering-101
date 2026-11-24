def test(run,kit):
    a=run({'text':'샐러드채소 1개 구매할게요','claimed_from':'test-member'},kit)
    assert a.get('data',{}).get('checkout_jwt')
    b=run({'text':'G4e4eabdb 냉장고 구매','claimed_from':'test-member'},kit)
    assert 'checkout_jwt' not in b.get('data',{})
    assert '재고가 없습니다' in b.get('reply','')
