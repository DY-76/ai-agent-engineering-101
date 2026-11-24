def test(run,kit):
 x=run({'op':'ledger_write','member':'테스트','record':{'purchases':[]}},kit); assert x['ok']
 assert '테스트' in run({'op':'ledger_read'},kit)['members']
 y=run({'op':'supply_buy','wei':200001,'to':'0x0','data':'0x','quote':{}},kit); assert 'error' in y