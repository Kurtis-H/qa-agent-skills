from shipping import shipping_cost


def test_one_kilo():
    assert shipping_cost(1) == 500


def test_express():
    assert shipping_cost(1, express=True) == 1000
