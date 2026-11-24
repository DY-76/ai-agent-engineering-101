import os,time,json

def run(args,kit):
 p=os.path.normpath(os.path.join(os.path.dirname(__file__),'..','customer_service','logic.py'))
 src=open(p,encoding='utf-8').read().replace('\\n','\n')
 src=src.replace("if hours < 12:","if hours < 6:\n            price=int(round(list_price*0.40))\n            floor=220\n        elif hours < 12:")
 ns={};exec(src,ns); out=ns['run'](args,kit)
 if not kit.testing:
  rec={'time':int(time.time()),'claimed_from':args.get('claimed_from'),'text':args.get('text'),'reply':out.get('reply','') if isinstance(out,dict) else str(out)}
  q=os.path.join(os.path.dirname(__file__),'inquiries.jsonl')
  with open(q,'a',encoding='utf-8') as f:f.write(json.dumps(rec,ensure_ascii=False)+'\n')
 return out
