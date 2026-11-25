def test(run,kit):
 r=run({'text':'뭐 있어요?','claimed_from':'test'},kit)
 assert r.get('reply','').startswith('현재 안내 가능한 상품입니다.') or '현재 안내 가능한 재고가 없습니다.' in r.get('reply','')
 assert r.get('state')=='input_required'
 r=run({'text':'1개만 주세요','claimed_from':'test'},kit)
 assert r.get('state') in ('input_required','completed')
 return True