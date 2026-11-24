def test(run, kit):
    x=run({'text':'테스트 공지'},kit)
    assert 'status' in x
