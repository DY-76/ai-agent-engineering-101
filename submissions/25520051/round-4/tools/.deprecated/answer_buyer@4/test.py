def test(run,kit):
 r=run({},kit)
 assert isinstance(r,dict)
 return True