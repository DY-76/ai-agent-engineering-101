def test(run,kit):
 a=run({'text':'감자 주세요','claimed_from':'테스트','history':[]},kit)
 assert 'reply' in a
