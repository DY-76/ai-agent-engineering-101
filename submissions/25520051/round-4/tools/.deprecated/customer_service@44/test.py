def test(run,kit):
 out=run({'text':'두부가 필요해요. 실큰두부 300g 한 팩 재고가 있나요? 조건이 괜찮으면 이 상품 그대로 유효한 서명 checkout_jwt도 부탁드려요.','claimed_from':'테스트고객'},kit)
 assert (out.get('data') or {}).get('checkout_jwt'), out
 return {'ok':True,'checkout_jwt':True}
