import time

def run(args,kit):
    p='tools/.deprecated/customer_service@8/logic.py'
    with open(p,encoding='utf-8') as f: src=f.read()
    needle="price=max(math.ceil(float(c.get('list_price',0))*.63),floor)"
    add="""\n        rem=float(c.get('expires_at',0))-time.time()\n        if rem<21600:\n            floor=220; price=max(math.ceil(float(c.get('list_price',0))*.40),floor)\n        elif rem<43200:\n            floor=220; price=max(math.ceil(float(c.get('list_price',0))*.50),floor)"""
    src=src.replace(needle,needle+add)
    ns={'__file__':p,'__name__':'deprecated_customer_service','kit':kit,'time':time}
    exec(compile(src,p,'exec'),ns)
    out=ns['run'](args,kit)
    if isinstance(out,dict) and isinstance(out.get('reply'),str):
        out['reply']=' '.join(out['reply'].splitlines())
    return out
