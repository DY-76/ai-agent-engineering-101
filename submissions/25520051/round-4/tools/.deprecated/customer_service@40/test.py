def test(run,kit):
 a=run({'text':'G1dbd0b7a 결제서 보내 주세요'},kit)
 assert 'checkout_jwt' not in str(a)
 return {'ok':True}
