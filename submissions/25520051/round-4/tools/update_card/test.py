def test(run, kit):
    result = run({'description': '테스트 설명'}, kit)
    assert result['ok'] is True
    assert result['written'] is False
