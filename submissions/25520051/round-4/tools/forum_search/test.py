def test(run, kit):
    r=run({'query':'255번','limit':10},kit)
    assert r['count']==0
