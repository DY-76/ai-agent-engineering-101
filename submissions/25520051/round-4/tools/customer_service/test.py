def test(run,kit):
 a=run({'text':'샐러드채소 1개 구매할게요','claimed_from':'test-member'},kit)
 d=a.get('data',{})
 assert d.get('checkout_jwt')
 payload=d['checkout_jwt'].split('.')[1]
 import base64,json
 payload += '='*((4-len(payload)%4)%4)
 obj=json.loads(base64.urlsafe_b64decode(payload))
 assert 'cert' not in obj
 assert str(obj.get('unit','')).startswith('u-')
 b=run({'text':'G4e4eabdb 냉장고 구매','claimed_from':'test-member'},kit)
 assert 'checkout_jwt' not in b.get('data',{})
 assert '재고가 없습니다' in b.get('reply','')
 c=run({'text':'두부 한 팩 주세요','claimed_from':'test-member'},kit)
 if c.get('data',{}).get('checkout_jwt'): assert c['data'].get('item')!='G013cad55'
 e=run({'text':'감자 주세요','claimed_from':'test-member'},kit)
 assert e.get('data',{}).get('checkout_jwt')