import re
def test(run,kit):
 a=run({'text':'뭐 있어요?','claimed_from':'test-member'},kit)
 assert any('어묵' in line and re.search(r'\b[0-9]{1,3}(?:,[0-9]{3})?\b',line) and int(re.search(r'([0-9]{1,3}(?:,[0-9]{3})?)',line).group(1).replace(',',''))<=3000 for line in a.get('reply','').splitlines())
 b=run({'text':'감자 주세요','claimed_from':'test-member'},kit)
 assert b.get('data',{}).get('checkout_jwt')
