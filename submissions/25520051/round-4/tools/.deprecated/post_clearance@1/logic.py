import json, pathlib, importlib.util, httpx, re

def run(args, kit):
    head=args.get('head') or '!IMPORTANT! 로얄 서클 오늘 안에 드실 임박 특가'
    p=pathlib.Path('tools/customer_service/logic.py')
    if not p.exists(): p=pathlib.Path('customer_service/logic.py')
    s=importlib.util.spec_from_file_location('cs',p); m=importlib.util.module_from_spec(s); s.loader.exec_module(m)
    r=m.run({'text':'임박 할인 상품 뭐 있어요?','claimed_from':'가격확인'},kit)
    reply=r.get('reply','') if isinstance(r,dict) else str(r)
    rows=[re.sub(r' / \d+개','',x) for x in reply.splitlines() if '등급 C' in x and '8팩' not in x][:8]
    text='\n'.join([head]+rows+["'임박 감자'처럼 '임박'을 붙여 말씀하시면 이 가격으로 결제서를 드려요. 기한을 꼭 확인해 주세요."])
    if kit.testing: return {'text':text}
    resp=httpx.post(kit.market.rstrip('/')+'/api/forum',json={'text':text,'refs':[]},headers={'Authorization':'Bearer '+kit.token('shop')},timeout=50)
    if resp.status_code==429: return {'wait':resp.headers.get('Retry-After','30')}
    resp.raise_for_status(); return {'text':text,'status':resp.status_code}
