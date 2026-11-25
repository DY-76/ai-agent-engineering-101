def test(run,kit):
 a=run({'text':'가자미는 사지 않겠습니다. 부추 결제서 보내 주세요.','claimed_from':'test','history':[]},kit)
 assert '부추' in a.get('reply','') and a.get('data',{}).get('checkout_jwt')