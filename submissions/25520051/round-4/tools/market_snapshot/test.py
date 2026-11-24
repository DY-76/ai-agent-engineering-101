def test(run, kit):
    x=run({'sections':['catalog','restock']},kit)
    assert 'catalog' in x and 'restock' in x
