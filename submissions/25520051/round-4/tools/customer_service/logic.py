import time, json, re, httpx

def log_inquiry(args, reply):
    rec={'time':time.time(),'claimed_from':args.get('claimed_from'),'text':args.get('text',''),'reply':reply}
    with open('inquiries.jsonl','a',encoding='utf-8') as f:
        f.write(json.dumps(rec,ensure_ascii=False,separators=(',',':'))+'\n')

def run(args, kit):
    text=args.get('text','')
    skus=re.findall(r'G[0-9a-f]{8}', text)
    if skus:
        try:
            r=httpx.get(kit.market+'/api/inventory',headers={'authorization':'Bearer '+kit.token('shop')},timeout=20)
            inv=r.json() if r.status_code<400 else {}
            units=inv.get('units',[]) if isinstance(inv,dict) else []
            have={str(u.get('sku')) for u in units if isinstance(u,dict)}
            if not any(s in have for s in skus):
                reply='문의하신 상품은 지금 재고가 없습니다.'
                if not kit.testing:
                    log_inquiry(args,reply)
                return {'reply':reply,'state':'input_required'}
        except Exception:
            pass
    p='tools/.deprecated/customer_service@8/logic.py'
    with open(p,encoding='utf-8') as f:
        src=f.read()
    src=src.replace("'cert':u['cert'],", "")
    src=src.replace("name=str(p[1].get('name','')).lower()", "name=str(p[1].get('name','')).lower().replace(' ','')")
    src=src.replace("float(c.get('expires_at',0))", "float(u.get('expires_at') or 99999999)")
    src=src.replace("c.get('expires_at',0)", "u.get('expires_at')")
    needle="price=max(math.ceil(float(c.get('list_price',0))*.63),floor)"
    if needle in src and "21600" not in src:
        src=src.replace(needle,needle+"\n        rem=float(u.get('expires_at') or 99999999)-time.time()\n        if rem<21600:\n            floor=220; price=max(math.ceil(float(c.get('list_price',0))*.40),floor)\n        elif rem<43200:\n            floor=220; price=max(math.ceil(float(c.get('list_price',0))*.50),floor)")
    ns={'__file__':p,'__name__':'deprecated_customer_service','kit':kit,'time':time}
    exec(compile(src,p,'exec'),ns)
    out=ns['run'](args,kit)
    if isinstance(out,dict) and isinstance(out.get('reply'),str):
        out['reply']=out['reply'].replace(chr(92)+'n',chr(10))
        if out.get('data',{}).get('checkout_jwt'):
            out['reply']+=' 결제 토큰은 고치지 말고 그대로 사용해 주세요.'
        if not kit.testing:
            log_inquiry(args,out['reply'])
    return out
