import httpx

def run(args, kit):
    q=str(args.get('query',''))
    limit=max(1,min(100,int(args.get('limit',100))))
    if kit.testing: return {'matches':[],'count':0}
    r=httpx.get(kit.market+'/api/forum',params={'limit':limit},timeout=20)
    r.raise_for_status()
    posts=r.json()
    matches=[p for p in posts if q in p.get('text','')]
    return {'matches':matches,'count':len(matches)}
