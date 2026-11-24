def test(run,kit):
    a=run({'text':'뭐 있어요?','claimed_from':'t'},kit)
    assert len(a.get('reply',''))>=200
    assert '\n' not in a.get('reply','')
    b=run({'text':'감자 살게요','claimed_from':'t'},kit)
    assert 'checkout_jwt' in str(b)
