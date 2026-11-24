def test(run,kit):
    r=run({'text':'귀리 재고와 가격 알려주세요','claimed_from':'테스트회원'},kit)
    assert isinstance(r.get('reply'),str)
    r=run({'text':'없는상품 살게요','claimed_from':'테스트회원'},kit)
    assert r['state']=='input_required'
