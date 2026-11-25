def test(run, kit):
    r=run({'head':'테스트'},kit)
    if r.get('none'):
        assert r == {'none': True}
    else:
        lines=r['text'].splitlines()[1:-1]
        assert len(lines) >= 2
        for line in lines:
            assert '8팩' not in line and '김수미' not in line
            import re
            m=re.search(r'남은 기한\s*([0-9]+(?:\.[0-9]+)?)\s*시간',line)
            assert m and float(m.group(1)) > 1
            assert '등급 C' in line or float(m.group(1)) <= 24
