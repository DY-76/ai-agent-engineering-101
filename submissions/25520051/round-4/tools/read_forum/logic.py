import httpx

def run(args, kit):
    if kit.testing:
        return []
    limit=max(1,min(100,int(args.get('limit',100))))
    r=httpx.get(kit.market+'/api/forum',params={'limit':limit},timeout=20)
    r.raise_for_status()
    return r.json()
