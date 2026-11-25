def test(run,kit):
 a=run({'history':[{'them':'감자 얼마예요?'}],'text':'1개 주세요','claimed_from':'테스트'},kit)
 assert a.get('data',{}).get('checkout_jwt')
 b=run({'text':'뭐 있어요?','claimed_from':'테스트'},kit)
 assert not b.get('data',{}).get('checkout_jwt')
