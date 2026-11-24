import time, json

def run(args, kit):
    p='tools/.deprecated/customer_service@8/logic.py'
    with open(p, encoding='utf-8') as f:
        src=f.read()
    # v8 price calculation uses the matching inventory unit as u.
    src=src.replace("float(c.get('expires_at',0))", "float(u.get('expires_at') or 99999999)")
    src=src.replace("c.get('expires_at',0)", "u.get('expires_at')")
    # Preserve the intended urgent/perishable pricing additions.
    needle="price=max(math.ceil(float(c.get('list_price',0))*.63),floor)"
    if needle in src and "21600" not in src:
        src=src.replace(needle, needle+"\n        rem=float(u.get('expires_at') or 99999999)-time.time()\n        if rem<21600:\n            floor=220; price=max(math.ceil(float(c.get('list_price',0))*.40),floor)\n        elif rem<43200:\n            floor=220; price=max(math.ceil(float(c.get('list_price',0))*.50),floor)")
    ns={'__file__':p,'__name__':'deprecated_customer_service','kit':kit,'time':time}
    exec(compile(src,p,'exec'),ns)
    out=ns['run'](args,kit)
    if isinstance(out,dict) and isinstance(out.get('reply'),str):
        # Convert escaped newline sequences, without collapsing real line breaks.
        out['reply']=out['reply'].replace(chr(92)+'n',chr(10))
        if not kit.testing:
            rec={'time':time.time(),'claimed_from':args.get('claimed_from'),'text':args.get('text',''),'reply':out['reply']}
            with open('inquiries.jsonl','a',encoding='utf-8') as f:
                f.write(json.dumps(rec,ensure_ascii=False,separators=(',',':'))+'\n')
    return out
