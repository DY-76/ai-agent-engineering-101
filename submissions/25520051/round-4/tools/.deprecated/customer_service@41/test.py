import httpx,time,base64,json

def test(run,kit):
 headers={'authorization':'Bearer '+kit.token('shop')}
 r=httpx.get(kit.market+'/api/inventory',headers=headers,timeout=20); r.raise_for_status(); data=r.json(); units=data.get('units',[]) if isinstance(data,dict) else []
 eligible=[u for u in units if float(u.get('expires_at',0)) >= time.time()+7200]
 assert eligible, '기한이 2시간 이상 남은 재고 unit이 없습니다.'
 sku=eligible[0]['sku']
 out=run({'text':sku+' 결제서 보내 주세요','claimed_from':'test-buyer'},kit)
 token=(out.get('data') or {}).get('checkout_jwt')
 assert token, '재고 SKU checkout_jwt가 없습니다: '+str(out)
 payload=token.split('.')[1]; payload += '='*((4-len(payload)%4)%4)
 decoded=json.loads(base64.urlsafe_b64decode(payload.encode()).decode())
 assert decoded.get('item')==sku, (decoded,sku)
 missing=run({'text':'G1dbd0b7a 결제서 보내 주세요','claimed_from':'test-buyer'},kit)
 assert 'checkout_jwt' not in str(missing), missing
 return {'ok':True,'sku':sku,'decoded_item':decoded.get('item'),'missing_sku_has_checkout':False}
