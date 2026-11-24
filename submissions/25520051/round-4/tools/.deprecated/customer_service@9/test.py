def test(run,kit):
 r=run({'text':'현재 상품을 알려주세요','data':{},'claimed_from':'테스트','task_id':'t','context_id':'c','history':[]},kit)
 assert r
 s=r.get('reply','') if isinstance(r,dict) else str(r)
 assert s and '\\n' not in s
