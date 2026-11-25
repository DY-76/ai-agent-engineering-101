import importlib.util, pathlib, re, httpx

def run(args, kit):
    head=args.get('head') or '!IMPORTANT! 로얄 서클 오늘 안에 드실 임박 특가'
    p=pathlib.Path('tools/customer_service/logic.py')
    if not p.exists(): p=pathlib.Path('customer_service/logic.py')
    s=importlib.util.spec_from_file_location('cs',p); m=importlib.util.module_from_spec(s); s.loader.exec_module(m)
    r=m.run({'text':'임박 할인 상품 뭐 있어요?','claimed_from':'가격확인'},kit)
    reply=r.get('reply','') if isinstance(r,dict) else str(r)
    rows=[]
    for line in reply.splitlines():
        if not line.strip() or '8팩' in line or '김수미' in line:
            continue
        hm=re.search(r'남은 기한\s*([0-9]+(?:\.[0-9]+)?)\s*시간',line)
        if not hm:
            continue
        hours=float(hm.group(1))
        if hours <= 1:
            continue
        if '등급 C' in line or hours <= 24:
            rows.append(re.sub(r' / \d+개','',line))
        if len(rows)>=8:
            break
    if len(rows)<2:
        return {'none':True}
    text='\n'.join([head]+rows+["'임박 감자'처럼 '임박'을 붙여 말씀하시면 이 가격으로 결제서를 드려요. 기한을 꼭 확인해 주세요."])
    if kit.testing:
        return {'text':text}
    resp=httpx.post(kit.market.rstrip('/')+'/api/forum',json={'text':text,'refs':[]},headers={'Authorization':'Bearer '+kit.token('shop')},timeout=50)
    if resp.status_code==429:
        return {'wait':resp.headers.get('Retry-After','30')}
    resp.raise_for_status()
    return {'text':text,'status':resp.status_code}
