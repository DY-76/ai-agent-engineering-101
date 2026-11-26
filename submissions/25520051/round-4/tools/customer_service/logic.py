def run(args, kit):
    path = 'tools/.deprecated/customer_service@53/logic.py'
    with open(path, 'r', encoding='utf-8') as f:
        s = f.read()
    old = "'포장 소포장 소량 재고 "
    assert s.count(old) == 1
    s = s.replace(old, "'신선한 대용량 적당한 며칠 있는 지금 좋은 포장 소포장 소량 재고 ")
    g = {}
    exec(compile(s, path, 'exec'), g)
    return g['run'](args, kit)
