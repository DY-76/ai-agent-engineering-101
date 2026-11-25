def test(run, kit):
    r = run({}, kit)
    assert 'items' in r and 'table' in r
    assert 'total_units' in r
    assert len(r['table']) >= 1
