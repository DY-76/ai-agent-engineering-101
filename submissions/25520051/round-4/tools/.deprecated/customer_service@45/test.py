def test(run,kit):
 out=run({'text':'계란 20구 주세요','claimed_from':'테스트고객'},kit)
 assert (out.get('data') or {}).get('checkout_jwt'), out
 return {'ok':True,'checkout_jwt':True}
