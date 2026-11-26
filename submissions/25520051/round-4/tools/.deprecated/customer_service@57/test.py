def test(run, kit):
    first = run({'text': '현재 안내 가능한 상품을 알려 주세요'}, kit)
    reply = first.get('reply', '') if isinstance(first, dict) else str(first)
    lines = [x.strip() for x in reply.splitlines() if x.strip() and '건취나물' not in x and ('등급 A' in x or '등급 B' in x)]
    assert lines, 'A/B 안내 상품이 없습니다'
    line = lines[0]
    import re
    price_match = re.search(r'/\s*([0-9,]+)크레딧', line)
    assert price_match, '안내 가격을 읽을 수 없습니다: ' + line
    price = price_match.group(1).replace(',', '')
    name = line.split('/')[0].strip()
    result = run({'text': '지금 살 수 있는 ' + name + ' ' + price + '크레딧 살게요', 'claimed_from': 'test-buyer'}, kit)
    out = result.get('reply', '') if isinstance(result, dict) else str(result)
    data = result.get('data', {}) if isinstance(result, dict) else {}
    assert data.get('checkout_jwt') and name in out, '체크아웃 발급 또는 상품명 확인 실패'
    return True