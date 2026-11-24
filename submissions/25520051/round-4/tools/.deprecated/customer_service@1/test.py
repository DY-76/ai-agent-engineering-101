def test(run, kit):
    r=run({'text':'회원 추천 할인 알려주세요'},kit)
    assert r['state']=='input_required'
    assert '10%' in r['reply']
