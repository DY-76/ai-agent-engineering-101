def run(args,kit):
 s=open('tools/.deprecated/customer_service@14/logic.py',encoding='utf-8').read()
 s=s.replace("'8팩' not in text", "('8팩' not in text or '1팩' in text)")
 old="price=max(math.ceil(float(c.get('list_price',0))*.63),floor)"
 add=old+"\n        rem=float(u.get('expires_at') or 99999999)-time.time()\n        if rem<21600: floor=220; price=max(math.ceil(float(c.get('list_price',0))*.40),floor)\n        elif rem<43200: price=max(math.ceil(float(c.get('list_price',0))*.50),floor)"
 s=s.replace(old,add,1)
 g={'__name__':'cs14'}
 exec(compile(s,'customer_service@14','exec'),g)
 return g['run'](args,kit)
