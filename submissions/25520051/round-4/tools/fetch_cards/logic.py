import httpx

def run(args, kit):
    out={}
    for u in args.get('urls',[]):
        try:
            r=httpx.get(u,timeout=15); out[u]={'status':r.status_code,'text':r.text[:20000]}
        except Exception as e: out[u]={'error':str(e)}
    return out
