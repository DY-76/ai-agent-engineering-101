import json, os

def run(args, kit):
    p='tools/.deprecated/customer_service@32/logic.py'
    if not os.path.exists(p): p='tools/customer_service/logic.py'
    g={}; exec(compile(open(p,encoding='utf-8').read(),p,'exec'),g)
    out=g['run'](args,kit); r=out.get('reply','')
    if not r.startswith('찾으시는 상품은 지금 재고가 없습니다'): return out
    try:
        d=kit.market.rstrip('/')+'/api/catalog'; c=__import__('httpx').get(d,headers={'authorization':'Bearer '+kit.token('shop')},timeout=15).json()
        names=' '.join(x.get('name','').replace(' ','').lower() for x in c)
    except Exception: names=''
    import re
    words=[w for w in re.findall(r'[가-힣]{2,}',args.get('text','')) if w not in ('있어요','있나요','주세요','알려주세요')]
    if any(w in names for w in words): return out
    for h in reversed(args.get('history',[])):
        if not isinstance(h,dict) or not h.get('them'): continue
        alt=g['run'](dict(args,text=h['them']+' '+args.get('text',''),history=[]),kit)
        if alt.get('data',{}).get('checkout_jwt') or alt.get('reply','').startswith('현재 안내 가능한'): out=alt; break
    else: out['reply']=r.replace('찾으시는 상품은 지금 재고가 없습니다. 지금 있는 상품입니다.\n','',1)
    if any(x in args.get('text','') for x in ('포장량','중량','보관')): out['reply']=out.get('reply','')+'\n포장량과 보관 상태는 상품명에 적힌 것 외에 확인된 정보가 없습니다.'
    return out
