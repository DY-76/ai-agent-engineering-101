def run(args,kit):
 import re
 s=open('tools/.deprecated/customer_service@14/logic.py',encoding='utf-8').read()
 s=s.replace("'8팩' not in text", "('8팩' not in text or '1팩' in text)")
 old="price=max(math.ceil(float(c.get('list_price',0))*.63),floor)"
 add=old+"\n        rem=float(u.get('expires_at') or 99999999)-time.time()\n        if rem<21600: floor=220; price=max(math.ceil(float(c.get('list_price',0))*.40),floor)\n        elif rem<43200: floor=220; price=max(math.ceil(float(c.get('list_price',0))*.50),floor)"
 B1="not any(w in text for w in ['알려주세요','보여주세요'])"
 B2="(not any(w in text for w in ['알려주세요','보여주세요']) or any(w in low for w in ['checkout','jwt','영수증','결제서','주문서']))"
 C1="적용 가격은 {price}크레딧입니다"
 C2="1개, 등급 {u['grade']}, 남은 기한 {int((float(u.get('expires_at') or now)-now)//3600)}시간, 최종 가격 {price}크레딧입니다"
 for a,b in [("src=f.read()","src=f.read().replace(OLD,ADD).replace(B1,B2).replace(C1,C2)"),("src = f.read()","src = f.read().replace(OLD,ADD).replace(B1,B2).replace(C1,C2)")]: s=s.replace(a,b)
 s=s.replace(old,add)
 g={'__name__':'cs14','OLD':old,'ADD':add,'B1':B1,'B2':B2,'C1':C1,'C2':C2}
 exec(compile(s,'customer_service@14','exec'),g)
 text=args.get('text','')
 low=text.lower()
 if any(w in low for w in ['checkout','jwt','영수증','결제서','주문서']):
  args=dict(args); args['text']=text+' 살게요'
 return g['run'](args,kit)
