def test(run,kit):
 r=run({'text':'현재 상품 알려주세요','claimed_from':None,'history':[]},kit)
 assert 'reply' in r and r.get('state')=='input_required'
 assert 'checkout_jwt:' not in r['reply']
