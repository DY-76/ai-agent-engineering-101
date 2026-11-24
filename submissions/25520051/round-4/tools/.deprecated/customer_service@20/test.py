def test(run,kit):
 r=run({'text':'시금치 남은 기한과 가격 알려주시고 checkout_jwt를 부탁드려요','claimed_from':'테스트'},kit)
 assert 'checkout_jwt' in str(r)
 r2=run({'text':'뭐 있어요?','claimed_from':'테스트'},kit)
 assert 'checkout_jwt' not in str(r2)