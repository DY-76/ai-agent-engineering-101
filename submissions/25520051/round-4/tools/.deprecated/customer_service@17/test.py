def test(run,kit):
    r=run({'text':'뭐 있어요?','claimed_from':'테스트'},kit)
    reply=r.get('reply','')
    assert '사과' in reply
    assert '생수' in reply
    import re
    m=re.search(r'사과[^0-9]*([0-9,]+)',reply)
    assert m and int(m.group(1).replace(',','')) < 4000
    m=re.search(r'생수[^0-9]*([0-9,]+)',reply)
    assert m and int(m.group(1).replace(',','')) == 3402
    r=run({'text':'감자 주세요','claimed_from':'테스트'},kit)
    assert 'checkout_jwt' in str(r)