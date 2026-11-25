def test(run,kit):
 r=run({'text':'가정용 가스레인지 결제서 부탁합니다','claimed_from':'test','history':[]},kit)
 assert 'checkout_jwt' not in (r.get('data') or {})
 assert isinstance(r.get('reply'),str)
