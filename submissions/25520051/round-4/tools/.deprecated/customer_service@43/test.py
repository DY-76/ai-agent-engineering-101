import httpx,time

def test(run,kit):
 out=run({'text':'우유 살게요','claimed_from':'김성우-8bd1'},kit)
 assert '회원 재구매' in out.get('reply',''), out
 assert (out.get('data') or {}).get('checkout_jwt'), out
 return {'ok':True,'reply_has_member_repurchase':True,'checkout_jwt':True}
