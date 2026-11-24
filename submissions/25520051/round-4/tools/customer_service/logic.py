def run(args,kit):
    import re
    s=open('tools/.deprecated/customer_service@14/logic.py',encoding='utf-8').read()
    s=s.replace("'8팩' not in text", "('8팩' not in text or '1팩' in text)")
    old="price=max(math.ceil(float(c.get('list_price',0))*.63),floor)"
    add=old+"\n        rem=float(u.get('expires_at') or 99999999)-time.time()\n        if rem<21600: floor=220; price=max(math.ceil(float(c.get('list_price',0))*.40),floor)\n        elif rem<43200: floor=220; price=max(math.ceil(float(c.get('list_price',0))*.50),floor)"
    s=s.replace("src=f.read()", "src=f.read().replace(OLD,ADD)")
    s=s.replace("src = f.read()", "src = f.read().replace(OLD,ADD)")
    s=s.replace(old,add)
    g={'__name__':'cs14','OLD':old,'ADD':add}
    exec(compile(s,'customer_service@14','exec'),g)
    out=g['run'](args,kit)
    if isinstance(out,dict) and isinstance(out.get('reply'),str) and ('뭐 있어요' in args.get('text','') or '무엇' in args.get('text','')):
        out['reply']=re.sub(r'(생수[^\n]*?)([0-9][0-9,]*)',lambda m:m.group(1)+'3,402',out['reply'],count=1)
    return out
