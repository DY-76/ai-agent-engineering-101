def test(run, kit):
    r = run({}, kit)
    assert 'items' in r and 'table' in r and 'total_units' in r
    assert 'stock_by_sku' in r and 'fresh_by_sku' in r
    assert len(r['table']) >= 1
