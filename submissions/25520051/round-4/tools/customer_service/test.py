def test(run,kit):
 a=run({'text':'감자 주세요','claimed_from':'테스트','history':[]},kit)
 assert a.get('data',{}).get('checkout_jwt')
 b=run({'text':'C등급이 아닌 상품 뭐 있어요?','claimed_from':'테스트','history':[]},kit)
 assert '등급 C' not in b.get('reply','')
