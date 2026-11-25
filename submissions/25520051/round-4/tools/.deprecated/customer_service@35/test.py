def test(run,kit):
 a=run({'text':'감자 주세요','claimed_from':'test','history':[]},kit)
 assert a.get('data',{}).get('checkout_jwt')
 assert '가게 지갑' in a.get('reply','')
