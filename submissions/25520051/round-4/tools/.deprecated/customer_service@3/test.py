def test(run,kit):
 r=run({'text':'사과 재고와 가격 알려주세요'},kit)
 assert r['state'] in ('input_required','completed')
 assert isinstance(r['reply'],str)