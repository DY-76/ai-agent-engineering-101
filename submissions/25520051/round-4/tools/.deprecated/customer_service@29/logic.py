import os
import re

def run(args,kit):
 p='tools/.deprecated/customer_service@28/logic.py'
 if not os.path.exists(p): p='tools/customer_service/logic.py'
 g={}
 exec(open(p,encoding='utf-8').read(),g)
 t=str(args.get('text',''))
 t2=re.sub(r'(?<=[가-힣]{2})(이랑|랑|와|하고)(?=[ ,])',' ',t)
 return g['run'](dict(args,text=t2),kit)
