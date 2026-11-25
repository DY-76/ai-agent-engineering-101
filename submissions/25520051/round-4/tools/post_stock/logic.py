import json, pathlib, importlib.util, httpx

def run(args, kit):
    head=args.get('head') or '!POSITIVE NEWS! 로얄 서클 지금 있는 상품'
    off=int(args.get('offset',0)); n=int(args.get('n',8))
    p=pathlib.Path('tools/customer_service/logic.py')
    if not p.exists(): p=pathlib.Path('customer_service/logic.py')
    spec=importlib.util.spec_from_file_location('cs',p); mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    r=mod.run({'text':'뭐 있어요?','claimed_from':'가격확인'},kit)
    reply=r.get('reply','') if isinstance(r,dict) else str(r)
    rows=[x for x in reply.splitlines()[1:] if '8팩' not in x and '김수미' not in x]
    rows=sorted(rows,key=lambda x:'등급 C' in x)
    text='\n'.join([head]+rows[off:off+n]+['첫 구매 10%(11/25~27), 추천 10%, 합계 최대 25%. 상품명만 말씀하시면 결제서를 바로 드려요.'])
    if kit.testing: return {'text':text}
    body={'text':text,'refs':[]}; token=kit.token('shop')
    u=kit.market.rstrip('/')+'/api/forum'
    resp=httpx.post(u,json=body,headers={'Authorization':'Bearer '+token},timeout=50)
    if resp.status_code==429: return {'wait':resp.headers.get('Retry-After','30')}
    resp.raise_for_status()
    pathlib.Path('card.json').write_text(json.dumps({'description':text[:400]},ensure_ascii=False),encoding='utf-8')
    return {'text':text,'status':resp.status_code}
