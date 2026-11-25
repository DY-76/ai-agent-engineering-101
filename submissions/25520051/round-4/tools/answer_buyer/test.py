def test(run,kit):
 r=run({},kit)
 assert isinstance(r,dict)
 assert r.get('testing') is True
 return True
