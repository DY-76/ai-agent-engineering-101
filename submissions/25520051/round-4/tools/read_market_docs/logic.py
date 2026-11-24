import httpx

def run(args, kit):
    out={}
    for u in args.get('urls',[]):
        r=httpx.get(u,timeout=20)
        out[u]={'status':r.status_code,'text':r.text}
    return out
