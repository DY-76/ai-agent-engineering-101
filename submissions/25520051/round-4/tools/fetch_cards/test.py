def test(run, kit):
    x=run({'urls':['https://market.ourolabs.ai/.well-known/agent-card.json']},kit)
    assert x
