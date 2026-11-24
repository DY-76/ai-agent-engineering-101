import json, httpx

def run(args, kit):
    op=args.get('op')
    if op=='ledger_read':
        try:
            with open('ledger.json',encoding='utf-8') as f:return json.load(f)
        except Exception:return {'members':{},'transactions':[]}
    if op=='ledger_write':
        try:
            with open('ledger.json',encoding='utf-8'):
                db=json.load(open('ledger.json',encoding='utf-8'))
        except Exception: db={'members':{},'transactions':[]}
        if args.get('member'): db['members'][args['member']]=args.get('record',{})
        else: db['transactions'].append(args.get('record',{}))
        with open('ledger.json','w',encoding='utf-8') as f: json.dump(db,f,ensure_ascii=False,indent=2)
        return {'ok':True,'ledger':db}
    headers={'authorization':'Bearer '+kit.token('shop'),'content-type':'application/json'}
    if op=='inventory': method='GET'; path='/api/inventory'; body=None
    elif op=='catalog': method='GET'; path='/api/catalog'; body=None
    elif op=='supply_quote': method='POST'; path='/api/supply'; body={'sku':args['sku'],'qty':args['qty']}
    elif op=='supply_pay': method='POST'; path='/api/supply'; body={'quote':args['quote'],'tx_hash':args['tx_hash']}
    else:return {'error':'unknown op'}
    url=kit.market+path
    r=httpx.get(url,headers=headers,timeout=30) if method=='GET' else httpx.post(url,headers=headers,json=body,timeout=30)
    try: result=r.json()
    except Exception: result={'text':r.text}
    return {'status':r.status_code,'result':result}
