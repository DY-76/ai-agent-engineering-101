def test(run, kit):
    path = 'tools/.deprecated/customer_service@49/test.py'
    with open(path, 'r', encoding='utf-8') as f:
        s = f.read()
    g = {'__name__': '__customer_service_v49_test__'}
    exec(compile(s, path, 'exec'), g)
    return g['test'](run, kit)
