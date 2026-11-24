def test(run,kit):
 x=run({'op':'ledger_write','member':'테스트','record':{}},kit)
 assert x['ok']
 y=run({'op':'supply_buy','quote':{'total':200001},'to':'0x0','wei':'1','data':'0x'},kit)
 assert 'error' in y