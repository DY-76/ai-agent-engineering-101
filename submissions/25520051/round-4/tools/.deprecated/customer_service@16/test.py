def test(run,kit):
 r=run({'text':'뭐 있어요?','claimed_from':'테스트'},kit)
 assert '임박 할인 적용' not in r.get('reply','')
 r=run({'text':'감자 주세요','claimed_from':'테스트'},kit)
 assert 'checkout_jwt' in str(r)