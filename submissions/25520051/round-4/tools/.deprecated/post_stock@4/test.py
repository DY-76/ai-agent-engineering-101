def test(run,kit):
    r=run({},kit)
    assert '•' in r['text']
