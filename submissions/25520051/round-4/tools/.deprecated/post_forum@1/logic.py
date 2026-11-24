import json, httpx

def run(args, kit):
    text=args.get('text','')
    card=args.get('card')
    if card is not None:
        with open('card.json','w',encoding='utf-8') as f:
            json.dump({'description':card},f,ensure_ascii=False,indent=2)
    if kit.testing or not text:
        return {'posted':False,'card_updated':card is not None}
    headers={'authorization':'Bearer '+kit.token('shop'),'content-type':'application/json'}
    # forum API is documented through the forum entity endpoint
    r=httpx.post(kit.market+'/api/forum/posts',headers=headers,json={'title':text[:120],'body':text},timeout=20)
    if r.status_code==429:
        return {'posted':False,'status':429,'retry_after':r.headers.get('retry-after')}
    r.raise_for_status()
    return {'posted':True,'result':r.json(),'card_updated':card is not None}
