import re

def PATCH(src):
 pairs=[(r"re.split(r'[.!?\n]+',text)",r"re.split(r'[!?\n]+|\.(?!\d)',text)"),("|아니라|말고|제외')","|아니라|말고|제외|많소|많아요|많습니다|부담')"),("def score(p,ws): return sum(len(w) for w in ws if w in p.get('name','').replace(' ','').lower())","def score(p,ws):\n  n=p.get('name','').replace(' ','').lower(); b=sum(len(w) for w in ws if w in n)\n  return b+(sum(3 for z in re.findall(r'[0-9]+(?:[.][0-9]+)?(?:kg|g|구|팩|ml|l)',' '.join(sentences).lower()) if z in n) if b else 0)"),("for cut,lim in ((.52,24),(.42,12),(.32,6),(.20,3)):","for cut,lim in ((.64,24),(.54,12),(.38,6),(.20,3)):")]
 for old,new in pairs:
  assert old in src, old
  src=src.replace(old,new,1)
 return src

def run(args,kit):
 p='tools/.deprecated/customer_service@46/logic.py'
 try:
  with open(p,encoding='utf-8') as f: src=f.read()
 except FileNotFoundError:
  with open('tools/customer_service/logic.py',encoding='utf-8') as f: src=f.read()
 M="src=src.replace(prior,'prior=who in BUYERS',1)"
 assert M in src
 src=src.replace(M,M+'\n src=PATCH(src)',1)
 g={'__name__':'cs46','PATCH':PATCH}
 exec(src,g)
 args2=dict(args); text=args2.get('text','')
 if 'A등급' in text and 'B등급' not in text and 'C등급' not in text and 'A등급만' not in text:
  args2['text']=text+' A등급만'
 return g['run'](args2,kit)
