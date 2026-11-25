def test(run,kit):
 r=run({'text':'가정용 가스레인지 교체 재고 모델 배송 설치 조건 checkout 부탁합니다','claimed_from':'테스트'},kit)
 assert 'checkout_jwt' not in str(r)
 r2=run({'text':'감자 주세요','claimed_from':'테스트'},kit)
 assert 'checkout_jwt' in str(r2)
