def test(run, kit):
    r=run({'head':'테스트'},kit)
    assert '등급' in r['text']
