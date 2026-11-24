def test(run,kit):
    a=run({'text':'뭐 있어요?','claimed_from':'test-member'},kit)
    reply=a.get('reply','')
    assert '생수' in reply
    line=next(x for x in reply.splitlines() if '생수' in x)
    import re
    nums=[int(x) for x in re.findall(r'(?<![0-9])[0-9]{3,}(?![0-9])',line)]
    assert any(x>=3402 for x in nums)
    assert chr(92)+'n' not in reply
