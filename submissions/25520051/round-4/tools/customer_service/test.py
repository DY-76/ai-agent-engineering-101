def test(run,kit):
 a=run({'text':'감자 주세요','claimed_from':'테스트','history':[]},kit)
 assert a.get('data',{}).get('checkout_jwt')
 assert '함께 찾으신 상품' not in a.get('reply','')
