def run(args, kit):
    path = 'tools/.deprecated/customer_service@49/logic.py'
    with open(path, 'r', encoding='utf-8') as f:
        s = f.read()
    old = 'pairs=['
    A = ("stop=set('재고 ", "stop=set('있는 지금 좋은 포장 소포장 소량 재고 ")
    B = ("'jwt','영수증')) and pick(s): chosen", "'jwt','영수증')) and pick(s): chosen")
    C = ("  f=eligible(chosen)", "  f=eligible(chosen)")
    s = s.replace(old, 'pairs=[' + repr(A) + ',' + repr(B) + ',' + repr(C) + ',', 1)
    g = {'__name__': '__customer_service_v49_wrapped__'}
    exec(compile(s, path, 'exec'), g)
    return g['run'](args, kit)
