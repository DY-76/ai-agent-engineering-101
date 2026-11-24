import httpx

def test(run, kit):
    # ledger API 모킹
    import time
    now = int(time.time())
    dummy = [
        {'buyer': '0x111', 'buyer_label': '회원1', 'shop': kit.address('shop'), 'sku': 'S1', 'qty': 1, 'price': 4000, 'recommended_by': '회원2', 'time': now-3600, 'half_price_ticket': False},
        {'buyer': '0x222', 'buyer_label': '회원2', 'shop': kit.address('shop'), 'sku': 'S3', 'qty': 1, 'price': 5000, 'recommended_by': '', 'time': now-3200, 'half_price_ticket': False},
        {'buyer': '0x111', 'buyer_label': '회원1', 'shop': kit.address('shop'), 'sku': 'S1', 'qty': 1, 'price': 3999, 'recommended_by': '회원2', 'time': now-2200, 'half_price_ticket': True},
        {'buyer': '0x333', 'buyer_label': '회원3', 'shop': kit.address('shop'), 'sku': 'S1', 'qty': 1, 'price': 4050, 'recommended_by': '회원2', 'time': now-1800, 'half_price_ticket': False},
        {'buyer': '0x444', 'buyer_label': '비회원', 'shop': '0xother', 'sku': 'S1', 'qty': 1, 'price': 4050, 'recommended_by': '', 'time': now-900, 'half_price_ticket': False},
    ]
    def fake_get(url, headers=None, timeout=None):
        class Dummy:
            def raise_for_status(self):
                pass
            def json(self):
                return dummy
        return Dummy()
    httpx.get, old = fake_get, httpx.get
    out = run({'members': ['회원1', '회원2', '회원3']}, kit)
    m1, m2, m3 = out['members']['회원1'], out['members']['회원2'], out['members']['회원3']
    assert m1['purchase_count'] == 2 and m2['purchase_count'] == 1
    assert m2['recommended_count'] == 3
    assert m1['half_price_tickets_used'] == 1
    httpx.get = old
    return True
