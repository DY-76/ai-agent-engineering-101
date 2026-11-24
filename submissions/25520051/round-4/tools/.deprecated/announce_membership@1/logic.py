import httpx, json

def run(args, kit):
    card={"name":"로얄 서클 (Royal Circle)","description":"신선한 식품과 좋은 제품을 회원제로 판매하며 추천과 장기 고객 혜택을 중시합니다.","version":"1.0","provider":{"organization":"Royal Circle"},"supportedInterfaces":[{"url":kit.shop_url,"protocolBinding":"A2A","protocolVersion":"1"}],"capabilities":{"streaming":False,"pushNotifications":False},"skills":[{"id":"membership","name":"회원제 및 추천 혜택","description":"회원 등록, 추천인 할인, 추천 누적 등급 혜택 안내","tags":["shop","membership"]}]}
    open('card.json','w',encoding='utf-8').write(json.dumps(card,ensure_ascii=False))
    text=args.get('text') or '로얄 서클 회원을 모집합니다.'
    r=httpx.post(kit.market+'/api/forum/posts',headers={'authorization':'Bearer '+kit.token('shop'),'content-type':'application/json'},json={'text':text},timeout=60)
    try: body=r.json()
    except Exception: body=r.text
    return {'status':r.status_code,'body':body}
