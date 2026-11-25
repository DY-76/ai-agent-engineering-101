def test(run, kit):
    r=run({},kit)
    assert 'items' in r and 'table' in r
