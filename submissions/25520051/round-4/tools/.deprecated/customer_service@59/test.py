import re
def test(run,kit):
 L=[x for x in run({'text':'현재 안내 가능한 상품을 알려 주세요'},kit)['reply'].splitlines() if '건취나물' not in x and ('등급 A' in x or '등급 B' in x)]
 assert L
 n=L[0].split('/')[0].strip();pr=re.search(r'([0-9]+)크레딧',L[0]).group(1)
 r=run({'text':'지금 살 수 있는 '+n+' '+pr+'크레딧 살게요','claimed_from':'test-buyer'},kit)
 assert (r.get('data') or {}).get('checkout_jwt') and n in r['reply']
 h=re.search(r'남은 기한 ([0-9]+)시간',r['reply']).group(1)
 a=run({'text':'남은 기한 '+h+'시간 맞나요','claimed_from':'test-buyer','force_nostock':1},kit)
 assert (a.get('data') or {}).get('checkout_jwt') and n in a['reply'],'후속 재안내 실패'
 b=run({'text':'다른 거','claimed_from':'nobody-test','force_nostock':1},kit)
 assert b['reply'].startswith('찾으시는 상품은 지금 재고가 없')
 return True