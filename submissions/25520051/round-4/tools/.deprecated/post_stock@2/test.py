def test(run,kit):
    r=run({},kit)
    assert '크레딧' in r['text']
