import re

def test(run,kit):
 r=run({'text':'4.5kg은 많소. 노지감귤 소과 2.5kg 결제서를 보내주이소','claimed_from':'test','history':[],'task_id':'testtask','context_id':'testctx'},kit)
 assert r and r.get('data',{}).get('checkout_jwt')
 assert '2.5kg' in r.get('reply','')
 info=run({'text':'현재 안내 가능한 상품을 알려 주세요','claimed_from':'test','history':[],'task_id':'testtask','context_id':'testctx'},kit)
 found=None
 for line in info.get('reply','').splitlines()[1:]:
  m=re.match(r'(.+?) / .*? / 등급 [ABC] / .*? / ([0-9,]+)크레딧',line)
  if m:
   found=(m.group(1),m.group(2).replace(',','')); break
 assert found, info
 bought=run({'text':f'{found[0]} {found[1]}크레딧 살게요','claimed_from':'test','history':[],'task_id':'testtask','context_id':'testctx'},kit)
 assert bought and bought.get('data',{}).get('checkout_jwt'), bought
 assert found[0] in bought.get('reply',''), bought
