import httpx, statistics

def arr(d, keys):
    if isinstance(d,list): return d
    if isinstance(d,dict):
        for k in keys:
            if isinstance(d.get(k),list): return d[k]
    return []

def run(args, kit):
    if kit.testing: return {'items':[],'table':[]}
    b=kit.market; h={'authorization':'Bearer '+kit.token('shop')}
    def g(p,q=None,a=False):
        r=httpx.get(b+p,params=q,headers=h if a else {},timeout=20); r.raise_for_status(); return r.json()
    first=g('/api/ledger',{'after':-500}); rs=arr(first,['entries','settles'])
    last=max([int(x.get('seq',0)) for x in rs] or [0]); after=max(-1,last-2500); rows=[]
    while len(rows)<2500:
        xs=arr(g('/api/ledger',{'after':after,'limit':500}),['entries','settles'])
        if not xs: break
        rows+=xs; n=max(int(x.get('seq',after)) for x in xs)
        if n<=after or len(xs)<500: break
        after=n
    counts={}; now=1795584735
    for x in rows:
        try: t=float(x.get('created_at',x.get('timestamp',x.get('at',0))))
        except: continue
        d=x.get('data',{}); sku=d.get('sku') if isinstance(d,dict) else None
        if sku and now-10800<=t<=now: counts.setdefault(sku,[]).append(float(x.get('amount',d.get('amount',0))))
    cs=arr(g('/api/catalog'),['items','catalog']); iu=arr(g('/api/inventory',a=True),['units']); stock={}
    for u in iu:
        if str(u.get('grade','')).upper()!='C': stock[u.get('sku')]=stock.get(u.get('sku'),0)+1
    tab=[]
    for c in cs:
        s=c.get('sku'); v=counts.get(s,[])
        if not v or c.get('kind')!='food' or s in ('G013cad55','G0102056d'): continue
        q=max(0,min(6,len(v)//4+1)-stock.get(s,0)); q=min(q,2) if c.get('shelf_hours',999)<=24 else q
        tab.append({'sku':s,'name':c.get('name'),'count':len(v),'median_amount':statistics.median(v),'stock':stock.get(s,0),'want':q,'list_price':c.get('list_price'),'shelf_hours':c.get('shelf_hours')})
    tab.sort(key=lambda x:x['count'],reverse=True)
    return {'items':[{'sku':x['sku'],'qty':x['want']} for x in tab[:8] if x['want']>0],'table':tab}
