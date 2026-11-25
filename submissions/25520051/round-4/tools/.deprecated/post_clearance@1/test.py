def test(run, kit):
    r=run({'head':'테스트'},kit)
    assert '임박' in r['text']
