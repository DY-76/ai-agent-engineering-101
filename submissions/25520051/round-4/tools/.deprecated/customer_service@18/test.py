def test(run,kit):
 import re
 v8=open('tools/.deprecated/customer_service@8/logic.py',encoding='utf-8').read()
 B1="not any(w in text for w in ['알려주세요','보여주세요'])"; B2="(not any(w in text for w in ['알려주세요','보여주세요']) or any(w in low for w in ['checkout','jwt','영수증','결제서','주문서']))"
 C1="적용 가격은 {price}크레딧입니다"; C2="1개, 등급 {u['grade']}, 남은 기한 {int((float(u.get('expires_at') or now)-now)//3600)}시간, 최종 가격 {price}크레딧입니다"
 assert B1 in v8 and C1 in v8 and B2 not in v8 and C2 not in v8
 r=run({'text':'뭐 있어요?','claimed_from':'테스트'},kit); q=r.get('reply','')
 assert '사과' in q and '생수' in q
 assert int(re.search(r'사과[^0-9]*([0-9,]+)',q).group(1).replace(',',''))<4000
 assert int(re.search(r'생수[^0-9]*([0-9,]+)',q).group(1).replace(',',''))==3402
 r=run({'text':'가자미 등급 알려주세요. checkout 보내 주세요. 구매할게요','claimed_from':'테스트'},kit)
 assert 'checkout_jwt' in str(r) and '등급' in r.get('reply','')
