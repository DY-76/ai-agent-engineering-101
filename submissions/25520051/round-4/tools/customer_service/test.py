def test(run,kit):
 out=run({'text':'서명이 맞지 않아 거절됐습니다. 다시 보내 주세요','claimed_from':'고객 offers 없는 테스트'},kit)
 assert not (out.get('data') or {}).get('checkout_jwt') or isinstance((out.get('data') or {}).get('checkout_jwt'),str), out
 out=run({'text':'감자 주세요','claimed_from':'감자 테스트 고객'},kit)
 if out.get('data'):
  assert isinstance(out['data'].get('checkout_jwt'),str), out
 return {'ok':True,'no_offer_error':True,'normal_request_checked':True}
