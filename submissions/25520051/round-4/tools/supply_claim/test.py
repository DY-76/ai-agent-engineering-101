def test(run,kit):
 x=run({'quote':'test','to':'0x0','wei':'0','data':'0x','sku':'x','qty':1},kit)
 assert isinstance(x,dict)