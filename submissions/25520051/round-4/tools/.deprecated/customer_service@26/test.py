def test(run,kit):
 a=run({'text':'감자와 부추 주세요','claimed_from':'테스트','history':[]},kit)
 assert a.get('data',{}).get('checkout_jwt')
 assert '함께 찾으신 상품' in a.get('reply','')
