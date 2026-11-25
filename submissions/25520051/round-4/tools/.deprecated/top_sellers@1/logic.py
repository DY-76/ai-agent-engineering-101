import httpx, statistics

def run(args, kit):
    if kit.testing:
        return {"items":[],"table":[]}
    base=kit.market
    h={"authorization":"Bearer "+kit.token("shop")}
    def get(path, params=None, auth=False):
        r=httpx.get(base+path, params=params, headers=h if auth else {}, timeout=20)
        r.raise_for_status(); return r.json()
    led=get('/api/ledger',{'after':-500})
    rows=led.get('entries',led.get('settles',led if isinstance(led,list) else []))
    last=max([int(x.get('seq',0)) for x in rows] or [0])
    allrows=[]; after=max(-1,last-2500)
    while len(allrows)<2500:
        d=get('/api/ledger',{'after':after,'limit':500})
        xs=d.get('entries',d.get('settles',d if isinstance(d,list) else []))
        if not xs: break
        allrows+=xs; n=max(int(x.get('seq',after)) for x in xs)
        if n<=after: break
        after=n
        if len(xs)<500: break
    now=1795584735
    counts={}
    for x in allrows:
        t=x.get('created_at',x.get('timestamp',x.get('at',0)))
        try: t=float(t)
        except: continue
        data=x.get('data',{})
        if isinstance(data,str): continue
        sku=data.get('sku') if isinstance(data,dict) else None
        if sku and now-10800<=t<=now:
            a=x.get('amount',data.get('amount',0))
            counts.setdefault(sku,[]).append(float(a))
    cat=get('/api/catalog'); cs=cat.get('items',cat.get('catalog',cat if isinstance(cat,list) else []))
    inv=get('/api/inventory',auth=True); us=inv.get('units',inv if isinstance(inv,list) else [])
    stock={}
    for u in us:
        if u.get('grade','').upper()!='C': stock[u.get('sku')]=stock.get(u.get('sku'),0)+1
    table=[]
    for c in cs:
        s=c.get('sku'); vals=counts.get(s,[])
        if not vals or c.get('kind')!='food' or s in ('G013cad55','G0102056d'): continue
        want=max(0,min(6,len(vals)//4+1)-stock.get(s,0))
        if c.get('shelf_hours',999)>24: pass
        else: want=min(2,want)
        table.append({'sku':s,'name':c.get('name'),'count':len(vals),'median_amount':statistics.median(vals),'stock':stock.get(s,0),'want':want,'list_price':c.get('list_price'),'shelf_hours':c.get('shelf_hours')})
    table.sort(key=lambda x:x['count'],reverse=True)
    return {'items':[{'sku':x['sku'],'qty':x['want']} for x in table[:8] if x['want']>0],'table':table}
