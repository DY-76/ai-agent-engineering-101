import httpx, json, datetime, os

def run(args, kit):
    card = {
        "name": "로얄 서클 (Royal Circle)",
        "description": "신선식품·회원제 마트. 추천인 10% 할인, 누적 추천 10/20/30회 15/20/25% 할인, 10회마다 등급 상승 및 반값 티켓. 추천/등급/행사/티켓 포함 할인은 최대 25%, 하한은 원가+210/0.99 이상. settle로 추천 등 확정, 오픈 3일간 모든 신규 첫 구매자 10% 추가할인.",
        "version": "2.1",
        "provider": {"organization": "Royal Circle"},
        "supportedInterfaces": [{"url": kit.shop_url, "protocolBinding": "A2A", "protocolVersion": "1"}],
        "capabilities": {"streaming": False, "pushNotifications": False},
        "skills": [
            {"id": "membership_discount", "name": "회원제·추천인 할인·등급/티켓 정책",
             "description": "1) 회원은 첫 구매시 자동 등록. 2) 추천인 제시시 양쪽 10% 할인, 같은 회원에게 추천 누적 10/20/30회시 15/20/25%로 할인 단계 상향. 3) 추천 10회마다 등급+1 및 반값 구매티켓 자동 지급. 4) 오픈 3일간 신규 첫구매 10% 행사. 5) 할인가는 원가+210/0.99 이상. 6) settle로만 추천·등급 확정.",
             "tags":["회원제","추천","등급","할인","티켓"]},
            {"id":"event_notice","name":"7일장/오픈행사","description":"매주 1회 7일장, 오픈 3일간 첫구매 10%. 모든 행사는 최저가(원가210+보관료/0.99) 이상 준수.","tags":["행사","이벤트"]}
        ]
    }
    with open('card.json', 'w', encoding='utf-8') as f:
        f.write(json.dumps(card, ensure_ascii=False, indent=2))
    # 테스트 환경에서는 포럼 게시 대신 가상 결과 반환
    if getattr(kit, 'testing', False):
        return {'status': 200, 'body': 'test mode: posting skipped'}
    # 실거래시는 실제 포럼에 게시
    text = args.get('text') or '로얄 서클 회원제·추천 할인·등급/티켓 구간별 혜택, 오픈행사/7일장 안내드립니다.'
    r = httpx.post(kit.market + '/api/forum',
                   headers={'authorization': 'Bearer ' + kit.token('shop'), 'content-type': 'application/json'},
                   json={'text': text, 'refs': []}, timeout=50)
    try:
        body = r.json()
    except Exception:
        body = r.text
    return {'status': r.status_code, 'body': body}
