import base64,json

def test(run,kit):
    a=run({'text':'뭐 있어요?','claimed_from':'test-buyer'},kit)
    assert '현재 안내 가능한 상품입니다.' in a['reply'], a
    b=run({'text':'감자 주세요','claimed_from':'test-buyer'},kit)
    if '감자' in b['reply'] and 'checkout_jwt:' in b['reply']:
        token=b['reply'].split('checkout_jwt: ',1)[1].split()[0]
        payload=json.loads(base64.urlsafe_b64decode(token.split('.')[1]+'==='))
        assert payload['item'] and payload['unit'].startswith('u-') and int(payload['price'])>=1
    else:
        # 테스트 재고에 감자가 없는 경우에는 실제 보유 상품으로 구매 흐름을 검증
        lines=a['reply'].splitlines()[1:]
        assert lines, a
        name=lines[0].split(' / ')[0]
        c=run({'text':name+' 주세요','claimed_from':'test-buyer'},kit)
        assert 'checkout_jwt:' in c['reply'], c
        token=c['reply'].split('checkout_jwt: ',1)[1].split()[0]
        payload=json.loads(base64.urlsafe_b64decode(token.split('.')[1]+'==='))
        assert payload['item'] and payload['unit'].startswith('u-') and int(payload['price'])>=1