import httpx

def run(args, kit):
    base=kit.market
    paths={'catalog':'/api/catalog','demand':'/api/demand','restock':'/api/restock','supply_prices':'/api/supply-prices','inventory':'/api/inventory'}
    sections=args.get('sections') or list(paths)
    h={'authorization':'Bearer '+kit.token('shop')} if 'inventory' in sections else {}
    out={}
    for s in sections:
        if s not in paths: continue
        try:
            r=httpx.get(base+paths[s],headers=h,timeout=15)
            out[s]={'status':r.status_code,'body':r.json()}
        except Exception as e: out[s]={'error':str(e)}
    return out
