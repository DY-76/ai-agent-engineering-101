def test(run,kit):
 r=run({'text':'4.5kg은 많소. 노지감귤 소과 2.5kg 결제서를 보내주이소','claimed_from':'test','history':[],'task_id':'testtask','context_id':'testctx'},kit)
 assert r and r.get('data',{}).get('checkout_jwt')
 assert '2.5kg' in r.get('reply','')
