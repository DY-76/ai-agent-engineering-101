def run(args, kit):
    path = 'tools/.deprecated/customer_service@49/logic.py'
    with open(path, 'r', encoding='utf-8') as f:
        s = f.read()
    old = 'pairs=['
    assert s.count(old) == 1
    A = ("stop=set('재고 ", "stop=set('포장 소포장 소량 재고 ")
    B = ("'jwt','영수증')) and pick(s): chosen", "'jwt','영수증')) and set(pick(s))-{'과일','채소','생선','고기'} and pick(s): chosen")
    s = s.replace(old, 'pairs=[' + repr(A) + ',' + repr(B) + ',', 1)
    g = {'__name__': '__customer_service_v49_wrapped__'}
    exec(compile(s, path, 'exec'), g)
    return g['run'](args, kit)
