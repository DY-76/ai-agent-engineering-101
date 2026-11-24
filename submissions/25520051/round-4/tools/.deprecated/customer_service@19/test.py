def test(run,kit):
 r=run({'text':'감자 주세요','claimed_from':'테스트'},kit)
 assert 'checkout_jwt' in str(r)