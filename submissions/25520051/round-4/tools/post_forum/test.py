def test(run, kit):
    r=run({'text':'테스트 공지','card':'테스트 설명'},kit)
    assert r['posted'] is False
    assert r['card_updated'] is True
